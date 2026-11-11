#!/usr/bin/env python3
"""pasm.py -- 本書の Piet アセンブラ

テキストのアセンブリ言語（スタック命令＋ラベル＋ジャンプ）から Piet 画像を生成する。

  python3 pasm.py prog.pasm -o prog.png [-cs N] [--text]

文法（1 行 1 命令、; 以降はコメント）
  label:                 ラベル
  push N                 整数 N を積む（0・負数・大きな数は自動で計算式に展開）
  pop add sub mul div mod not gt dp cc dup roll inn inc outn outc
  jmp L                  無条件ジャンプ
  jz L / jnz L           先頭を取り出し、0 なら / 0 以外なら L へ
  halt                   停止
  prints "文字列"        文字列を出力（\\n などのエスケープ可）
  swap                   上 2 つを交換
  pick D                 深さ D（0 = 先頭）の値を複製して積む
  bury D                 先頭を深さ D へ沈める
"""
import sys, re, functools
sys.path.insert(0, __import__("os").path.dirname(__file__))
from piet import Program, next_color, WHITE, BLACK, ALIASES, CMD_DELTA

PRIMS = {"push", "pop", "add", "subtract", "multiply", "divide", "mod", "not", "greater",
         "pointer", "switch", "duplicate", "roll", "in_number", "in_char", "out_number", "out_char"}
START_COLOR = (0, 0)   # 淡赤
DIRECT_MAX = 12        # この値以下はブロックの大きさで直接 push する


# ------------------------------------------------------------------ 数値の生成
@functools.lru_cache(maxsize=None)
def number_plan(n):
    """正の整数 n を積むための (コスト, 命令列)。コスト ≒ 使うコーデル数"""
    assert n >= 1
    best = (n + 1, [("push", n)]) if n <= DIRECT_MAX else (10 ** 9, None)
    # 平方 a*a = a dup mul
    r = int(n ** 0.5)
    if r * r == n and r >= 2:
        c, s = number_plan(r)
        cand = (c + 2, s + [("duplicate",), ("multiply",)])
        if cand[0] < best[0]:
            best = cand
    # 積 a*b
    for a in range(2, r + 1):
        if n % a == 0:
            ca, sa = number_plan(a)
            cb, sb = number_plan(n // a)
            cand = (ca + cb + 1, sa + sb + [("multiply",)])
            if cand[0] < best[0]:
                best = cand
    # 和 m + k（k は小さい数）
    if n > DIRECT_MAX:
        for k in range(1, DIRECT_MAX + 1):
            cm, sm = number_plan(n - k)
            cand = (cm + k + 2, sm + [("push", k), ("add",)])
            if cand[0] < best[0]:
                best = cand
    return best


@functools.lru_cache(maxsize=None)
def big_plan(n):
    """大きな数 n（> 20000）: n = (n // k) * k + r と分解する（再帰は log n 段）"""
    if n <= 20000:
        for i in range(300, n, 300):
            number_plan(i)
        return number_plan(n)
    best = None
    for k in range(2, DIRECT_MAX + 1):
        q, r = divmod(n, k)
        cq, sq = big_plan(q)
        cost = cq + k + 1
        seq = sq + [("push", k), ("multiply",)]
        if r:
            cr, sr = number_plan(r)
            cost += cr + 1
            seq = seq + sr + [("add",)]
        if best is None or cost < best[0]:
            best = (cost, seq)
    return best


def push_seq(n):
    if n > 20000:
        return big_plan(n)[1]
    if n > 600:   # 再帰が深くなりすぎないよう、小さい値から順にキャッシュを温める（結果は変わらない）
        for i in range(300, n, 300):
            number_plan(i)
    if n >= 1:
        return number_plan(n)[1]
    if n == 0:
        return [("push", 1), ("not",)]
    # 負数: 1 - (|n|+1)
    return [("push", 1)] + number_plan(-n + 1)[1] + [("subtract",)]


# ------------------------------------------------------------------ 構文解析
def unescape(s):
    return bytes(s, "utf-8").decode("unicode_escape").encode("latin-1").decode("utf-8")


def parse(src):
    """ソースを [(op, arg, lineno)] に"""
    out = []
    for no, line in enumerate(src.split("\n"), 1):
        m = re.match(r'\s*(prints)\s+"((?:[^"\\]|\\.)*)"', line)
        if m:
            out.append(("prints", unescape(m.group(2)), no))
            continue
        line = line.split(";")[0].strip()
        while line:
            m = re.match(r"([A-Za-z_][\w.]*):\s*(.*)", line)
            if m:
                out.append(("label", m.group(1), no))
                line = m.group(2).strip()
                continue
            parts = line.split()
            op = parts[0].lower()
            op = ALIASES.get(op, op)
            arg = parts[1] if len(parts) > 1 else None
            out.append((op, arg, no))
            break
    return out


def expand(items):
    """マクロを展開し、基本命令とジャンプ・ラベルだけの列にする"""
    res = []
    for op, arg, no in items:
        if op == "push":
            if arg is None:
                raise SyntaxError(f"{no}行目: push には数が必要です")
            v = int(arg, 0) if not (arg.startswith("'") and arg.endswith("'")) else ord(unescape(arg[1:-1]))
            res += push_seq(v)
        elif op == "prints":
            for ch in arg:
                res += push_seq(ord(ch)) + [("out_char",)]
        elif op == "swap":
            res += push_seq(2) + push_seq(1) + [("roll",)]
        elif op == "pick":
            d = int(arg)
            if d == 0:
                res.append(("duplicate",))
            else:
                res += push_seq(d + 1) + push_seq(d) + [("roll",), ("duplicate",)] + push_seq(d + 2) + push_seq(1) + [("roll",)]
        elif op == "bury":
            d = int(arg)
            if d > 0:
                res += push_seq(d + 1) + push_seq(1) + [("roll",)]
        elif op in ("label", "jmp", "jz", "jnz"):
            res.append((op, arg))
        elif op == "halt":
            res.append(("halt",))
        elif op in PRIMS:
            res.append((op,))
        else:
            raise SyntaxError(f"{no}行目: 不明な命令 {op}")
    return res


def basic_blocks(seq):
    """[(label, [cmds], terminator)] terminator = ('jmp',L) | ('br',kind,L,Lnext) | ('halt',)"""
    blocks = []
    cur_label = "__start"
    cur = []
    gen = [0]

    def fresh():
        gen[0] += 1
        return f"__L{gen[0]}"

    i = 0
    while i < len(seq):
        it = seq[i]
        op = it[0]
        if op == "label":
            if cur_label is not None:
                blocks.append((cur_label, cur, ("jmp", it[1])))
            cur_label, cur = it[1], []
        elif op == "jmp":
            if cur_label is not None:
                blocks.append((cur_label, cur, ("jmp", it[1])))
            cur_label, cur = None, []   # 到達不能（次のラベルまで捨てる）
        elif op in ("jz", "jnz"):
            nxt = fresh()
            if cur_label is not None:
                blocks.append((cur_label, cur, ("br", op, it[1], nxt)))
            cur_label, cur = nxt, []
        elif op == "halt":
            if cur_label is not None:
                blocks.append((cur_label, cur, ("halt",)))
            cur_label, cur = None, []
        else:
            if cur_label is not None:
                cur.append(it)
        i += 1
    if cur_label is not None:
        blocks.append((cur_label, cur, ("halt",)))
    return blocks


# ------------------------------------------------------------------ 行（1 列の色ブロック）の生成
def row_colors(cmds, start=START_COLOR):
    """命令列 → [(色, 幅)] 。push N の直前のブロックは幅 N"""
    blocks = []
    c = start
    for k, cmd in enumerate(cmds):
        width = cmd[1] if cmd[0] == "push" else 1
        blocks.append([c, width])
        c = next_color(c, cmd[0])
    blocks.append([c, 1])
    return blocks


def split_long(blocks_in, maxw):
    """長すぎる基本ブロックを複数行に分割"""
    out = []
    n = 0
    for label, cmds, term in blocks_in:
        while True:
            w = 0
            cut = None
            for k, cmd in enumerate(cmds):
                w += cmd[1] if cmd[0] == "push" else 1
                if w > maxw:
                    cut = k
                    break
            if cut is None or cut == 0:
                out.append((label, cmds, term))
                break
            n += 1
            nl = f"__W{n}"
            out.append((label, cmds[:cut], ("jmp", nl)))
            label, cmds = nl, cmds[cut:]
    return out


# ------------------------------------------------------------------ レイアウト
class Canvas:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.g = [[WHITE] * w for _ in range(h)]
        self.fixed = {}

    def put(self, x, y, c, why=""):
        if not (0 <= x < self.w and 0 <= y < self.h):
            raise ValueError(f"範囲外 ({x},{y}) {why}")
        old = self.fixed.get((x, y))
        if old is not None and old != c:
            raise ValueError(f"衝突 ({x},{y}): {old} と {c} ({why})")
        self.fixed[(x, y)] = c
        self.g[y][x] = c


def layout_linear(cmds):
    """ジャンプのない短いプログラム: 1 行 + 終端トラップ"""
    blocks = row_colors(cmds)
    xs = sum(w for _, w in blocks)
    W, H = xs + 2, 3
    cv = Canvas(W, H)
    x = 0
    for c, w in blocks:
        for i in range(w):
            cv.put(x + i, 0, c)
        x += w
    # 最後のブロック P の右に、下向き L 字のトラップ T を置く
    xP = x - 1
    _place_trap(cv, xP, 0, blocks[-1][0], down=True)
    return Program(cv.g)


def _place_trap(cv, xP, y, pcolor, down):
    """P=(xP,y) の右に 3 コーデルの終端ブロックを置き、周囲を黒で囲む"""
    t = next_color(pcolor, "push")   # 最後の遷移は無害な push
    s = 1 if down else -1
    for (x, yy) in [(xP, y + s), (xP + 1, y + s), (xP + 1, y)]:
        cv.put(x, yy, t, "trap")
    blacks = [(xP + 2, y), (xP + 2, y + s), (xP + 1, y - s), (xP, y + 2 * s), (xP + 1, y + 2 * s), (xP - 1, y + s)]
    for (x, yy) in blacks:
        if 0 <= x < cv.w and 0 <= yy < cv.h:
            cv.put(x, yy, BLACK, "trap")


def layout_general(blocks):
    labels = [b[0] for b in blocks]
    idx = {l: i for i, l in enumerate(labels)}
    n = len(blocks)
    # 行の命令列を確定（分岐は 正規化 → push 3 → mul → pointer）
    rows = []
    for label, cmds, term in blocks:
        cmds = list(cmds)
        if term[0] == "br":
            if term[1] == "jz":
                cmds.append(("not",))
            else:
                cmds += [("not",), ("not",)]
            cmds += [("push", 3), ("multiply",), ("pointer",)]
        if term[0] == "halt":
            cmds.append(("push", 1))   # トラップへの遷移用のダミー（実際の push は T への遷移）
            cmds = cmds[:-1]
        rows.append((label, cmds, term))

    for lab, _, term in rows:
        for t in ([term[1]] if term[0] == "jmp" else [term[2], term[3]] if term[0] == "br" else []):
            if t not in idx:
                raise SyntaxError(f"未定義のラベル: {t}")

    nl = n                         # 各行（=ラベル）に左右の縦レーンと下の水平チャネルを 1 本ずつ
    X0 = 2 * nl + 1                # コード開始列
    row_blocks = [row_colors(c) for _, c, _ in rows]
    code_w = max(sum(w for _, w in rb) for rb in row_blocks) + 3
    XR0 = X0 + code_w + 1          # 右レーン領域（偶数オフセットにレーン）
    W = XR0 + 2 * nl + 1
    Y = lambda i: 3 + 4 * i        # 行 i のコード行
    YB = Y(n) - 1                  # 下部チャネル開始
    H = YB + 2 * nl + 1
    cv = Canvas(W, H)
    xl = lambda i: 1 + 2 * i
    xr = lambda i: XR0 + 2 * i
    yb = lambda i: YB + 2 * i

    # 開始: (0,0) の色コーデルから右へ → 最初の行へジャンプ
    cv.put(0, 0, START_COLOR, "start")
    sources = [(0, 0)]   # (y, 行番号) 右向き配線
    targets_from = []
    targets_from.append((0, 0))  # 行 0 → ラベル 0

    for i, (label, cmds, term) in enumerate(rows):
        y = Y(i)
        rb = row_blocks[i]
        x = X0
        for c, w in rb:
            for k in range(w):
                cv.put(x + k, y, c, f"row {label}")
            x += w
        xe = x - 1   # 最後のブロック（幅 1）
        if term[0] == "jmp":
            targets_from.append((y, idx[term[1]]))
        elif term[0] == "br":
            targets_from.append((y, idx[term[3]]))        # 偽 → 右へ
            cv.put(xe, y - 2, BLACK, "br-up")               # 真 → 上に出て右へ曲がる
            targets_from.append((y - 1, idx[term[2]]))
        else:
            _place_trap(cv, xe, y, rb[-1][0], down=False)

    used = set(t for _, t in targets_from)
    for y, t in targets_from:
        cv.put(xr(t) + 1, y, BLACK, f"turn-down {t}")
    for t in used:
        cv.put(xr(t), yb(t) + 1, BLACK, f"turn-left {t}")
        cv.put(xl(t) - 1, yb(t), BLACK, f"turn-up {t}")
        cv.put(xl(t), Y(t) - 1, BLACK, f"turn-right {t}")
    return Program(cv.g)


def assemble(src, maxw=48):
    seq = expand(parse(src))
    if not any(op[0] in ("label", "jmp", "jz", "jnz") for op in seq):
        cmds = [c for c in seq if c[0] != "halt"]
        if "halt" in [c[0] for c in seq]:
            cmds = cmds[:[c[0] for c in seq].index("halt")]
        if sum(c[1] if c[0] == "push" else 1 for c in cmds) <= maxw * 3:
            return layout_linear(cmds)
    blocks = split_long(basic_blocks(seq), maxw)
    return layout_general(blocks)


def main(argv):
    import argparse
    ap = argparse.ArgumentParser(prog="pasm.py")
    ap.add_argument("src")
    ap.add_argument("-o", "--out")
    ap.add_argument("-cs", type=int, default=1)
    ap.add_argument("--maxw", type=int, default=48)
    ap.add_argument("--text", action="store_true", help="テキスト表現を表示")
    a = ap.parse_args(argv)
    prog = assemble(open(a.src, encoding="utf-8").read(), a.maxw)
    if a.text:
        print(prog.to_text())
    if a.out:
        prog.save_png(a.out, a.cs)
        print(f"{a.out}: {prog.w}x{prog.h} codels", file=sys.stderr)


if __name__ == "__main__":
    main(sys.argv[1:])
