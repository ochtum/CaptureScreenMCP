<p align="left">
  <a href="README_en.md"><img src="https://img.shields.io/badge/English Mode-blue.svg" alt="English"></a>
  <a href="README.md"><img src="https://img.shields.io/badge/日本語 モード-red.svg" alt="日本語"></a>
</p>

# CaptureScreenMCP

Windows向けの画面キャプチャ用MCPサーバーです。<br>
現在見ている画面をAIに見せることができます。<br>
操作のサポート、デザイン崩れのアドバイス、コピペできない画面でのエラーメッセージに関する質問などにご利用いただけます。<br>


デフォルトの出力先ディレクトリ: `C:\capture_screen`。

## ツール

- `list_displays()`
  - 接続されているモニター情報（`index`, `is_primary`, `x`, `y`, `width`, `height`）を返します。
- `capture_screen(output_path?: string)`
  - 仮想デスクトップ全体をキャプチャし、PNGとして保存します。
- `capture_display(display?: int | "primary" | "left" | "right" | "プライマリ" | "左" | "右", output_path?: string)`
  - 指定したモニターをキャプチャし、PNGとして保存します。`display` を省略した場合は環境変数 `CAPTURE_SCREEN_DEFAULT_DISPLAY`（例: `left`, `右`）を使用し、未設定時は `primary` を使います。
- `capture_region(x: int, y: int, width: int, height: int, output_path?: string)`
  - 指定した画面領域をキャプチャし、PNGとして保存します。
- `capture_active_window(output_path?: string)`
  - 現在アクティブなウィンドウをキャプチャし、PNGとして保存します。

## セットアップ（Windows）

```powershell
cd C:\MCP-PATH\CaptureScreenMCP
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## セットアップ（WSL）

```bash
cd /mnt/c/jMCP-PATH/CaptureScreenMCP
/mnt/c/Windows/py.exe -3 -m venv .venv
./.venv/Scripts/python.exe -m pip install -r requirements.txt
```

## 実行（Windows）

```powershell
cd C:\MCP-PATH\CaptureScreenMCP
.\.venv\Scripts\Activate.ps1
python server.py
```

## 実行（WSL）

```bash
cd /mnt/c/jMCP-PATH/CaptureScreenMCP
./.venv/Scripts/python.exe server.py
```

## Codex MCP設定

### WSL から使う場合（この環境）

```toml
[mcp_servers.capture-screen]
command = "/mnt/c/MCP-PATH/CaptureScreenMCP/.venv/Scripts/python.exe"
args = ["C:\\MCP-PATH\\CaptureScreenMCP\\server.py"]
startup_timeout_sec = 30
```

### Windows ネイティブで使う場合

```toml
[mcp_servers.capture-screen]
command = "C:\\MCP-PATH\\CaptureScreenMCP\\.venv\\Scripts\\python.exe"
args = ["C:\\MCP-PATHe\\CaptureScreenMCP\\server.py"]
startup_timeout_sec = 30
```

注: `command` は実行環境に合わせて `WSL形式(/mnt/c/...)` か `Windows形式(C:\\...)` を使い分けてください。
注: 既定の対象モニターを変更したい場合は、環境変数 `CAPTURE_SCREEN_DEFAULT_DISPLAY` を設定します（例: `left`, `right`, `プライマリ`, `左`, `右`）。
注: 出力先ディレクトリを変更したい場合は、環境変数 `CAPTURE_SCREEN_OUTPUT_DIR` を設定します（未設定時は `C:\capture_screen`）。

### Codex で出力先ディレクトリを指定する例

```toml
[mcp_servers.capture-screen]
command = "/mnt/c/MCP-PATH/CaptureScreenMCP/.venv/Scripts/python.exe"
args = ["C:\\MCP-PATH\\CaptureScreenMCP\\server.py"]
startup_timeout_sec = 30
env = { "CAPTURE_SCREEN_OUTPUT_DIR" = "C:\\capture_screen" }
```

## GitHub Copilot MCP設定（VS Code）

`.vscode/mcp.json` を作成または更新し、以下を設定します。

### Windows ネイティブで使う場合

```json
{
  "servers": {
    "capture-screen": {
      "command": "C:\\MCP-PATH\\CaptureScreenMCP\\.venv\\Scripts\\python.exe",
      "args": [
        "C:\\MCP-PATHe\\CaptureScreenMCP\\server.py"
      ]
    }
  }
}
```

`CAPTURE_SCREEN_OUTPUT_DIR` を指定する場合の例:

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

## Claude Desktop MCP設定

`claude_desktop_config.json` の `mcpServers` に以下を追加します。

### Windows ネイティブで使う場合

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

`CAPTURE_SCREEN_OUTPUT_DIR` を指定する場合の例:

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

## ❗このプロジェクトは MIT ライセンスの下で提供されています。詳細は LICENSE ファイルをご覧ください。
