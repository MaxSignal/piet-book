#!/usr/bin/env python3
"""全サンプル（site/img）と外部サンプルの Python 版実行結果を JSON に書き出す（JS エンジン照合用）"""
import sys, os, glob, json
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from piet import Program, Machine
cases = []
for png in sorted(glob.glob(os.path.join(ROOT, "site/img/**/*.png"), recursive=True)) + sys.argv[2:]:
    if png.endswith("-big.png"): continue
    sid = os.path.relpath(png, os.path.join(ROOT, "site/img"))[:-4]
    base = os.path.join(ROOT, "samples", sid)
    ins = [open(f).read() for f in sorted(glob.glob(base + ".in*"))] or [""]
    try: prog = Program.from_image(png)
    except Exception: continue
    for inp in ins:
        m = Machine(prog, inp); out = m.run(300000)
        cases.append({"id": sid, "text": prog.to_text(), "input": inp, "out": out, "steps": m.steps})
json.dump(cases, open(sys.argv[1], "w"))
print(len(cases), "cases")
