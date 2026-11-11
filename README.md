# Piet プログラミング入門 ― 付属ツールとサンプル

同人誌『Piet プログラミング入門 ― 絵を描いてプログラムを書く』（MaxSignal 著、-Rainy Angel- 発行）の付属ツールと、本に掲載したすべての Piet サンプルプログラムです。

[Piet](https://www.dangermouse.net/esoteric/piet.html) は、David Morgan-Mar 氏が設計した、色のついたマス目（コーデル）を並べた画像そのものがプログラムになる難解プログラミング言語です。

## 内容

| パス | 内容 |
|---|---|
| `tools/pietstudio.py` | **Piet スタジオ**。Piet のエディタ兼デバッガ（Python 標準の tkinter だけで動くデスクトップアプリ） |
| `tools/piet.py` | 仕様に従った Piet インタプリタ（画像の読み込み・トレース・テキスト記法との変換） |
| `tools/pasm.py` | アセンブラ。スタック命令とラベル・ジャンプを書いたテキストから Piet の画像を生成する |
| `tools/minic.py` | 小さな言語 Mini から Piet へのコンパイラ（pasm.py を使う） |
| `tools/samples.py` | サンプルを画像に変換し、piet.py（と、あれば npiet）で実行して期待される出力と照合する |
| `samples/` | 本に掲載したサンプルのソース（`.txt` テキスト記法、`.pasm` アセンブリ、`.mini` Mini）と、入力 `.in*`・期待される出力 `.out*` |
| `images/` | 全サンプルの PNG 画像（1 コーデル = 10 ピクセル） |

ファイル名の `chNN` は本の章（`appI` は付録I）に対応しています。

## 必要なもの

- Python 3.8 以降
- Piet スタジオ: tkinter（python.org 版の Python には同梱。Ubuntu などでは `sudo apt install python3-tk`）
- piet.py・pasm.py・minic.py で画像を読み書きするとき: Pillow（`pip install pillow`）
- samples.py で npiet と照合するとき: [npiet](https://www.bertnase.de/npiet/)（PATH に置くか、環境変数 `NPIET` で指定）

## 使い方

```sh
python3 tools/pietstudio.py images/ch01/five.png      # Piet スタジオで開く
python3 tools/piet.py run images/ch01/five.png         # 実行する（5 が出力される）
python3 tools/piet.py run -t images/ch01/five.png      # トレースを表示しながら実行する
python3 tools/piet.py png samples/ch01/five.txt five.png -cs 10   # テキスト記法から画像を作る
python3 tools/pasm.py samples/ch10/countup.pasm -o countup.png    # アセンブリから画像を作る
python3 tools/minic.py samples/ch18/fizzbuzz.mini -o fizzbuzz.png # Mini から画像を作る
python3 tools/samples.py ch05                          # 第5章のサンプルを検証する
```

テキスト記法は 1 文字が 1 コーデルです（淡い色 `r y g c b m`、通常の色 `R Y G C B M`、濃い色 `1`〜`6`（赤・黄・緑・シアン・青・マゼンタの順）、白 `.`、黒 `#`）。

## ライセンス

このリポジトリのすべてのファイル（ツールのソースコードとサンプル）は [CC0 1.0](LICENSE)（パブリックドメイン提供）です。著作権表示なしで、自由に使い、改変し、自分のものとして配布してかまいません。

ツールとサンプルは、AI アシスタントの Claude（Anthropic）を用いて作成しました。
