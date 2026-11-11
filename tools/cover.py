"""cover.py -- 表紙（site/index.html）とプレイグラウンド（site/playground.html）を生成する"""
import os, html
import build as B

HERO = "ch15/mondrian"
HERO_CAPTION = "第15章のモンドリアン風のプログラム。「実行」を押すと Piet と出力します。「再生」で動きを目で追えます"


def hero_figure():
    ctx = B.Ctx("cover")
    h = B.render_piet(ctx, f'{HERO} caption="{HERO_CAPTION}"')
    return h.replace('<span class="fno">図 0.1</span>', "")


def build(titles, stats):
    total = sum(s[0] for n, s in stats.items() if n != "appG")
    figs = sum(s[1] for s in stats.values())
    nch = sum(1 for n in stats if n.startswith("ch"))
    napp = sum(1 for n in stats if n.startswith("app"))
    parts_html = []
    for label, name, desc, pages in B.PARTS:
        items = []
        for n in pages:
            if titles.get(n) is None:
                continue
            no = B.page_label(n)
            items.append(f'<li><a href="{n}.html"><span class="no">{no}</span><span>{html.escape(titles[n])}</span></a></li>')
        if not items:
            continue
        head = f"{label}　{name}" if name else label
        parts_html.append(f'<section class="cover-part"><h2>{head}</h2>' + (f"<p>{desc}</p>" if desc else "")
                          + f'<ol>{"".join(items)}</ol></section>')
    band = "".join(f'<span style="background:{c}"></span>' for c in ["#FF0000", "#FFFF00", "#00FF00", "#00FFFF", "#0000FF", "#FF00FF"])
    nav = B.nav_lists("index", titles)
    page = f"""<meta charset="utf-8">
<title>{B.BOOK}</title>
<meta name="claude:viewport-fit-sides" content="cover">
{B.FONTS}
<link rel="stylesheet" href="style.css">
<header class="topbar" style="display:flex"><a class="book" href="index.html">{B.BOOK}</a>
<details><summary>目次</summary><div class="toc-drop"><ul class="toc-list">{nav}</ul></div></details></header>
<main><div class="cover">
<section class="cover-hero">
<div>
<h1>Piet<br>プログラミング<br>入門<small>{B.SUB}</small></h1>
<p class="lead">Piet（ピート）は、色のついたマス目を並べた「絵」そのものがプログラムになる言語です。
色が変わるたびに命令が実行され、ブロックの大きさが数になり、黒い壁と白い通路が処理の流れを導きます。
本書は小さなサンプルから始めて、スタックと分岐・ループ、実践的なプログラム、そしてインタプリタやコンパイラの自作まで、Piet を体系的に解説します。</p>
<div class="cta"><a class="btn primary" href="ch01.html">第1章から読む</a><a class="btn" href="preface.html">はじめに</a><a class="btn" href="playground.html">プレイグラウンド</a></div>
<div class="cover-meta"><span><b>{nch}</b> 章</span><span>付録 <b>{napp}</b></span><span>図 <b>{figs}</b> 点（すべて実行可能）</span><span>原稿 約 <b>{total // 1000 * 1000:,}</b> 字</span></div>
</div>
<div>{hero_figure()}</div>
</section>
<div class="palette-band" aria-hidden="true">{band}</div>
<div class="cover-toc">
{"".join(parts_html)}
</div>
<p style="color:var(--muted);font-size:.85rem">本文中の Piet プログラムはすべて、本書付属のインタプリタと npiet 1.3h の両方で実行して出力を確かめています。図の「実行」「1 ステップ」でブラウザ上でも動かせます。</p>
</div></main>
<script src="piet.js"></script>
"""
    with open(os.path.join(B.SITE, "index.html"), "w", encoding="utf-8") as f:
        f.write(page)
    pg = os.path.join(B.HERE, "web", "playground.html")
    if os.path.exists(pg):
        body = open(pg, encoding="utf-8").read()
        doc = ('<!doctype html>\n<html lang="ja"><head><meta charset="utf-8">'
               '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
               f'<title>プレイグラウンド｜{B.BOOK}</title><meta name="claude:viewport-fit-sides" content="cover">{B.FONTS}'
               '<link rel="stylesheet" href="style.css"></head><body>\n'
               f'<header class="topbar" style="display:flex"><a class="book" href="index.html">{B.BOOK}</a>'
               f'<details><summary>目次</summary><div class="toc-drop"><ul class="toc-list">{nav}</ul></div></details></header>\n'
               + body + '\n<script src="piet.js"></script><script src="playground.js"></script></body></html>\n')
        with open(os.path.join(B.SITE, "playground.html"), "w", encoding="utf-8") as f:
            f.write(doc)
