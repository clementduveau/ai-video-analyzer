# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog, and this project adheres to Semantic Versioning.

## [Unreleased]
### Added
- GitHub Actions CI to run tests on PRs and pushes to `main`
- Issue and PR templates to standardize contributions

### Changed
- Moved `docs/QUICKSTART.md` to `QUICKSTART.md` at repo root and updated links

## [2.3.0] - 2025-12-18
### Added
- Docker deployment smoke tests (build, compose, container start, volumes, env vars)

### Fixed
- Port conflict handling for Docker tests (standard 8501 mapping with graceful skip)
- Docker BuildKit output detection in tests

## [2.1.0] - 2025-12-??
### Added
- End-to-end test suite and documentation

## [2.0.2] - 2025-??-??
### Fixed
- Stability and minor fixes

---

Links:
- [Unreleased]: https://github.com/dsmilne3/ai-video-analyzer/compare/v2.3.0...HEAD
- [2.3.0]: https://github.com/dsmilne3/ai-video-analyzer/releases/tag/v2.3.0
- [2.1.0]: https://github.com/dsmilne3/ai-video-analyzer/releases/tag/v2.1.0
