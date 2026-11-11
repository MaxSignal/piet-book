#!/usr/bin/env python3
"""gen_numtable.py -- 付録J「数と文字の作り方表」（src/appJ.md）を生成する

各数の積み方は tools/pasm.py の number_plan / push_seq（第17章）で求め、スタックで検算する。
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pasm

SYM = {"multiply": "×", "add": "＋", "subtract": "−", "duplicate": "dup", "not": "not"}


def rpn(seq):
    return " ".join(str(c[1]) if c[0] == "push" else SYM[c[0]] for c in seq)


def evaluate(seq):
    st = []
    for c in seq:
        if c[0] == "push":
            st.append(c[1])
        elif c[0] == "duplicate":
            st.append(st[-1])
        elif c[0] == "not":
            st[-1] = 1 if st[-1] == 0 else 0
        else:
            b, a = st.pop(), st.pop()
            st.append({"multiply": a * b, "add": a + b, "subtract": a - b}[c[0]])
    assert len(st) == 1
    return st[0]


def codels(seq):
    """命令列を 1 列に並べたときのコーデル数（push k の前のブロックは k、ほかは 1、最後のブロック 1）"""
    return sum(c[1] if c[0] == "push" else 1 for c in seq) + 1


def char_of(n):
    if n == 10:
        return "改行（LF）"
    if n == 9:
        return "タブ"
    if n == 13:
        return "復帰（CR）"
    if n == 32:
        return "空白"
    if n == 127 or n < 32:
        return ""
    if n == 96:
        return "`` ` ``"
    if n == 124:
        return "｜（縦棒）"
    return f"`{chr(n)}`" if n < 127 else ""


def row(n):
    seq = pasm.push_seq(n)
    assert evaluate(seq) == n, n
    return f"| {n} | {char_of(n)} | {rpn(seq)} | {codels(seq)} |"


def main():
    out = ["# 付録J 数と文字の作り方表", "",
           "Piet には数をそのまま書く方法がなく、`push` が積めるのは「出ていく色ブロックの大きさ」だけです。"
           "小さな数はブロックの大きさで直接積めますが、大きな数は掛け算や足し算で組み立てたほうが、使うコーデルが少なくて済みます（第6章）。"
           "この付録は、1〜255 の数と、よく使う大きな数について、少ないコーデルで積む手順をまとめた表です。"
           "手でプログラムを描くとき、とくに文字コードを積んで `out(char)` で出力するときに使ってください。", "",
           "## J.1 表の見方", "",
           "「積み方」は、スタックに積む数と命令を左から順に並べた逆ポーランド記法です。",
           "数字は「その大きさのブロックから `push` する」ことを、`×` は `multiply`、`＋` は `add`、`−` は `subtract`、`dup` は `duplicate`、`not` は `not` を表します。"
           "たとえば 72 の「2 6 dup × ×」は「2 コーデルのブロックから push、6 コーデルのブロックから push、duplicate、multiply、multiply」で、"
           "スタックは [2] → [2 6] → [2 6 6] → [2 36] → [72] と変わり、最後に 72 が 1 つだけ残ります。"
           "素直に「8 9 ×」と積むと 19 コーデルかかるところを、12 コーデルで済ませています。", "",
           "「コーデル数」は、その手順を 1 列に並べたときに使うコーデルの数です（`push k` の直前のブロックが k コーデル、ほかの命令は 1 コーデル、最後のブロックが 1 コーデル）。",
           "ブロックの形は自由なので、たとえば 9 コーデルのブロックは 3×3 の正方形に描いてもかまいません。", "",
           "この表は、本書のアセンブラ pasm.py（第17章）が使う動的計画法 `number_plan` で求めたもので、すべての手順をスタックの計算で検算しています。"
           "12 以下の数はブロックの大きさで直接積み、それより大きい数は、約数の積・平方（`dup ×`）・小さい数との和のうち、コーデル数が最も少ないものを選んでいます。"
           "最短である保証はありませんが、手で考えるときの目安になります。", "",
           "!!! tip \"ヒント\"",
           "    同じ数を何度も使うときは、一度積んだ数を `duplicate` で複製するほうが安上がりです。また、文字列を出力するときは、隣り合う文字の差を足し引きする方法（第13章）も有効です。", "",
           "## J.2 1〜127（ASCII）", "",
           "32〜126 は ASCII の印字可能文字です。「文字」の列は、その数を `out(char)` で出力したときの文字です。", "",
           "| 数 | 文字 | 積み方 | コーデル数 |", "|---|---|---|---|"]
    out += [row(n) for n in range(1, 128)]
    out += ["", "## J.3 128〜255", "",
            "128〜255 は Unicode の U+0080〜U+00FF（ラテン文字の補助）にあたります。npiet の `out(char)` は値の下位 8 ビットを 1 バイトとして出力するので、端末によっては文字化けします（付録C）。"
            "ここでは数として使う場合の積み方だけを示します。", "",
            "| 数 | 積み方 | コーデル数 |", "|---|---|---|"]
    for n in range(128, 256):
        seq = pasm.push_seq(n)
        assert evaluate(seq) == n
        out.append(f"| {n} | {rpn(seq)} | {codels(seq)} |")
    out += ["", "## J.4 よく使う大きな数と文字", "",
            "| 数 | 意味 | 積み方 | コーデル数 |", "|---|---|---|---|"]
    special = [(256, "2⁸"), (360, ""), (365, "1 年の日数"), (500, ""), (999, ""), (1000, "千"), (1024, "2¹⁰"),
               (3600, "1 時間の秒数"), (4096, "2¹²"), (10000, "1 万"), (12354, "「あ」（U+3042）"), (12450, "「ア」（U+30A2）"),
               (19968, "「一」（U+4E00）"), (65535, "2¹⁶−1"), (65536, "2¹⁶"), (1000000, "100 万")]
    for n, label in special:
        seq = pasm.push_seq(n)
        assert evaluate(seq) == n
        out.append(f"| {n} | {label} | {rpn(seq)} | {codels(seq)} |")
    out += ["", "ひらがなや漢字などの文字コードは大きな数になります。本書の piet.py や Piet スタジオは `out(char)` で Unicode の文字を出力しますが、npiet は下位 8 ビットしか出力しません（付録C）。", ""]
    with open(os.path.join(os.path.dirname(HERE), "src", "appJ.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")
    print("src/appJ.md を生成しました")


if __name__ == "__main__":
    main()
