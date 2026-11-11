#!/usr/bin/env python3
"""piet.py -- 本書付属の Piet ツールキット（インタプリタ・画像入出力）

  python3 piet.py run  prog.png [-cs N] [-t] [-e STEPS]
  python3 piet.py show prog.png              # テキスト表現で表示
  python3 piet.py png  prog.txt out.png [-cs N]

仕様: https://www.dangermouse.net/esoteric/piet.html
"""
import sys, math

# ---------------------------------------------------------------- 色
HUES = ["red", "yellow", "green", "cyan", "blue", "magenta"]
LIGHTS = ["light", "normal", "dark"]
RGB = {
    (0, 0): 0xFFC0C0, (1, 0): 0xFFFFC0, (2, 0): 0xC0FFC0, (3, 0): 0xC0FFFF, (4, 0): 0xC0C0FF, (5, 0): 0xFFC0FF,
    (0, 1): 0xFF0000, (1, 1): 0xFFFF00, (2, 1): 0x00FF00, (3, 1): 0x00FFFF, (4, 1): 0x0000FF, (5, 1): 0xFF00FF,
    (0, 2): 0xC00000, (1, 2): 0xC0C000, (2, 2): 0x00C000, (3, 2): 0x00C0C0, (4, 2): 0x0000C0, (5, 2): 0xC000C0,
}
WHITE, BLACK = "W", "K"
# 色 = (hue, light) のタプル、または "W" / "K"
RGB2COL = {v: k for k, v in RGB.items()}
RGB2COL[0xFFFFFF] = WHITE
RGB2COL[0x000000] = BLACK

# テキスト表現: 1 コーデル = 1 文字
#   淡 (light) : r y g c b m      通常 (normal): R Y G C B M
#   濃 (dark)  : 1 2 3 4 5 6      白: .   黒: #
CHARS = {}
for h, ch in enumerate("rygcbm"):
    CHARS[ch] = (h, 0)
for h, ch in enumerate("RYGCBM"):
    CHARS[ch] = (h, 1)
for h, ch in enumerate("123456"):
    CHARS[ch] = (h, 2)
CHARS["."] = WHITE
CHARS["#"] = BLACK
COL2CHAR = {v: k for k, v in CHARS.items()}

JNAMES = {"red": "赤", "yellow": "黄", "green": "緑", "cyan": "シアン", "blue": "青", "magenta": "マゼンタ"}
LNAMES = {"light": "淡", "normal": "", "dark": "濃"}


def color_name(c, ja=False):
    if c == WHITE:
        return "白" if ja else "white"
    if c == BLACK:
        return "黒" if ja else "black"
    h, l = c
    if ja:
        return LNAMES[LIGHTS[l]] + JNAMES[HUES[h]]
    return ("" if l == 1 else LIGHTS[l] + " ") + HUES[h]


# ---------------------------------------------------------------- 命令
# CMDS[hue_change][light_change]
CMDS = [
    [None, "push", "pop"],
    ["add", "subtract", "multiply"],
    ["divide", "mod", "not"],
    ["greater", "pointer", "switch"],
    ["duplicate", "roll", "in_number"],
    ["in_char", "out_number", "out_char"],
]
CMD_DELTA = {}
for dh, row in enumerate(CMDS):
    for dl, name in enumerate(row):
        if name:
            CMD_DELTA[name] = (dh, dl)
# よく使う別名
ALIASES = {"sub": "subtract", "mul": "multiply", "div": "divide", "dup": "duplicate",
           "gt": "greater", "inn": "in_number", "inc": "in_char", "outn": "out_number",
           "outc": "out_char", "dp": "pointer", "cc": "switch"}


def command_between(a, b):
    """色 a のブロックから色 b のブロックへ移ったときの命令名"""
    dh = (b[0] - a[0]) % 6
    dl = (b[1] - a[1]) % 3
    return CMDS[dh][dl]


def next_color(c, cmd):
    """色 c から命令 cmd を実行するための次の色"""
    cmd = ALIASES.get(cmd, cmd)
    dh, dl = CMD_DELTA[cmd]
    return ((c[0] + dh) % 6, (c[1] + dl) % 3)


# ---------------------------------------------------------------- プログラム（コーデル格子）
class Program:
    def __init__(self, grid):
        self.grid = grid            # grid[y][x] -> 色
        self.h = len(grid)
        self.w = len(grid[0]) if grid else 0
        self._blocks = {}

    # --- 入出力
    @staticmethod
    def from_text(text):
        rows = [ln.rstrip("\n") for ln in text.strip("\n").split("\n")]
        rows = [r.split(";")[0].rstrip() for r in rows]   # ; 以降はコメント
        rows = [r.replace(" ", "") for r in rows if r.strip()]
        w = max(len(r) for r in rows)
        grid = [[CHARS[ch] for ch in r.ljust(w, ".")] for r in rows]
        return Program(grid)

    def to_text(self):
        return "\n".join("".join(COL2CHAR[c] for c in row) for row in self.grid)

    @staticmethod
    def from_image(path, codel_size=None, unknown="white"):
        from PIL import Image
        im = Image.open(path).convert("RGB")
        W, H = im.size
        px = im.load()
        if codel_size is None:
            codel_size = guess_codel_size(im)
        w, h = W // codel_size, H // codel_size
        grid = []
        for y in range(h):
            row = []
            for x in range(w):
                r, g, b = px[x * codel_size, y * codel_size]
                v = (r << 16) | (g << 8) | b
                c = RGB2COL.get(v)
                if c is None:
                    c = WHITE if unknown == "white" else BLACK
                row.append(c)
            grid.append(row)
        return Program(grid)

    def save_png(self, path, codel_size=1, grid_color=None):
        from PIL import Image
        cs = codel_size
        im = Image.new("RGB", (self.w * cs, self.h * cs))
        px = im.load()
        for y in range(self.h):
            for x in range(self.w):
                c = self.grid[y][x]
                v = 0xFFFFFF if c == WHITE else 0 if c == BLACK else RGB[c]
                rgb = (v >> 16, (v >> 8) & 255, v & 255)
                for dy in range(cs):
                    for dx in range(cs):
                        px[x * cs + dx, y * cs + dy] = rgb
        im.save(path)

    def save_ppm(self, path):
        with open(path, "w") as f:
            f.write(f"P3\n{self.w} {self.h}\n255\n")
            for row in self.grid:
                vals = []
                for c in row:
                    v = 0xFFFFFF if c == WHITE else 0 if c == BLACK else RGB[c]
                    vals.append(f"{v >> 16} {(v >> 8) & 255} {v & 255}")
                f.write(" ".join(vals) + "\n")

    # --- 色ブロック
    def color(self, x, y):
        if 0 <= x < self.w and 0 <= y < self.h:
            return self.grid[y][x]
        return None   # 画像の外

    def block(self, x, y):
        """(x, y) を含む色ブロックのコーデル集合（4 近傍の連結成分）"""
        key = (x, y)
        if key in self._blocks:
            return self._blocks[key]
        c = self.grid[y][x]
        seen = {key}
        todo = [key]
        while todo:
            cx, cy = todo.pop()
            for nx, ny in ((cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)):
                if (nx, ny) not in seen and self.color(nx, ny) == c:
                    seen.add((nx, ny))
                    todo.append((nx, ny))
        fs = frozenset(seen)
        for p in fs:
            self._blocks[p] = fs
        return fs


def guess_codel_size(im):
    """同じ色が続く長さの最大公約数をコーデルサイズと推定する（npiet と同じ考え方）"""
    W, H = im.size
    px = im.load()
    g = 0
    for y in range(H):
        run = 1
        for x in range(1, W + 1):
            if x < W and px[x, y] == px[x - 1, y]:
                run += 1
            else:
                g = math.gcd(g, run)
                run = 1
                if g == 1:
                    return 1
    for x in range(W):
        run = 1
        for y in range(1, H + 1):
            if y < H and px[x, y] == px[x, y - 1]:
                run += 1
            else:
                g = math.gcd(g, run)
                run = 1
                if g == 1:
                    return 1
    return g or 1


# ---------------------------------------------------------------- インタプリタ
DP_VEC = [(1, 0), (0, 1), (-1, 0), (0, -1)]   # 右, 下, 左, 上 (時計回り)
DP_NAMES = ["右", "下", "左", "上"]
DP_SYM = [">", "v", "<", "^"]
CC_NAMES = ["左", "右"]


def fmt_stack(st):
    """本書の表記 [3 5 7]（右端が先頭）"""
    return "[" + " ".join(str(v) for v in st) + "]"


def exit_codel(block, dp, cc):
    """DP 方向に最も遠い辺の上で、CC 方向に最も遠いコーデル"""
    if dp == 0:   # 右
        m = max(x for x, y in block)
        edge = [(x, y) for x, y in block if x == m]
        return min(edge, key=lambda p: p[1]) if cc == 0 else max(edge, key=lambda p: p[1])
    if dp == 1:   # 下
        m = max(y for x, y in block)
        edge = [(x, y) for x, y in block if y == m]
        return max(edge, key=lambda p: p[0]) if cc == 0 else min(edge, key=lambda p: p[0])
    if dp == 2:   # 左
        m = min(x for x, y in block)
        edge = [(x, y) for x, y in block if x == m]
        return max(edge, key=lambda p: p[1]) if cc == 0 else min(edge, key=lambda p: p[1])
    m = min(y for x, y in block)  # 上
    edge = [(x, y) for x, y in block if y == m]
    return min(edge, key=lambda p: p[0]) if cc == 0 else max(edge, key=lambda p: p[0])


class Machine:
    """仕様準拠の Piet インタプリタ。

    div   : 床関数による整数除算（Python の //）
    mod   : 除数と同じ符号（仕様どおり）
    実行不能な命令（スタック不足・0 除算・負の深さの roll）は無視し、スタックは変更しない
    """

    def __init__(self, prog, inp="", trace=False, out=None):
        self.p = prog
        self.x = self.y = 0
        self.dp = 0
        self.cc = 0
        self.stack = []
        self.inp = inp
        self.ipos = 0
        self.out = [] if out is None else out
        self.trace = trace
        self.steps = 0
        self.halted = False
        self.log = []    # トレース行

    # --- 入力
    def read_char(self):
        if self.ipos < len(self.inp):
            ch = self.inp[self.ipos]
            self.ipos += 1
            return ord(ch)
        return None

    def read_number(self):
        s = self.inp
        i = self.ipos
        while i < len(s) and s[i].isspace():
            i += 1
        j = i
        if j < len(s) and s[j] in "+-":
            j += 1
        k = j
        while k < len(s) and s[k].isdigit():
            k += 1
        if k == j:
            return None
        self.ipos = k
        return int(s[i:k])

    # --- 命令実行
    def execute(self, cmd, size):
        st = self.stack
        if cmd == "push":
            st.append(size)
        elif cmd == "pop":
            if not st:
                return "ignored"
            st.pop()
        elif cmd in ("add", "subtract", "multiply", "divide", "mod", "greater"):
            if len(st) < 2:
                return "ignored"
            a, b = st[-2], st[-1]
            if cmd in ("divide", "mod") and b == 0:
                return "ignored"
            st.pop(); st.pop()
            st.append({"add": lambda: a + b, "subtract": lambda: a - b, "multiply": lambda: a * b,
                       "divide": lambda: a // b, "mod": lambda: a % b,
                       "greater": lambda: 1 if a > b else 0}[cmd]())
        elif cmd == "not":
            if not st:
                return "ignored"
            st[-1] = 1 if st[-1] == 0 else 0
        elif cmd == "pointer":
            if not st:
                return "ignored"
            self.dp = (self.dp + st.pop()) % 4
        elif cmd == "switch":
            if not st:
                return "ignored"
            self.cc = (self.cc + abs(st.pop())) % 2
        elif cmd == "duplicate":
            if not st:
                return "ignored"
            st.append(st[-1])
        elif cmd == "roll":
            if len(st) < 2:
                return "ignored"
            depth, n = st[-2], st[-1]
            if depth < 0 or depth > len(st) - 2:
                return "ignored"
            st.pop(); st.pop()
            if depth > 0:
                n %= depth
                if n:
                    seg = st[-depth:]
                    st[-depth:] = seg[-n:] + seg[:-n]
        elif cmd == "in_number":
            v = self.read_number()
            if v is None:
                return "ignored"
            st.append(v)
        elif cmd == "in_char":
            v = self.read_char()
            if v is None:
                return "ignored"
            st.append(v)
        elif cmd == "out_number":
            if not st:
                return "ignored"
            self.out.append(str(st.pop()))
        elif cmd == "out_char":
            if not st:
                return "ignored"
            try:
                ch = chr(st[-1])
            except (ValueError, OverflowError):
                return "ignored"     # 文字にできない値はスタックに残したまま無視する
            st.pop()
            self.out.append(ch)
        return None

    # --- 1 ステップ
    def step(self):
        """1 回の遷移（ブロック → ブロック）を行う。停止したら False"""
        if self.halted:
            return False
        p = self.p
        cur = p.color(self.x, self.y)
        if cur == WHITE:
            return self._slide(self.x, self.y, None)
        block = p.block(self.x, self.y)
        for attempt in range(8):
            ex, ey = exit_codel(block, self.dp, self.cc)
            dx, dy = DP_VEC[self.dp]
            nx, ny = ex + dx, ey + dy
            nc = p.color(nx, ny)
            if nc is not None and nc != BLACK:
                if nc == WHITE:
                    return self._slide(nx, ny, cur)
                cmd = command_between(cur, nc)
                before = list(self.stack)
                dp0, cc0 = self.dp, self.cc
                res = self.execute(cmd, len(block))
                self.steps += 1
                if self.trace:
                    self._trace(cmd, cur, nc, len(block), before, res, dp0, cc0, (nx, ny))
                self.x, self.y = nx, ny
                return True
            if attempt % 2 == 0:
                self.cc ^= 1
                what = f"CC を{CC_NAMES[self.cc]}に切り替え"
            else:
                self.dp = (self.dp + 1) % 4
                what = f"DP を{DP_NAMES[self.dp]}に回転"
            if self.trace:
                why = "画像の外" if nc is None else "黒"
                self.log.append(f"  進めない: ({ex},{ey}) の{DP_NAMES[(self.dp - (attempt % 2)) % 4]}は{why} → {what}")
        self.halted = True
        if self.trace:
            self.log.append(f"halt: ({self.x},{self.y}) から出られない（8 回失敗）")
        return False

    def _slide(self, x, y, frm):
        """白い領域を DP 方向に滑る（2008 年の仕様明確化に従う）"""
        p = self.p
        seen = set()
        while True:
            dx, dy = DP_VEC[self.dp]
            while p.color(x + dx, y + dy) == WHITE:
                x, y = x + dx, y + dy
            nc = p.color(x + dx, y + dy)
            if nc is not None and nc != BLACK:
                self.x, self.y = x + dx, y + dy
                self.steps += 1
                if self.trace:
                    self.log.append(f"step {self.steps}: 白を滑って ({self.x},{self.y}) {color_name(nc, True)} へ（命令なし）"
                                    f"  DP={DP_NAMES[self.dp]} CC={CC_NAMES[self.cc]}")
                return True
            state = (x, y, self.dp, self.cc)
            if state in seen:
                self.halted = True
                if self.trace:
                    self.log.append(f"halt: 白ブロック内で同じ経路をたどり始めた ({x},{y})")
                return False
            seen.add(state)
            self.cc ^= 1
            self.dp = (self.dp + 1) % 4
            if self.trace:
                self.log.append(f"  白の中で進めない: ({x},{y}) → CC を{CC_NAMES[self.cc]}に、DP を{DP_NAMES[self.dp]}に")

    def _trace(self, cmd, cur, nc, size, before, res, dp0, cc0, pos):
        s = f"step {self.steps}: {color_name(cur, True)}({size}) → {color_name(nc, True)}  {cmd}"
        if cmd == "push":
            s = f"step {self.steps}: {color_name(cur, True)}({size}) → {color_name(nc, True)}  push {size}"
        if res:
            s += "  （無視）"
        s += f"  stack={fmt_stack(self.stack)}"
        if (dp0, cc0) != (self.dp, self.cc):
            s += f"  DP={DP_NAMES[self.dp]} CC={CC_NAMES[self.cc]}"
        self.log.append(s)

    def run(self, max_steps=1_000_000):
        while self.steps < max_steps and self.step():
            pass
        return "".join(self.out)


def run_program(prog, inp="", max_steps=1_000_000, trace=False):
    m = Machine(prog, inp, trace=trace)
    out = m.run(max_steps)
    return out, m


# ---------------------------------------------------------------- CLI
def main(argv):
    import argparse
    ap = argparse.ArgumentParser(prog="piet.py")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("file")
    r.add_argument("-cs", type=int)
    r.add_argument("-t", action="store_true", help="トレース表示")
    r.add_argument("-e", type=int, default=1_000_000, help="最大ステップ数")
    s = sub.add_parser("show")
    s.add_argument("file")
    s.add_argument("-cs", type=int)
    g = sub.add_parser("png")
    g.add_argument("txt")
    g.add_argument("out")
    g.add_argument("-cs", type=int, default=1)
    a = ap.parse_args(argv)
    if a.cmd == "run":
        prog = Program.from_text(open(a.file).read()) if a.file.endswith(".txt") else Program.from_image(a.file, a.cs)
        inp = "" if sys.stdin.isatty() else sys.stdin.read()
        m = Machine(prog, inp, trace=a.t)
        if a.t:
            while m.steps < a.e and m.step():
                pass
            print("\n".join(m.log), file=sys.stderr)
            sys.stdout.write("".join(m.out))
        else:
            sys.stdout.write(m.run(a.e))
    elif a.cmd == "show":
        print(Program.from_image(a.file, a.cs).to_text())
    elif a.cmd == "png":
        Program.from_text(open(a.txt).read()).save_png(a.out, a.cs)


if __name__ == "__main__":
    main(sys.argv[1:])
