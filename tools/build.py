#!/usr/bin/env python3
"""build.py -- 原稿（src/*.md）から書籍サイト（site/*.html）を生成する

  python3 tools/build.py          # 全ページ
  python3 tools/build.py --check  # 生成はするが、警告があれば終了コード 1
"""
import sys, os, re, html, glob, shutil, json
import markdown

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from piet import Program, Machine, RGB, HUES, color_name, CMDS, WHITE, BLACK
import pasm

SRC = os.path.join(ROOT, "src")
SITE = os.path.join(ROOT, "site")
BOOK = "Piet プログラミング入門"
SUB = "絵を描いてプログラムを書く"

PARTS = [
    ("第I部", "Piet の基本", "最初のプログラムを動かし、色・コーデル・命令・実行の流れという Piet の仕組みをひととおり理解します。",
     ["ch01", "ch02", "ch03", "ch04", "ch05"]),
    ("第II部", "プログラミングの基礎", "スタックと演算、入出力、白と黒による配線、分岐と繰り返し、スタック操作の技法を身につけます。",
     ["ch06", "ch07", "ch08", "ch09", "ch10", "ch11"]),
    ("第III部", "実践プログラミング", "数値計算、文字列処理、総合演習を通して、まとまったプログラムを設計して描く力をつけます。",
     ["ch12", "ch13", "ch14", "ch15"]),
    ("第IV部", "処理系を作る", "インタプリタ、アセンブラ、コンパイラを自作し、デバッグの技法と Piet を取り巻く世界を知ります。",
     ["ch16", "ch17", "ch18", "ch19", "ch20"]),
    ("付録", "", "", ["appA", "appB", "appC", "appD", "appE", "appF", "appG", "appH", "appI", "appJ"]),
]
ORDER = ["preface"] + [p for part in PARTS for p in part[3]]
WARN = []
FIG_INDEX = []   # (sid, caption, page, no) プレイグラウンドのサンプル一覧用


def warn(msg):
    WARN.append(msg)
    print("警告:", msg, file=sys.stderr)


# ------------------------------------------------------------------ ページ情報
def page_label(name):
    if name == "preface":
        return ""
    if name.startswith("ch"):
        return f"第{int(name[2:])}章"
    return f"付録{name[3]}"


def fig_prefix(name):
    if name.startswith("ch"):
        return str(int(name[2:]))
    if name.startswith("app"):
        return name[3]
    return "0"


def read_title(name):
    if name == "appD":
        return "練習問題の解答"
    if name == "appG":
        return "付属ツールのソースコード"
    path = os.path.join(SRC, name + ".md")
    if not os.path.exists(path):
        return None
    for line in open(path, encoding="utf-8"):
        if line.startswith("# "):
            t = line[2:].strip()
            t = re.sub(r"^(第\d+章|付録[A-Z])\s*", "", t)
            return t
    return name


# ------------------------------------------------------------------ 特殊記法
ARG_RE = re.compile(r'(\w+)=("(?:[^"\\]|\\.)*"|\S+)')


def parse_args(s):
    args = {}
    for k, v in ARG_RE.findall(s):
        if v.startswith('"'):
            v = v[1:-1].replace('\\"', '"')
        args[k] = v
    return args


def unesc(s):
    return s.replace("\\n", "\n").replace("\\t", "\t")


def inline_md(s):
    s = html.escape(s)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
    return s


def grid_attr(prog):
    return html.escape(prog.to_text().replace("\n", "/")) if prog else ""


def sample_png(sid):
    return os.path.join(SITE, "img", sid + ".png")


def load_sample(sid):
    p = sample_png(sid)
    if not os.path.exists(p):
        warn(f"サンプル画像がありません: {sid}（python3 tools/samples.py を実行）")
        return None
    return Program.from_image(p, 1)


def sample_input(sid):
    f = os.path.join(ROOT, "samples", sid + ".in")
    return open(f, encoding="utf-8").read() if os.path.exists(f) else None


class Ctx:
    def __init__(self, name):
        self.name = name
        self.fig = 0
        self.uid = 0

    def next_fig(self):
        self.fig += 1
        return f"{fig_prefix(self.name)}.{self.fig}"


def render_piet(ctx, rest):
    m = re.match(r"(\S+)\s*(.*)", rest)
    sid, args = m.group(1), parse_args(m.group(2))
    prog = load_sample(sid)
    no = ctx.next_fig()
    cap = args.get("caption")
    if not cap:
        warn(f"{ctx.name}: @piet {sid} に caption がありません")
        cap = ""
    inp = args.get("input")
    if inp is None:
        inp = sample_input(sid)
    else:
        inp = unesc(inp)
    ctx.uid += 1
    fid = f"pv-{ctx.name}-{ctx.uid}"
    if ctx.name != "cover":
        FIG_INDEX.append({"id": sid, "caption": cap, "page": ctx.name, "no": no, "input": inp or "",
                          "grid": prog.to_text() if prog and prog.w * prog.h <= 160 * 160 else ""})
    size = f"（{prog.w}×{prog.h} コーデル）" if prog else ""
    zoom = args.get("zoom", "")
    io_input = ""
    if inp is not None:
        io_input = (f'<div><label for="{fid}-in">入力</label>'
                    f'<textarea class="pv-input" id="{fid}-in" rows="2" spellcheck="false">{html.escape(inp.replace(chr(0), chr(92) + "0"))}</textarea></div>')
    return (
        f'<figure class="pv" id="fig-{no.replace(".", "-")}" data-grid="{grid_attr(prog)}" data-zoom="{html.escape(zoom)}">'
        f'<div class="pv-stage"><canvas role="img" aria-label="Piet プログラム: {html.escape(cap)}"></canvas></div>'
        f'<div class="pv-panel"><div class="pv-controls">'
        f'<button type="button" class="pv-run">実行</button><button type="button" class="pv-play">再生</button>'
        f'<button type="button" class="pv-step">1 ステップ</button><button type="button" class="pv-reset">リセット</button></div>'
        f'<div class="pv-io{" has-input" if io_input else ""}">{io_input}'
        f'<div><label>出力</label><pre class="pv-out" aria-live="polite"></pre></div></div>'
        f'<div class="pv-state"></div></div>'
        f'<figcaption><span class="fno">図 {no}</span>{inline_md(cap)}<span class="fsize">{size}</span></figcaption></figure>'
    )


def render_trace(ctx, rest):
    m = re.match(r"(\S+)\s*(.*)", rest)
    sid, args = m.group(1), parse_args(m.group(2))
    prog = load_sample(sid)
    if prog is None:
        return ""
    inp = unesc(args["input"]) if "input" in args else (sample_input(sid) or "")
    steps = int(args.get("steps", 60))
    mach = Machine(prog, inp, trace=True)
    while mach.steps < steps and mach.step():
        pass
    lines = list(mach.log)
    if not mach.halted:
        lines.append(f"…（{steps} ステップで打ち切り）")
    out = "".join(mach.out)
    lines.append("出力: " + repr(out)[1:-1] if out else "出力: （なし）")
    return f'<pre class="trace" aria-label="実行トレース {html.escape(sid)}">{html.escape(chr(10).join(lines))}</pre>'


def render_grid(ctx, rest):
    sid = rest.split()[0]
    prog = load_sample(sid)
    if prog is None:
        return ""
    return f'<pre class="grid">{html.escape(prog.to_text())}</pre>'


def render_img(ctx, rest):
    m = re.match(r"(\S+)\s*(.*)", rest)
    path, args = m.group(1), parse_args(m.group(2))
    if not os.path.exists(os.path.join(SITE, "img", path)):
        warn(f"{ctx.name}: 画像がありません img/{path}")
    no = ctx.next_fig()
    cap = args.get("caption", "")
    return (f'<figure class="img" id="fig-{no.replace(".", "-")}"><div class="img-stage"><img src="img/{html.escape(path)}" alt="{html.escape(cap)}" loading="lazy"></div>'
            f'<figcaption><span class="fno">図 {no}</span>{inline_md(cap)}</figcaption></figure>')


def hexc(c):
    if c == WHITE:
        return "#FFFFFF"
    if c == BLACK:
        return "#000000"
    return "#%06X" % RGB[c]


def render_colortable(ctx, rest):
    rows = []
    hj = ["赤", "黄", "緑", "シアン", "青", "マゼンタ"]
    for h in range(6):
        cells = []
        for l in range(3):
            c = (h, l)
            dark = l == 2 or (l == 1 and h in (0, 4, 5))
            cells.append(f'<td class="chip{" darkchip" if dark else ""}" style="background:{hexc(c)}">{color_name(c, True)}<br>{hexc(c)}</td>')
        rows.append(f"<tr><th>{hj[h]}</th>{''.join(cells)}</tr>")
    rows.append('<tr><th>無彩色</th><td class="chip" style="background:#FFFFFF">白<br>#FFFFFF</td>'
                '<td class="chip darkchip" style="background:#000000">黒<br>#000000</td><td></td></tr>')
    return ('<div class="table-wrap"><table class="colortable"><thead><tr><th>色相＼明度</th><th>淡い (light)</th><th>通常 (normal)</th><th>濃い (dark)</th></tr></thead>'
            f"<tbody>{''.join(rows)}</tbody></table></div>")


def render_cmdtable(ctx, rest):
    lab = ["0 段階", "1 段階", "2 段階"]
    rows = []
    for dh in range(6):
        cells = "".join(f"<td><code>{(CMDS[dh][dl] or '（なし）').replace('_number', '(number)').replace('_char', '(char)')}</code></td>" if CMDS[dh][dl] else "<td>（なし）</td>" for dl in range(3))
        rows.append(f"<tr><td>{dh} 段階</td>{cells}</tr>")
    return ('<div class="table-wrap"><table class="cmdtable"><thead><tr><th>色相の変化＼明度の変化</th>'
            + "".join(f"<th>{l}</th>" for l in lab) + f"</tr></thead><tbody>{''.join(rows)}</tbody></table></div>")


DIRECTIVES = {"piet": render_piet, "trace": render_trace, "grid": render_grid, "img": render_img,
              "colortable": render_colortable, "cmdtable": render_cmdtable}


MODE = "web"   # "web" または "print"（書籍版）


def select_mode(text, mode=None):
    """<!--web--> ... <!--/web--> と <!--print--> ... <!--/print--> を出し分ける"""
    mode = mode or MODE
    other = "print" if mode == "web" else "web"
    text = re.sub(rf"<!--{other}-->.*?<!--/{other}-->\n?", "", text, flags=re.S)
    return re.sub(rf"<!--/?{mode}-->\n?", "", text)


def preprocess(ctx, text):
    text = select_mode(text)
    out = []
    in_code = False
    for line in text.split("\n"):
        if line.lstrip().startswith("```"):
            in_code = not in_code
            out.append(line)
            continue
        m = None if in_code else re.match(r"^(\s*)@(\w+)\s*(.*)$", line)
        if m and m.group(2) in DIRECTIVES:
            indent = m.group(1)
            h = DIRECTIVES[m.group(2)](ctx, m.group(3).strip())
            out.append("")
            out.append(indent + h)
            out.append("")
        else:
            out.append(line)
    return "\n".join(out)


def slugify(value, sep):
    m = re.match(r"\s*([0-9A-Z]+(?:\.\d+)*)", value)
    if m:
        return "s" + m.group(1).replace(".", "-")
    return "h"


def md_to_html(ctx, text):
    text = preprocess(ctx, text)
    md = markdown.Markdown(extensions=["extra", "admonition", "sane_lists", "toc"],
                           extension_configs={"toc": {"slugify": slugify, "toc_depth": "2-3"}})
    body = md.convert(text)
    body = re.sub(r"<table>", '<div class="table-wrap"><table>', body)
    body = re.sub(r"</table>", "</table></div>", body)
    body = body.replace('<div class="table-wrap"><div class="table-wrap">', '<div class="table-wrap">').replace("</table></div></div>", "</table></div>")
    return body, md.toc_tokens


# ------------------------------------------------------------------ 章扉の帯
def chapter_strip(name):
    label = page_label(name) or "はじめに"
    sid = f"strip/{name}"
    p = os.path.join(SITE, "img", sid + ".png")
    os.makedirs(os.path.dirname(p), exist_ok=True)
    prog = pasm.assemble(f'prints "{label}"', maxw=400)
    prog.save_png(p, 1)
    out = Machine(prog).run()
    assert out == label, (out, label)
    return (f'<div class="strip" data-grid="{grid_attr(prog)}" data-zoom="7"><div class="strip-canvas"><canvas role="img" aria-label="「{label}」を出力する Piet プログラム"></canvas></div>'
            f'<span>この帯は「{label}」を出力する Piet プログラムです（{prog.w}×{prog.h} コーデル）</span>'
            f'<button type="button">実行する</button><span class="strip-out" aria-live="polite"></span></div>')


# ------------------------------------------------------------------ テンプレート
FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=BIZ+UDGothic:wght@400;700&family=BIZ+UDPGothic:wght@400;700'
         '&family=Dela+Gothic+One&family=JetBrains+Mono:wght@400;600&display=swap">')


def nav_lists(current, titles):
    items = []
    for part in [("", "", "", ["preface"])] + PARTS:
        if part[0]:
            items.append(f'<li class="part">{part[0]}{"　" + part[1] if part[1] else ""}</li>')
        for n in part[3]:
            if titles.get(n) is None:
                continue
            cur = ' aria-current="page"' if n == current else ""
            no = page_label(n).replace("付録", "") if n != "preface" else ""
            items.append(f'<li><a href="{n}.html"{cur}><span class="no">{no}</span><span>{html.escape(titles[n])}</span></a></li>')
    return "\n".join(items)


def page_html(name, titles, body, toc, standalone=True):
    label = page_label(name)
    title = titles[name]
    nav = nav_lists(name, titles)
    idx = [n for n in ORDER if titles.get(n) is not None]
    i = idx.index(name)
    prev = idx[i - 1] if i > 0 else None
    nxt = idx[i + 1] if i + 1 < len(idx) else None
    pager = '<nav class="pager" aria-label="前後のページ">'
    if prev:
        pager += f'<a class="prev" href="{prev}.html"><small>前へ</small>{html.escape((page_label(prev) + " ") if page_label(prev) else "")}{html.escape(titles[prev])}</a>'
    else:
        pager += '<a class="prev" href="index.html"><small>前へ</small>表紙</a>'
    if nxt:
        pager += f'<a class="next" href="{nxt}.html"><small>次へ</small>{html.escape((page_label(nxt) + " ") if page_label(nxt) else "")}{html.escape(titles[nxt])}</a>'
    pager += "</nav>"
    ptoc = ""
    secs = [t for t in toc if t["level"] == 2]
    if len(secs) >= 3:
        ptoc = ('<nav class="page-toc" aria-label="この章の内容"><b>この章の内容</b><ol>'
                + "".join(f'<li><a href="#{t["id"]}">{t["name"]}</a></li>' for t in secs) + "</ol></nav>")
    part = ""
    for p in PARTS:
        if name in p[3]:
            part = p[0] + ("　" + p[1] if p[1] else "")
    head_t = f"{label} {title}" if label else title
    h1 = f'<h1><span class="num">{label}</span>{html.escape(title)}</h1>' if label else f"<h1>{html.escape(title)}</h1>"
    doc = f"""<title>{html.escape(head_t)}｜{BOOK}</title>
<meta name="claude:viewport-fit-sides" content="cover">
{FONTS}
<link rel="stylesheet" href="style.css">
<div class="shell">
<aside class="toc-side" aria-label="目次"><a class="book" href="index.html">{BOOK}</a><ul class="toc-list">{nav}</ul></aside>
<div>
<header class="topbar"><a class="book" href="index.html">{BOOK}</a>
<details><summary>目次</summary><div class="toc-drop"><ul class="toc-list">{nav}</ul></div></details></header>
<main><article class="page">
<header class="ch-head"><div class="eyebrow">{html.escape(part)}</div>{h1}{chapter_strip(name)}</header>
{ptoc}
<div class="prose">
{body}
</div>
{pager}
</article></main>
</div></div>
<script src="piet.js"></script>
"""
    if standalone:
        doc = ('<!doctype html>\n<html lang="ja"><head><meta charset="utf-8">'
               '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n' + doc.replace("\n<div class=\"shell\">", "</head><body>\n<div class=\"shell\">", 1)
               + "</body></html>\n")
    return doc


def strip_title(text):
    lines = text.split("\n")
    for i, l in enumerate(lines):
        if l.startswith("# "):
            return "\n".join(lines[:i] + lines[i + 1:])
    return text


def build_answers(titles):
    parts = ["# 付録D 練習問題の解答", "",
             "各章末の練習問題の解答例です。Piet のプログラムには多くの書き方があるので、ここに示すのは一例です。"
             "自分の解答は、本書のビューアや npiet で実行して確かめてください。", ""]
    for n in ORDER:
        f = os.path.join(SRC, "answers", n + ".md")
        if not os.path.exists(f):
            continue
        t = strip_title(open(f, encoding="utf-8").read())
        t = re.sub(r"^(#{2,5}) ", lambda m: "#" + m.group(1) + " ", t, flags=re.M)
        parts.append(f"## {page_label(n)} {titles.get(n) or ''}")
        parts.append("")
        parts.append(t)
        parts.append("")
    return "\n".join(parts)


TOOLS = [
    ("pietstudio.py", "Piet スタジオ", "エディタ兼デバッガ（第2章）。tkinter だけで動くデスクトップアプリで、piet.py を使う。"),
    ("piet.py", "インタプリタ", "仕様に従った Piet インタプリタと画像入出力（第16章）。画像の読み書きに Pillow を使う。"),
    ("pasm.py", "アセンブラ", "アセンブリ言語から Piet の画像を生成する（第17章）。"),
    ("minic.py", "コンパイラ", "小さな言語 Mini を pasm のアセンブリに変換する（第18章）。"),
    ("samples.py", "サンプル検証スクリプト", "サンプルを画像化し、piet.py と npiet で実行して照合する（第19章）。"),
]


def build_tools_appendix():
    parts = ["# 付録G 付属ツールのソースコード", "",
             "本書付属のツールはすべて Python 3 で書かれています。下のコードをそれぞれのファイル名で同じフォルダに保存すれば使えます"
             "（各コードの右上の「コピー」ボタンでクリップボードにコピーできます）。"
             "ツールと本書のすべてのサンプルプログラム（テキスト記法・アセンブリ・Mini のソースと画像）は、本書の原稿・PDF・生成スクリプトとともに GitHub の https://github.com/MaxSignal/piet-book で公開しています。"
             "ライセンスは CC0 1.0（パブリックドメイン提供）で、著作権表示なしで自由に使い、改変し、自分のものとして配布できます。",
             "", "| ファイル | 名前 | 内容 | 行数 |", "|---|---|---|---|"]
    rows, bodies = [], []
    k = 0
    for fn, name, desc in TOOLS:
        path = os.path.join(HERE, fn)
        if not os.path.exists(path):
            continue
        src = open(path, encoding="utf-8").read()
        k += 1
        n = src.count("\n")
        rows.append(f"| `{fn}` | {name} | {desc} | {n} |")
        bodies += [f"## G.{k} {fn} ― {name}", "", desc, "", "```python", src.rstrip("\n"), "```", ""]
    parts += rows + ["",
                     "必要なもの: Python 3.8 以降。Piet スタジオには tkinter（python.org 版の Python には同梱。Ubuntu などでは "
                     "`sudo apt install python3-tk`）、piet.py・pasm.py・minic.py で画像を扱うには Pillow（`pip install pillow`）、"
                     "samples.py には npiet（第2章）が必要です。", ""] + bodies
    return "\n".join(parts)


def main(argv):
    check = "--check" in argv
    os.makedirs(SITE, exist_ok=True)
    for f in ("style.css", "piet.js", "playground.js"):
        src = os.path.join(HERE, "web", f)
        if os.path.exists(src):
            shutil.copy(src, os.path.join(SITE, f))
    titles = {n: read_title(n) for n in ORDER}
    titles["preface"] = titles["preface"] or "はじめに"
    stats = {}
    for n in ORDER:
        if n == "appD":
            text = build_answers(titles)
        elif n == "appG":
            text = build_tools_appendix()
        else:
            path = os.path.join(SRC, n + ".md")
            if not os.path.exists(path):
                titles[n] = None
                continue
            text = open(path, encoding="utf-8").read()
        ctx = Ctx(n)
        text = strip_title(text)
        body, toc = md_to_html(ctx, text)
        stats[n] = (len(re.sub(r"\s", "", text)), ctx.fig)
        with open(os.path.join(SITE, n + ".html"), "w", encoding="utf-8") as f:
            f.write(page_html(n, titles, body, toc))
    with open(os.path.join(SITE, "samples.json"), "w", encoding="utf-8") as f:
        json.dump([dict(x, label=page_label(x["page"])) for x in FIG_INDEX], f, ensure_ascii=False)
    import cover
    cover.build(titles, stats)
    total = sum(s[0] for s in stats.values())
    figs = sum(s[1] for s in stats.values())
    print(f"{len(stats)} ページ, 原稿 {total:,} 字, 図 {figs} 点")
    for n, (c, fg) in stats.items():
        print(f"  {n}: {c:,} 字, 図 {fg}")
    if WARN:
        print(f"警告 {len(WARN)} 件")
    return 1 if (check and WARN) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
