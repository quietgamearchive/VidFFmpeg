# VidFFmpeg

**Lightweight FFmpeg batch transcoding queue manager** / **軽量なFFmpegバッチ変換キュー管理ツール**

---

## Overview / 概要

VidFFmpeg is a batch video transcoding tool based on FFmpeg, available in two versions: CLI and GUI.

VidFFmpeg は FFmpeg ベースのバッチ動画トランスコードツールです。CLI版とGUI版の2種類があります。

The idea came from [VidCoder](https://vidcoder.net/). Its **Encoding settings** combined with **Picker** are very convenient, but the GUI felt a bit heavy and it did not support cross-platform use. Based on my actual workflow, I extracted only the features I needed and completed this project with AI assistance.

このプロジェクトのアイデアは [VidCoder](https://vidcoder.net/) から来ています。**Encoding settings** と **Picker** の組み合わせは非常に便利ですが、GUIが少し重く感じられ、またクロスプラットフォームに対応していませんでした。自分の実際のワークフローに合わせて必要な機能だけを抽出し、AIの支援を受けてこのプロジェクトを完成させました。

This project is mainly for personal use. There is no plan to add unnecessary features or make it overly complicated. Since it is open source, anyone can freely download, use, and modify it.

このプロジェクトは主に個人用途を目的としています。不要な機能を追加したり、必要以上に複雑にしたりする予定はありません。オープンソースなので、誰でも自由にダウンロードして使用・改変できます。

## Versions / バージョン

| Version | Description / 説明 |
|---------|---------------------|
| **VidFFmpeg_CLI** | Command-line version, for users who prefer a lightweight terminal workflow. / コマンドライン版。軽量なターミナル操作を好むユーザー向け。 |
| **VidFFmpeg_GUI** | Graphical interface version, providing the same core transcoding functions. / グラフィカルインターフェース版。同じコア変換機能を提供します。 |

Both versions use FFmpeg for video processing. / どちらのバージョンもFFmpegを使用して動画処理を行います。

## Requirements / 必要なソフトウェア

- **FFmpeg** + **FFprobe** — must be installed separately, not bundled with the package / 別途インストールが必要です（ソフトウェアには含まれていません）
- The compiled versions do not require a Python environment. / コンパイル済みバージョンを使用する場合、Python環境は必要ありません。

## Quick Start / クイックスタート

### First-time Setup / 初回設定

1. Download VidFFmpeg. / VidFFmpegをダウンロードします。
2. Configure the FFmpeg and FFprobe paths. / FFmpegとFFprobeのパスを設定します。

#### CLI

Edit `config.json` and set the ffmpeg/ffprobe paths according to your operating system:

`config.json` を編集し、お使いのOSに合わせてffmpeg/ffprobeのパスを設定します:

```json
{
    "ffmpeg_win": "C:/path/to/ffmpeg.exe",
    "ffprobe_win": "C:/path/to/ffprobe.exe",
    "ffmpeg_linux": "/usr/bin/ffmpeg",
    "ffprobe_linux": "/usr/bin/ffprobe"
}
```

#### GUI

After launching, open the **Config** menu and set the paths directly from the graphical interface. The configuration is saved automatically.

起動後、**Config** メニューを開き、グラフィカルインターフェースから直接パスを設定します。設定は自動的に保存されます。

### Basic Workflow / 基本的な使用方法

#### CLI

1. Run `VidFFmpeg_CLI`. / `VidFFmpeg_CLI` を起動します。
2. Configure the FFmpeg/FFprobe paths on first run. / 初回起動時にFFmpeg/FFprobeのパスを設定します。
3. Select an encoding profile and add files to the queue. / エンコードプロファイルを選択し、ファイルをキューに追加します。
4. Start the conversion. / 変換を開始します。

#### GUI

1. Run `VidFFmpeg_GUI`. / `VidFFmpeg_GUI` を起動します。
2. On first run, open **Config** and set the FFmpeg/FFprobe paths. / 初回起動時は **Config** でFFmpeg/FFprobeのパスを設定します。
3. Drag and drop files to add them to the queue (or add via menu). / ファイルをドラッグ＆ドロップでキューに追加します（メニューからも追加可能）。
4. Select an encoding profile. / エンコードプロファイルを選択します。
5. Start the conversion. / 変換を開始します。

The queue is stored locally in `queue.json` and can be processed at any time. / キューはローカルの `queue.json` に保存され、いつでも処理できます。

## Platform Support / 対応プラットフォーム

### Windows

Primary development and testing platform. Compiled versions are provided for both CLI and GUI. / 主要な開発・テスト環境です。CLI版とGUI版のコンパイル済みバージョンを提供しています。

### Linux

Theoretically supported, but **not yet fully tested on Linux**. The core functionality should work, but the CLI version may require manually adjusting the FFmpeg/FFprobe paths in `config.json`. / 理論上は対応していますが、**Linux環境ではまだ十分なテストが行われていません**。コア機能は動作するはずですが、CLI版では `config.json` 内のFFmpeg/FFprobeパスを手動で調整する必要がある場合があります。

## Features / 機能

### Encoding Profiles / エンコードプロファイル

The `profiles/` folder contains FFmpeg encoding presets (JSON format). You can edit existing files or create your own configurations without modifying the main program.

`profiles/` フォルダにはFFmpegのエンコードプリセット（JSON形式）が保存されています。既存のファイルを編集したり、メインプログラムを変更せずに独自の設定を作成したりできます。

**Profile structure / プロファイル構造:**

```json
{
    "name": "av1 same dir",
    "ffmpeg_args": [
        "-c:v", "libsvtav1",
        "-preset", "4",
        "-crf", "50"
    ],
    "output": {
        "directory": "",
        "filename": "{source}_av1",
        "extension": ".mp4"
    },
    "after_finish": {
        "delete_source": false
    }
}
```

- `ffmpeg_args`: custom FFmpeg arguments / カスタムFFmpeg引数
- `output.directory`: output directory (empty = same directory as source) / 出力ディレクトリ（空 = ソースと同じディレクトリ）
- `output.filename`: output file name (`{source}` is replaced with the source file name) / 出力ファイル名（`{source}` はソースファイル名に置き換えられます）
- `output.extension`: output file extension / 出力拡張子
- `after_finish.delete_source`: whether to delete the source file after transcoding / 変換完了後にソースファイルを削除するかどうか

**Preset examples / プリセット例:**

| File | Description / 説明 |
|------|---------------------|
| `1.av1(same dir).json` | AV1 encoding, output to the source directory / AV1エンコード、ソースディレクトリに出力 |
| `2.av1(same dir+del).json` | AV1 encoding, output to the source directory, delete source after completion / AV1エンコード、ソースディレクトリに出力、完了後にソース削除 |
| `3.av1(custom dir).json` | AV1 encoding, output to a custom directory / AV1エンコード、カスタムディレクトリに出力 |
| `5.x265(same dir).json` | x265 encoding, output to the source directory / x265エンコード、ソースディレクトリに出力 |
| `7.x265(custom dir).json` | x265 encoding, output to a custom directory / x265エンコード、カスタムディレクトリに出力 |

### Automatic Cut Detection from Filename / ファイル名からの自動カット位置判定

VidFFmpeg can automatically detect video cut points from filenames. The filename itself is never changed, making it easier to verify the original file and cut points later.

VidFFmpegはファイル名から動画のカット位置を自動判定できます。ファイル名自体は変更されないため、後から元ファイルやカット位置を確認しやすくなっています。

**Time formats / 時間形式:**

- `MMSS` — minutes and seconds (e.g., `2510` = 00:25:10) / 分秒（例: `2510` = 00:25:10）
- `HHMMSS` — hours, minutes and seconds (e.g., `022230` = 02:22:30) / 時分秒（例: `022230` = 02:22:30）

**Examples / 使用例:**

| Input filename / 入力ファイル名 | Start / 開始 | End / 終了 |
|--------------------------------|-------------|-----------|
| `010102cut.mp4`                |             | `01:01:02` |
| `0103cut.mp4`                  |             | `00:01:03` |
| `1001cut~2020cut.mp4`          | `00:10:01`  | `00:20:20` |
| `011001cut~.mp4`               | `01:10:01`  |           |
| `011946cut~023903cut.mp4`      | `01:19:46`  | `02:39:03` |

### Conversion Control / 変換中の操作

#### CLI

- **Ctrl+C**: stop the current conversion and automatically clean up temporary files / 現在の変換を停止し、一時ファイルを自動的に削除します
- **Enter**: automatically exit after the current file finishes converting / 現在のファイルの変換終了後に自動終了します
- **Ctrl+C twice**: force quit / **Ctrl+C を2回**: 強制終了します

#### GUI

- **Stop**: stop the current conversion (cleans up temporary files) / 現在の変換を停止します（一時ファイルを削除）
- **Pause/Resume**: pause/resume the current conversion / 現在の変換を一時停止/再開します
  - Windows: suspends/resumes threads using the Windows API / Windows APIを使用してスレッドを一時停止/再開
  - Linux: uses SIGSTOP/SIGCONT / SIGSTOP/SIGCONTを使用
- **Close Application**: automatically close the program after the current conversion finishes / 現在の変換完了後にプログラムを自動的に閉じます

### Configuration Items / 設定項目

`config.json` supports the following settings / `config.json` では以下の設定が可能です:

| Key / キー | Type / 型 | Description / 説明 |
|------------|-----------|---------------------|
| `ffmpeg_win` | string | Windows FFmpeg path / Windows版FFmpegのパス |
| `ffprobe_win` | string | Windows FFprobe path / Windows版FFprobeのパス |
| `ffmpeg_linux` | string | Linux FFmpeg path / Linux版FFmpegのパス |
| `ffprobe_linux` | string | Linux FFprobe path / Linux版FFprobeのパス |
| `video_extensions` | string array | Supported file extensions / 対応するファイル拡張子 |
| `exclude_keywords` | string array | Files containing these keywords are excluded / これらのキーワードを含むファイルを除外 |
| `current_profile` | string | Currently selected encoding profile / 現在選択中のエンコードプロファイル |
| `ffprobe_threads` | integer | ffprobe concurrent thread count / ffprobeの並行スレッド数 |
| `Left` / `Top` | integer | Window position (GUI only) / ウィンドウ位置（GUIのみ） |

A `$` prefix in a path means relative to the program root directory. / パスの先頭の `$` はプログラムのルートディレクトリからの相対パスを意味します。

### Log System / ログシステム

- `finished.txt`: records successfully transcoded files (path, duration, elapsed time, completion time, size, compression ratio) / 変換に成功したファイルを記録（パス、時間、所要時間、完了時刻、サイズ、圧縮率）
- `error.txt`: records failed files (path, time, error reason) / 変換に失敗したファイルを記録（パス、時刻、エラー理由）
- The GUI provides paged views (Finished / Error pages) with right-click deletion support / GUIにはページ表示（Finished / Error ページ）があり、右クリックでレコードを削除できます

## Project Structure / プロジェクト構成

```
VidFFmpeg/
├── VidFFmpeg_CLI.py          # CLI entry / CLIエントリ
├── VidFFmpeg_GUI.py          # GUI entry / GUIエントリ
├── config.json               # Config file (generated after first run) / 設定ファイル（初回起動後に生成）
├── queue.json                # Conversion queue (generated after importing videos) / 変換キュー（動画インポート後に生成）
├── finished.txt              # Success log (generated after successful conversion) / 成功ログ（変換成功後に生成）
├── error.txt                 # Error log (generated after failed conversion) / エラーログ（変換失敗後に生成）
├── cli/
│   ├── config.py             # Config load/save / 設定の読み込み/保存
│   ├── convert.py            # Core transcoding engine / コア変換エンジン
│   ├── queuefile.py          # Queue file read/write / キューファイルの読み書き
│   ├── queuestatus.py        # Queue statistics / キュー統計
│   ├── selprofile_addfiles.py # Select profile + add files / プロファイル選択+ファイル追加
│   ├── checkmissingfiles.py  # Check missing files / 欠落ファイルのチェック
│   └── startup_check_ffmpeg.py # Startup check / 起動時チェック
├── gui/
│   ├── treeview.py           # Main queue list / メインキューのリスト
│   ├── treeview_contextmenu.py # Context menu / コンテキストメニュー
│   ├── treeview_dragdrop.py  # Drag & drop file adding / ドラッグ＆ドロップによるファイル追加
│   ├── convert_win.py        # Windows transcoding engine / Windows変換エンジン
│   ├── convert_linux.py      # Linux transcoding engine / Linux変換エンジン
│   ├── btns.py               # Control buttons / コントロールボタン
│   ├── menu.py               # Top menu / トップメニュー
│   ├── config.py             # Config load/path resolution / 設定読み込み/パス解決
│   ├── configwindow.py       # Config window / 設定ウィンドウ
│   ├── paged_treeview.py     # Paged logs / ページ式ログ
│   ├── msgbox.py             # Message dialogs / メッセージダイアログ
│   ├── profile_selector.py   # Profile selector / プロファイルセレクタ
│   ├── init_check.py         # Startup check / 起動チェック
│   └── debug.py              # Debug tools / デバッグツール
├── profiles/                 # Encoding presets / エンコードプリセット
│   ├── 1.av1(same dir).json
│   ├── 2.av1(same dir+del).json
│   ├── 3.av1(custom dir).json
│   ├── ...
├── common/                   # Common modules / 共通モジュール
│   ├── single_instance.py    # Single-instance lock / シングルインスタンスロック
│   └── __init__.py
```

## Build / ビルド

The project uses GitHub Actions for automatic builds (`workflow/pyinstaller.yml`), supporting both Windows and Linux.

このプロジェクトはGitHub Actionsを使用して自動ビルド（`workflow/pyinstaller.yml`）を行い、WindowsとLinuxの両方に対応しています。

Build commands / ビルドコマンド:

```bash
pip install pyinstaller tkinterdnd2
pyinstaller --clean --noconfirm --onedir VidFFmpeg_CLI.py
pyinstaller --clean --noconfirm --onedir --windowed --collect-all tkinterdnd2 VidFFmpeg_GUI.py
```

## External Dependencies / 外部依存ソフトウェア

| Software / ソフトウェア | Description / 説明 |
|--------------------------|---------------------|
| [FFmpeg](https://ffmpeg.org/) | Core video processing engine / コア動画処理エンジン |
| [FFprobe](https://ffmpeg.org/) | Video information probing (part of the FFmpeg suite) / 動画情報の取得（FFmpegスイートの一部） |
| PyInstaller | Build-time only, packages the program into an executable / ビルド時のみ必要、実行ファイルにパッケージング |
| tkinterdnd2 | GUI dependency, provides drag & drop support / GUI版の依存、ドラッグ＆ドロップ対応 |

Please refer to the [FFmpeg official license](https://ffmpeg.org/legal.html) for the applicable license terms.

ライセンス条件については [FFmpeg公式ライセンス](https://ffmpeg.org/legal.html) をご確認ください。

## License / ライセンス

[Quiet Game Archive](https://www.youtube.com/@quietgamearchive)

Copyright (c) 2026 Quiet Game Archive

VidFFmpeg is released under the GNU General Public License v3.0. / VidFFmpegはGNU General Public License v3.0のもとで公開されています。

See the `LICENSE` file for details. / 詳しい内容は `LICENSE` ファイルをご確認ください。
