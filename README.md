# VidFFmpeg

## 1. English

VidFFmpeg is a lightweight FFmpeg batch transcoding queue manager.

The idea of this project came from VidCoder. Its **Encoding settings**
combined with **Picker** is very convenient, but the GUI feels a little
heavy for my needs, and it does not support cross-platform usage.

Based on my own workflow, I extracted only the functions I actually need
and created this project with the help of ChatGPT.

This project is still mainly developed for personal use. I do not plan
to add unnecessary features. Since it is open source, anyone can
download it and use AI-assisted development to modify it for their own
needs.

## Requirements

-   Python 3
-   FFmpeg
-   FFprobe

Linux support is theoretically possible. The current version has not
been tested on Linux yet. You may only need to adjust the FFmpeg/FFprobe
paths.

## External dependencies

VidFFmpeg uses FFmpeg and FFprobe for video processing.

FFmpeg and FFprobe are not included in this project.  
Please install them separately and refer to the official FFmpeg license for the corresponding licensing terms.

## Setup

Before running, you need to modify:

1.  `1.queue_win.py`
    -   Currently designed for Windows Terminal.
    -   Supports drag and drop for adding files/folders.
    -   Linux terminal usage has not been tested and may require
        manually entering paths.
2.  `2.converter.py`
    -   Change the `ffmpeg.exe` and `ffprobe.exe` paths at the beginning
        of the file to match your system.

You need to prepare FFmpeg and FFprobe yourself.

## Profiles

The `profiles` folder contains FFmpeg parameter presets.

You can edit these files and create your own encoding configurations.

## Basic workflow

1.  Run `1.queue_win.py`
    -   Add files to `queue.json`.
2.  Run `2.converter.py`
    -   Automatically process the queue.

During conversion:

-   Press `Ctrl+C` once to stop conversion and automatically delete
    temporary files.
-   Press `Enter` to exit automatically after the current file finishes
    converting.

## Custom feature: Automatic cut detection from filename

This project includes a special feature for my own workflow.

It can automatically detect video cut points from filenames.

The filename itself is not changed. This makes it easier to confirm the
original file and verify the cut points later.

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

-   MMSS
-   HHMMSS

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

------------------------------------------------------------------------

## License

[Quiet Game Archive](https://www.youtube.com/@quietgamearchive)

Copyright (c) 2026 Quiet Game Archive

VidFFmpeg is released under the GNU General Public License v3.0.

See LICENSE for details.

# 2. 日本語

VidFFmpegは軽量なFFmpegバッチ変換キュー管理ツールです。

このプロジェクトのアイデアはVidCoderから来ています。 VidCoderの
**Encoding settings** と **Picker**
の組み合わせは非常に便利ですが、GUIが少し重く感じられ、またクロスプラットフォーム対応ではありません。

自分の実際の使用環境に合わせて、必要な機能だけを取り出して、このプロジェクトを作成しました。
開発にはChatGPTも利用しています。

このソフトは基本的に個人用途向けです。
不要な機能を追加する予定はありません。

オープンソースなので、自由にダウンロードして、AIなどを利用しながら自分向けに改造できます。

## 必要環境

-   Python 3
-   FFmpeg
-   FFprobe

Linuxでも理論上動作可能です。
ただし、現在Linux環境ではまだテストしていません。 FFmpeg /
FFprobeのパスを変更するだけで動作する可能性があります。

## 外部依存ソフトウェア

VidFFmpegは動画処理のためにFFmpegおよびFFprobeを使用しています。

FFmpegおよびFFprobeはこのプロジェクトには含まれていません。  
別途インストールしてください。また、ライセンス条件についてはFFmpegの公式ライセンスを確認してください。

## 初期設定

実行前に以下を変更してください。

1.  `1.queue_win.py`
    -   現在はWindows Terminal向けです。
    -   ファイルやフォルダのドラッグ＆ドロップ追加に対応しています。
    -   Linux端末では未検証で、パスを手入力する必要がある可能性があります。
2.  `2.converter.py`
    -   ファイル先頭にある`ffmpeg.exe` /
        `ffprobe.exe`のパスを環境に合わせて変更してください。

FFmpegとFFprobeは各自で準備してください。

## Profiles

`profiles`フォルダにはFFmpeg設定プリセットがあります。

必要に応じて編集し、自分用のエンコード設定を作成できます。

## 基本的な使用方法

1.  `1.queue_win.py`を実行
    -   ファイルを追加して`queue.json`を作成します。
2.  `2.converter.py`を実行
    -   キューの内容を自動変換します。

変換中:

-   `Ctrl+C`を1回押すと変換を停止し、一時ファイルを自動削除します。
-   `Enter`を押すと、現在のファイル変換終了後に自動終了します。

## 独自機能: ファイル名から自動カット位置判定

この機能は自分の用途向けに追加したものです。

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

-   MMSS
-   HHMMSS

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

VidFFmpegは動画処理のためにFFmpegおよびFFprobeを使用しています。

FFmpegおよびFFprobeはこのプロジェクトには含まれていません。  
別途インストールしてください。また、ライセンス条件についてはFFmpegの公式ライセンスを確認してください。

## ライセンス

[Quiet Game Archive](https://www.youtube.com/@quietgamearchive)

Copyright (c) 2026 Quiet Game Archive

VidFFmpegはGNU General Public License v3.0のもとで公開されています。

詳しいライセンス内容については、LICENSEファイルをご確認ください。
