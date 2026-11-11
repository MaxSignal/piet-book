#!/usr/bin/env python3
"""printsplit.py -- 本文 PDF を「巻頭カラー＋モノクロ」の入稿用 PDF に変換する

  python3 tools/printsplit.py raw.pdf out.pdf

ちょ古っ都製本工房の「カラー・モノクロ混在印刷 お得Ver.」向け:
  - カラーページは巻頭から連続、総ページ数の半分以下
  - カラーページ: CMYK（黒とグレーは墨 K のみ）
  - モノクロページ: グレースケール（K のみ）
  - 文字はすべてアウトライン化
カラーとモノクロの境目は、第IV部の部扉の直前のページ。
"""
import sys, re, subprocess, os

GCR = "{ } setblackgeneration { } setundercolorremoval"   # 黒・グレーは K だけで刷る


def pages(pdf):
    return int(re.search(r"Pages:\s+(\d+)", subprocess.run(["pdfinfo", pdf], capture_output=True, text=True).stdout).group(1))


def page_text(pdf, p):
    return subprocess.run(["pdftotext", "-f", str(p), "-l", str(p), pdf, "-"], capture_output=True, text=True).stdout


MARKER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "print", "mono_marker.txt")


def find_boundary(pdf, n):
    """最初のモノクロページ（print/mono_marker.txt の文字列を含む章扉）を探し、その直前までをカラーにする"""
    marker = open(MARKER, encoding="utf-8").read().strip()
    norm = lambda t: re.sub(r"\s+", "", t)
    for p in range(1, n + 1):
        t = page_text(pdf, p)
        if norm(marker) in norm(t) and "目次" not in t and "はじめに" not in t[:40]:
            c = p - 1
            return c + (c % 2)   # 用紙の表裏で境目をそろえる（カラーページ数は偶数。増えた 1 ページは K だけのデータ）
    raise SystemExit(f"最初のモノクロページ（{marker}）が見つかりません")


def gs(args):
    subprocess.run(["gs", "-q", "-dBATCH", "-dNOPAUSE", "-dSAFER", "-sDEVICE=pdfwrite", "-dAutoRotatePages=/None"] + args, check=True)


def needed_pad(raw):
    """お得Ver.の条件（カラー ≤ 総ページの半分）と 4 の倍数を満たすために足すページ数"""
    n = pages(raw)
    c = find_boundary(raw, n)
    target = max(n, 2 * c)
    target += (4 - target % 4) % 4
    if target > 500:
        raise SystemExit(f"ページ数が上限 500 を超えます（カラー {c} ページ → 総 {target} ページが必要）")
    return target - n


def main(raw, out):
    n = pages(raw)
    c = find_boundary(raw, n)
    print(f"総ページ {n}、カラー 1〜{c}（{c} ページ）、モノクロ {c + 1}〜{n}（{n - c} ページ）")
    if c * 2 > n:
        raise SystemExit(f"カラーページが総ページ数の半分を超えています（お得Ver.の条件）: {c} > {n}/2")
    d = os.path.dirname(out) or "."
    a, b = os.path.join(d, "_color.pdf"), os.path.join(d, "_mono.pdf")
    common = ["-dNoOutputFonts", "-dCompatibilityLevel=1.3"]
    gs(common + [f"-dFirstPage=1", f"-dLastPage={c}", "-sColorConversionStrategy=CMYK", "-dProcessColorModel=/DeviceCMYK",
                 "-dUseFastColor=true", f"-sOutputFile={a}", "-c", GCR, "-f", raw])
    gs(common + [f"-dFirstPage={c + 1}", f"-dLastPage={n}", "-sColorConversionStrategy=Gray", "-dProcessColorModel=/DeviceGray",
                 f"-sOutputFile={b}", raw])
    gs(["-dCompatibilityLevel=1.3", "-sColorConversionStrategy=LeaveColorUnchanged", f"-sOutputFile={out}", a, b])
    os.remove(a)
    os.remove(b)
    with open(os.path.join(d, "color_pages.txt"), "w") as f:
        f.write(f"{n} {c}\n")
    print(f"→ {out}")


if __name__ == "__main__":
    if sys.argv[1] == "pad":
        print(needed_pad(sys.argv[2]))
    else:
        main(sys.argv[1], sys.argv[2])
