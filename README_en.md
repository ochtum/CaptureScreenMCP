<p align="left">
  <a href="README_en.md"><img src="https://img.shields.io/badge/English Mode-blue.svg" alt="English"></a>
  <a href="README.md"><img src="https://img.shields.io/badge/日本語 モード-red.svg" alt="日本語"></a>
</p>

# CaptureScreenMCP

A Windows screen capture MCP server.<br>
It lets you show your current screen to AI.<br>
You can use it for operation support, advice on broken layouts, and questions about error messages on screens where copy-and-paste is not available.<br>
Screen capture is implemented with `mss + Pillow + ctypes`, so no PowerShell invocation is required.<br>

Default output directory: `C:\capture_screen`.

## Tools

- `list_displays()`
  - Returns connected monitor information (`index`, `is_primary`, `x`, `y`, `width`, `height`).
- `capture_screen(output_path?: string)`
  - Captures the full virtual desktop and saves it as PNG.
- `capture_display(display?: int | "primary" | "left" | "right" | "プライマリ" | "左" | "右", output_path?: string)`
  - Captures the specified monitor and saves it as PNG. If `display` is omitted, it uses the `CAPTURE_SCREEN_DEFAULT_DISPLAY` environment variable (for example, `left`, `右`). If not set, `primary` is used.
- `capture_region(x: int, y: int, width: int, height: int, output_path?: string)`
  - Captures the specified screen region and saves it as PNG.
- `capture_active_window(output_path?: string)`
  - Captures the currently active window and saves it as PNG.
- `delete_all_capture_images()`
  - Deletes all capture image files directly under `CAPTURE_SCREEN_OUTPUT_DIR` (defaults to `C:\capture_screen`).
- `delete_capture_images_by_datetime(target_date?: string, start_datetime?: string, end_datetime?: string)`
  - Deletes capture image files by file modified time using a specific day or datetime range.
  - `target_date` uses `YYYY-MM-DD`, and `start_datetime`/`end_datetime` use `YYYY-MM-DD HH:MM[:SS]` or `YYYY-MM-DDTHH:MM[:SS]`.

## Required Python Libraries Before Running MCP

Install the following libraries (included in `requirements.txt`).

- `mcp>=1.0.0`
- `mss>=9.0.1`
- `Pillow>=10.0.0`

Install command:

```bash
python -m pip install -r requirements.txt
```

## Tool-Specific Usage Examples (Prompt Examples)

### `list_displays()`

- "Get the list of connected monitors and tell me each `index` and resolution."
- "I want to confirm which monitor is primary, so run `list_displays`."
- "Based on monitor positions (`x`, `y`), tell me whether the desktop is extended to the left or right."

### `capture_screen(output_path?: string)`

- "Capture the whole screen and save it."
- "Save the entire desktop to `C:\\capture_screen\\full_desktop.png`."
- "Capture the current multi-monitor view as one image."

### `capture_display(display?: ..., output_path?: string)`

- "Capture only the primary monitor."
- "Please check my left monitor. When I delete a CloudFormation stack, a protected bucket remains, and even if I choose 'disable', it still won't be deleted. What should I do?"
- "Capture only `display=2`."

### `capture_region(x, y, width, height, output_path?: string)`

- "Capture only the area around `protected bucket`."
- "I want only the area around the error dialog, so save that region."
- "Please check the image I just captured; it looks cropped."

### `capture_active_window(output_path?: string)`

- "Capture only the currently active window."
- "Save the currently focused app window to `C:\\capture_screen\\active_window.png`."
- "Capture only the browser window."

### `delete_all_capture_images()`

- "Delete all capture images."

### `delete_capture_images_by_datetime(target_date?, start_datetime?, end_datetime?)`

- "Delete capture images from `2026-03-04`."
- "Delete only files from `2026-03-04 09:00` to `2026-03-04 18:00`."
- "I want to delete files from `2026-03-01` through `2026-03-03`."

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

### For WSL

```toml
[mcp_servers.capture-screen]
command = "/mnt/c/MCP-PATH/CaptureScreenMCP/.venv/Scripts/python.exe"
args = ["C:\\MCP-PATH\\CaptureScreenMCP\\server.py"]
startup_timeout_sec = 30
env = { "CAPTURE_SCREEN_OUTPUT_DIR" = "C:\\MCP-PATH\\capture_screen", "WSLENV" = "CAPTURE_SCREEN_OUTPUT_DIR" }
```

### For Windows Native

```toml
[mcp_servers.capture-screen]
command = "C:\\MCP-PATH\\CaptureScreenMCP\\.venv\\Scripts\\python.exe"
args = ["C:\\MCP-PATH\\CaptureScreenMCP\\server.py"]
startup_timeout_sec = 30
```

Note: Use either `WSL format (/mnt/c/...)` or `Windows format (C:\\...)` for `command`, depending on your runtime environment.
Note: To change the default monitor target, set the `CAPTURE_SCREEN_DEFAULT_DISPLAY` environment variable (for example, `left`, `right`, `プライマリ`, `左`, `右`).
Note: To change the output directory, set the `CAPTURE_SCREEN_OUTPUT_DIR` environment variable (defaults to `C:\capture_screen` when unset).

### Codex Example for Setting Output Directory

```toml
[mcp_servers.capture-screen]
command = "/mnt/c/MCP-PATH/CaptureScreenMCP/.venv/Scripts/python.exe"
args = ["C:\\MCP-PATH\\CaptureScreenMCP\\server.py"]
startup_timeout_sec = 30
env = { "CAPTURE_SCREEN_OUTPUT_DIR" = "C:\\capture_screen" }
```

## GitHub Copilot MCP Configuration (VS Code)

Create or update `.vscode/mcp.json` with the following.

### For Windows Native

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

Add the following under `mcpServers` in `%USERPROFILE%\AppData\Roaming\Claude\claude_desktop_config.json`.

### For Windows Native

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

Add the following under `mcpServers` in `%USERPROFILE%\.claude.json`.

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
