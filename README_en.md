<p align="left">
  <a href="README_en.md"><img src="https://img.shields.io/badge/English Mode-blue.svg" alt="English"></a>
  <a href="README.md"><img src="https://img.shields.io/badge/日本語 モード-red.svg" alt="日本語"></a>
</p>

# CaptureScreenMCP

This is an MCP server for screen capture on Windows.<br>
It lets you show your current screen to AI.<br>
You can use it for operation support, layout issue advice, or questions about error messages on screens where copy/paste is not possible.<br>
Screen capture is implemented with `mss + Pillow + ctypes`, so no PowerShell call is required.<br>

Default output directory: `C:\capture_screen`

- Includes **Auto Hide Capture**
  - If a Windows Terminal window exists in the screenshot target area, all Windows Terminal windows in that area are hidden before capture and then restored afterward.
  - You can simply ask something like: "Can you show me how to operate the system displayed on this monitor?" The AI can hide its own CLI window before taking a screenshot, then review the screen and guide you.

## Tools

- `list_displays()`
  - Returns connected monitor info (`index`, `is_primary`, `x`, `y`, `width`, `height`).
- `capture_screen(output_path?: string)`
  - Captures the entire desktop and saves it as PNG.
- `capture_display(display?: int | "primary" | "left" | "right" | "プライマリ" | "左" | "右", output_path?: string)`
  - Captures the specified monitor and saves it as PNG. If `display` is omitted, it uses environment variable `CAPTURE_SCREEN_DEFAULT_DISPLAY` (e.g., `left`, `右`); if unset, it uses `primary`.
- `capture_region(x: int, y: int, width: int, height: int, output_path?: string)`
  - Captures the specified screen region and saves it as PNG.
- `capture_active_window(output_path?: string)`
  - Captures the currently active window and saves it as PNG.
  - Note: `capture_screen`, `capture_display`, and `capture_region` temporarily hide visible `Windows Terminal` windows that overlap the capture area until capture is complete. `capture_active_window` is excluded so terminal-window capture behavior is not broken.
- `delete_all_capture_images()`
  - Deletes all captured image files directly under `CAPTURE_SCREEN_OUTPUT_DIR` (or `C:\capture_screen` if unset).
- `delete_capture_images_by_datetime(target_date?: string, start_datetime?: string, end_datetime?: string)`
  - Deletes capture image files whose modified timestamps match the specified date or datetime range.
  - `target_date` format: `YYYY-MM-DD`; `start_datetime` / `end_datetime` format: `YYYY-MM-DD HH:MM[:SS]` or `YYYY-MM-DDTHH:MM[:SS]`.

## Required Python Libraries Before Running MCP

Install the following libraries (included in `requirements.txt`):

- `mcp>=1.0.0`
- `mss>=9.0.1`
- `Pillow>=10.0.0`

Install command:

```bash
python -m pip install -r requirements.txt
```

## Tool-Specific Usage Examples (Prompt Examples)

### `list_displays()`

- "Get the list of connected monitors and tell me the `index` and resolution."
- "Run `list_displays` so I can confirm which monitor is the primary one."
- "Check monitor layout (`x`, `y`) and tell me whether the display is extended to the left or right."

### `capture_screen(output_path?: string)`

- "Capture and save the entire screen."
- "Save the full desktop to `C:\\capture_screen\\full_desktop.png`."
- "Capture all currently visible monitors as one image."

### `capture_display(display?: ..., output_path?: string)`

- "Capture only the primary monitor."
- "I want you to check the left monitor. When I deleted a CloudFormation stack, the protected bucket remained. Even if I choose 'Disable', it still won't be deleted. What should I do?"
- "Capture only `display=2`."

### `capture_region(x, y, width, height, output_path?: string)`

- "Capture only the region that contains the `protected bucket`."
- "I only want the area around the dialog showing the error, so save the specified region."
- "Please check the image I just captured. It is cut off."

### `capture_active_window(output_path?: string)`

- "Capture only the currently active window."
- "Save the currently focused app window to `C:\\capture_screen\\active_window.png`."
- "Capture only the browser window."

### `delete_all_capture_images()`

- "Delete all captured images."

### `delete_capture_images_by_datetime(target_date?, start_datetime?, end_datetime?)`

- "Delete captured images from `2026-03-04`."
- "Delete only files in the range `2026-03-04 09:00` to `2026-03-04 18:00`."
- "I want to delete captures from `2026-03-01` through `2026-03-03`."

## Setup (Windows)

```powershell
cd C:\MCP-PATH\CaptureScreenMCP
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## Setup (WSL)

```bash
cd /mnt/c/MCP-PATH/CaptureScreenMCP
/mnt/c/Windows/py.exe -3 -m venv .venv
./.venv/Scripts/python.exe -m pip install -r requirements.txt
```

## Run (Windows)

```powershell
cd C:\MCP-PATH\CaptureScreenMCP
.\.venv\Scripts\Activate.ps1
python server.py
```

## Run (WSL)

```bash
cd /mnt/c/MCP-PATH/CaptureScreenMCP
./.venv/Scripts/python.exe server.py
```

## Codex MCP Configuration

### When using from WSL

```toml
[mcp_servers.capture-screen]
command = "/mnt/c/MCP-PATH/CaptureScreenMCP/.venv/Scripts/python.exe"
args = ["C:\\MCP-PATH\\CaptureScreenMCP\\server.py"]
startup_timeout_sec = 30
env = { "CAPTURE_SCREEN_OUTPUT_DIR" = "C:\\MCP-PATH\\capture_screen", "WSLENV" = "CAPTURE_SCREEN_OUTPUT_DIR" }
```

### When using natively on Windows

```toml
[mcp_servers.capture-screen]
command = "C:\\MCP-PATH\\CaptureScreenMCP\\.venv\\Scripts\\python.exe"
args = ["C:\\MCP-PATH\\CaptureScreenMCP\\server.py"]
startup_timeout_sec = 30
```

Note: Set `command` to either WSL style (`/mnt/c/...`) or Windows style (`C:\\...`) depending on your runtime environment.
Note: To change the default target monitor, set `CAPTURE_SCREEN_DEFAULT_DISPLAY` (e.g., `left`, `right`, `プライマリ`, `左`, `右`).
Note: To change the output directory, set `CAPTURE_SCREEN_OUTPUT_DIR` (default: `C:\capture_screen`).
Note: If you do not want to temporarily hide overlapping `Windows Terminal` windows in `capture_screen` / `capture_display` / `capture_region`, set `CAPTURE_SCREEN_HIDE_FOREGROUND_WINDOWS_TERMINAL=0`.

### Example: Specify output directory in Codex

```toml
[mcp_servers.capture-screen]
command = "/mnt/c/MCP-PATH/CaptureScreenMCP/.venv/Scripts/python.exe"
args = ["C:\\MCP-PATH\\CaptureScreenMCP\\server.py"]
startup_timeout_sec = 30
env = { "CAPTURE_SCREEN_OUTPUT_DIR" = "C:\\capture_screen" }
```

## GitHub Copilot MCP Configuration (VS Code)

Create or update `.vscode/mcp.json` and set the following.

### When using natively on Windows

```json
{
  "servers": {
    "capture-screen": {
      "command": "C:\\MCP-PATH\\CaptureScreenMCP\\.venv\\Scripts\\python.exe",
      "args": [
        "C:\\MCP-PATH\\CaptureScreenMCP\\server.py"
      ]
    }
  }
}
```

Example with `CAPTURE_SCREEN_OUTPUT_DIR`:

```json
{
  "servers": {
    "capture-screen": {
      "command": "C:\\MCP-PATH\\CaptureScreenMCP\\.venv\\Scripts\\python.exe",
      "args": [
        "C:\\MCP-PATH\\CaptureScreenMCP\\server.py"
      ],
      "env": {
        "CAPTURE_SCREEN_OUTPUT_DIR": "C:\\capture_screen"
      }
    }
  }
}
```

## Claude Desktop MCP Configuration

Add the following under `mcpServers` in `%USERPROFILE%\\AppData\\Roaming\\Claude\\claude_desktop_config.json`.

### When using natively on Windows

```json
{
  "mcpServers": {
    "capture-screen": {
      "command": "C:\\MCP-PATH\\CaptureScreenMCP\\.venv\\Scripts\\python.exe",
      "args": [
        "C:\\MCP-PATH\\CaptureScreenMCP\\server.py"
      ]
    }
  }
}
```

Example with `CAPTURE_SCREEN_OUTPUT_DIR`:

```json
{
  "mcpServers": {
    "capture-screen": {
      "command": "C:\\MCP-PATH\\CaptureScreenMCP\\.venv\\Scripts\\python.exe",
      "args": [
        "C:\\MCP-PATH\\CaptureScreenMCP\\server.py"
      ],
      "env": {
        "CAPTURE_SCREEN_OUTPUT_DIR": "C:\\capture_screen"
      }
    }
  }
}
```

## Claude Code MCP Configuration

Add the following under `mcpServers` in `%USERPROFILE%\\.claude.json`.

```json
{
  "mcpServers": {
    "capture-screen": {
      "type": "stdio",
      "command": "C:\\MCP-PATH\\CaptureScreenMCP\\.venv\\Scripts\\python.exe",
      "args": [
        "C:\\MCP-PATH\\CaptureScreenMCP\\server.py"
      ]
    }
  }
}
```

Example with `CAPTURE_SCREEN_OUTPUT_DIR`:

```json
{
  "mcpServers": {
    "capture-screen": {
      "type": "stdio",
      "command": "C:\\MCP-PATH\\CaptureScreenMCP\\.venv\\Scripts\\python.exe",
      "args": [
        "C:\\MCP-PATH\\CaptureScreenMCP\\server.py"
      ],
      "env": {
        "CAPTURE_SCREEN_OUTPUT_DIR": "C:\\capture_screen"
      }
    }
  }
}
```

## ❗This project is provided under the MIT License. See the LICENSE file for details.
