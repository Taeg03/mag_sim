"""Small local web server for the ideal-dipole frontend."""

from __future__ import annotations

import json
import os
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

import numpy as np

from src.array import create_planar_array
from src.dipole import dipole_field


FRONTEND_DIR = Path(__file__).resolve().parent
DETECTION_THRESHOLD = 10e-9


def _number(value: Any, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a number")
    result = float(value)
    if not np.isfinite(result):
        raise ValueError(f"{name} must be finite")
    return result


def _vector(value: Any, name: str) -> list[float]:
    if not isinstance(value, list) or len(value) != 3:
        raise ValueError(f"{name} must contain exactly 3 numbers")
    return [_number(item, name) for item in value]


def simulate(payload: dict[str, Any]) -> dict[str, Any]:
    """Calculate ideal-dipole field vectors and vertical sensor readings."""
    source_position = np.asarray(
        _vector(payload.get("source_position"), "source_position"),
        dtype=float,
    )
    moment = np.asarray(_vector(payload.get("moment"), "moment"), dtype=float)
    spacing = _number(payload.get("sensor_spacing", 0.10), "sensor_spacing")
    if spacing <= 0:
        raise ValueError("sensor_spacing must be greater than zero")

    sensors = create_planar_array(3, 3, spacing)
    fields = dipole_field(sensors, source_position, moment)
    bz = fields[:, 2]

    return {
        "sensor_positions_m": sensors.tolist(),
        "field_vectors_t": fields.tolist(),
        "bz_t": bz.tolist(),
        "max_abs_bz_t": float(np.max(np.abs(bz))),
        "detection_threshold_t": DETECTION_THRESHOLD,
        "detectable": bool(np.max(np.abs(bz)) >= DETECTION_THRESHOLD),
    }


class FrontendHandler(SimpleHTTPRequestHandler):
    """Serve the frontend and expose its simulation endpoint."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, directory=str(FRONTEND_DIR), **kwargs)

    def do_GET(self) -> None:
        if self.path == "/health":
            self._send_json({"status": "ok"})
            return
        super().do_GET()

    def do_POST(self) -> None:
        if self.path != "/api/simulate":
            self._send_json({"error": "not found"}, status=404)
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length))
            if not isinstance(payload, dict):
                raise ValueError("request body must be a JSON object")
            response = simulate(payload)
        except (ValueError, json.JSONDecodeError) as exc:
            self._send_json({"error": str(exc)}, status=400)
            return

        self._send_json(response)

    def _send_json(self, payload: dict[str, Any], status: int = 200) -> None:
        encoded = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(encoded)

    def log_message(self, format: str, *args: Any) -> None:
        print(f"[frontend] {format % args}")


def main() -> None:
    host = os.environ.get("FRONTEND_HOST", "127.0.0.1")
    port = int(os.environ.get("FRONTEND_PORT", "8000"))
    server = ThreadingHTTPServer((host, port), FrontendHandler)
    display_host = "127.0.0.1" if host in {"0.0.0.0", "::"} else host
    print(f"Frontend available at http://{display_host}:{port}")
    print("Press Ctrl-C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping frontend server.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
