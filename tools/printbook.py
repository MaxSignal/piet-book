#!/usr/bin/env python3
"""printbook.py -- 書籍版（PDF 入稿用）の HTML を生成する

  python3 tools/printbook.py          # print/book.html を作る（組版は print/build.sh）

原稿（src/*.md）は Web 版と共通。<!--print--> ブロックが有効になり、
Piet の図は SVG（ベクター）＋実行結果、目次・索引・奥付が付く。
"""
import os, re, sys, json, html, shutil
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import build as B
from piet import Program, Machine, RGB, WHITE, BLACK
from bs4 import BeautifulSoup, NavigableString

B.MODE = "print"
OUT = os.path.join(ROOT, "print")
CONF = json.load(open(os.path.join(OUT, "book.json"), encoding="utf-8"))
TEXT_W_MM = 140.0          # 版面の幅（mm）


# ------------------------------------------------------------------ 図（SVG）
def hexc(c):
    if c == WHITE:
        return "#FFFFFF"
    if c == BLACK:
        return "#000000"
    return "#%06X" % RGB[c]


PLATE_CH = None
GRAY = {0: "#E2E2E2", 1: "#A9A9A9", 2: "#6A6A6A"}   # 明度（淡・通常・濃）で灰色の濃さを変える


def mono_color(c):
    if c == WHITE:
        return "#FFFFFF"
    if c == BLACK:
        return "#000000"
    return GRAY[c[1]]


MAX_CODEL = 4.2   # 図の 1 コーデルの最大の大きさ（mm）


def prog_svg(prog, max_w=TEXT_W_MM, max_h=150.0, max_codel=None, cls="psvg", mono=False):
    if max_codel is None:
        max_codel = MAX_CODEL
    w, h = prog.w, prog.h
    cm = min(max_codel, max_w / w, max_h / h)
    rects = []
    for y in range(h):
        x = 0
        row = prog.grid[y]
        while x < w:
            c = row[x]
            x2 = x
            while x2 + 1 < w and row[x2 + 1] == c:
                x2 += 1
            if c != WHITE:
                fill = mono_color(c) if mono else hexc(c)
                rects.append(f'<rect x="{x}" y="{y}" width="{x2 - x + 1}" height="1" fill="{fill}"/>')
            x = x2 + 1
    grid = ""
    if cm >= 1.2:
        sw = 0.18 / cm   # 線の太さ約 0.18mm
        lines = [f'<line x1="{i}" y1="0" x2="{i}" y2="{h}"/>' for i in range(1, w)]
        lines += [f'<line x1="0" y1="{j}" x2="{w}" y2="{j}"/>' for j in range(1, h)]
        grid = f'<g stroke="#9a9a9a" stroke-width="{sw:.4f}">{"".join(lines)}</g>'
    labels = ""
    if mono and cm >= 1.9:   # コーデルに色の記号（テキスト記法）を書く
        from piet import COL2CHAR
        ts = []
        for y in range(h):
            for x in range(w):
                c = prog.grid[y][x]
                if c in (WHITE, BLACK):
                    continue
                fg = "#FFFFFF" if c[1] == 2 else "#000000"
                ts.append(f'<text x="{x + 0.5}" y="{y + 0.72}" fill="{fg}">{COL2CHAR[c]}</text>')
        labels = (f'<g font-family="Noto Sans Mono, monospace" font-size="0.62" font-weight="700" text-anchor="middle">'
                  + "".join(ts) + "</g>")
    border = f'<rect x="0" y="0" width="{w}" height="{h}" fill="none" stroke="#000" stroke-width="{0.25 / cm:.4f}"/>'
    return (f'<svg class="{cls}" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" '
            f'width="{w * cm:.2f}mm" height="{h * cm:.2f}mm">'
            f'<rect width="{w}" height="{h}" fill="#FFFFFF"/>{"".join(rects)}{grid}{labels}{border}</svg>')


def show_text(s, max_lines=14):
    s = s.replace("\r", "")
    vis = "".join(ch if (ch == "\n" or ord(ch) >= 32) else f"\\x{ord(ch):02x}" for ch in s)
    lines = vis.split("\n")
    if lines and lines[-1] == "":
        lines = lines[:-1]
    note = ""
    if len(lines) > max_lines:
        note = f"…（以下略。全 {len(lines)} 行）"
        lines = lines[:max_lines - 3] + ["⋮"] + lines[-2:]
    lines = [l if len(l) <= 200 else l[:200] + "…" for l in lines]
    return "\n".join(lines), note


def print_piet(ctx, rest):
    m = re.match(r"(\S+)\s*(.*)", rest)
    sid, args = m.group(1), B.parse_args(m.group(2))
    prog = B.load_sample(sid)
    no = ctx.next_fig()
    cap = args.get("caption", "")
    inp = args.get("input")
    inp = B.unesc(inp) if inp is not None else B.sample_input(sid)
    flags_f = os.path.join(ROOT, "samples", sid + ".flags")
    flags = open(flags_f).read().split() if os.path.exists(flags_f) else []
    mach = Machine(prog, inp or "")
    out = mach.run(20000 if "noterm" in flags else 3_000_000)
    run = []
    if inp:
        t, _ = show_text(inp, 6)
        run.append(f'<div class="prun-row"><span class="prun-k">入力</span><pre>{html.escape(t)}</pre></div>')
    t, note = show_text(out)
    if not mach.halted:
        note = (note + " " if note else "") + "（停止しないプログラム。途中までの出力）"
    run.append(f'<div class="prun-row"><span class="prun-k">実行結果</span><pre>{html.escape(t) if t else "（出力なし）"}</pre></div>'
               + (f'<div class="prun-note">{html.escape(note)}</div>' if note else ""))
    size = f"（{prog.w}×{prog.h} コーデル）"
    big = prog.w * prog.h > 6000
    mono = is_mono(ctx.name)
    plate = ""
    if mono and PLATE_CH == ctx.name:
        plate = f' <span class="pref">カラー図版 <a href="#plate-{no.replace(".", "-")}"></a> ページ</span>'
    img = f'<div class="pimg">{prog_svg(prog, mono=mono)}</div>'
    if mono and not plate and min(MAX_CODEL, TEXT_W_MM / prog.w, 150.0 / prog.h) < 1.9:
        img, note = mono_tiles(prog)
        cap += note
        big = True
    return (f'<figure class="pfig{" pbig" if big else ""}" id="fig-{no.replace(".", "-")}">{img}'
            f'<div class="prun">{"".join(run)}</div>'
            f'<figcaption><span class="fno">図 {no}</span>{B.inline_md(cap)}<span class="fsize">{size}</span>{plate}</figcaption></figure>')


TILE_CODEL = 2.0   # モノクロで記号が読める 1 コーデルの大きさ（mm）


def mono_tiles(prog):
    """モノクロで記号を書くには小さすぎる図を、記号が読める大きさに分割して描く"""
    import math
    cols = int(TEXT_W_MM // TILE_CODEL)
    rows = int(190 // TILE_CODEL)
    nx, ny = math.ceil(prog.w / cols), math.ceil(prog.h / rows)
    if nx * ny > 6:
        return (f'<div class="pimg">{prog_svg(prog, mono=True)}</div>',
                "（大きいため色の記号は省略。アセンブリのソースから pasm.py で画像を作れます）")
    tw, th = math.ceil(prog.w / nx), math.ceil(prog.h / ny)
    parts = []
    k = 0
    for j in range(ny):
        for i in range(nx):
            k += 1
            x0, y0 = i * tw, j * th
            x1, y1 = min(prog.w, x0 + tw), min(prog.h, y0 + th)
            sub = Program([row[x0:x1] for row in prog.grid[y0:y1]])
            svg = prog_svg(sub, max_w=TEXT_W_MM, max_h=200, max_codel=TILE_CODEL, mono=True)
            parts.append(f'<div class="ptile"><div class="ptile-cap">分割 {k}/{nx * ny}（列 {x0}〜{x1 - 1}、行 {y0}〜{y1 - 1}）</div>'
                         f'<div class="pimg">{svg}</div></div>')
    return "".join(parts), f"（色の記号が読めるよう {nx * ny} つに分割して掲載）"


def print_img(ctx, rest):
    m = re.match(r"(\S+)\s*(.*)", rest)
    path, args = m.group(1), B.parse_args(m.group(2))
    no = ctx.next_fig()
    cap = args.get("caption", "")
    src = os.path.join(ROOT, "site/img", path)
    dst = os.path.join(OUT, "img", path)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    from PIL import Image
    im = Image.open(src).convert("RGB")
    k = 1
    while im.width * (k + 1) <= 2400:   # 拡大は整数倍・最近傍（ぼけを防ぐ）
        k += 1
    if k > 1:
        im = im.resize((im.width * k, im.height * k), Image.NEAREST)
    im.save(dst)
    wmm = min(TEXT_W_MM, Image.open(src).width / 8.5) if "studio" not in path else TEXT_W_MM
    return (f'<figure class="pimgfig" id="fig-{no.replace(".", "-")}"><img src="img/{path}" style="width:{wmm:.1f}mm" alt="">'
            f'<figcaption><span class="fno">図 {no}</span>{B.inline_md(cap)}</figcaption></figure>')


B.DIRECTIVES["piet"] = print_piet
B.DIRECTIVES["img"] = print_img


# ------------------------------------------------------------------ 章の HTML
def scope_ids(name, body):
    """id を章ごとに一意にし、章間リンクを書籍内リンクにする"""
    body = re.sub(r'id="([^"]+)"', lambda m: f'id="{name}-{m.group(1)}"', body)
    body = re.sub(r'href="#([^"]+)"', lambda m: f'href="#{name}-{m.group(1)}"', body)
    body = re.sub(r'href="(ch\d\d|app[A-K]|preface)\.html#([^"]+)"', lambda m: f'href="#{m.group(1)}-{m.group(2)}"', body)
    body = re.sub(r'href="(ch\d\d|app[A-K]|preface)\.html"', lambda m: f'href="#{m.group(1)}"', body)
    body = re.sub(r'href="(playground|index)\.html"', 'href="#"', body)
    return body


def strip_svg(name):
    label = B.page_label(name) or "はじめに"
    import pasm
    prog = pasm.assemble(f'prints "{label}"', maxw=400)
    assert Machine(prog).run() == label
    return prog_svg(prog, max_w=TEXT_W_MM, max_codel=1.6, cls="strip-svg", mono=is_mono(name)), prog


PART_NOTE = {"第IV部": '<p class="part-note">第IV部と付録はモノクロで印刷しています。Piet の図は、明度を灰色の濃さ（淡い色ほど明るい灰色）で表し、'
                       '各コーデルに色をテキスト記法の記号（淡: r y g c b m／通常: R Y G C B M／濃: 1〜6、赤・黄・緑・シアン・青・マゼンタの順）で記しています。'
                       '色の一覧は第3章と付録B を参照してください。</p>'}


MONO_NOTE = ('<div class="mono-note">ここから先のページはモノクロで印刷しています。Piet の図は、明度を灰色の濃さ（淡い色ほど明るい灰色）で、'
             '色相をテキスト記法の記号（淡: r y g c b m／通常: R Y G C B M／濃: 1〜6、赤・黄・緑・シアン・青・マゼンタの順、白 .、黒 #）で示しています。'
             '色見本は巻頭の「色と命令の早見表」（<a class="pg" href="#quickref"></a> ページ）にあります。</div>')


def chapter_html(name, titles, text):
    ctx = B.Ctx(name)
    text = B.strip_title(text)
    body, toc = B.md_to_html(ctx, text)
    body = scope_ids(name, body)
    label = B.page_label(name)
    title = titles[name]
    svg, sp = strip_svg(name)
    strip = (f'<div class="ch-strip">{svg}<div class="ch-strip-cap">この帯は「{label or "はじめに"}」を出力する Piet プログラム'
             f'（{sp.w}×{sp.h} コーデル）</div></div>')
    kind = "chapter" if name.startswith("ch") else "appendix" if name.startswith("app") else "front"
    head = (f'<header class="ch-open"><div class="ch-no">{label}</div><h1 class="ch-title" data-run="{html.escape((label + "　" if label else "") + title)}">{html.escape(title)}</h1>{strip}</header>')
    secs = [(f"{name}-{t['id']}", t["name"]) for t in toc if t["level"] == 2]
    if is_mono(name):
        kind += " mono"
    if ED and name == ED.get("mono_from"):
        body = MONO_NOTE + body
    return f'<section class="{kind}" id="{name}">{head}<div class="prose">{body}</div></section>', secs, ctx.fig


# ------------------------------------------------------------------ 索引
import unicodedata
YOMI = {}
ROWS = ["あいうえお", "かきくけこ", "さしすせそ", "たちつてと", "なにぬねの", "はひふへほ", "まみむめも", "やゆよ", "らりるれろ", "わをん"]


def kana_key(y):
    """索引の並べ替えキー: 濁点・半濁点・長音を無視し、小書きを並字に"""
    y = "".join(ch for ch in unicodedata.normalize("NFD", y) if not unicodedata.combining(ch)).replace("ー", "")
    return y.translate(str.maketrans("ぁぃぅぇぉっゃゅょ", "あいうえおつやゆよ"))


def kana_row(y):
    c = kana_key(y)[:1]
    for r in ROWS:
        if c in r:
            return r[0]
    return "その他"


def index_terms():
    """print/index_terms.txt の用語（よみ順）と参照先、命令とその解説章"""
    terms, where = [], {}
    rows = []
    for line in open(os.path.join(OUT, "index_terms.txt"), encoding="utf-8"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        t, yomi, *rest = line.split("|")
        rows.append((yomi, t))
        where[t] = set(rest[0].split()) if rest else set()
    terms = [t for _, t in sorted(rows, key=lambda r: (kana_key(r[0]), r[0]))]
    global YOMI
    YOMI = {t: y for y, t in rows}
    cmd_ch = {"push": "ch06", "pop": "ch06", "add": "ch06", "subtract": "ch06", "multiply": "ch06", "divide": "ch06",
              "mod": "ch06", "not": "ch09", "greater": "ch09", "pointer": "ch09", "switch": "ch09", "duplicate": "ch11",
              "roll": "ch11", "in(number)": "ch07", "in(char)": "ch07", "out(number)": "ch07", "out(char)": "ch07"}
    for c, ch in cmd_ch.items():
        where[c] = {"ch04", ch, "appA"}
    return terms, list(cmd_ch), where


def add_index(soup, chapters):
    terms, cmds, where = index_terms()
    refs = {t: [] for t in terms + cmds}
    skip = {"pre", "code", "h1", "h2", "h3", "h4", "figcaption", "a", "svg", "header", "script", "style"}
    n = 0
    for sec in soup.select("section.chapter, section.appendix, section.front"):
        sid = sec.get("id")
        if sid in ("appF", "appG", "appD", "index"):
            continue
        texts = [s for s in sec.find_all(string=True) if not any(p.name in skip for p in s.parents)]
        for t in terms:
            if refs[t] and sid not in where.get(t, set()):
                continue        # 最初の出現と、用語集が示す章だけを拾う
            for s in texts:
                i = s.find(t)
                if i >= 0:
                    n += 1
                    aid = f"ix{n}"
                    anchor = soup.new_tag("span", id=aid, attrs={"class": "ixa"})
                    new_after = NavigableString(s[i:])
                    before = NavigableString(s[:i])
                    s.replace_with(new_after)
                    new_after.insert_before(before)
                    new_after.insert_before(anchor)
                    texts = [x for x in texts if x is not s] + [before, new_after]
                    refs[t].append(aid)
                    break
        codes = sec.select("p code, li code, td code")
        for c in cmds:
            if refs[c] and sid not in where[c]:
                continue
            for el in codes:
                if el.get_text() == c and not el.get("id"):
                    n += 1
                    el["id"] = f"ix{n}"
                    refs[c].append(el["id"])
                    break
    def entry(t, ids):
        pages = "".join(f'<a class="ixp" href="#{i}"></a>' for i in ids)
        return f'<li><span class="ixt">{html.escape(t)}</span><span class="ixps">{pages}</span></li>'
    body = ""
    cur = None
    for t in terms:
        if not refs[t]:
            continue
        r = kana_row(YOMI[t])
        if r != cur:
            body += ("</ul>" if cur else "") + f'<h2 class="ix-h">{r}</h2><ul class="ix-list">'
            cur = r
        body += entry(t, refs[t])
    body += "</ul>"
    body += '<h2 class="ix-h">命令</h2><ul class="ix-list ix-cmd">' + "".join(entry(c, refs[c]) for c in sorted(cmds) if refs[c]) + "</ul>"
    return body


# ------------------------------------------------------------------ 版（エディション）
CH = [f"ch{i:02d}" for i in range(1, 21)]
EDITIONS = {
    # 版A: 1 冊。第I〜III部をカラー、第IV部と付録はモノクロ
    "A": dict(title_suffix="", pages=["quickref", "preface"] + CH + ["appA", "appB", "appC", "appD", "appE", "appF", "appG", "index"],
              mono_from="part-ch16", mono={"ch16", "ch17", "ch18", "ch19", "ch20"}),
    # 版B: 1 冊。版A に「第IV部 カラー図版」を加える（第III部の直後＝カラー領域の末尾）
    "B": dict(title_suffix="", pages=["quickref", "preface"] + CH[:15] + ["plates4"] + CH[15:] + ["appA", "appB", "appC", "appD", "appE", "appF", "appG", "index"],
              mono_from="part-ch16", mono={"ch16", "ch17", "ch18", "ch19", "ch20"}, plates=CH[15:]),
    # 版C: 上下 2 分冊。付録以外はすべてカラー
    "C1": dict(title_suffix="上巻", vol=1, pages=["quickref", "preface"] + CH[:11] + ["appA", "appB", "appD", "appF", "appH", "appI", "appJ", "appK", "index"],
               mono_from="appA", mono=set(), answers=CH[:11], samples=CH[:11], extra_css=["book-monobig.css"]),
    # 版D: 1 冊。付録以外すべてカラー（詰めたレイアウト）。後半のモノクロは付録＋サンプル集＋方眼メモ
    "D": dict(title_suffix="", pages=["quickref", "preface"] + CH + ["appA", "appB", "appC", "appD", "appE", "appF", "appG", "appH", "appI", "appJ", "appK", "index"],
              mono_from="appA", mono=set(), samples=CH, compact=True),
    # 版S: 販売版（版D と同じ構成＋著者・発行所・ISDN・価格）
    "S": dict(title_suffix="", pages=["quickref", "preface"] + CH + ["appA", "appB", "appC", "appD", "appE", "appF", "appG", "appH", "appI", "appJ", "appK", "index"],
              mono_from="appA", mono=set(), samples=CH, compact=True, sale=True),
    "C2": dict(title_suffix="下巻", vol=2, pages=["quickref", "preface2"] + CH[11:] + ["appC", "appD", "appE", "appG", "appK", "index"],
               mono_from="appC", mono=set(), answers=CH[11:], samples=CH[11:], extra_css=["book-monobig.css"]),
}
ED = None   # 現在の版


def apply_sale():
    """販売版: book.json の sale の値で著者・奥付などを上書きする"""
    if not ED.get("sale"):
        return
    sale = CONF["sale"]
    CONF["author"] = sale["author"]
    CONF["colophon"] = list(sale["colophon"])
    if sale.get("isdn"):
        CONF["colophon"].append(["ISDN", isdn_text()])
    if sale.get("price"):
        CONF["colophon"].append(["頒布価格", f"{sale['price']:,} 円"])
    notes = [sale.get("ai_credit", ""), sale.get("tools_license", "")]
    CONF["colophon_note"] = "<br>".join(x for x in notes if x) + "<br>" + CONF["colophon_note"]


def isdn_digits():
    import ean13
    return ean13.full(CONF["sale"]["isdn"])


def isdn_text():
    """ISDN278-4-XXXXXX-XX-X C3055 ¥2520E の形"""
    sale = CONF["sale"]
    raw = sale["isdn"].replace("ISDN", "").strip()
    t = f"ISDN{raw}" if "-" in raw else f"ISDN{isdn_digits()}"
    if sale.get("ccode"):
        t += f" {sale['ccode']}"
    if sale.get("price"):
        t += f" ¥{sale['price']}E"
    return t


def barcode_block():
    """裏表紙の 2 段バーコード（ISDN と 292＋Cコード＋価格）"""
    sale = CONF.get("sale", {})
    if not ED.get("sale"):
        return ""
    if not sale.get("isdn"):
        return f'<div class="bbar"><div class="bbar-t">頒布価格 {int(sale["price"]):,} 円</div></div>' if sale.get("price") else ""
    import ean13
    code1 = isdn_digits()
    code2 = "292" + sale["ccode"].lstrip("C") + f"{int(sale.get('price', 0)):05d}"
    return (f'<div class="bbar">{ean13.svg(code1)}{ean13.svg(code2)}'
            f'<div class="bbar-t">{html.escape(isdn_text())}</div></div>')


def is_mono(name):
    return name in ED["mono"] or (name.startswith("app") or name == "index")


def scan_figures(name):
    """章の原稿から図の番号・ID・キャプションを順に取り出す（@piet と @img を数える）"""
    text = B.select_mode(open(os.path.join(B.SRC, name + ".md"), encoding="utf-8").read())
    figs, k, in_code = [], 0, False
    for line in text.split("\n"):
        if line.lstrip().startswith("```"):
            in_code = not in_code
            continue
        m = None if in_code else re.match(r"^\s*@(piet|img)\s+(\S+)\s*(.*)$", line)
        if m:
            k += 1
            if m.group(1) == "piet":
                figs.append((f"{int(name[2:])}.{k}", m.group(2), B.parse_args(m.group(3))))
    return figs


CMD_SHORT = [("push", "push"), ("pop", "pop"), ("add", "add"), ("subtract", "sub"), ("multiply", "mul"), ("divide", "div"),
             ("mod", "mod"), ("not", "not"), ("greater", "gt"), ("pointer", "ptr"), ("switch", "sw"), ("duplicate", "dup"),
             ("roll", "roll"), ("in_number", "inN"), ("in_char", "inC"), ("out_number", "outN"), ("out_char", "outC")]


def quickref_html():
    """巻頭（カラー）の「色と命令の早見表」2 ページ"""
    from piet import COL2CHAR, next_color, color_name, CMDS
    hj = ["赤", "黄", "緑", "シアン", "青", "マゼンタ"]
    lj = ["淡い（light）", "通常（normal）", "濃い（dark）"]
    def chip(c, big=False):
        fg = "#fff" if (c == BLACK or (c != WHITE and (c[1] == 2 or (c[1] == 1 and c[0] in (0, 4, 5))))) else "#000"
        return f'<span class="qr-chip{" big" if big else ""}" style="background:{hexc(c)};color:{fg}">{COL2CHAR[c]}</span>'
    def gray(c):
        fg = "#fff" if (c == BLACK or (c != WHITE and c[1] == 2)) else "#000"
        return f'<span class="qr-chip" style="background:{mono_color(c)};color:{fg}">{COL2CHAR[c]}</span>'
    rows = []
    for h in range(6):
        cells = "".join(f'<td>{chip((h, l), True)}<div class="qr-name">{color_name((h, l), True)}</div>'
                        f'<div class="qr-hex">{hexc((h, l))}</div></td>' for l in range(3))
        rows.append(f"<tr><th>{hj[h]}</th>{cells}</tr>")
    rows.append(f'<tr><th>無彩色</th><td>{chip(WHITE, True)}<div class="qr-name">白</div><div class="qr-hex">#FFFFFF</div></td>'
                f'<td>{chip(BLACK, True)}<div class="qr-name">黒</div><div class="qr-hex">#000000</div></td><td></td></tr>')
    colors = ('<table class="qr-colors"><thead><tr><th></th>' + "".join(f"<th>{x}</th>" for x in lj) + "</tr></thead><tbody>"
              + "".join(rows) + "</tbody></table>")
    grays = ('<div class="qr-mono">モノクロのページでの表し方: ' + gray((0, 0)) + gray((0, 1)) + gray((0, 2)) + gray(WHITE) + gray(BLACK)
             + '　淡い色は明るい灰、通常の色は中間の灰、濃い色は暗い灰で塗り、色相は記号の文字（r y g c b m など）で示します。</div>')
    lab = ["0 段階", "1 段階", "2 段階"]
    cmd_rows = "".join(f"<tr><th>{dh} 段階</th>" + "".join(
        f"<td>{(CMDS[dh][dl] or '（なし）').replace('_number', '(number)').replace('_char', '(char)')}</td>" for dl in range(3)) + "</tr>"
        for dh in range(6))
    cmds = ('<table class="qr-cmds"><thead><tr><th>色相の変化＼明度の変化</th>' + "".join(f"<th>{x}</th>" for x in lab)
            + f"</tr></thead><tbody>{cmd_rows}</tbody></table>")
    page1 = (f'<section class="front quickref" id="quickref"><header class="ch-open"><div class="ch-no"></div>'
             f'<h1 class="ch-title" data-run="色と命令の早見表">色と命令の早見表</h1></header>'
             f'<p class="qr-lead">Piet の 20 色と、本書のテキスト記法の記号です。色相は 赤→黄→緑→シアン→青→マゼンタ→赤、明度は 淡い→通常→濃い→淡い の順に循環します（第3章）。</p>'
             f'{colors}{grays}</section>')
    head = "".join(f"<th><span>{sh}</span></th>" for _, sh in CMD_SHORT)
    body = []
    for l in range(3):
        for h in range(6):
            c = (h, l)
            body.append(f"<tr><th>{chip(c)}</th>" + "".join(f"<td>{chip(next_color(c, cmd))}</td>" for cmd, _ in CMD_SHORT) + "</tr>")
    legend = "、".join(f"{sh}＝{cmd.replace('_number', '(number)').replace('_char', '(char)')}" for cmd, sh in CMD_SHORT if sh != cmd)
    page2 = (f'<section class="front quickref" id="quickref2"><h2 class="qr-h">命令表（第4章）</h2>'
             f'<p class="qr-lead">色ブロックから次の色ブロックへ移るとき、色相と明度が何段階進んだかで命令が決まります。</p>{cmds}'
             f'<h2 class="qr-h qr-h2">次の色の早見表</h2>'
             f'<p class="qr-lead">左端の「今の色」から、上の命令を実行するために次に置く色です（付録B の表と同じ内容）。{legend}。</p>'
             f'<table class="qr-next"><thead><tr><th>今の色</th>{head}</tr></thead><tbody>{"".join(body)}</tbody></table></section>')
    return page1 + page2


def plates_html(chapters):
    """第IV部の図をカラーでまとめた図版ページ"""
    items = []
    for ch in chapters:
        for no, sid, args in scan_figures(ch):
            prog = B.load_sample(sid)
            svg = prog_svg(prog, max_w=TEXT_W_MM, max_h=110, max_codel=3.2)
            items.append(f'<figure class="plate" id="plate-{no.replace(".", "-")}"><div class="pimg">{svg}</div>'
                         f'<figcaption><span class="fno">図 {no}</span>{B.inline_md(args.get("caption", ""))}'
                         f'<span class="fsize">（{prog.w}×{prog.h} コーデル）</span></figcaption></figure>')
    head = ('<header class="ch-open"><div class="ch-no">第IV部</div><h1 class="ch-title" data-run="第IV部 カラー図版">カラー図版</h1></header>'
            '<p class="plates-lead">第IV部の Piet の図をカラーでまとめました。本文中の図はモノクロ（灰色の濃さと色の記号）で示し、'
            'キャプションにこの図版のページを記しています。</p>')
    return f'<section class="front plates" id="plates4">{head}<div class="plates-grid">{"".join(items)}</div></section>'


def samples_md(chapters, titles):
    """付録K: 図のプログラムのソース（テキスト記法・アセンブリ・Mini）"""
    out = ["# 付録K サンプルプログラム集", "",
           "本文の図に載せた Piet のプログラムを、そのまま打ち込める形で載せます。",
           "テキスト記法（第3章、付録B）のものは Piet スタジオの「ファイル → テキスト記法を開く」で読み込めます"
           "（またはテキストファイルに保存して `python3 piet.py png 名前.txt 名前.png`）。",
           "アセンブリ（pasm）のものは `python3 pasm.py 名前.pasm -o 名前.png`、Mini のものは `python3 minic.py 名前.mini -o 名前.png` で画像になります"
           "（ツールのソースコードは付録G）。", ""]
    for ch in chapters:
        figs = scan_figures(ch)
        if not figs:
            continue
        out += [f"## K.{int(ch[2:])} {B.page_label(ch)} {titles[ch]}", ""]
        for no, sid, args in figs:
            base = os.path.join(ROOT, "samples", sid)
            cap = args.get("caption", "")
            out.append(f"**図 {no}** {cap}")
            out.append("")
            if os.path.exists(base + ".txt"):
                kind, src = "テキスト記法", open(base + ".txt", encoding="utf-8").read().strip("\n")
            elif os.path.exists(base + ".pasm"):
                kind, src = "アセンブリ（pasm）", open(base + ".pasm", encoding="utf-8").read().strip("\n")
            elif os.path.exists(base + ".mini"):
                kind, src = "Mini", open(base + ".mini", encoding="utf-8").read().strip("\n")
            else:
                prog = B.load_sample(sid)
                if prog.w <= 90:
                    kind, src = "テキスト記法（画像から変換）", prog.to_text()
                else:
                    out += ["（画像のみ。大きいため省略）", ""]
                    continue
            inp = B.sample_input(sid)
            out += [f"{kind}" + (f"／入力例: `{inp.strip()[:40]}`" if inp and inp.strip() and "`" not in inp else ""), "",
                    "```text", src, "```", ""]
    return "\n".join(out)


def grid_pad_page():
    """方眼メモ（5mm 方眼）"""
    w, h, st = 140, 180, 5
    lines = [f'<line x1="{x}" y1="0" x2="{x}" y2="{h}"/>' for x in range(0, w + 1, st)]
    lines += [f'<line x1="0" y1="{y}" x2="{w}" y2="{y}"/>' for y in range(0, h + 1, st)]
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}mm" height="{h}mm">'
           f'<g stroke="#b3b3b3" stroke-width="0.15">{"".join(lines)}</g></svg>')
    return (f'<section class="padpage"><div class="pad-head">方眼メモ<span>Piet のプログラムの下書きに使えます（1 マス＝1 コーデル）。'
            f'色はテキスト記法の記号（r R 1 …）で書き込むと便利です。</span></div>{svg}</section>')


def main():
    titles = {n: B.read_title(n) for n in B.ORDER}
    titles["preface"] = titles["preface"] or "はじめに"
    titles["appK"] = "サンプルプログラム集"
    titles["preface2"] = "下巻について"
    titles["plates4"] = "第IV部 カラー図版"
    parts_html, toc_items, figs = [], [], 0
    plate_refs = set(ED.get("plates", []))
    for n in ED["pages"]:
        for p in B.PARTS:
            if p[3][0] == n and p[1]:
                pid = "part-" + p[3][0]
                lis = "".join(f'<li><span>{B.page_label(c)}</span>{html.escape(titles[c])}</li>' for c in p[3])
                note = PART_NOTE.get(p[0], "") if n in ED["mono"] else ""
                if note and ED.get("plates"):
                    note = note.replace("</p>", "図のカラー版は、この部の直前の「カラー図版」にまとめ、各図のキャプションにそのページを記しています。</p>")
                mono = " mono" if n in ED["mono"] else ""
                parts_html.append(f'<section class="part-open{mono}" id="{pid}"><div class="part-no">{p[0]}</div>'
                                  f'<h1 class="part-title" data-run="{p[0]}　{p[1]}">{p[1]}</h1><p class="part-desc">{p[2]}</p>{note}'
                                  f'<ol class="part-list">{lis}</ol><div class="part-band"></div></section>')
                toc_items.append(f'<li class="toc-part"><a href="#{pid}">{p[0]}　{p[1]}</a></li>')
        if n.startswith("app") and not any(x.startswith("toc-app") for x in toc_items):
            toc_items.append('<li class="toc-part toc-app">付録</li>')
        if n == "index":
            parts_html.append('<section class="appendix mono" id="index"><header class="ch-open"><div class="ch-no"></div>'
                              '<h1 class="ch-title" data-run="索引">索引</h1></header><div class="prose ix">@@INDEX@@</div></section>')
            toc_items.append('<li class="toc-ch"><a href="#index"><span class="toc-no"></span>索引</a></li>')
            continue
        if n == "quickref":
            parts_html.append(quickref_html())
            toc_items.append('<li class="toc-ch"><a href="#quickref"><span class="toc-no"></span>色と命令の早見表</a></li>')
            continue
        if n == "plates4":
            parts_html.append(plates_html(ED["plates"]))
            toc_items.append(f'<li class="toc-ch"><a href="#plates4"><span class="toc-no"></span>{titles[n]}</a></li>')
            continue
        if n == "appD":
            text = answers_md(titles, ED.get("answers"))
        elif n == "appG":
            text = B.build_tools_appendix()
            if ED.get("sale") and CONF["sale"].get("tools_license"):
                text = text.replace("\n\n| ファイル |", "\n\n" + CONF["sale"]["tools_license"] + "\n\n| ファイル |", 1)
        elif n == "appK":
            text = samples_md(ED["samples"], titles)
        elif n == "preface2":
            text = open(os.path.join(OUT, "preface2.md"), encoding="utf-8").read()
        else:
            text = open(os.path.join(B.SRC, n + ".md"), encoding="utf-8").read()
        if n == "preface" and ED.get("vol") == 1:
            text = text.replace("\n## 本書の対象読者", "\n" + VOL_NOTE + "\n\n## 本書の対象読者", 1)
        global PLATE_CH
        PLATE_CH = n if n in plate_refs else None
        sec, secs, nf = chapter_html(n if n != "preface2" else "preface", titles, text) if n != "preface2" else chapter_html_named("preface2", titles, text)
        figs += nf
        parts_html.append(sec)
        label = B.page_label(n) if n not in ("preface2",) else ""
        sub = "".join(f'<li class="toc-sec"><a href="#{i}">{nm}</a></li>' for i, nm in secs) if n.startswith("ch") else ""
        toc_items.append(f'<li class="toc-ch"><a href="#{n}"><span class="toc-no">{label}</span>{html.escape(titles[n])}</a></li>{sub}')
        if n in ("preface", "preface2"):
            parts_html.append("@@TOC@@")
    c = CONF
    suffix = ED["title_suffix"]
    tp_title = c["title_html"] + (f'<span class="tp-vol">{suffix}</span>' if suffix else "")
    title_page = (f'<section class="titlepage"><div class="tp-band"></div><div class="tp-title">{tp_title}</div>'
                  f'<div class="tp-sub">{html.escape(c["subtitle"])}</div><div class="tp-author">{html.escape(c["author"])}</div></section>'
                  f'<section class="titleverso"><p>{c["verso_note"]}</p></section>')
    toc = (f'<section class="toc" id="toc"><header class="ch-open"><div class="ch-no"></div><h1 class="ch-title" data-run="目次">目次</h1></header>'
           f'<ol class="toc-list">{"".join(toc_items)}</ol></section>')
    rows = "".join(f"<tr><th>{html.escape(k)}</th><td>{html.escape(v)}</td></tr>" for k, v in c["colophon"] if v)
    full_title = c["title"] + (f"　{suffix}" if suffix else "")
    colophon = (f'<section class="colophon"><div class="col-title">{html.escape(full_title)}</div>'
                f'<div class="col-sub">{html.escape(c["subtitle"])}</div><div class="col-date">{html.escape(c["edition"])}</div>'
                f'<table>{rows}</table><p class="col-note">{c["colophon_note"]}</p></section>')
    pad = int(os.environ.get("PAD_PAGES", "0"))
    colophon = grid_pad_page() * pad + colophon
    doc = "\n".join(parts_html).replace("@@TOC@@", toc)
    page = (f'<!doctype html><html lang="ja"><head><meta charset="utf-8"><title>{html.escape(full_title)}</title>'
            f'<link rel="stylesheet" href="book.css">' + ('<link rel="stylesheet" href="book-compact.css">' if ED.get("compact") else "") + "".join(f'<link rel="stylesheet" href="{x}">' for x in ED.get("extra_css", [])) + f'</head><body>{title_page}{doc}{colophon}</body></html>')
    soup = BeautifulSoup(page, "lxml")
    idx = add_index(soup, None)
    out = str(soup).replace("@@INDEX@@", idx)
    with open(os.path.join(OUT, "book.html"), "w", encoding="utf-8") as f:
        f.write(out)
    # 最初のモノクロページを見分けるための文字列（printsplit.py が使う）
    mf = ED["mono_from"]
    marker = "インタプリタ、アセンブラ、コンパイラを自作し" if mf == "part-ch16" else f"この帯は「{B.page_label(mf)}」を出力する"
    with open(os.path.join(OUT, "mono_marker.txt"), "w", encoding="utf-8") as f:
        f.write(marker)
    print(f"print/book.html（版{os.environ.get('EDITION', 'A')}）: 図 {figs} 点, {len(out) // 1024} KB")


VOL_NOTE = """!!! note "上巻と下巻"
    本書は上下 2 冊に分かれています。上巻には第I部・第II部（第1〜11章）と、付録A（命令早見表）・付録B（色一覧とテキスト記法）・付録D（第1〜11章の練習問題の解答）・付録F（用語集）・付録H（Piet の派生言語と関連言語）・付録I（Piet イディオム集）・付録J（数と文字の作り方表）・付録K（上巻のサンプルプログラム集）を、下巻には第III部・第IV部（第12〜20章）と、付録C（仕様の曖昧な点と処理系ごとの違い）・付録D（第12〜20章の解答）・付録E（参考文献とリンク）・付録G（付属ツールのソースコード）・付録K（下巻のサンプルプログラム集）を収めています。本文で別の巻の章や付録を参照している箇所は、その巻をご覧ください。"""


def answers_md(titles, chapters):
    if chapters is None:
        return B.build_answers(titles)
    parts = ["# 付録D 練習問題の解答", "",
             "この巻に収めた章の練習問題の解答例です。Piet のプログラムには多くの書き方があるので、ここに示すのは一例です。", ""]
    for n in chapters:
        f = os.path.join(B.SRC, "answers", n + ".md")
        if not os.path.exists(f):
            continue
        t = B.strip_title(open(f, encoding="utf-8").read())
        t = re.sub(r"^(#{2,5}) ", lambda m: "#" + m.group(1) + " ", t, flags=re.M)
        parts += [f"## {B.page_label(n)} {titles.get(n) or ''}", "", t, ""]
    return "\n".join(parts)


def chapter_html_named(name, titles, text):
    """はじめに以外の前付（下巻について）"""
    ctx = B.Ctx("preface")
    body, toc = B.md_to_html(ctx, B.strip_title(text))
    body = scope_ids(name, body)
    head = f'<header class="ch-open"><div class="ch-no"></div><h1 class="ch-title" data-run="{titles[name]}">{titles[name]}</h1></header>'
    return f'<section class="front" id="{name}">{head}<div class="prose">{body}</div></section>', [], 0


# ------------------------------------------------------------------ 表紙（表4・背・表1 を一続きに）
def build_cover(pages):
    c = CONF
    import math
    spine = round(pages * c["spine_mm_per_page"] + 2 * c["cover_paper_mm"], 1)   # 本文厚み＋表紙の紙厚×2
    if c.get("spine_mm"):
        spine = float(c["spine_mm"])            # 印刷所の自動計算の値を優先
    if os.environ.get("SPINE_MM"):
        spine = float(os.environ["SPINE_MM"])   # 印刷所の計算ツールで出た背幅で上書き
    W, H, BL = 182.0, 257.0, 3.0
    total_w = BL + W + spine + W + BL
    prog = Program.from_image(os.path.join(ROOT, "site/img/ch15/mondrian.png"), 1)
    art = prog_svg(prog, max_w=W + BL, max_h=200, max_codel=99, cls="cv-art")
    five = Program.from_image(os.path.join(ROOT, "site/img/ch01/five.png"), 1)
    five_svg = prog_svg(five, max_w=40, max_codel=5, cls="cv-five")
    vol = (ED or {}).get("title_suffix", "")
    vol_html = f'<span class="fvol">{vol}</span>' if vol else ""
    band = "".join(f'<span style="background:{x}"></span>' for x in ["#FF0000", "#FFFF00", "#00FF00", "#00FFFF", "#0000FF", "#FF00FF"])
    texts = list(c["back_blurb"])
    if vol == "上巻":
        texts[-1] = texts[-1].replace("のソースコードも全文収録。", "のソースコードも全文収録（下巻）。上巻は第I部・第II部（第1〜11章）、下巻は第III部・第IV部（第12〜20章）を収めています。")
    elif vol == "下巻":
        texts[-1] = texts[-1] + "上巻は第I部・第II部（第1〜11章）、下巻は第III部・第IV部（第12〜20章）を収めています。"
    blurb = "".join(f"<p>{html.escape(t)}</p>" for t in texts)
    page = f"""<!doctype html><html lang="ja"><head><meta charset="utf-8"><title>表紙</title><style>
@font-face {{ font-family: "Dela Gothic One"; src: url("fonts/DelaGothicOne-Regular.ttf"); }}
@page {{ size: {total_w:.2f}mm {H + 2 * BL:.2f}mm; margin: 0; }}
html, body {{ margin: 0; }}
body {{ width: {total_w:.2f}mm; height: {H + 2 * BL:.2f}mm; position: relative; overflow: hidden; background: #fff; font-family: "Noto Sans CJK JP", sans-serif; color: #000; }}
.panel {{ position: absolute; top: 0; height: {H + 2 * BL:.2f}mm; }}
.back {{ left: 0; width: {BL + W:.2f}mm; }}
.spine {{ left: {BL + W:.2f}mm; width: {spine:.2f}mm; background: #fff; color: #000; }}
.front {{ left: {BL + W + spine:.2f}mm; width: {W + BL:.2f}mm; }}
.band {{ position: absolute; left: 0; right: 0; height: 9mm; display: flex; }}
.band span {{ flex: 1; }}
.front .art {{ position: absolute; top: 0; left: 0; line-height: 0; }}
.front .art svg {{ display: block; }}
.fvol {{ display: inline-block; margin-left: 5mm; font-size: 22pt; border: 1.2mm solid #000; padding: 0 3mm; vertical-align: 6pt; }}
.ftitle {{ position: absolute; left: 16mm; top: 112mm; font-family: "Dela Gothic One", sans-serif; font-size: 44pt; line-height: 1.12; }}
.fsub {{ position: absolute; left: 16mm; top: 196mm; font-weight: 700; font-size: 14pt; }}
.fnote {{ position: absolute; left: 16mm; top: 206mm; font-size: 7.5pt; color: #333; width: 150mm; }}
.fauthor {{ position: absolute; left: 16mm; bottom: {BL + 18:.2f}mm; font-size: 13pt; font-weight: 700; }}
.front .band {{ bottom: 0; height: {BL + 9:.2f}mm; }}
.back .band {{ bottom: 0; height: {BL + 9:.2f}mm; }}
.btext {{ position: absolute; left: {BL + 20:.2f}mm; top: {BL + 26:.2f}mm; width: 142mm; font-family: "Noto Serif CJK JP", serif; font-size: 9.5pt; line-height: 1.9; }}
.btext p {{ margin: 0 0 4mm; text-indent: 1em; text-align: justify; }}
.bhead {{ font-family: "Dela Gothic One", sans-serif; font-size: 16pt; margin-bottom: 8mm; border-top: 2mm solid #000; padding-top: 4mm; }}
.bbar {{ position: absolute; top: {BL + 10:.2f}mm; right: 12mm; display: flex; flex-direction: column; align-items: flex-end; gap: 1.5mm; background: #fff; padding: 2mm; }}
.bbar svg {{ display: block; }}
.bbar-t {{ font-family: "Noto Sans Mono", monospace; font-size: 7pt; letter-spacing: 0.02em; }}
.btext.with-bar {{ top: {BL + 62:.2f}mm; }}
.btext.with-bar ~ .bfive {{ top: {BL + 182:.2f}mm; }}
.bfive {{ position: absolute; left: {BL + 20:.2f}mm; top: {BL + 150:.2f}mm; display: flex; gap: 6mm; align-items: center; font-size: 8pt; line-height: 1.7; width: 142mm; }}
.stitle {{ position: absolute; top: {BL + 22:.2f}mm; left: 0; right: 0; writing-mode: vertical-rl; margin: 0 auto; font-family: "Dela Gothic One", sans-serif; font-size: {min(spine * 0.55, 15):.1f}mm; line-height: 1; display: flex; align-items: center; width: 100%; }}
.sauthor {{ position: absolute; bottom: {BL + 22:.2f}mm; left: 0; right: 0; writing-mode: vertical-rl; margin: 0 auto; font-size: {min(spine * 0.35, 4.5):.1f}mm; font-weight: 700; display: flex; align-items: center; width: 100%; }}
.spine .band {{ top: 0; height: {BL + 9:.2f}mm; }}
</style></head><body>
<div class="panel back">{barcode_block()}<div class="btext{' with-bar' if barcode_block() else ''}"><div class="bhead">絵を描いて、プログラムを書く。</div>{blurb}</div>
<div class="bfive">{five_svg}<div>これが本書の最初のプログラムです。<br>赤い 5 マスが「5」を表し、濃い赤へ移ると 5 を積み（push）、<br>淡いマゼンタへ移ると 5 を出力します（out(number)）。</div></div>
<div class="band">{band}</div></div>
<div class="panel spine"><div class="band">{band}</div><div class="stitle">Piet プログラミング入門{"　" + vol if vol else ""}</div><div class="sauthor">{html.escape(c["author"])}</div></div>
<div class="panel front"><div class="art">{art}</div>
<div class="ftitle">Piet<br>プログラミング<br>入門{vol_html}</div><div class="fsub">{html.escape(c["subtitle"])}</div>
<div class="fnote">上の絵は、実行すると「Piet」と出力する Piet のプログラムです（第15章）。</div>
<div class="fauthor">{html.escape(c["author"])}</div><div class="band">{band}</div></div>
</body></html>"""
    with open(os.path.join(OUT, "cover.html"), "w", encoding="utf-8") as f:
        f.write(page)
    print(f"print/cover.html: 背幅 {spine} mm（{pages} ページ）、全体 {total_w:.1f} × {H + 2 * BL:.1f} mm")
    return spine, total_w


if __name__ == "__main__" and len(sys.argv) > 2 and sys.argv[1] == "cover":
    ED = EDITIONS[os.environ.get("EDITION", "A")]
    apply_sale()
    build_cover(int(sys.argv[2]))


if __name__ == "__main__" and len(sys.argv) == 1:
    ED = EDITIONS[os.environ.get("EDITION", "A")]
    apply_sale()
    if ED.get("compact"):
        TEXT_W_MM = 146.0
        MAX_CODEL = 3.5
    main()
