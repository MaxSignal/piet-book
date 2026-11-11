#!/usr/bin/env python3
"""samples.py -- サンプルのビルドと検証

  python3 tools/samples.py            # 全サンプルを PNG 化し、piet.py と npiet で実行して検証
  python3 tools/samples.py ch07       # 章を絞る
  python3 tools/samples.py ch07/hello # 1 本だけ

samples/chNN/NAME.txt   テキスト格子（1 文字 = 1 コーデル）
samples/chNN/NAME.pasm  アセンブリ（tools/pasm.py で変換）
samples/chNN/NAME.png   既製の画像（そのまま使う）
samples/chNN/NAME.mini  ミニ言語（tools/minic.py があれば変換）
samples/chNN/NAME.in    標準入力（任意。複数ケースは NAME.in2, NAME.in3 ...）
samples/chNN/NAME.out   期待される出力（任意。.in2 には .out2 が対応）
samples/chNN/NAME.flags 特殊指定（任意）: "noterm" = 停止しないことが意図どおり（-e で打ち切って比較）
                                          "nonpiet" = npiet との比較を省略（仕様差の実演用）
出力: site/img/chNN/NAME.png（コーデルサイズ 1） と NAME-big.png（コーデルサイズ 10）
npiet は環境変数 NPIET、PATH 上の npiet、ext/npiet-1.3h/npiet の順に探す（見つからなければ npiet との比較を省略）
"""
import sys, os, glob, subprocess
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from piet import Program, Machine
import pasm

import shutil
NPIET = os.environ.get("NPIET") or shutil.which("npiet") or os.path.join(ROOT, "ext/npiet-1.3h/npiet")


def build_one(src):
    base, ext = os.path.splitext(src)
    sid = os.path.relpath(base, os.path.join(ROOT, "samples"))
    if ext == ".txt":
        prog = Program.from_text(open(src, encoding="utf-8").read())
    elif ext == ".pasm":
        prog = pasm.assemble(open(src, encoding="utf-8").read())
    elif ext == ".png":
        prog = Program.from_image(src)
    elif ext == ".mini":
        import minic
        prog = pasm.assemble(minic.compile_src(open(src, encoding="utf-8").read()))
    else:
        return None
    out = os.path.join(ROOT, "site/img", sid)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    prog.save_png(out + ".png", 1)
    prog.save_png(out + "-big.png", 10)
    return sid, prog, out + ".png"


def cases(base):
    res = []
    for inf in sorted(glob.glob(base + ".in*")):
        suf = inf[len(base) + 3:]
        outf = base + ".out" + suf
        res.append((open(inf, encoding="utf-8").read(), open(outf, encoding="utf-8").read() if os.path.exists(outf) else None))
    if not res:
        outf = base + ".out"
        res.append(("", open(outf, encoding="utf-8").read() if os.path.exists(outf) else None))
    return res


def run_npiet(png, inp, steps=None):
    if not os.path.exists(NPIET) and not shutil.which(NPIET):
        return None
    cmd = [NPIET, "-q", "-cs", "1"] + (["-e", str(steps)] if steps else []) + [png]
    try:
        r = subprocess.run(cmd, input=inp.encode("utf-8"), capture_output=True, timeout=60)
        return r.stdout.decode("utf-8", "replace")
    except subprocess.TimeoutExpired:
        return "<<TIMEOUT>>"


def main(argv):
    pat = argv[0] if argv else ""
    srcs = []
    for ext in ("txt", "pasm", "png", "mini"):
        srcs += glob.glob(os.path.join(ROOT, "samples", "**", "*." + ext), recursive=True)
    srcs = sorted(s for s in srcs if pat in os.path.relpath(s, os.path.join(ROOT, "samples")))
    ok = bad = 0
    for src in srcs:
        base = os.path.splitext(src)[0]
        flagf = base + ".flags"
        flags = open(flagf).read().split() if os.path.exists(flagf) else []
        try:
            r = build_one(src)
        except Exception as e:
            print(f"ERROR {src}: {e}")
            bad += 1
            continue
        if r is None:
            continue
        sid, prog, png = r
        for k, (inp, exp) in enumerate(cases(base)):
            steps = 5000 if "noterm" in flags else 3_000_000
            m = Machine(prog, inp)
            mine = m.run(steps)
            status = []
            if not m.halted and "noterm" not in flags:
                status.append(f"停止せず({m.steps}step)")
            np_ = None if "nonpiet" in flags else run_npiet(png, inp, steps if "noterm" in flags else None)
            if np_ is not None:
                if "noterm" in flags:
                    np_ = np_[:len(mine)]
                    mine_c = mine[:len(np_)]
                else:
                    mine_c = mine
                if np_ != mine_c:
                    status.append(f"npiet不一致 npiet={np_[:60]!r} mine={mine[:60]!r}")
            if exp is not None and mine != exp:
                status.append(f"期待値不一致 exp={exp[:60]!r} got={mine[:60]!r}")
            tag = f"{sid}" + (f" [case {k+1}]" if k else "")
            if status:
                bad += 1
                print(f"NG  {tag} ({prog.w}x{prog.h}): " + "; ".join(status))
            else:
                ok += 1
                print(f"ok  {tag} ({prog.w}x{prog.h}, {m.steps} steps) out={mine[:50]!r}")
    print(f"--- {ok} ok, {bad} NG")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
