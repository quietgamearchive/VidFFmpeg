# VidFFmpeg

## 1. English

VidFFmpeg is a lightweight FFmpeg batch transcoding queue manager.

The idea of this project came from VidCoder. Its **Encoding settings** combined with **Picker** are very convenient, but the GUI feels a little heavy for my needs, and I wanted a simpler tool that could be used across different platforms.

Based on my own workflow, I extracted only the functions I actually need and created this project with the help of ChatGPT.

VidFFmpeg is mainly developed for personal use. I do not plan to add unnecessary features or make it overly complicated.

Since the project is open source, anyone can download it, use it, and modify it for their own needs.

## Versions

VidFFmpeg currently provides two versions:

- **VidFFmpeg_CLI** — Command-line version
- **VidFFmpeg_GUI** — Graphical user interface version

Both versions use FFmpeg for video processing.

### VidFFmpeg_CLI

The CLI version is designed for users who prefer a lightweight command-line interface.

Download the compiled `VidFFmpeg_CLI` executable and run it directly from the terminal.

The CLI version uses `config.json` to store the FFmpeg and FFprobe paths.

### VidFFmpeg_GUI

The GUI version provides the same core transcoding functionality through a graphical interface.

FFmpeg and FFprobe paths can be configured through the **Config** menu, so manually editing the configuration file is not required.

## Requirements

- FFmpeg
- FFprobe

Python is **not required** when using the compiled versions.

FFmpeg and FFprobe must be installed separately.

## First-time setup

After downloading VidFFmpeg, you need to configure the paths to FFmpeg and FFprobe before using the converter.

### CLI

For `VidFFmpeg_CLI`, edit `config.json` and set the FFmpeg and FFprobe paths for your operating system.

The configuration file contains separate settings for different operating systems. Set the paths corresponding to your system.

The exact paths depend on where FFmpeg and FFprobe are installed on your system.

### GUI

For `VidFFmpeg_GUI`, open the **Config** menu after the first launch.

You can configure the FFmpeg and FFprobe paths directly from the graphical interface.

The configuration is saved automatically.

## Platform support

### Windows

Windows is the primary development and testing platform.

Compiled Windows versions are provided for both CLI and GUI.

### Linux

Linux support is theoretically possible, but the current version has **not been tested on Linux yet**.

The main functionality should work in theory, but the current release should be considered untested on Linux.

You may need to adjust the FFmpeg and FFprobe paths in `config.json` when using the CLI version.

## Profiles

The `profiles` folder contains FFmpeg encoding presets.

You can edit the existing profiles or create your own encoding configurations according to your needs.

Profiles allow you to define your preferred FFmpeg encoding parameters without modifying the main program.

## Basic workflow

### CLI

1. Run `VidFFmpeg_CLI`.
2. Configure FFmpeg and FFprobe paths if this is the first run.
3. Add files to the queue.
4. Select an encoding profile.
5. Start the conversion.

### GUI

1. Run `VidFFmpeg_GUI`.
2. Open **Config** and configure FFmpeg and FFprobe paths if this is the first run.
3. Add files to the queue.
4. Select an encoding profile.
5. Start the conversion.

The queue is stored locally and can be processed by VidFFmpeg.

## Conversion control

During conversion:

- Press `Ctrl+C` once in the CLI version to stop the current conversion and automatically clean up temporary files.
- Press `Enter` to exit after the current file finishes converting.

The exact available controls may differ between the CLI and GUI versions.

## Custom feature: Automatic cut detection from filename

VidFFmpeg includes a special feature created for my own workflow.

It can automatically detect video cut points from filenames.

The filename itself is not changed. This makes it easier to identify the original file and verify the intended cut points later.

Examples:

    name 010102cut.mp4
    Keep content from the beginning to 01:01:02

    name 0103cut.mp4
    Keep content from the beginning to 00:01:03

    name 1001cut~2020cut.mp4
    Keep content from 00:10:01 to 00:20:20

    name 011001cut~.mp4
    Keep content from 01:10:01 to the end

    name 011946cut~023903cut.mp4
    Keep content from 01:19:46 to 02:39:03

Time format supports:

- `MMSS`
- `HHMMSS`

Examples:

    2510   = 00:25:10
    022230 = 02:22:30

| Input | Start | End |
| ------------------------- | ---------- | ---------- |
| `010102cut.mp4`           |            | `01:01:02` |
| `0103cut.mp4`             |            | `00:01:03` |
| `1001cut~2020cut.mp4`     | `00:10:01` | `00:20:20` |
| `011001cut~.mp4`          | `01:10:01` |            |
| `011946cut~023903cut.mp4` | `01:19:46` | `02:39:03` |

## External dependencies

VidFFmpeg uses **FFmpeg** and **FFprobe** for video processing.

FFmpeg and FFprobe are **not included** with VidFFmpeg.

Please install them separately.

Please refer to the official FFmpeg license and documentation for the corresponding licensing terms.

## License

[Quiet Game Archive](https://www.youtube.com/@quietgamearchive)

Copyright (c) 2026 Quiet Game Archive

VidFFmpeg is released under the GNU General Public License v3.0.

See `LICENSE` for details.

---

# 2. 日本語

VidFFmpegは軽量なFFmpegバッチ変換キュー管理ツールです。

このプロジェクトのアイデアはVidCoderから来ています。VidCoderの
**Encoding settings** と **Picker**
の組み合わせは非常に便利ですが、自分の用途にはGUIが少し重く感じられ、よりシンプルで複数のプラットフォームで使用できるツールが欲しいと思ったことから、このプロジェクトを作りました。

自分の実際の使用環境に合わせて、必要な機能だけを取り出して、このプロジェクトを作成しました。
開発にはChatGPTも利用しています。

VidFFmpegは基本的に個人用途を目的として開発しています。
不要な機能を追加したり、必要以上に複雑なソフトウェアにしたりする予定はありません。

オープンソースなので、自由にダウンロードして使用したり、自分の用途に合わせて改造したりできます。

## バージョン

現在、VidFFmpegには以下の2種類があります。

- **VidFFmpeg_CLI** — コマンドライン版
- **VidFFmpeg_GUI** — GUI版

どちらもFFmpegを使用して動画処理を行います。

### VidFFmpeg_CLI

CLI版は、軽量なコマンドラインインターフェースを好むユーザー向けです。

コンパイル済みの`VidFFmpeg_CLI`をダウンロードし、ターミナルから直接実行できます。

CLI版では`config.json`を使用してFFmpegおよびFFprobeのパスを設定します。

### VidFFmpeg_GUI

GUI版では、グラフィカルなインターフェースから動画変換を行えます。

FFmpegおよびFFprobeのパスは**Config**メニューから設定できます。
設定ファイルを手動で編集する必要はありません。

## 必要なソフトウェア

- FFmpeg
- FFprobe

コンパイル済みのバージョンを使用する場合、Pythonは必要ありません。

FFmpegおよびFFprobeは別途インストールしてください。

## 初回設定

VidFFmpegをダウンロードした後、使用する前にFFmpegおよびFFprobeのパスを設定する必要があります。

### CLI

`VidFFmpeg_CLI`では、`config.json`を編集し、使用するOSに対応するFFmpegおよびFFprobeのパスを設定してください。

設定ファイルにはOSごとの設定項目があります。
使用するシステムに対応する項目のパスを設定してください。

実際のパスは、FFmpegおよびFFprobeをインストールした場所によって異なります。

### GUI

`VidFFmpeg_GUI`では、初回起動後に**Config**メニューを開いてください。

GUIからFFmpegおよびFFprobeのパスを直接設定できます。

設定は自動的に保存されます。

## 対応プラットフォーム

### Windows

Windowsを主な開発およびテスト環境としています。

Windows向けにはCLI版とGUI版のコンパイル済みバージョンを提供しています。

### Linux

Linuxでの動作は理論上可能ですが、現在のバージョンは**Linux環境ではまだテストされていません**。

基本的な機能は理論上動作するはずですが、現在のリリースではLinuxでの動作を保証していません。

LinuxでCLI版を使用する場合、`config.json`内のFFmpegおよびFFprobeのパスを環境に合わせて変更する必要がある場合があります。

## Profiles

`profiles`フォルダにはFFmpegのエンコードプリセットが保存されています。

既存のプロファイルを編集したり、自分用のエンコード設定を作成したりできます。

プロファイルを使用することで、メインプログラムを変更せずに、好みのFFmpegエンコード設定を使用できます。

## 基本的な使用方法

### CLI

1. `VidFFmpeg_CLI`を起動します。
2. 初回起動時はFFmpegおよびFFprobeのパスを設定します。
3. ファイルをキューに追加します。
4. エンコードプロファイルを選択します。
5. 変換を開始します。

### GUI

1. `VidFFmpeg_GUI`を起動します。
2. 初回起動時は**Config**からFFmpegおよびFFprobeのパスを設定します。
3. ファイルをキューに追加します。
4. エンコードプロファイルを選択します。
5. 変換を開始します。

キューはローカルに保存され、VidFFmpegから処理できます。

## 変換中の操作

変換中:

- CLI版で`Ctrl+C`を1回押すと、現在の変換を停止し、一時ファイルを自動的に削除します。
- `Enter`を押すと、現在のファイルの変換終了後に自動終了します。

CLI版とGUI版では利用できる操作が異なる場合があります。

## 独自機能: ファイル名から自動カット位置判定

VidFFmpegには、自分の用途向けに追加した特殊な機能があります。

ファイル名から動画のカット位置を自動判定できます。

ファイル名自体は変更しません。
後から元ファイルやカット位置を確認しやすくするためです。

例:

    name 010102cut.mp4
    先頭から01:01:02まで保存

    name 0103cut.mp4
    先頭から00:01:03まで保存

    name 1001cut~2020cut.mp4
    00:10:01から00:20:20まで保存

    name 011001cut~.mp4
    01:10:01から最後まで保存

    name 011946cut~023903cut.mp4
    01:19:46から02:39:03まで保存

時間形式:

- `MMSS`
- `HHMMSS`

例:

    2510   = 00:25:10
    022230 = 02:22:30

| 入力ファイル | 開始 | 終了 |
| ------------------------- | ---------- | ---------- |
| `010102cut.mp4`           |            | `01:01:02` |
| `0103cut.mp4`             |            | `00:01:03` |
| `1001cut~2020cut.mp4`     | `00:10:01` | `00:20:20` |
| `011001cut~.mp4`          | `01:10:01` |            |
| `011946cut~023903cut.mp4` | `01:19:46` | `02:39:03` |

## 外部依存ソフトウェア

VidFFmpegは動画処理のために**FFmpeg**および**FFprobe**を使用しています。

FFmpegおよびFFprobeはVidFFmpegには含まれていません。

別途インストールしてください。

ライセンス条件については、FFmpegの公式ドキュメントおよびライセンス情報を確認してください。

## ライセンス

[Quiet Game Archive](https://www.youtube.com/@quietgamearchive)

Copyright (c) 2026 Quiet Game Archive

VidFFmpegはGNU General Public License v3.0のもとで公開されています。

詳しいライセンス内容については`LICENSE`ファイルをご確認ください。