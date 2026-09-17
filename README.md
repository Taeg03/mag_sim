# Magnetic Sensor Array Simulation

This repository studies magnetic-field detection and source observability for a planar sensor array. The core model is a magnetic dipole evaluated at sensor locations. Most experiments use a 3 x 3 array and the measured vertical field component, `Bz`.

## Repository Layout

- `src/`: reusable dipole-field and sensor-array functions.
- `experiments/`: standalone Python experiments. Each script computes one study and saves its figures.
- `figures/`: generated figures organized by experiment script.
- `ref/`: reference work, data, and legacy project material.

The scripts currently save figures using relative filenames. Run a script from the repository root if you want new outputs to appear there, then move or copy them into the corresponding `figures/<experiment>/` directory.

## Common Concepts

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

- `bfield.png`: heatmap of `Bz` over a 3 x 3 sensor array for one fixed dipole position and orientation.

This is a basic field-pattern sanity check. It does not measure detection range or inversion quality.

### `distance_sweep.py`

Output directory: `figures/distance_sweep/`

- `distance_sweep.png`: center-sensor field magnitude versus source distance.
- `spatial_variation.png`: difference between the maximum and minimum field across the array versus distance.

These plots show dipole-field decay and how spatial variation, which carries localization information, decreases with distance. The script also fits the field decay on log-log axes and compares it with the expected inverse-cube behavior.

### `detection_range.py`

Output directory: `figures/detection_range/`

- `detection_range.png`: center-sensor `|Bz|` versus distance with the detection threshold marked.

The threshold crossing gives the maximum detection distance for one fixed dipole moment and array configuration. This is a signal-strength result, not a conditioning result.

### `moment_sweep.py`

Output directory: `figures/moment_sweep/`

- `moment_sweep.png`: maximum detection range versus dipole moment magnitude.

Stronger moments produce stronger fields and longer detection ranges. The expected dipole scaling is approximately:

```text
maximum range proportional to moment magnitude^(1/3)
```

The script fits a log-log slope to check this relationship.

### `spacing_sweep.py`

Output directory: `figures/spacing_sweep/`

- `spacing_detection_range.png`: maximum detection distance versus sensor spacing.

The plot compares vertical and horizontal dipole orientations. It asks how physical sensor spacing affects the distance at which the array can detect a source. It does not calculate Jacobian conditioning.

### `operating_range.py`

Output directory: `figures/operating_range/`

- `orientation_detection_range.png`: maximum detectable distance versus dipole orientation, from vertical (`0` degrees) to horizontal (`90` degrees).
- `orientation_field_ratio.png`: map of `log10(max(|Bz|) / threshold)` over distance and orientation.

In the field-ratio map, values above zero exceed the detection threshold and values below zero are undetectable. These are orientation-dependent detection plots; they do not evaluate source-parameter conditioning.

The same directory also contains older outputs named `operating_range.png` and `operating_range_field.png`.

### `jacobian_analysis.py`

Output directory: `figures/jacobian_analysis/`

- `jacobian_singular_values.png`: singular values of the measurement Jacobian at one selected source configuration.

A small singular value identifies a weak parameter combination. A large gap between the largest and smallest singular values indicates poor conditioning. This is a local diagnostic rather than a spatial sweep.

### `aperture_observability.py`

Output directory: `figures/aperture_observability/`

- `aperture_condition_number.png`: normalized condition number versus aperture-to-depth ratio, `L/z`.
- `aperture_smallest_singular_value.png`: smallest normalized singular value versus `L/z`.

The experiment varies array aperture while keeping source depth fixed. It asks how large the array should be relative to source distance for local observability. Lower condition number and higher smallest singular value are favorable.

### `aperture_robustness.py`

Output directory: `figures/aperture_robustness/`

- `robustness_best_condition.png`: best condition number anywhere in the lateral source region.
- `robustness_median_condition.png`: median condition number across the region.
- `robustness_good_fraction.png`: fraction of the region with `kappa < 100`.

Each curve represents a different source depth. The good-fraction plot is usually the most useful design summary because it measures how much of the operating region is well conditioned rather than showing only a best-case location.

### `scaled_aperture_observability.py`

Output directory: `figures/scaled_aperture_observability/`

- `scaled_best_condition.png`: best condition number versus `L/z`.
- `scaled_best_smallest_sv.png`: best smallest singular value versus `L/z`.

This experiment scales array aperture and source depth together. It tests whether observability is primarily controlled by the dimensionless geometry ratio `L/z`, rather than by absolute physical size.

### `observability_map.py`

Output directory: `figures/observability_map/`

Each figure is an `x-y` cross-section at a fixed source depth `z`.

- `observability_condition_z*.png`: heatmap of `log10(kappa)`. Lower values are better conditioned.
- `observability_smallest_sv_z*.png`: heatmap of `log10(sigma_min)`. Higher values indicate stronger weakest-direction observability.
- `detectability_z*.png`: heatmap of `log10(max(|Bz|) / threshold)`. Positive values exceed the threshold.
- `detection_region_z*.png`: binary detectable/not-detectable mask.
- `practical_observability_z*.png`: combined mask requiring detection and `kappa <= 100`.

These plots separate signal strength from parameter-estimation quality and then show the combined usable region. The `z` value is encoded in each filename.

The older `observability_rank_z*.png` files are in `figures/observability_map/legacy/`. They show numerical Jacobian rank and are not generated by the current version of the script.

### `moment_aperture_tradeoff.py`

Output directory: `figures/moment_aperture_tradeoff/`

- `moment_tradeoff_z*.png`: fraction of the lateral region that is both detectable and well conditioned versus `L/z`.

Each plot corresponds to one source depth, and each curve corresponds to a different moment magnitude. These figures combine source strength and array geometry into a practical design tradeoff.

### `sensing_volume.py`

Output directory: `figures/sensing_volume/`

- `sensing_m*_z*.png`: `x-y` classification slices for one moment magnitude and one source depth.

The color classes are the combined detection and conditioning result:

```text
0 = not detectable
1 = detectable but poorly conditioned
2 = detectable and well conditioned
```

These are the most complete spatial figures because they show where a source can both produce a measurable signal and be estimated reliably. The moment magnitude and depth are encoded in each filename.

## How to Read the Results

- Detection plots answer: is the magnetic signal large enough?
- Conditioning plots answer: can different source parameters be distinguished reliably?
- Spatial maps answer: where in the operating region does each condition hold?
- Aperture and spacing studies answer: how should the sensor geometry be designed?
- Moment and orientation studies answer: how do source strength and orientation change the operating envelope?
- Sensing-volume plots answer: where is the source both detectable and reliably estimable?

## Experiments Without Current Figure Outputs

The following scripts are present but do not currently correspond to saved figures in `figures/`:

- `first_dipole_test.py`
- `noise_test.py`
- `localization_accuracy.py`

