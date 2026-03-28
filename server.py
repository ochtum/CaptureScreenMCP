from __future__ import annotations

import ctypes
import os
import time as time_module
from ctypes import wintypes
from contextlib import contextmanager
from datetime import date, datetime, time
from pathlib import Path

import mss
from PIL import Image
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("capture-screen-mcp")
DEFAULT_DISPLAY_ENV = "CAPTURE_SCREEN_DEFAULT_DISPLAY"
OUTPUT_DIR_ENV = "CAPTURE_SCREEN_OUTPUT_DIR"
HIDE_FOREGROUND_WINDOWS_TERMINAL_ENV = "CAPTURE_SCREEN_HIDE_FOREGROUND_WINDOWS_TERMINAL"
DEFAULT_OUTPUT_DIR = Path(r"C:\capture_screen")
CAPTURE_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp"}
WINDOW_TERMINAL_CLASS_NAMES = {"CASCADIA_HOSTING_WINDOW_CLASS"}
WINDOW_TERMINAL_PROCESS_NAMES = {"windowsterminal.exe", "wt.exe"}
HIDE_CAPTURE_SETTLE_SECONDS = 0.15

MONITORINFOF_PRIMARY = 1
CCHDEVICENAME = 32
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
DWMWA_CLOAKED = 14
SW_HIDE = 0
SW_SHOW = 5


def _ensure_windows() -> None:
    if os.name != "nt":
        raise RuntimeError("This MCP server only works on Windows.")


def _set_process_dpi_aware() -> None:
    # Best-effort only: keeps capture coordinates aligned on HiDPI displays.
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass


class MONITORINFOEXW(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("rcMonitor", wintypes.RECT),
        ("rcWork", wintypes.RECT),
        ("dwFlags", wintypes.DWORD),
        ("szDevice", wintypes.WCHAR * CCHDEVICENAME),
    ]


def _env_flag(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    normalized = value.strip().lower()
    if normalized in {"", "1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    return default


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


def _rects_intersect(a: dict, b: dict) -> bool:
    a_left = int(a["x"])
    a_top = int(a["y"])
    a_right = a_left + int(a["width"])
    a_bottom = a_top + int(a["height"])
    b_left = int(b["x"])
    b_top = int(b["y"])
    b_right = b_left + int(b["width"])
    b_bottom = b_top + int(b["height"])
    return a_left < b_right and b_left < a_right and a_top < b_bottom and b_top < a_bottom


def _capture_rect(x: int, y: int, width: int, height: int) -> dict:
    return {
        "x": int(x),
        "y": int(y),
        "width": int(width),
        "height": int(height),
    }


def _enumerate_displays() -> list[dict]:
    _ensure_windows()
    _set_process_dpi_aware()

    user32 = ctypes.windll.user32
    user32.GetMonitorInfoW.argtypes = [ctypes.c_void_p, ctypes.POINTER(MONITORINFOEXW)]
    user32.GetMonitorInfoW.restype = wintypes.BOOL

    displays: list[dict] = []

    monitor_enum_proc = ctypes.WINFUNCTYPE(
        wintypes.BOOL,
        ctypes.c_void_p,
        ctypes.c_void_p,
        ctypes.POINTER(wintypes.RECT),
        wintypes.LPARAM,
    )

    @monitor_enum_proc
    def _callback(h_monitor, _hdc, _lprc_monitor, _lparam):
        info = MONITORINFOEXW()
        info.cbSize = ctypes.sizeof(MONITORINFOEXW)
        if not user32.GetMonitorInfoW(h_monitor, ctypes.byref(info)):
            return True

        left = int(info.rcMonitor.left)
        top = int(info.rcMonitor.top)
        right = int(info.rcMonitor.right)
        bottom = int(info.rcMonitor.bottom)
        displays.append(
            {
                "index": len(displays) + 1,
                "device_name": info.szDevice,
                "is_primary": bool(info.dwFlags & MONITORINFOF_PRIMARY),
                "x": left,
                "y": top,
                "width": right - left,
                "height": bottom - top,
            }
        )
        return True

    if not user32.EnumDisplayMonitors(None, None, _callback, 0):
        raise RuntimeError("Failed to enumerate displays.")

    return displays


def _load_displays() -> list[dict]:
    return _enumerate_displays()


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


def _save_capture_png(left: int, top: int, width: int, height: int, target: Path) -> str:
    monitor = {
        "left": int(left),
        "top": int(top),
        "width": int(width),
        "height": int(height),
    }

    with mss.mss() as sct:
        shot = sct.grab(monitor)
        image = Image.frombytes("RGB", shot.size, shot.bgra, "raw", "BGRX")
        image.save(str(target), format="PNG")

    return str(target.resolve())


def _window_process_name(hwnd: int) -> str | None:
    _ensure_windows()
    _set_process_dpi_aware()

    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32

    user32.GetWindowThreadProcessId.argtypes = [ctypes.c_void_p, ctypes.POINTER(wintypes.DWORD)]
    user32.GetWindowThreadProcessId.restype = wintypes.DWORD
    kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel32.OpenProcess.restype = wintypes.HANDLE
    kernel32.QueryFullProcessImageNameW.argtypes = [
        wintypes.HANDLE,
        wintypes.DWORD,
        wintypes.LPWSTR,
        ctypes.POINTER(wintypes.DWORD),
    ]
    kernel32.QueryFullProcessImageNameW.restype = wintypes.BOOL
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel32.CloseHandle.restype = wintypes.BOOL

    pid = wintypes.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    if not pid.value:
        return None

    process = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid.value)
    if not process:
        return None

    try:
        size = wintypes.DWORD(32768)
        buffer = ctypes.create_unicode_buffer(size.value)
        if not kernel32.QueryFullProcessImageNameW(process, 0, buffer, ctypes.byref(size)):
            return None
        return Path(buffer.value).name.lower()
    finally:
        kernel32.CloseHandle(process)


def _is_window_cloaked(hwnd: int) -> bool:
    _ensure_windows()

    try:
        dwmapi = ctypes.windll.dwmapi
    except AttributeError:
        return False

    cloaked = wintypes.DWORD()
    dwmapi.DwmGetWindowAttribute.argtypes = [
        ctypes.c_void_p,
        wintypes.DWORD,
        ctypes.c_void_p,
        wintypes.DWORD,
    ]
    dwmapi.DwmGetWindowAttribute.restype = ctypes.c_long
    result = dwmapi.DwmGetWindowAttribute(
        hwnd,
        DWMWA_CLOAKED,
        ctypes.byref(cloaked),
        ctypes.sizeof(cloaked),
    )
    if result != 0:
        return False
    return bool(cloaked.value)


def _window_info(hwnd: int) -> dict:
    _ensure_windows()
    _set_process_dpi_aware()

    user32 = ctypes.windll.user32
    user32.GetWindowRect.argtypes = [ctypes.c_void_p, ctypes.POINTER(wintypes.RECT)]
    user32.GetWindowRect.restype = wintypes.BOOL
    user32.GetWindowTextW.argtypes = [ctypes.c_void_p, wintypes.LPWSTR, ctypes.c_int]
    user32.GetWindowTextW.restype = ctypes.c_int
    user32.GetClassNameW.argtypes = [ctypes.c_void_p, wintypes.LPWSTR, ctypes.c_int]
    user32.GetClassNameW.restype = ctypes.c_int
    user32.IsWindowVisible.argtypes = [ctypes.c_void_p]
    user32.IsWindowVisible.restype = wintypes.BOOL
    user32.IsIconic.argtypes = [ctypes.c_void_p]
    user32.IsIconic.restype = wintypes.BOOL

    rect = wintypes.RECT()
    if not user32.GetWindowRect(hwnd, ctypes.byref(rect)):
        raise RuntimeError("Failed to get window bounds.")

    width = int(rect.right - rect.left)
    height = int(rect.bottom - rect.top)
    if width <= 0 or height <= 0:
        raise RuntimeError("Window has invalid bounds (possibly minimized).")

    title_buffer = ctypes.create_unicode_buffer(1024)
    user32.GetWindowTextW(hwnd, title_buffer, 1024)
    class_buffer = ctypes.create_unicode_buffer(256)
    user32.GetClassNameW(hwnd, class_buffer, 256)

    return {
        "hwnd": int(hwnd),
        "x": int(rect.left),
        "y": int(rect.top),
        "width": width,
        "height": height,
        "title": title_buffer.value,
        "class_name": class_buffer.value,
        "is_visible": bool(user32.IsWindowVisible(hwnd)),
        "is_minimized": bool(user32.IsIconic(hwnd)),
        "is_cloaked": _is_window_cloaked(int(hwnd)),
        "process_name": _window_process_name(hwnd),
    }


def _active_window_info() -> dict:
    _ensure_windows()
    _set_process_dpi_aware()

    user32 = ctypes.windll.user32
    user32.GetForegroundWindow.restype = ctypes.c_void_p
    hwnd = user32.GetForegroundWindow()
    if not hwnd:
        raise RuntimeError("No active window found.")

    return _window_info(int(hwnd))


def _is_windows_terminal_window(window: dict) -> bool:
    class_name = str(window.get("class_name", "")).strip()
    process_name = str(window.get("process_name", "")).strip().lower()
    return (
        class_name in WINDOW_TERMINAL_CLASS_NAMES
        or process_name in WINDOW_TERMINAL_PROCESS_NAMES
    )


def _enumerate_top_level_windows() -> list[dict]:
    _ensure_windows()
    _set_process_dpi_aware()

    user32 = ctypes.windll.user32
    windows: list[dict] = []

    enum_windows_proc = ctypes.WINFUNCTYPE(wintypes.BOOL, ctypes.c_void_p, wintypes.LPARAM)

    @enum_windows_proc
    def _callback(hwnd, _lparam):
        try:
            window = _window_info(int(hwnd))
        except RuntimeError:
            return True

        windows.append(window)
        return True

    if not user32.EnumWindows(_callback, 0):
        raise RuntimeError("Failed to enumerate top-level windows.")

    return windows


def _is_effectively_visible_window(window: dict) -> bool:
    return (
        bool(window.get("is_visible"))
        and not bool(window.get("is_minimized"))
        and not bool(window.get("is_cloaked"))
    )


def _windows_terminal_windows_to_hide(capture_rect: dict) -> list[dict]:
    matches: list[dict] = []
    for window in _enumerate_top_level_windows():
        if not _is_effectively_visible_window(window):
            continue
        if not _is_windows_terminal_window(window):
            continue
        if not _rects_intersect(window, capture_rect):
            continue
        matches.append(window)
    return matches


def _show_window(hwnd: int, command: int) -> bool:
    _ensure_windows()
    _set_process_dpi_aware()

    user32 = ctypes.windll.user32
    user32.ShowWindow.argtypes = [ctypes.c_void_p, ctypes.c_int]
    user32.ShowWindow.restype = wintypes.BOOL
    return bool(user32.ShowWindow(hwnd, command))


@contextmanager
def _hidden_windows_terminal_windows(capture_rect: dict):
    hidden_windows: list[dict] = []

    if _env_flag(HIDE_FOREGROUND_WINDOWS_TERMINAL_ENV, True):
        for window in _windows_terminal_windows_to_hide(capture_rect):
            was_visible = _show_window(int(window["hwnd"]), SW_HIDE)
            if was_visible:
                hidden_windows.append(window)

        if hidden_windows:
            time_module.sleep(HIDE_CAPTURE_SETTLE_SECONDS)

    try:
        yield hidden_windows
    finally:
        for window in reversed(hidden_windows):
            _show_window(int(window["hwnd"]), SW_SHOW)


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
    with mss.mss() as sct:
        monitor = sct.monitors[0]
    capture_rect = _capture_rect(
        int(monitor["left"]),
        int(monitor["top"]),
        int(monitor["width"]),
        int(monitor["height"]),
    )
    with _hidden_windows_terminal_windows(capture_rect):
        saved = _save_capture_png(
            capture_rect["x"],
            capture_rect["y"],
            capture_rect["width"],
            capture_rect["height"],
            target,
        )

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
    capture_rect = _capture_rect(
        int(selected["x"]),
        int(selected["y"]),
        int(selected["width"]),
        int(selected["height"]),
    )
    with _hidden_windows_terminal_windows(capture_rect):
        saved = _save_capture_png(
            capture_rect["x"],
            capture_rect["y"],
            capture_rect["width"],
            capture_rect["height"],
            target,
        )

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
    capture_rect = _capture_rect(x, y, width, height)
    with _hidden_windows_terminal_windows(capture_rect):
        saved = _save_capture_png(
            capture_rect["x"],
            capture_rect["y"],
            capture_rect["width"],
            capture_rect["height"],
            target,
        )

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

    window = _active_window_info()

    target = _default_output_path("active_window", output_path)
    saved = _save_capture_png(
        int(window["x"]),
        int(window["y"]),
        int(window["width"]),
        int(window["height"]),
        target,
    )

    return {
        "saved_path": saved,
        "x": window["x"],
        "y": window["y"],
        "width": window["width"],
        "height": window["height"],
        "title": window["title"],
    }


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
    mcp.run(transport="stdio")
