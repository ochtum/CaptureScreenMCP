using System.ComponentModel;
using System.Diagnostics;
using System.Drawing;
using System.Drawing.Imaging;
using System.Globalization;
using System.Runtime.InteropServices;
using System.Runtime.Versioning;
using System.Text;
using ModelContextProtocol.Server;

namespace CaptureScreenMcp;

[SupportedOSPlatform("windows")]
public sealed class CaptureTools
{
    private const string DefaultDisplayEnv = "CAPTURE_SCREEN_DEFAULT_DISPLAY";
    private const string OutputDirEnv = "CAPTURE_SCREEN_OUTPUT_DIR";
    private const string HideForegroundWindowsTerminalEnv = "CAPTURE_SCREEN_HIDE_FOREGROUND_WINDOWS_TERMINAL";
    private const string DefaultOutputDir = @"C:\capture_screen";
    private const int DwmwaCloaked = 14;
    private const int SwHide = 0;
    private const int SwShow = 5;
    private const uint ProcessQueryLimitedInformation = 0x1000;

    private static readonly HashSet<string> CaptureImageExtensions =
    [
        ".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp"
    ];

    private static readonly HashSet<string> WindowsTerminalClassNames =
    [
        "CASCADIA_HOSTING_WINDOW_CLASS"
    ];

    private static readonly HashSet<string> WindowsTerminalProcessNames =
    [
        "windowsterminal.exe", "wt.exe"
    ];

    [McpServerTool]
    [Description("List all connected displays with bounds and primary flag.")]
    public object ListDisplays()
    {
        EnsureWindows();
        var displays = EnumerateDisplays();
        return new { displays };
    }

    [McpServerTool]
    [Description("Capture full virtual desktop and save as PNG.")]
    public object CaptureScreen(
        [Description("Full output path like C:\\tmp\\shot.png. If omitted, auto-generates under CAPTURE_SCREEN_OUTPUT_DIR or C:\\capture_screen.")]
        string? outputPath = null)
    {
        EnsureWindows();

        var target = DefaultOutputPath("capture", outputPath);
        var displays = EnumerateDisplays();
        if (displays.Count == 0)
        {
            throw new InvalidOperationException("No displays detected.");
        }

        var left = displays.Min(d => d.x);
        var top = displays.Min(d => d.y);
        var right = displays.Max(d => d.x + d.width);
        var bottom = displays.Max(d => d.y + d.height);
        var rect = new CaptureRect(left, top, right - left, bottom - top);

        using var _ = HiddenWindowsTerminalWindows(rect);
        var saved = SaveCapturePng(rect, target);
        return new { saved_path = saved };
    }

    [McpServerTool]
    [Description("Capture a specific display (monitor) and save as PNG.")]
    public object CaptureDisplay(
        [Description("Monitor selector. Use monitor index (1..n), or primary/left/right/プライマリ/左/右. If omitted, uses CAPTURE_SCREEN_DEFAULT_DISPLAY or primary.")]
        object? display = null,
        [Description("Full output path like C:\\tmp\\monitor1.png. If omitted, auto-generates under CAPTURE_SCREEN_OUTPUT_DIR or C:\\capture_screen.")]
        string? outputPath = null)
    {
        EnsureWindows();

        var displays = EnumerateDisplays();
        var selector = display ?? DefaultDisplaySelector();
        var selected = ResolveDisplay(displays, selector);
        var target = DefaultOutputPath($"display{selected.index}", outputPath);
        var rect = new CaptureRect(selected.x, selected.y, selected.width, selected.height);

        using var _ = HiddenWindowsTerminalWindows(rect);
        var saved = SaveCapturePng(rect, target);

        return new
        {
            saved_path = saved,
            display = selected
        };
    }

    [McpServerTool]
    [Description("Capture a screen region and save as PNG.")]
    public object CaptureRegion(
        [Description("Left coordinate.")] int x,
        [Description("Top coordinate.")] int y,
        [Description("Region width (>0).")] int width,
        [Description("Region height (>0).")] int height,
        [Description("Full output path like C:\\tmp\\region.png. If omitted, auto-generates under CAPTURE_SCREEN_OUTPUT_DIR or C:\\capture_screen.")]
        string? outputPath = null)
    {
        EnsureWindows();

        if (width <= 0 || height <= 0)
        {
            throw new ArgumentOutOfRangeException(nameof(width), "width and height must be > 0");
        }

        var target = DefaultOutputPath("region", outputPath);
        var rect = new CaptureRect(x, y, width, height);

        using var _ = HiddenWindowsTerminalWindows(rect);
        var saved = SaveCapturePng(rect, target);

        return new
        {
            saved_path = saved,
            x,
            y,
            width,
            height
        };
    }

    [McpServerTool]
    [Description("Capture the currently active window and save as PNG.")]
    public object CaptureActiveWindow(
        [Description("Full output path like C:\\tmp\\active_window.png. If omitted, auto-generates under CAPTURE_SCREEN_OUTPUT_DIR or C:\\capture_screen.")]
        string? outputPath = null)
    {
        EnsureWindows();

        var window = ActiveWindowInfo();
        var rect = new CaptureRect(window.x, window.y, window.width, window.height);
        var target = DefaultOutputPath("active_window", outputPath);
        var saved = SaveCapturePng(rect, target);

        return new
        {
            saved_path = saved,
            x = window.x,
            y = window.y,
            width = window.width,
            height = window.height,
            title = window.title
        };
    }

    [McpServerTool]
    [Description("Delete all capture image files in CAPTURE_SCREEN_OUTPUT_DIR.")]
    public object DeleteAllCaptureImages()
    {
        EnsureWindows();
        var files = CaptureImagesInDefaultDir();
        var deleted = DeleteFiles(files);
        return new
        {
            output_dir = Path.GetFullPath(DefaultOutputDirPath()),
            deleted_count = deleted.Count,
            deleted_files = deleted
        };
    }

    [McpServerTool]
    [Description("Delete capture images by date or datetime range using file modified time.")]
    public object DeleteCaptureImagesByDatetime(
        [Description("Date in YYYY-MM-DD. Deletes files modified on that day.")]
        string? targetDate = null,
        [Description("Lower bound in YYYY-MM-DD HH:MM[:SS] (inclusive).")]
        string? startDatetime = null,
        [Description("Upper bound in YYYY-MM-DD HH:MM[:SS] (inclusive).")]
        string? endDatetime = null)
    {
        EnsureWindows();

        if (!string.IsNullOrWhiteSpace(targetDate) &&
            (!string.IsNullOrWhiteSpace(startDatetime) || !string.IsNullOrWhiteSpace(endDatetime)))
        {
            throw new ArgumentException("Use either target_date or start_datetime/end_datetime, not both");
        }

        if (string.IsNullOrWhiteSpace(targetDate) &&
            string.IsNullOrWhiteSpace(startDatetime) &&
            string.IsNullOrWhiteSpace(endDatetime))
        {
            throw new ArgumentException("Specify target_date or start_datetime/end_datetime");
        }

        DateTime? start = null;
        DateTime? end = null;

        if (!string.IsNullOrWhiteSpace(targetDate))
        {
            var d = ParseDate(targetDate);
            start = d.Date;
            end = d.Date.AddDays(1).AddTicks(-1);
        }
        else
        {
            start = string.IsNullOrWhiteSpace(startDatetime) ? null : ParseDateTime(startDatetime);
            end = string.IsNullOrWhiteSpace(endDatetime) ? null : ParseDateTime(endDatetime);

            if (start.HasValue && end.HasValue && start.Value > end.Value)
            {
                throw new ArgumentException("start_datetime must be earlier than or equal to end_datetime");
            }
        }

        var matches = new List<string>();
        foreach (var path in CaptureImagesInDefaultDir())
        {
            var modified = File.GetLastWriteTime(path);
            if (start.HasValue && modified < start.Value)
            {
                continue;
            }

            if (end.HasValue && modified > end.Value)
            {
                continue;
            }

            matches.Add(path);
        }

        var deleted = DeleteFiles(matches);
        return new
        {
            output_dir = Path.GetFullPath(DefaultOutputDirPath()),
            deleted_count = deleted.Count,
            deleted_files = deleted,
            filter = new
            {
                target_date = targetDate,
                start_datetime = startDatetime,
                end_datetime = endDatetime
            }
        };
    }

    private static void EnsureWindows()
    {
        if (!OperatingSystem.IsWindows())
        {
            throw new PlatformNotSupportedException("This MCP server only works on Windows.");
        }
    }

    private static bool EnvFlag(string name, bool defaultValue)
    {
        var value = Environment.GetEnvironmentVariable(name);
        if (value is null)
        {
            return defaultValue;
        }

        var normalized = value.Trim().ToLowerInvariant();
        if (normalized is "" or "1" or "true" or "yes" or "on")
        {
            return true;
        }

        if (normalized is "0" or "false" or "no" or "off")
        {
            return false;
        }

        return defaultValue;
    }

    private static string DefaultOutputDirPath()
    {
        var configured = Environment.GetEnvironmentVariable(OutputDirEnv)?.Trim();
        var path = string.IsNullOrWhiteSpace(configured) ? DefaultOutputDir : configured;
        Directory.CreateDirectory(path);
        return path;
    }

    private static string DefaultOutputPath(string prefix, string? outputPath)
    {
        if (!string.IsNullOrWhiteSpace(outputPath))
        {
            var targetDirectory = Path.GetDirectoryName(outputPath);
            if (!string.IsNullOrWhiteSpace(targetDirectory))
            {
                Directory.CreateDirectory(targetDirectory);
            }

            return Path.GetFullPath(outputPath);
        }

        var ts = DateTime.Now.ToString("yyyyMMdd_HHmmss", CultureInfo.InvariantCulture);
        return Path.GetFullPath(Path.Combine(DefaultOutputDirPath(), $"{prefix}_{ts}.png"));
    }

    private static List<string> CaptureImagesInDefaultDir()
    {
        return Directory.EnumerateFiles(DefaultOutputDirPath())
            .Where(path => CaptureImageExtensions.Contains(Path.GetExtension(path).ToLowerInvariant()))
            .ToList();
    }

    private static DateTime ParseDate(string value)
    {
        if (!DateTime.TryParseExact(value, "yyyy-MM-dd", CultureInfo.InvariantCulture, DateTimeStyles.None, out var parsed))
        {
            throw new ArgumentException("date must be in YYYY-MM-DD format");
        }

        return parsed;
    }

    private static DateTime ParseDateTime(string value)
    {
        var normalized = value.Trim().Replace('T', ' ');
        var formats = new[] { "yyyy-MM-dd HH:mm:ss", "yyyy-MM-dd HH:mm" };

        if (!DateTime.TryParseExact(normalized, formats, CultureInfo.InvariantCulture, DateTimeStyles.None, out var parsed))
        {
            throw new ArgumentException("datetime must be YYYY-MM-DD HH:MM[:SS] (or ISO with T)");
        }

        return parsed;
    }

    private static List<string> DeleteFiles(IEnumerable<string> files)
    {
        var deleted = new List<string>();
        foreach (var file in files)
        {
            if (File.Exists(file))
            {
                File.Delete(file);
            }

            deleted.Add(Path.GetFullPath(file));
        }

        return deleted;
    }

    private static string SaveCapturePng(CaptureRect rect, string targetPath)
    {
        using var bitmap = new Bitmap(rect.width, rect.height, PixelFormat.Format32bppArgb);
        using var graphics = Graphics.FromImage(bitmap);
        graphics.CopyFromScreen(rect.x, rect.y, 0, 0, new Size(rect.width, rect.height), CopyPixelOperation.SourceCopy);
        bitmap.Save(targetPath, ImageFormat.Png);
        return Path.GetFullPath(targetPath);
    }

    private static List<DisplayInfo> EnumerateDisplays()
    {
        var displays = new List<DisplayInfo>();

        NativeMethods.EnumDisplayMonitors(
            IntPtr.Zero,
            IntPtr.Zero,
            (monitor, _, _, _) =>
            {
                var info = new NativeMethods.MonitorInfoEx();
                info.cbSize = Marshal.SizeOf<NativeMethods.MonitorInfoEx>();

                if (!NativeMethods.GetMonitorInfo(monitor, ref info))
                {
                    return true;
                }

                var left = info.rcMonitor.Left;
                var top = info.rcMonitor.Top;
                var right = info.rcMonitor.Right;
                var bottom = info.rcMonitor.Bottom;
                var index = displays.Count + 1;

                displays.Add(new DisplayInfo(
                    index,
                    info.szDevice,
                    (info.dwFlags & NativeMethods.MonitorInfofPrimary) != 0,
                    left,
                    top,
                    right - left,
                    bottom - top));

                return true;
            },
            IntPtr.Zero);

        return displays;
    }

    private static DisplayInfo ResolveDisplay(IReadOnlyList<DisplayInfo> displays, object selector)
    {
        if (displays.Count == 0)
        {
            throw new InvalidOperationException("No displays detected.");
        }

        if (selector is int asInt)
        {
            var foundByIndex = displays.FirstOrDefault(d => d.index == asInt);
            return foundByIndex ?? throw new ArgumentException($"display index {asInt} was not found");
        }

        if (selector is long asLong)
        {
            return ResolveDisplay(displays, checked((int)asLong));
        }

        var key = selector.ToString()?.Trim().ToLowerInvariant() ?? string.Empty;
        var aliases = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase)
        {
            ["primary"] = "primary",
            ["プライマリ"] = "primary",
            ["left"] = "left",
            ["leftmost"] = "left",
            ["左"] = "left",
            ["right"] = "right",
            ["rightmost"] = "right",
            ["右"] = "right"
        };
        key = aliases.GetValueOrDefault(key, key);

        if (key == "primary")
        {
            return displays.FirstOrDefault(d => d.is_primary) ?? displays[0];
        }

        var ordered = displays.OrderBy(d => d.x).ThenBy(d => d.y).ThenBy(d => d.index).ToList();
        if (key == "left")
        {
            return ordered[0];
        }

        if (key == "right")
        {
            return ordered[^1];
        }

        if (int.TryParse(key, out var parsed))
        {
            var found = displays.FirstOrDefault(d => d.index == parsed);
            return found ?? throw new ArgumentException($"display index {parsed} was not found");
        }

        throw new ArgumentException("display must be monitor index (1..n) or one of: primary/left/right/プライマリ/左/右");
    }

    private static object DefaultDisplaySelector()
    {
        var configured = Environment.GetEnvironmentVariable(DefaultDisplayEnv)?.Trim();
        return string.IsNullOrWhiteSpace(configured) ? "primary" : configured;
    }

    private static WindowInfo ActiveWindowInfo()
    {
        var hwnd = NativeMethods.GetForegroundWindow();
        if (hwnd == IntPtr.Zero)
        {
            throw new InvalidOperationException("No active window found.");
        }

        return GetWindowInfo(hwnd);
    }

    private static WindowInfo GetWindowInfo(IntPtr hwnd)
    {
        if (!NativeMethods.GetWindowRect(hwnd, out var rect))
        {
            throw new InvalidOperationException("Failed to get window bounds.");
        }

        var width = rect.Right - rect.Left;
        var height = rect.Bottom - rect.Top;
        if (width <= 0 || height <= 0)
        {
            throw new InvalidOperationException("Window has invalid bounds (possibly minimized).");
        }

        var titleBuilder = new StringBuilder(1024);
        NativeMethods.GetWindowText(hwnd, titleBuilder, titleBuilder.Capacity);

        var classBuilder = new StringBuilder(256);
        NativeMethods.GetClassName(hwnd, classBuilder, classBuilder.Capacity);

        return new WindowInfo(
            hwnd,
            rect.Left,
            rect.Top,
            width,
            height,
            titleBuilder.ToString(),
            classBuilder.ToString(),
            NativeMethods.IsWindowVisible(hwnd),
            NativeMethods.IsIconic(hwnd),
            IsWindowCloaked(hwnd),
            WindowProcessName(hwnd));
    }

    private static bool IsWindowCloaked(IntPtr hwnd)
    {
        if (NativeMethods.DwmGetWindowAttribute(hwnd, DwmwaCloaked, out var cloaked, sizeof(int)) != 0)
        {
            return false;
        }

        return cloaked != 0;
    }

    private static string? WindowProcessName(IntPtr hwnd)
    {
        NativeMethods.GetWindowThreadProcessId(hwnd, out var processId);
        if (processId == 0)
        {
            return null;
        }

        var processHandle = NativeMethods.OpenProcess(ProcessQueryLimitedInformation, false, processId);
        if (processHandle == IntPtr.Zero)
        {
            return null;
        }

        try
        {
            var buffer = new StringBuilder(32768);
            var length = buffer.Capacity;
            if (!NativeMethods.QueryFullProcessImageName(processHandle, 0, buffer, ref length))
            {
                return null;
            }

            return Path.GetFileName(buffer.ToString()).ToLowerInvariant();
        }
        finally
        {
            NativeMethods.CloseHandle(processHandle);
        }
    }

    private static bool IsWindowsTerminalWindow(WindowInfo window)
    {
        return WindowsTerminalClassNames.Contains(window.class_name) ||
               (!string.IsNullOrWhiteSpace(window.process_name) &&
                WindowsTerminalProcessNames.Contains(window.process_name));
    }

    private static bool IsEffectivelyVisibleWindow(WindowInfo window)
    {
        return window.is_visible && !window.is_minimized && !window.is_cloaked;
    }

    private static List<WindowInfo> EnumerateTopLevelWindows()
    {
        var windows = new List<WindowInfo>();

        NativeMethods.EnumWindows((hwnd, _) =>
        {
            try
            {
                windows.Add(GetWindowInfo(hwnd));
            }
            catch
            {
                // Ignore windows that cannot provide valid rect or metadata.
            }

            return true;
        }, IntPtr.Zero);

        return windows;
    }

    private static bool RectsIntersect(CaptureRect a, WindowInfo b)
    {
        var aRight = a.x + a.width;
        var aBottom = a.y + a.height;
        var bRight = b.x + b.width;
        var bBottom = b.y + b.height;

        return a.x < bRight && b.x < aRight && a.y < bBottom && b.y < aBottom;
    }

    private static IDisposable HiddenWindowsTerminalWindows(CaptureRect captureRect)
    {
        if (!EnvFlag(HideForegroundWindowsTerminalEnv, defaultValue: true))
        {
            return EmptyDisposable.Instance;
        }

        var hidden = new List<IntPtr>();
        foreach (var window in EnumerateTopLevelWindows())
        {
            if (!IsEffectivelyVisibleWindow(window))
            {
                continue;
            }

            if (!IsWindowsTerminalWindow(window))
            {
                continue;
            }

            if (!RectsIntersect(captureRect, window))
            {
                continue;
            }

            if (NativeMethods.ShowWindow(window.hwnd, SwHide))
            {
                hidden.Add(window.hwnd);
            }
        }

        if (hidden.Count > 0)
        {
            Thread.Sleep(TimeSpan.FromMilliseconds(150));
        }

        return new RestoreHiddenWindows(hidden);
    }

    private sealed class RestoreHiddenWindows(List<IntPtr> hidden) : IDisposable
    {
        public void Dispose()
        {
            for (var i = hidden.Count - 1; i >= 0; i--)
            {
                NativeMethods.ShowWindow(hidden[i], SwShow);
            }
        }
    }

    private sealed class EmptyDisposable : IDisposable
    {
        public static readonly EmptyDisposable Instance = new();
        public void Dispose()
        {
        }
    }

    public sealed record DisplayInfo(
        int index,
        string device_name,
        bool is_primary,
        int x,
        int y,
        int width,
        int height);

    private sealed record WindowInfo(
        IntPtr hwnd,
        int x,
        int y,
        int width,
        int height,
        string title,
        string class_name,
        bool is_visible,
        bool is_minimized,
        bool is_cloaked,
        string? process_name);

    private sealed record CaptureRect(int x, int y, int width, int height);
}
