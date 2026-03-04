from __future__ import annotations

import json
import os
import subprocess
from datetime import date, datetime, time
from pathlib import Path

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("capture-screen-mcp")
DEFAULT_DISPLAY_ENV = "CAPTURE_SCREEN_DEFAULT_DISPLAY"
OUTPUT_DIR_ENV = "CAPTURE_SCREEN_OUTPUT_DIR"
DEFAULT_OUTPUT_DIR = Path(r"C:\capture_screen")
CAPTURE_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp"}


def _ensure_windows() -> None:
    if os.name != "nt":
        raise RuntimeError("This MCP server only works on Windows.")


def _ps_quote(value: str) -> str:
    return value.replace("'", "''")


def _run_powershell(script: str) -> str:
    proc = subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            script,
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if proc.returncode != 0:
        msg = proc.stderr.strip() or proc.stdout.strip() or "PowerShell execution failed"
        raise RuntimeError(msg)
    return proc.stdout.strip()


def _default_output_dir() -> Path:
    configured = os.getenv(OUTPUT_DIR_ENV, "").strip()
    base = Path(configured) if configured else DEFAULT_OUTPUT_DIR
    base.mkdir(parents=True, exist_ok=True)
    return base


def _default_output_path(prefix: str, output_path: str | None) -> Path:
    if output_path:
        target = Path(output_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        return target
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return _default_output_dir() / f"{prefix}_{ts}.png"


def _capture_images_in_default_dir() -> list[Path]:
    base = _default_output_dir()
    return [
        p
        for p in base.iterdir()
        if p.is_file() and p.suffix.lower() in CAPTURE_IMAGE_EXTENSIONS
    ]


def _parse_date(value: str) -> date:
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as exc:
        raise ValueError("date must be in YYYY-MM-DD format") from exc


def _parse_datetime(value: str) -> datetime:
    normalized = value.strip().replace("T", " ")
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(normalized, fmt)
        except ValueError:
            continue
    raise ValueError("datetime must be YYYY-MM-DD HH:MM[:SS] (or ISO with T)")


def _delete_files(files: list[Path]) -> list[str]:
    deleted: list[str] = []
    for path in files:
        path.unlink(missing_ok=True)
        deleted.append(str(path.resolve()))
    return deleted


def _load_displays() -> list[dict]:
    _ensure_windows()
    script = r'''
Add-Type -AssemblyName System.Windows.Forms
$screens = [System.Windows.Forms.Screen]::AllScreens
$result = @()
for ($i = 0; $i -lt $screens.Length; $i++) {
  $b = $screens[$i].Bounds
  $result += [pscustomobject]@{
    index = $i + 1
    device_name = $screens[$i].DeviceName
    is_primary = $screens[$i].Primary
    x = $b.X
    y = $b.Y
    width = $b.Width
    height = $b.Height
  }
}
$result | ConvertTo-Json -Depth 3 -Compress
'''
    raw = _run_powershell(script)
    if not raw:
        return []
    parsed = json.loads(raw)
    if isinstance(parsed, dict):
        return [parsed]
    return parsed


def _resolve_display(displays: list[dict], display: int | str) -> dict:
    if not displays:
        raise RuntimeError("No displays detected.")

    if isinstance(display, int):
        for d in displays:
            if int(d["index"]) == display:
                return d
        raise ValueError(f"display index {display} was not found")

    key = str(display).strip().lower()
    aliases = {
        "primary": "primary",
        "プライマリ": "primary",
        "left": "left",
        "leftmost": "left",
        "左": "left",
        "right": "right",
        "rightmost": "right",
        "右": "right",
    }
    key = aliases.get(key, key)
    if key == "primary":
        for d in displays:
            if d.get("is_primary"):
                return d
        return displays[0]

    ordered = sorted(displays, key=lambda d: (int(d["x"]), int(d["y"]), int(d["index"])))
    if key == "left":
        return ordered[0]
    if key == "right":
        return ordered[-1]
    if key.isdigit():
        wanted = int(key)
        for d in displays:
            if int(d["index"]) == wanted:
                return d
        raise ValueError(f"display index {wanted} was not found")

    raise ValueError(
        "display must be monitor index (1..n) or one of: "
        "primary/left/right/プライマリ/左/右"
    )


def _default_display_selector() -> int | str:
    configured = os.getenv(DEFAULT_DISPLAY_ENV, "").strip()
    if configured:
        return configured
    return "primary"


@mcp.tool()
def list_displays() -> dict:
    """List all connected displays with bounds and primary flag."""
    displays = _load_displays()
    return {"displays": displays}


@mcp.tool()
def capture_screen(output_path: str | None = None) -> dict:
    """Capture full virtual desktop and save as PNG.

    Args:
        output_path: Full output path like C:\\tmp\\shot.png. If omitted, auto-generates
            under CAPTURE_SCREEN_OUTPUT_DIR or C:\\capture_screen.
    """
    _ensure_windows()

    target = _default_output_path("capture", output_path)
    target_str = str(target.resolve())

    script = f"""
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
$bounds = [System.Windows.Forms.SystemInformation]::VirtualScreen
$bmp = New-Object System.Drawing.Bitmap $bounds.Width, $bounds.Height
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.CopyFromScreen($bounds.Left, $bounds.Top, 0, 0, $bounds.Size)
$bmp.Save('{_ps_quote(target_str)}', [System.Drawing.Imaging.ImageFormat]::Png)
$g.Dispose()
$bmp.Dispose()
Write-Output '{_ps_quote(target_str)}'
"""

    saved = _run_powershell(script)
    return {"saved_path": saved}


@mcp.tool()
def capture_display(display: int | str | None = None, output_path: str | None = None) -> dict:
    """Capture a specific display (monitor) and save as PNG.

    Args:
        display: Monitor selector. Use monitor index (1..n), or `primary`, `left`, `right`,
            `プライマリ`, `左`, `右`. If omitted, uses CAPTURE_SCREEN_DEFAULT_DISPLAY
            environment variable, or `primary` when unset.
        output_path: Full output path like C:\\tmp\\monitor1.png. If omitted, auto-generates
            under CAPTURE_SCREEN_OUTPUT_DIR or C:\\capture_screen.
    """
    displays = _load_displays()
    selector = _default_display_selector() if display is None else display
    selected = _resolve_display(displays, selector)

    target = _default_output_path(f"display{selected['index']}", output_path)
    target_str = str(target.resolve())

    x = int(selected["x"])
    y = int(selected["y"])
    width = int(selected["width"])
    height = int(selected["height"])

    script = f"""
Add-Type -AssemblyName System.Drawing
$bmp = New-Object System.Drawing.Bitmap {width}, {height}
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.CopyFromScreen({x}, {y}, 0, 0, $bmp.Size)
$bmp.Save('{_ps_quote(target_str)}', [System.Drawing.Imaging.ImageFormat]::Png)
$g.Dispose()
$bmp.Dispose()
Write-Output '{_ps_quote(target_str)}'
"""

    saved = _run_powershell(script)
    return {
        "saved_path": saved,
        "display": selected,
    }


@mcp.tool()
def capture_region(x: int, y: int, width: int, height: int, output_path: str | None = None) -> dict:
    """Capture a screen region and save as PNG.

    Args:
        x: Left coordinate.
        y: Top coordinate.
        width: Region width (>0).
        height: Region height (>0).
        output_path: Full output path like C:\\tmp\\region.png. If omitted, auto-generates
            under CAPTURE_SCREEN_OUTPUT_DIR or C:\\capture_screen.
    """
    _ensure_windows()

    if width <= 0 or height <= 0:
        raise ValueError("width and height must be > 0")

    target = _default_output_path("region", output_path)
    target_str = str(target.resolve())

    script = f"""
Add-Type -AssemblyName System.Drawing
$bmp = New-Object System.Drawing.Bitmap {width}, {height}
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.CopyFromScreen({x}, {y}, 0, 0, $bmp.Size)
$bmp.Save('{_ps_quote(target_str)}', [System.Drawing.Imaging.ImageFormat]::Png)
$g.Dispose()
$bmp.Dispose()
Write-Output '{_ps_quote(target_str)}'
"""

    saved = _run_powershell(script)
    return {
        "saved_path": saved,
        "x": x,
        "y": y,
        "width": width,
        "height": height,
    }


@mcp.tool()
def capture_active_window(output_path: str | None = None) -> dict:
    """Capture the currently active window and save as PNG.

    Args:
        output_path: Full output path like C:\\tmp\\active_window.png. If omitted, auto-generates
            under CAPTURE_SCREEN_OUTPUT_DIR or C:\\capture_screen.
    """
    _ensure_windows()

    target = _default_output_path("active_window", output_path)
    target_str = str(target.resolve())

    script = f"""
Add-Type -AssemblyName System.Drawing
Add-Type @"
using System;
using System.Runtime.InteropServices;
using System.Text;

public static class NativeMethods
{{
    [DllImport("user32.dll")]
    public static extern IntPtr GetForegroundWindow();

    [DllImport("user32.dll", SetLastError=true)]
    public static extern bool GetWindowRect(IntPtr hWnd, out RECT lpRect);

    [DllImport("user32.dll", CharSet=CharSet.Unicode)]
    public static extern int GetWindowTextW(IntPtr hWnd, StringBuilder lpString, int nMaxCount);
}}

[StructLayout(LayoutKind.Sequential)]
public struct RECT
{{
    public int Left;
    public int Top;
    public int Right;
    public int Bottom;
}}
"@

$hWnd = [NativeMethods]::GetForegroundWindow()
if ($hWnd -eq [IntPtr]::Zero) {{
    throw "No active window found."
}}

$rect = New-Object RECT
if (-not [NativeMethods]::GetWindowRect($hWnd, [ref]$rect)) {{
    throw "Failed to get active window bounds."
}}

$width = $rect.Right - $rect.Left
$height = $rect.Bottom - $rect.Top
if ($width -le 0 -or $height -le 0) {{
    throw "Active window has invalid bounds (possibly minimized)."
}}

$titleBuilder = New-Object System.Text.StringBuilder 1024
[void][NativeMethods]::GetWindowTextW($hWnd, $titleBuilder, $titleBuilder.Capacity)
$title = $titleBuilder.ToString()

$bmp = New-Object System.Drawing.Bitmap $width, $height
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.CopyFromScreen($rect.Left, $rect.Top, 0, 0, $bmp.Size)
$bmp.Save('{_ps_quote(target_str)}', [System.Drawing.Imaging.ImageFormat]::Png)
$g.Dispose()
$bmp.Dispose()

[pscustomobject]@{{
  saved_path = '{_ps_quote(target_str)}'
  x = $rect.Left
  y = $rect.Top
  width = $width
  height = $height
  title = $title
}} | ConvertTo-Json -Compress
"""

    raw = _run_powershell(script)
    return json.loads(raw)


@mcp.tool()
def delete_all_capture_images() -> dict:
    """Delete all capture image files in CAPTURE_SCREEN_OUTPUT_DIR."""
    files = _capture_images_in_default_dir()
    deleted = _delete_files(files)
    return {
        "output_dir": str(_default_output_dir().resolve()),
        "deleted_count": len(deleted),
        "deleted_files": deleted,
    }


@mcp.tool()
def delete_capture_images_by_datetime(
    target_date: str | None = None,
    start_datetime: str | None = None,
    end_datetime: str | None = None,
) -> dict:
    """Delete capture images by date or datetime range using file modified time.

    Args:
        target_date: Date in YYYY-MM-DD. Deletes files modified on that day.
        start_datetime: Lower bound in YYYY-MM-DD HH:MM[:SS] (inclusive).
        end_datetime: Upper bound in YYYY-MM-DD HH:MM[:SS] (inclusive).
    """
    if target_date and (start_datetime or end_datetime):
        raise ValueError("Use either target_date or start_datetime/end_datetime, not both")
    if not target_date and not start_datetime and not end_datetime:
        raise ValueError("Specify target_date or start_datetime/end_datetime")

    if target_date:
        d = _parse_date(target_date)
        start = datetime.combine(d, time.min)
        end = datetime.combine(d, time.max)
    else:
        start = _parse_datetime(start_datetime) if start_datetime else None
        end = _parse_datetime(end_datetime) if end_datetime else None
        if start and end and start > end:
            raise ValueError("start_datetime must be earlier than or equal to end_datetime")

    matches: list[Path] = []
    for path in _capture_images_in_default_dir():
        modified = datetime.fromtimestamp(path.stat().st_mtime)
        if start and modified < start:
            continue
        if end and modified > end:
            continue
        matches.append(path)

    deleted = _delete_files(matches)
    return {
        "output_dir": str(_default_output_dir().resolve()),
        "deleted_count": len(deleted),
        "deleted_files": deleted,
        "filter": {
            "target_date": target_date,
            "start_datetime": start_datetime,
            "end_datetime": end_datetime,
        },
    }


if __name__ == "__main__":
    mcp.run()
