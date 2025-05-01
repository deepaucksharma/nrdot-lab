# Changelog

All notable changes to this project will be documented in this file.

## [v11.0.0] – 2025-05-05
* Fixed Compose seccomp interpolation with overrides.
* Added documentation for full-host mount risks.
* Ensured seccomp profile allows all necessary syscalls.
* Provided guidance for re-enabling `docker_stats`.
* Added `strace` to `load-image` for debugging.

## [v10.0.0] – 2025-04-15
* Initial release with basic functionality.
* Added New Relic Infrastructure and OTel integration.
* Implemented synthetic load generation.
* Created validation and smoke test scripts.