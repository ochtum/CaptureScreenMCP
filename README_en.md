# CaptureScreenMCP

A Windows screen capture MCP server.<br>
It lets you show your current screen to AI.<br>
You can use it for operation support, advice on broken layouts, and questions about error messages on screens where copy-and-paste is not available.<br>

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

### For WSL (this environment)

```toml
[mcp_servers.capture-screen]
command = "/mnt/c/MCP-PATH/CaptureScreenMCP/.venv/Scripts/python.exe"
args = ["C:\\jMCP-PATH\\CaptureScreenMCP\\server.py"]
startup_timeout_sec = 30
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

Create or update `.vscode/mcp.json` with the following:

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

Add the following to `mcpServers` in `claude_desktop_config.json`.

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
