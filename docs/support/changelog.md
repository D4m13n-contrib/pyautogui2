# Changelog

All notable changes to PyAutoGUI2 will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

> This section tracks changes not yet released. It will be split into versioned
> entries as releases are published.

### Added
- Complete rewrite of PyAutoGUI with a new component-based architecture
- Cross-platform support: Windows, MacOS, Linux (X11 and Wayland)
- New controller API: `screen`, `keyboard`, `pointer`, `dialogs`
- Wayland support via UInput and GNOME Shell extension
- Strict type hints throughout the codebase
- Comprehensive documentation

### Changed
- API structure — see [Migration Guide](../get-started/migration-v1-v2.md)
- Improved error handling
- Better multi-monitor support

### Deprecated
- Legacy PyAutoGUI v1 API (still available via the compatibility layer)

### Removed
- Python 2 support — Python 3.10+ is now required

---

## [2.0.0] - TBD

_First stable release of PyAutoGUI2._

See the [Migration Guide](../get-started/migration-v1-v2.md) for a full
overview of breaking changes from PyAutoGUI v1.

---

## Notes

- This file will be updated with each release going forward.
- For PyAutoGUI v1 history, see the [legacy documentation](https://pyautogui.readthedocs.io/).
- For contributing, see the [Contributing Guide](contributing.md).
