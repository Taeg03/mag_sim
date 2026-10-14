# Magnetic Sensor Array Simulation

This repository studies magnetic-field detection and source observability for a planar sensor array. The core model is a magnetic dipole evaluated at sensor locations. Most experiments use a 3 x 3 array and the measured vertical field component, `Bz`.

## Repository Layout

- `src/`: reusable dipole-field and sensor-array functions.
- `experiments/`: standalone Python experiments. Each script computes one study and saves its figures.
- `figures/`: generated figures organized by experiment script.
- `ref/`: reference work, data, and legacy project material.

The scripts currently save figures using relative filenames. Run a script from the repository root if you want new outputs to appear there, then move or copy them into the corresponding `figures/<experiment>/` directory.

## Interactive frontend

The first frontend integration lives in `frontend/`. It keeps the canvas visualization
in the browser while obtaining the nine sensor field values from the Python analytical
dipole model.

### View on the same computer

From the repository root, start the server:

```bash
./.venv/bin/python -m frontend.server
```

Keep this terminal running, then open <http://127.0.0.1:8000> in a browser on the
same computer. Stop the server with `Ctrl+C`.

Port `8000` may already be used by another application. In that case, choose an
available port:

```bash
FRONTEND_PORT=8765 ./.venv/bin/python -m frontend.server
```

Then open <http://127.0.0.1:8765>. The browser must use the same port as the
server. Do not open `frontend/index.html` directly from the filesystem because
the page needs the Python `/api/simulate` endpoint.

This initial slice intentionally uses the ideal point-dipole backend. Magpylib,
noise, localization, and finite-source options can be added behind the same API
as later increments.

## Common Concepts

### Dipole Field Equations & 1/r³ Scaling

The core physical model is an ideal point magnetic dipole:

$$\mathbf{B}(\mathbf{r}) = \frac{\mu_0}{4\pi}\left( \frac{3(\mathbf{m}\cdot\mathbf{r})\mathbf{r}}{r^5} - \frac{\mathbf{m}}{r^3} \right)$$

where $\mathbf{r} = \mathbf{r}_{\mathrm{sensor}} - \mathbf{r}_{\mathrm{source}}$, $r = \|\mathbf{r}\|_2$, and $\mu_0 / (4\pi) = 10^{-7}\text{ T}\cdot\text{m/A}$.

For a vertical dipole ($\mathbf{m} = [0, 0, m]$) on the z-axis, the vertical field component $B_z$ directly on-axis decays as an inverse-cube:

$$B_z = \frac{\mu_0}{4\pi}\frac{2m}{z^3}$$

Field magnitude decays as $1/r^3$, while spatial field gradients across the array decay as $1/r^4$. Consequently, spatial localization information diminishes significantly faster with distance than absolute signal strength.

### Localization Uncertainty (Fisher Information & CRLB)

When estimating source position $\mathbf{r} = [x, y, z]^T$ with known moment and independent sensor noise $\sigma_B$, the Fisher Information Matrix (FIM) and Cramér-Rao Lower Bound (CRLB) covariance are:

$$F = \frac{1}{\sigma_B^2} J^T J, \quad \mathbf{C}_{\mathbf{r}} = F^{-1} = \sigma_B^2 (J^T J)^{-1}$$

where $J = \frac{\partial \mathbf{B}_z}{\partial [x, y, z]} \in \mathbb{R}^{9 \times 3}$. The 1-sigma 3D position uncertainty is $\sigma_{\mathrm{pos}} = \sqrt{\mathrm{Tr}(\mathbf{C}_{\mathbf{r}})}$, which scales linearly with sensor noise $\sigma_B$.

### Detection

A source is detectable when at least one sensor has a vertical field magnitude above the configured hardware threshold. Most experiments use:

```text
detection_threshold = 10e-9 T (10 nT)
```

The detection test is based on `max(abs(Bz))` across the array. A detectable signal is not necessarily sufficient for reliable localization.

### Conditioning and observability

The experiments form a numerical Jacobian of the sensor measurements with respect to six source parameters:

```text
x, y, z position and mx, my, mz magnetic moment
```

The normalized Jacobian's singular values describe how strongly different parameter combinations affect the measurements. Its condition number is:

```text
kappa = largest singular value / smallest singular value
```

Lower `kappa` is better. The spatial observability experiments use `kappa <= 100` as the well-conditioned criterion. A small smallest singular value indicates a weakly observable parameter direction.

### Sensing classification

The sensing-volume experiment combines both tests:

| Class | Meaning |
| --- | --- |
| 0 | Not detectable: every sensor is below the field threshold. |
| 1 | Detectable but poorly conditioned: signal is above threshold, but `kappa > 100`. |
| 2 | Detectable and well conditioned: signal is above threshold and `kappa <= 100`. |

## Experiments and Figure Outputs

### `visualize_bz_field.py`

Output directory: `figures/visualize_bz_field/`

- `bfield.png`: heatmap of $B_z$ measured across the 3 x 3 sensor array for a vertical dipole ($m = 1\text{ A}\cdot\text{m}^2$ along $+z$) positioned at height $z = 0.20\text{ m}$ (20 cm) directly above the array center $(0, 0, 0)$. The 3 x 3 pixel grid directly represents the discrete vertical field component $B_z$ at each of the 9 sensors.

### `distance_sweep.py`

Output directory: `figures/distance_sweep/`

- `distance_sweep.png`: center-sensor field magnitude versus source distance, confirming the expected $1/r^3$ dipole field decay (fitted log-log slope $-3.0000$).
- `spatial_variation.png`: difference between maximum and minimum field across the array ($\max B_z - \min B_z$) versus distance, illustrating that spatial gradient information decays as $1/r^4$.

### `detection_range.py`

Output directory: `figures/detection_range/`

- `detection_range.png`: center-sensor $|B_z|$ versus distance with the 10 nT detection threshold marked. A marker highlights the intersection point at $z = 2.70\text{ m}$ (analytical: 2.714 m), where the center sensor drops below hardware detection limits.

### `moment_sweep.py`

Output directory: `figures/moment_sweep/`

- `moment_sweep.png`: maximum detection range versus dipole moment magnitude ($10^{-3}$ to $10^3\text{ A}\cdot\text{m}^2$). Confirms the theoretical cube-root scaling $r_{\mathrm{det}} \propto m^{1/3}$ (fitted log-log slope $0.3350$).

### `spacing_sweep.py`

Output directory: `figures/spacing_sweep/`

- `spacing_detection_range.png`: maximum detection distance versus physical sensor spacing for vertical ($0^\circ$) and horizontal ($90^\circ$) dipoles.

For vertical dipoles, the peak field across the array always occurs at the center sensor $(0, 0, 0)$. Because the center sensor's position is fixed regardless of sensor spacing $s$, the detection distance remains invariant at $2.714\text{ m}$. For horizontal dipoles, $B_z = 0$ along the z-axis by symmetry; detection relies entirely on off-axis outer sensors, which expand outward with wider spacing, increasing detection range from 0.74 m to 2.05 m.

### `operating_range.py`

Output directory: `figures/operating_range/`

- `orientation_detection_range.png`: maximum detectable distance versus dipole orientation tilt angle, from vertical ($0^\circ$) to horizontal ($90^\circ$).
- `orientation_field_ratio.png`: 2D heatmap of $\log_{10}(\max|B_z| / B_{\mathrm{threshold}})$ with two swept independent variables: source distance $z$ (horizontal axis) and dipole tilt angle $\theta$ (vertical axis). Values above 0 exceed the 10 nT threshold; the dashed black contour at 0 marks the detection threshold boundary.

### `jacobian_analysis.py`

Output directory: `figures/jacobian_analysis/`

- `jacobian_singular_values.png`: singular values of the measurement Jacobian at fixed source configuration ($z = 0.20\text{ m}$, $m = 1\text{ A}\cdot\text{m}^2$ along $+z$).

**Note on Singular Value Index:** The index (1 through 6) does **not** correspond to individual parameters ($x, y, z, m_x, m_y, m_z$). SVD decomposes the Jacobian into ordered principal sensitivity modes $\sigma_1 \ge \dots \ge \sigma_6$. Each singular value represents an orthogonal linear combination of parameters (right singular vector $\mathbf{v}_i$): $\sigma_1$ is predominantly vertical position $z$, $\sigma_2$ and $\sigma_3$ correspond to lateral positions $(x, y)$, $\sigma_4$ corresponds to vertical moment $m_z$, and $\sigma_5, \sigma_6$ represent transverse moment tilts $(m_x, m_y)$, which are the weakest observable directions by over four orders of magnitude.

### `aperture_observability.py`

Output directory: `figures/aperture_observability/`

- `aperture_condition_number.png`: normalized condition number versus aperture-to-depth ratio $L/z$, for a fixed source depth $z = 0.20\text{ m}$ (20 cm) and swept aperture $L = 2s \in [0.01, 2.0]\text{ m}$.
- `aperture_smallest_singular_value.png`: smallest normalized singular value versus $L/z$ at fixed $z = 0.20\text{ m}$.

Conditioning exhibits a convex minimum around $L/z \approx 1.0 - 2.0$. Arrays that are too small ($L/z \ll 1$) cannot resolve spatial derivatives, while arrays that are too large ($L/z \gg 2$) place outer sensors too far away into noise.

### `aperture_robustness.py`

Output directory: `figures/aperture_robustness/`

- `robustness_best_condition.png`: best condition number anywhere in the lateral region ($x/z, y/z \in [-2, 2]$).
- `robustness_median_condition.png`: median condition number across the region.
- `robustness_good_fraction.png`: fraction of the region with $\kappa < 100$.

**Why Curves Overlap:** Curves for different depths $z$ overlap perfectly because the normalized Jacobian condition number is dimensionless and scale-invariant. When lateral coordinates and array aperture are scaled proportionally to depth ($L/z = \mathrm{const}, x/z = \mathrm{const}$), physical scale $z$ cancels completely in the singular value ratio $\kappa = \sigma_{\max} / \sigma_{\min}$. Plotting across multiple depths proves that observability is governed strictly by the dimensionless ratio $L/z$, not absolute size.

### `scaled_aperture_observability.py`

Output directory: `figures/scaled_aperture_observability/`

- `scaled_best_condition.png`: best condition number versus $L/z$.
- `scaled_best_smallest_sv.png`: best smallest singular value versus $L/z$.

Mathematically, array aperture and lateral search coordinates are scaled proportionally to depth ($L = \mathrm{ratio} \cdot z$, $x = (x/z) \cdot z$). The resulting condition numbers are mathematically identical across all depths $z$ (e.g., $\kappa = 22.258$ at $L/z = 2.0$), confirming scale invariance.

### `observability_map.py`

Output directory: `figures/observability_map/`

Each figure is an x-y cross-section at fixed depth $z \in \{0.10, 0.20, 0.50, 1.00\}\text{ m}$.

- `observability_condition_z*.png`: heatmap of $\log_{10}(\kappa)$.
- `observability_smallest_sv_z*.png`: heatmap of $\log_{10}(\sigma_{\min})$.
- `detectability_z*.png`: heatmap of $\log_{10}(\max|B_z| / B_{\mathrm{threshold}})$.
- `detection_region_z*.png`: binary detectable mask.
- `practical_observability_z*.png`: combined mask requiring detection and $\kappa \le 100$.

Detection masks are uniformly 1 because a $1\text{ A}\cdot\text{m}^2$ dipole produces signals $> 10\text{ nT}$ across the entire $1\text{ m} \times 1\text{ m}$ region at these depths. However, practical observability ($\kappa \le 100$) drops to 0% beyond $z = 0.30\text{ m}$ for this 20 cm aperture array. Note: simulations use the ideal point dipole approximation; finite-magnet multipole near-field effects (relevant when $z \lesssim \text{magnet size}$) are not modeled.

### `moment_aperture_tradeoff.py`

Output directory: `figures/moment_aperture_tradeoff/`

- `moment_tradeoff_z*.png`: fraction of lateral area both detectable and well conditioned ($\kappa \le 100$) versus $L/z$.

Curves for small moments ($m \le 10^{-2}\text{ A}\cdot\text{m}^2$) at depths $z \ge 0.5\text{ m}$ are identically zero because the dipole field drops below 10 nT across the entire lateral area.

### `sensing_volume.py`

Output directory: `figures/sensing_volume/`

- `sensing_m*_z*.png`: 3D volumetric slices classified into Class 0 (not detectable), Class 1 (detectable, $\kappa > 100$), and Class 2 (detectable, $\kappa \le 100$).

Well-conditioned points (Class 2) only appear close to the array ($z \le 0.4\text{ m}$, such as $z = 0.05\text{ m}$) because for a fixed 20 cm array, depths $z > 0.4\text{ m}$ have $L/z < 0.5$, which is geometrically too narrow to achieve $\kappa \le 100$ anywhere in space.

### `aperture_depth_ratio_sweep.py`

Output directory: `figures/aperture_depth_ratio_sweep/`

- `aperture_depth_median_uncertainty.png`: median 1-sigma 3D position uncertainty versus aperture-to-depth ratio $L/z$.
- `aperture_depth_p90_uncertainty.png`: 90th percentile position uncertainty versus $L/z$.

Evaluates Cramér-Rao lower bounds on 3D localization error derived from the Fisher Information Matrix $F = \frac{1}{\sigma_B^2} J^T J$ and covariance $\mathbf{C} = F^{-1}$.

### `localization_aperture_map.py`

Output directory: `figures/localization_aperture_map/`

- `localization_z*.png`: 2D lateral heatmaps comparing 3D position uncertainty across physical array apertures ($L = 0.05$ to $0.80\text{ m}$) at fixed source depth $z$. Contours mark 5 cm and 10 cm uncertainty thresholds.

Heatmaps appear visually uniform at low depth ($z = 0.10\text{ m}$) because uncertainties are sub-millimeter on the fixed $0 - 50\text{ cm}$ color scale (dark purple), whereas at $z = 1.00\text{ m}$ uncertainties exceed 50 cm across much of the plane and clip to the upper color limit.

### `find_static_ambiguity.py`

Output directory: `figures/find_static_ambiguity/`

- `static_ambiguity_map.png`: heatmap of relative residual RMSE across candidate source locations when fitting the best magnetic moment to match a centered vertical dipole.
- `ambiguity_pair.npz`: saved reference and candidate dipole parameters demonstrating sub-threshold (3.07 nT) measurement residuals.

Calculates measurement RMSE across all 9 sensors between a reference vertical dipole at $(0, 0, 0.50)\text{ m}$ and candidate dipoles at $(x, y, 0.50)\text{ m}$ with optimal least-squares moment fitting. The central blank circle is an intentional 5 cm exclusion radius around the reference source to prevent trivial self-matching ($\Delta r \to 0$).

### `motion_breaks_ambiguity.py`

Output directory: `figures/motion_breaks_ambiguity/`

- `measurement_separation.png`: measurement RMSE between the statically ambiguous dipole pair as the array translates laterally.
- `sensor_measurements.png`: individual sensor traces demonstrating how array motion breaks static degeneracy.

Simulates array translation along x (quasi-static spatial synthetic aperture). Solid lines represent sensors 0 through 8 for Source A (centered vertical), and dashed lines represent Source B (off-center tilted). At $x = 0$, both sources produce nearly identical measurements ($<3.07\text{ nT}$ RMSE); as the array translates, measurements diverge by over $102\text{ nT}$.

### `moving_array_observability.py`

Output directory: `figures/moving_array_observability/`

- `singular_values.png`: normalized singular values $\sigma_1$ through $\sigma_6$ for static, z-translation, and x-translation array trajectories.
- `condition_numbers.png`: comparison of normalized Jacobian condition numbers across motion modes.

Evaluates a multi-pose stacked Jacobian ($189 \times 6$) formed by accumulating 21 array poses along a trajectory. Translation along z elevates the weakest normalized singular value by $21.7\times$ (from $2.26 \times 10^{-8}$ to $4.89 \times 10^{-7}$), reducing the normalized condition number from 530 to 136.

## How to Read the Results

- Detection plots answer: is the magnetic signal large enough?
- Conditioning plots answer: can different source parameters be distinguished reliably?
- Spatial maps answer: where in the operating region does each condition hold?
- Aperture and spacing studies answer: how should the sensor geometry be designed?
- Moment and orientation studies answer: how do source strength and orientation change the operating envelope?
- Sensing-volume plots answer: where is the source both detectable and reliably estimable?
- Ambiguity and motion studies answer: can static degeneracies be resolved by synthetic aperture movement?

## Experiments Without Current Figure Outputs

The following scripts are present but do not currently correspond to saved figures in `figures/`:

- `first_dipole_test.py`
- `noise_test.py`
- `localization_accuracy.py`
