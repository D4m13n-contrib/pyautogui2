# Changelog

All notable changes to PyAutoGUI2 will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-01-02

### Initial Release - Complete Rewrite

PyAutoGUI2 is a complete rewrite of the original PyAutoGUI library with a modern, object-oriented architecture.

#### Added
- **Modern OOP Architecture**: Complete rewrite using object-oriented programming principles
- **OSAL (OS Abstraction Layer)**: Modular platform abstraction for better maintainability
- **Full Wayland Support**: Native support for Wayland via GNOME Shell extension
- **Multi-Desktop Linux Support**: Support for GNOME, KDE, XFCE, and other desktop environments
- **Type Hints**: Full type annotations for better IDE support and code quality
- **Improved Error Handling**: Better exception handling and error messages
- **Modern Testing**: Comprehensive test suite with pytest
- **Automatic Platform Detection**: Intelligent platform and desktop environment detection
- **Command-line Tools**: CLI utilities for extension installation and platform detection

#### Changed
- **Breaking Change**: Package renamed from `pyautogui` to `pyautogui2`
- **API**: Modernized API while maintaining compatibility where possible
- **Dependencies**: Updated to modern dependency versions
- **Build System**: Migrated from setup.py to pyproject.toml

#### Technical Details
- Minimum Python version: 3.10+
- License: BSD-3-Clause (same as original PyAutoGUI)
- Architecture: Modular OSAL design with platform-specific implementations

---

## About This Project

PyAutoGUI2 is a fork and complete rewrite of [PyAutoGUI](https://github.com/asweigart/pyautogui) by Al Sweigart.
This project maintains the spirit of the original while modernizing the codebase and adding support for modern
Linux desktop environments, particularly Wayland.

### Credits
- Original PyAutoGUI: Al Sweigart
- PyAutoGUI2 Rewrite: Damien A.
