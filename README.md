# TopWindow

TopWindow is a lightweight Python utility that allows users to keep any application window on top of other windows. This tool is particularly useful when you need to reference information from one application while working in another, ensuring important windows remain visible at all times.

## Features

- Keep any window on top of all other applications
- Restore windows to their normal behavior
- Launch GUI version with modern interface
- Simple command-line interface
- Support for selecting multiple windows at once
- Automatic cleanup of window states on exit
- Persistent storage of previously selected windows

## Requirements

- Windows operating system
- Python 3.6 or higher
- Required Python packages:
  - `pygetwindow`
  - `pywin32`
  - `Pillow` (for GUI version)
  - `pystray` (for system tray integration)

## Installation

1. Clone or download this repository
2. Install the required dependencies:
   ```
   pip install pygetwindow pywin32 Pillow pystray
   ```

## Usage

Run the application from the command line:
```
python top_window.py
```

### Menu Options

1. **Keep window(s) on top**: Select one or more windows to keep on top of all other windows
2. **Restore window(s) from top**: Return selected windows to normal behavior
3. **Launch GUI version**: Open the modern graphical user interface
4. **Exit program**: Close the application and restore all windows to normal behavior

### Selecting Windows

When choosing windows, you can:
- Enter individual window numbers separated by commas (e.g., `1,3,5`)
- Type `all` to select all displayed windows
- Press Enter without input to return to the main menu

## How It Works

TopWindow uses the Windows API through the `pywin32` library to modify window positioning properties. When a window is set to "always on top," the application sets the window's position to `HWND_TOPMOST`, which instructs Windows to keep that window above all others.

On exit or when restoring windows, the application sets the window position to `HWND_NOTOPMOST`, returning it to normal stacking behavior.

Selected window titles are stored in a JSON file for persistence between sessions.

## GUI Version

The GUI version provides a modern, intuitive interface with the following features:
- Visual representation of windows with icons
- Single-click to toggle windows on top
- Right-click to minimize windows
- System tray integration
- Drag and drop positioning
- Automatic edge snapping
- Window persistence between sessions

## Building Executable

To create a standalone executable, you can use PyInstaller with the provided spec file:

```
pyinstaller top_window.spec
```

Note: You may need to update the spec file to match the correct script name if needed.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.