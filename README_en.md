<p align="left">
  <a href="README_en.md"><img src="https://img.shields.io/badge/English Mode-blue.svg" alt="English"></a>
  <a href="README.md"><img src="https://img.shields.io/badge/日本語 モード-red.svg" alt="日本語"></a>
</p>

# CaptureScreenMCP

<!-- mcp-name: io.github.junichi-takeda/capture-screen -->

A local MCP server for Windows (`stdio` transport).
Implemented in C# / .NET 10. It provides screen-capture and capture-file cleanup tools.

## What It Does

- Lists connected displays
- Captures full desktop, selected display, selected region, or active window as PNG
- Deletes all capture images under the output directory
- Deletes capture images by date or datetime range
- Temporarily hides overlapping `Windows Terminal` windows during `capture_screen` / `capture_display` / `capture_region` (enabled by default)

## Available Tools

- `list_displays()`
- `capture_screen(outputPath?: string)`
- `capture_display(display?: int | string, outputPath?: string)`
- `capture_region(x: int, y: int, width: int, height: int, outputPath?: string)`
- `capture_active_window(outputPath?: string)`
- `delete_all_capture_images()`
- `delete_capture_images_by_datetime(targetDate?: string, startDatetime?: string, endDatetime?: string)`

## Requirements

- Windows
- .NET 10 SDK (for local run)

## Environment Variables

- `CAPTURE_SCREEN_DEFAULT_DISPLAY`
  - Default selector when `capture_display` is called without `display`
  - Examples: `primary`, `left`, `right`, `プライマリ`, `左`, `右`, `2`
- `CAPTURE_SCREEN_OUTPUT_DIR`
  - Output directory (default: `C:\capture_screen`)
- `CAPTURE_SCREEN_HIDE_FOREGROUND_WINDOWS_TERMINAL`
  - Enable with `1/true/on`, disable with `0/false/off`
  - Enabled by default

## Local Run

### Build

```powershell
dotnet restore
dotnet build
```

### Run MCP server (stdio)

```powershell
dotnet run --project .
```

## Connection Example

### Codex / Claude Code / VS Code compatible (`stdio`)

```json
{
  "servers": {
    "capture-screen": {
      "type": "stdio",
      "command": "dotnet",
      "args": ["run", "--project", "."],
      "env": {
        "CAPTURE_SCREEN_OUTPUT_DIR": "C:\\capture_screen",
        "CAPTURE_SCREEN_DEFAULT_DISPLAY": "primary",
        "CAPTURE_SCREEN_HIDE_FOREGROUND_WINDOWS_TERMINAL": "1"
      }
    }
  }
}
```

## Publish To NuGet (Local MCP Distribution)

1. `dotnet pack -c Release`
2. `dotnet nuget push bin/Release/*.nupkg --api-key <NUGET_API_KEY> --source https://api.nuget.org/v3/index.json`

This repository includes NuGet MCP metadata:

- `.mcp/server.json`
- `<!-- mcp-name: ... -->` in `README.md`

## Permissions And Notes

- This is a local MCP server. It runs with the same user permissions as the MCP client process.
- Captures are saved as local files. Be careful not to expose sensitive information.
- Delete tools remove image files directly under `CAPTURE_SCREEN_OUTPUT_DIR`.
- Windows-only implementation. Running on non-Windows throws an error.

## Manifests

- Dev run manifest: `server.json`
- NuGet MCP manifest: `.mcp/server.json`
