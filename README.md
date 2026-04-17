<p align="left">
  <a href="README_en.md"><img src="https://img.shields.io/badge/English Mode-blue.svg" alt="English"></a>
  <a href="README.md"><img src="https://img.shields.io/badge/日本語 モード-red.svg" alt="日本語"></a>
</p>

# CaptureScreenMCP

<!-- mcp-name: io.github.ochtum/capture-screen -->

Windows 向けのローカル実行型 MCP サーバーです（`stdio` transport）。
C# / .NET 10 の .NET tool として NuGet.org に公開しており、画面キャプチャとキャプチャ画像削除ツールを提供します。

- NuGet: [CaptureScreenMcp](https://www.nuget.org/packages/CaptureScreenMcp)
- MCP Registry name: `io.github.ochtum/capture-screen`
- NuGet package ID: `CaptureScreenMcp`
- Tool command: `capture-screen-mcp`

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
- .NET 10 SDK
  - NuGet から MCP サーバーとして起動する場合は `dnx` を使用します。
  - 開発中にソースから起動する場合は `dotnet run` を使用します。

## 環境変数

- `CAPTURE_SCREEN_DEFAULT_DISPLAY`
  - `capture_display` で `display` 省略時の既定値
  - 例: `primary`, `left`, `right`, `プライマリ`, `左`, `右`, `2`
- `CAPTURE_SCREEN_OUTPUT_DIR`
  - 保存先ディレクトリ（既定: `C:\capture_screen`）
- `CAPTURE_SCREEN_HIDE_FOREGROUND_WINDOWS_TERMINAL`
  - `1/true/on` で有効、`0/false/off` で無効
  - 既定は有効

## NuGet から利用する

NuGet.org の公開済みパッケージを MCP クライアントから起動する場合は、`dnx` で `CaptureScreenMcp` を実行します。

```json
{
  "servers": {
    "capture-screen": {
      "type": "stdio",
      "command": "dnx",
      "args": ["CaptureScreenMcp@1.0.4", "--yes"],
      "env": {
        "CAPTURE_SCREEN_OUTPUT_DIR": "C:\\capture_screen",
        "CAPTURE_SCREEN_DEFAULT_DISPLAY": "primary",
        "CAPTURE_SCREEN_HIDE_FOREGROUND_WINDOWS_TERMINAL": "1"
      }
    }
  }
}
```

通常の .NET tool としてインストールして起動することもできます。

```powershell
dotnet tool install --global CaptureScreenMcp --version 1.0.4
capture-screen-mcp
```

## ソースから開発実行する

### ビルド

```powershell
dotnet restore
dotnet build
```

### MCP サーバー起動（stdio）

```powershell
dotnet run --project src
```

開発中にソースツリーを直接参照する場合の接続設定例です。

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

## 公開手順

### NuGet.org へ公開する

1. `src/CaptureScreenMcp.csproj` の `<Version>` を更新します。
2. `.mcp/server.json` のトップレベル `version` と `packages[0].version` を同じバージョンに更新します。
3. `dotnet pack src/CaptureScreenMcp.csproj -c Release`
4. `dotnet nuget push src/bin/Release/*.nupkg --api-key <NUGET_API_KEY> --source https://api.nuget.org/v3/index.json`

このパッケージは NuGet MCP サーバーとして認識されるため、以下を含めています。

- `.mcp/server.json`
- `README.md` の `<!-- mcp-name: io.github.ochtum/capture-screen -->` コメント
- `McpServer` package type
- .NET tool 設定（`PackAsTool` / `ToolCommandName`）

### MCP Registry へ公開する

NuGet.org への公開だけでは、`registry.modelcontextprotocol.io` には自動掲載されません。
NuGet.org のパッケージ検証が完了してから、MCP Publisher で `.mcp/server.json` を公開します。

```powershell
mcp-publisher login github
mcp-publisher publish .mcp/server.json
```

`server.json` の `name` と、NuGet パッケージに含まれる `README.md` の `mcp-name` は一致している必要があります。
また、`packages[0].version` は `mcp-name` が一致する NuGet パッケージのバージョンを指している必要があります。

## 権限と注意点

- 本サーバーはローカル実行型です。MCP クライアントと同じユーザー権限で動作します。
- 画面キャプチャ結果はローカルファイルとして保存されます。機密情報が映り込む可能性に注意してください。
- 画像削除ツールは `CAPTURE_SCREEN_OUTPUT_DIR` 直下の画像ファイルを削除します。
- Windows 専用実装です。Windows 以外で実行するとエラーになります。

## マニフェスト

- 開発実行用: `server.json`
- NuGet MCP 公開用: `.mcp/server.json`
