<p align="left">
  <a href="README_en.md"><img src="https://img.shields.io/badge/English Mode-blue.svg" alt="English"></a>
  <a href="README.md"><img src="https://img.shields.io/badge/日本語 モード-red.svg" alt="日本語"></a>
</p>

# CaptureScreenMCP

Windows向けの画面キャプチャ用MCPサーバーです。<br>
現在見ている画面をAIに見せることができます。<br>
操作のサポート、デザイン崩れのアドバイス、コピペできない画面でのエラーメッセージに関する質問などにご利用いただけます。<br>
画面キャプチャ処理は `mss + Pillow + ctypes` で実装しており、PowerShell呼び出しは不要です。<br>


デフォルトの出力先ディレクトリ: `C:\capture_screen`。

## ツール

- `list_displays()`
  - 接続されているモニター情報（`index`, `is_primary`, `x`, `y`, `width`, `height`）を返します。
- `capture_screen(output_path?: string)`
  - デスクトップ全体をキャプチャし、PNGとして保存します。
- `capture_display(display?: int | "primary" | "left" | "right" | "プライマリ" | "左" | "右", output_path?: string)`
  - 指定したモニターをキャプチャし、PNGとして保存します。`display` を省略した場合は環境変数 `CAPTURE_SCREEN_DEFAULT_DISPLAY`（例: `left`, `右`）を使用し、未設定時は `primary` を使います。
- `capture_region(x: int, y: int, width: int, height: int, output_path?: string)`
  - 指定した画面領域をキャプチャし、PNGとして保存します。
- `capture_active_window(output_path?: string)`
  - 現在アクティブなウィンドウをキャプチャし、PNGとして保存します。
- `delete_all_capture_images()`
  - `CAPTURE_SCREEN_OUTPUT_DIR`（未設定時は `C:\capture_screen`）直下のキャプチャ画像ファイルをすべて削除します。
- `delete_capture_images_by_datetime(target_date?: string, start_datetime?: string, end_datetime?: string)`
  - ファイル更新日時を基準に、指定日または日時範囲に一致するキャプチャ画像ファイルを削除します。
  - `target_date` は `YYYY-MM-DD`、`start_datetime`/`end_datetime` は `YYYY-MM-DD HH:MM[:SS]` または `YYYY-MM-DDTHH:MM[:SS]` 形式です。

## MCP実行前に必要なPythonライブラリ

以下のライブラリをインストールしてください（`requirements.txt` に含まれています）。

- `mcp>=1.0.0`
- `mss>=9.0.1`
- `Pillow>=10.0.0`

インストールコマンド:

```bash
python -m pip install -r requirements.txt
```

## ツール別の使用例（プロンプト例）

### `list_displays()`

- 「接続されているモニター一覧を取得して、`index` と解像度を教えてください。」
- 「プライマリモニターがどれか確認したいので、`list_displays` を実行してください。」
- 「モニターの配置（`x`, `y`）を見て、左右どちらに拡張されているか教えてください。」

### `capture_screen(output_path?: string)`

- 「画面全体をキャプチャして保存してください。」
- 「デスクトップ全体を `C:\\capture_screen\\full_desktop.png` に保存してください。」
- 「今の全モニター表示を1枚の画像として取得してください。」

### `capture_display(display?: ..., output_path?: string)`

- 「プライマリモニターだけをキャプチャしてください。」
- 「左モニタを見てほしいんですけど、CloudFormationでスタックを削除したときに、保護されたバケットに残ってしまいまして、、、「無効にする」にしても消えない状態なんですけど、どうしたらいいですかね？」
- 「`display=2` だけキャプチャしてください。」

### `capture_region(x, y, width, height, output_path?: string)`

- 「`保護されたバケット`の領域だけをキャプチャとってください」
- 「エラーが出ているダイアログ周辺だけ撮りたいので、指定領域を保存してください。」
- 「今キャプチャした画像を確認してほしいんですけど、見切れています」

### `capture_active_window(output_path?: string)`

- 「現在アクティブなウィンドウだけキャプチャしてください。」
- 「今フォーカスしているアプリ画面を `C:\\capture_screen\\active_window.png` に保存してください。」
- 「ブラウザのウィンドウだけを撮ってください。」

### `delete_all_capture_images()`

- 「キャプチャ画像を全部削除してください。」

### `delete_capture_images_by_datetime(target_date?, start_datetime?, end_datetime?)`

- 「`2026-03-04` のキャプチャ画像を削除してください。」
- 「`2026-03-04 09:00`～`2026-03-04 18:00` の範囲だけ削除してください。」
- 「`2026-03-01` から `2026-03-03` までの分を削除したいです。」

## セットアップ（Windows）

```powershell
cd C:\MCP-PATH\CaptureScreenMCP
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## セットアップ（WSL）

```bash
cd /mnt/c/MCP-PATH/CaptureScreenMCP
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
cd /mnt/c/MCP-PATH/CaptureScreenMCP
./.venv/Scripts/python.exe server.py
```

## Codex MCP設定

### WSL から使う場合

```toml
[mcp_servers.capture-screen]
command = "/mnt/c/MCP-PATH/CaptureScreenMCP/.venv/Scripts/python.exe"
args = ["C:\\MCP-PATH\\CaptureScreenMCP\\server.py"]
startup_timeout_sec = 30
env = { "CAPTURE_SCREEN_OUTPUT_DIR" = "C:\\MCP-PATH\\capture_screen", "WSLENV" = "CAPTURE_SCREEN_OUTPUT_DIR" }
```

### Windows ネイティブで使う場合

```toml
[mcp_servers.capture-screen]
command = "C:\\MCP-PATH\\CaptureScreenMCP\\.venv\\Scripts\\python.exe"
args = ["C:\\MCP-PATH\\CaptureScreenMCP\\server.py"]
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
        "C:\\MCP-PATH\\CaptureScreenMCP\\server.py"
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

`%USERPROFILE%\AppData\Roaming\Claude\claude_desktop_config.json` の `mcpServers` に以下を追加します。


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

## Claude Code MCP設定

`%USERPROFILE%\.claude.json` の `mcpServers` に以下を追加します。

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

`CAPTURE_SCREEN_OUTPUT_DIR` を指定する場合の例:

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

## ❗このプロジェクトは MIT ライセンスの下で提供されています。詳細は LICENSE ファイルをご覧ください。
