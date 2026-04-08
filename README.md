<p align="left">
  <a href="README_en.md"><img src="https://img.shields.io/badge/English Mode-blue.svg" alt="English"></a>
  <a href="README.md"><img src="https://img.shields.io/badge/日本語 モード-red.svg" alt="日本語"></a>
</p>

# CaptureScreenMCP

<!-- mcp-name: io.github.ochtum/capture-screen -->

Windows 向けのローカル実行型 MCP サーバーです（`stdio` transport）。
C# / .NET 10 で実装されており、画面キャプチャとキャプチャ画像削除ツールを提供します。

## 何ができるか

- 接続ディスプレイ情報の取得
- デスクトップ全体、指定ディスプレイ、指定領域、アクティブウィンドウの PNG キャプチャ
- 出力先ディレクトリ内のキャプチャ画像一括削除
- 日付/日時範囲でのキャプチャ画像削除
- `capture_screen` / `capture_display` / `capture_region` 実行時に、撮影領域に重なった `Windows Terminal` を一時的に非表示化（既定で有効）

## 利用可能な Tools

- `list_displays()`
- `capture_screen(outputPath?: string)`
- `capture_display(display?: int | string, outputPath?: string)`
- `capture_region(x: int, y: int, width: int, height: int, outputPath?: string)`
- `capture_active_window(outputPath?: string)`
- `delete_all_capture_images()`
- `delete_capture_images_by_datetime(targetDate?: string, startDatetime?: string, endDatetime?: string)`

## 必要環境

- Windows
- .NET 10 SDK（ローカル実行時）

## 環境変数

- `CAPTURE_SCREEN_DEFAULT_DISPLAY`
  - `capture_display` で `display` 省略時の既定値
  - 例: `primary`, `left`, `right`, `プライマリ`, `左`, `右`, `2`
- `CAPTURE_SCREEN_OUTPUT_DIR`
  - 保存先ディレクトリ（既定: `C:\capture_screen`）
- `CAPTURE_SCREEN_HIDE_FOREGROUND_WINDOWS_TERMINAL`
  - `1/true/on` で有効、`0/false/off` で無効
  - 既定は有効

## ローカルでの起動方法

### ビルド

```powershell
dotnet restore
dotnet build
```

### MCP サーバー起動（stdio）

```powershell
dotnet run --project src
```

## 接続設定例

### Codex / Claude Code / VS Code 互換（stdio）

```json
{
  "servers": {
    "capture-screen": {
      "type": "stdio",
      "command": "dotnet",
      "args": ["run", "--project", "src"],
      "env": {
        "CAPTURE_SCREEN_OUTPUT_DIR": "C:\\capture_screen",
        "CAPTURE_SCREEN_DEFAULT_DISPLAY": "primary",
        "CAPTURE_SCREEN_HIDE_FOREGROUND_WINDOWS_TERMINAL": "1"
      }
    }
  }
}
```

## NuGet 公開（ローカル実行型 MCP サーバー配布）

1. `dotnet pack -c Release`
2. `dotnet nuget push bin/Release/*.nupkg --api-key <NUGET_API_KEY> --source https://api.nuget.org/v3/index.json`

このリポジトリには、NuGet MCP 公開向けメタデータとして以下を含みます。

- `.mcp/server.json`
- `README.md` の `<!-- mcp-name: ... -->` コメント

## 権限と注意点

- 本サーバーはローカル実行型です。MCP クライアントと同じユーザー権限で動作します。
- 画面キャプチャ結果はローカルファイルとして保存されます。機密情報が映り込む可能性に注意してください。
- 画像削除ツールは `CAPTURE_SCREEN_OUTPUT_DIR` 直下の画像ファイルを削除します。
- Windows 専用実装です。Windows 以外で実行するとエラーになります。

## マニフェスト

- 開発実行用: `server.json`
- NuGet MCP 公開用: `.mcp/server.json`
