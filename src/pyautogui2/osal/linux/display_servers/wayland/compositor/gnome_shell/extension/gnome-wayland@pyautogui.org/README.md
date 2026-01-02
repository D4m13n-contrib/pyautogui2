# PyAutoGUI GNOME Wayland Backend

This GNOME Shell extension provides a backend for PyAutoGUI on Wayland sessions. It exposes necessary information such as pointer position, display information, and keyboard layout over D-Bus, allowing PyAutoGUI to function correctly in a Wayland environment.

## Features

*   **Pointer Position:** Reports the current X and Y coordinates of the mouse pointer.
*   **Display Information:** Provides details about connected displays (resolution, position, scale).
*   **Keyboard Layout:** Exposes the current keyboard layout information.
*   **D-Bus Interface:** Communications are handled via D-Bus for seamless integration.

## Requirements

*   Linux operating system
*   GNOME Shell
*   Wayland session (`XDG_SESSION_TYPE=wayland`)
*   Python 3 (for the installation script)

## Installation

1.  **Run the installation script:**
    This script will copy the extension files to the correct GNOME Shell extensions directory, generate an authentication token, and attempt to enable the extension.
    ```bash
    python3 install_extension.py --install
    ```
    Or to update an existing installation:
    ```bash
    python3 install_extension.py --install
    ```

2.  **Enable the extension (if not automatically enabled):**
    If the installation script doesn't automatically enable the extension, you can do so manually using the GNOME Extensions utility or the command line:
    ```bash
    gnome-extensions enable gnome-wayland@pyautogui.org
    ```

3.  **Restart GNOME Shell (recommended):**
    For the changes to take effect, it's recommended to restart GNOME Shell. You can usually do this by pressing `Alt + F2`, typing `r` and pressing `Enter`. Alternatively, logging out and logging back in will also apply the changes.

## How PyAutoGUI Uses This Extension

When PyAutoGUI detects a Wayland session, it will attempt to connect to the D-Bus service provided by this extension. The extension uses an authentication token to ensure that only authorized applications (like PyAutoGUI, when properly configured) can access its D-Bus methods.

The D-Bus service name is dynamically generated, starting with `pyautogui.`, followed by a unique token. The `install_extension.py` script generates this token and stores it securely.

## D-Bus Interface

The extension registers a D-Bus object at `/org/pyautogui/Wayland`. The service name will be in the format `org.pyautogui.Wayland`.

### Methods

*   **`GetPosition()`**
    *   **Returns:** `(x: double, y: double)` - The current pointer coordinates.
*   **`GetOutputs()`**
    *   **Returns:** `(outputs: array of dictionaries)` - Information about connected displays. Each dictionary may contain:
        *   `x: integer` - The X coordinate of the display's top-left corner.
        *   `y: integer` - The Y coordinate of the display's top-left corner.
        *   `width: integer` - The display's width in pixels.
        *   `height: integer` - The display's height in pixels.
        *   `scale: double` - The display's scale factor (e.g., 1.0, 2.0).
*   **`GetKeyboardLayout()`**
    *   **Returns:** `(layout: string)` - The current keyboard layout identifier (e.g., "us", "fr").
*   **`GetAuthTokenPath()`**
    *   **Returns:** `(path: string)` - The authentication token path of the extension.

## Removal

To remove the extension, run the following command:

```bash
python3 install_extension.py --remove
```

This will disable the extension and remove its files from your local GNOME Shell extensions directory.

