# CaptureScreenMCP

A Windows screen capture MCP server.<br>
It lets you show your current screen to AI.<br>
You can use it for operation support, advice on broken layouts, and questions about error messages on screens where copy-and-paste is not available.<br>

Default output directory: `C:\junichi.takeda\tool\capture_screen`.

## Tools

- `list_displays()`
  - Returns connected monitor information (`index`, `is_primary`, `x`, `y`, `width`, `height`).
- `capture_screen(output_path?: string)`
  - Captures the full virtual desktop and saves it as PNG.
- `capture_display(display?: int | "primary" | "left" | "right" | "プライマリ" | "左" | "右", output_path?: string)`
  - Captures the specified monitor and saves it as PNG. If `display` is omitted, it uses the `CAPTURE_SCREEN_DEFAULT_DISPLAY` environment variable (for example, `left`, `右`). If not set, `primary` is used.
- `capture_region(x: int, y: int, width: int, height: int, output_path?: string)`
  - Captures the specified screen region and saves it as PNG.

## Setup (Windows)

```powershell
cd C:\junichi.takeda\source\CaptureScreenMCP
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Run (Windows)

```powershell
cd C:\junichi.takeda\source\CaptureScreenMCP
.\.venv\Scripts\Activate.ps1
python server.py
```

## Codex MCP Configuration

### For WSL (this environment)

```toml
[mcp_servers.capture-screen]
command = "/mnt/c/junichi.takeda/source/CaptureScreenMCP/.venv/Scripts/python.exe"
args = ["C:\\junichi.takeda\\source\\CaptureScreenMCP\\server.py"]
startup_timeout_sec = 30
```

### For Windows Native

```toml
[mcp_servers.capture-screen]
command = "C:\\junichi.takeda\\source\\CaptureScreenMCP\\.venv\\Scripts\\python.exe"
args = ["C:\\junichi.takeda\\source\\CaptureScreenMCP\\server.py"]
startup_timeout_sec = 30
```

Note: Use either `WSL format (/mnt/c/...)` or `Windows format (C:\\...)` for `command`, depending on your runtime environment.
Note: To change the default monitor target, set the `CAPTURE_SCREEN_DEFAULT_DISPLAY` environment variable (for example, `left`, `right`, `プライマリ`, `左`, `右`).

## GitHub Copilot MCP Configuration (VS Code)

Create or update `.vscode/mcp.json` with the following:

### For WSL (this environment)

```json
{
  "servers": {
    "capture-screen": {
      "command": "/mnt/c/junichi.takeda/source/CaptureScreenMCP/.venv/Scripts/python.exe",
      "args": [
        "C:\\junichi.takeda\\source\\CaptureScreenMCP\\server.py"
      ]
    }
  }
}
```

### For Windows Native

```json
{
  "servers": {
    "capture-screen": {
      "command": "C:\\junichi.takeda\\source\\CaptureScreenMCP\\.venv\\Scripts\\python.exe",
      "args": [
        "C:\\junichi.takeda\\source\\CaptureScreenMCP\\server.py"
      ]
    }
  }
}
```

## Claude Desktop MCP Configuration

Add the following to `mcpServers` in `claude_desktop_config.json`.

### For WSL (this environment)

```json
{
  "mcpServers": {
    "capture-screen": {
      "command": "/mnt/c/junichi.takeda/source/CaptureScreenMCP/.venv/Scripts/python.exe",
      "args": [
        "C:\\junichi.takeda\\source\\CaptureScreenMCP\\server.py"
      ]
    }
  }
}
```

### For Windows Native

```json
{
  "mcpServers": {
    "capture-screen": {
      "command": "C:\\junichi.takeda\\source\\CaptureScreenMCP\\.venv\\Scripts\\python.exe",
      "args": [
        "C:\\junichi.takeda\\source\\CaptureScreenMCP\\server.py"
      ]
    }
  }
}
```
