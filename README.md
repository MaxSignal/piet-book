# Piet プログラミング入門 ― 絵を描いてプログラムを書く

MaxSignal 著、-Rainy Angel- 発行の書籍『Piet プログラミング入門 ― 絵を描いてプログラムを書く』の、原稿・PDF・付属ツール・全サンプル・生成スクリプト一式です。

[Piet](https://www.dangermouse.net/esoteric/piet.html) は、David Morgan-Mar 氏が設計したプログラミング言語です。色のついたマス目（コーデル）を並べた画像そのものがプログラムになります。本書は、5 を出力する小さな絵から始めて、色と命令の関係、スタックと分岐・ループ、実践的なプログラム、そしてインタプリタ・アセンブラ・コンパイラの自作までを、全 20 章と付録で解説します。

- **PDF**: [Releases](https://github.com/MaxSignal/piet-book/releases) からダウンロードできます（B5、488 ページ）。
- **紙の本**: 本として手元に置きたい方は、頒布の情報をご覧ください（X: [@MaxSignal_](https://x.com/MaxSignal_)）。

## 中身

| パス | 内容 |
|---|---|
| `src/` | 原稿（Markdown）。`chNN.md` が各章、`appX.md` が付録、`answers/` が練習問題の解答 |
| `samples/` | 本に掲載した Piet のサンプル。`.txt`（テキスト記法）、`.pasm`（アセンブリ）、`.mini`（Mini 言語）と、入力 `.in*`・期待される出力 `.out*` |
| `images/` | 全サンプルの PNG 画像（1 コーデル = 10 ピクセル） |
| `tools/pietstudio.py` | **Piet スタジオ**。Piet のエディタ兼デバッガ（Python 標準の tkinter だけで動くデスクトップアプリ） |
| `tools/piet.py` | 仕様に従った Piet インタプリタ（画像の読み込み・トレース・テキスト記法との変換） |
| `tools/pasm.py` | アセンブラ。スタック命令とラベル・ジャンプを書いたテキストから Piet の画像を生成する |
| `tools/minic.py` | 小さな言語 Mini から Piet へのコンパイラ |
| `tools/samples.py` | サンプルを画像に変換し、piet.py（と、あれば npiet）で実行して期待される出力と照合する |
| `tools/build.py` ほか | Web 版（ブラウザで図を実行できる HTML）の生成。`tools/web/` はブラウザ用のインタプリタとプレイグラウンド |
| `tools/printbook.py`、`print/` | 書籍版（PDF）の組版。Vivliostyle と Ghostscript を使う |
| `STYLE.md` | 執筆ガイド（原稿の書き方と特殊記法） |

## ツールを使う

必要なもの: Python 3.8 以降。Piet スタジオには tkinter（python.org 版の Python には同梱。Ubuntu などでは `sudo apt install python3-tk`）、画像の読み書きには Pillow（`pip install pillow`）。

```sh
python3 tools/pietstudio.py images/ch01/five.png      # Piet スタジオで開く
python3 tools/piet.py run images/ch01/five.png         # 実行する（5 が出力される）
python3 tools/piet.py run -t images/ch01/five.png      # トレースを表示しながら実行する
python3 tools/piet.py png samples/ch01/five.txt five.png -cs 10   # テキスト記法から画像を作る
python3 tools/pasm.py samples/ch10/countup.pasm -o countup.png    # アセンブリから画像を作る
python3 tools/minic.py samples/ch18/fizzbuzz.mini -o fizzbuzz.png # Mini から画像を作る
```

テキスト記法は 1 文字が 1 コーデルです（淡い色 `r y g c b m`、通常の色 `R Y G C B M`、濃い色 `1`〜`6`（赤・黄・緑・シアン・青・マゼンタの順）、白 `.`、黒 `#`）。

## 本を作る

```sh
pip install pillow markdown beautifulsoup4 lxml
python3 tools/samples.py          # 全サンプルを画像にして検証する（npiet があれば npiet とも照合）
python3 tools/build.py            # Web 版を site/ に作る
cd print && npm install && bash build.sh S   # 書籍版の PDF を print/out/S/ に作る
```

- npiet は https://www.bertnase.de/npiet/ から入手してビルドし、PATH に置くか環境変数 `NPIET` で指定します（無ければ照合を省略します）。
- 書籍版には Noto Serif CJK JP・Noto Sans CJK JP・Noto Sans Mono（システムにインストール）と、Chromium（環境変数 `CHROME`）、Ghostscript が必要です。見出しのフォント Dela Gothic One は `build.sh` が自動で取得します。
- `print/build.sh` の版: `S`（本書。付録以外カラー）、`D`（S から頒布価格・ISDN を除いた版）、`C1`/`C2`（上下 2 分冊）、`A`（第IV部をモノクロにした版）。印刷所向けの調整（巻頭カラー・モノクロ混在、背幅の自動取得）は、ちょ古っ都製本工房の仕様に合わせています。

## ライセンス

このリポジトリのすべて（原稿・PDF・ツールのソースコード・サンプル・生成スクリプト）は [CC0 1.0](LICENSE)（パブリックドメイン提供）です。著作権表示なしで、自由に使い、改変し、自分のものとして配布してかまいません。

ただし、本文中で出典を示して引用している他者の文章（Piet の仕様の一節など）の権利は、それぞれの著作者にあります。

本書の文章・サンプルプログラム・ツールは、AI アシスタントの Claude（Anthropic）を用いて作成しました。
