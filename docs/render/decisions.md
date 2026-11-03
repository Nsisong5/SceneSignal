# SceneSignal Render Module — Architecture Decisions

- **D-R01**: Separate sub-package `scene_signal.render` with zero cross-module imports between Module 01 and Module 02.
- **D-R02**: Strict JSON parsing (K-10) rejecting NaN, Infinity, duplicate keys, trailing data, oversize (>1 MiB), and float precision violations (>6 decimal places without snapping).
- **D-R03**: Exact rational math (`Fraction`) for time and frame rates.
