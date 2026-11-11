#!/usr/bin/env python3
"""minic.py -- 小さな言語 Mini から pasm（本書の Piet アセンブリ）へのコンパイラ

  python3 minic.py prog.mini            # pasm を標準出力へ
  python3 minic.py prog.mini -o a.png   # そのまま Piet 画像まで作る

Mini の文法
  文:   x = 式;   print 式;   putc 式;   prints "文字列";   read x;   getc x;
        if (式) { ... } else { ... }      while (式) { ... }      { ... }
  式:   整数  'a'（文字）  変数  ( 式 )
        単項 - not !     * / %     + -     < > <= >= == !=     and &&     or ||
  コメント: // から行末まで、または # から行末まで
  変数はすべて整数で、プログラム全体で共通（宣言不要、初期値 0）。
  read / getc は入力が尽きると -1 を代入する（read は 0 以上の整数の入力を前提とする）。

実装の考え方
  変数はスタックの底に固定の位置で並べる。式の計算中にスタックに積まれている
  一時的な値の数（深さ）をコンパイル時に追跡し、変数の読み出しは pick、
  書き込みは roll で行う。
"""
import re, sys, os

# ------------------------------------------------------------------ 字句解析
TOKEN_RE = re.compile(r"""
    (?P<ws>\s+|//[^\n]*|\#[^\n]*)
  | (?P<num>\d+)
  | (?P<chr>'(?:\\.|[^'\\])')
  | (?P<str>"(?:\\.|[^"\\])*")
  | (?P<id>[A-Za-z_]\w*)
  | (?P<op><=|>=|==|!=|&&|\|\||[-+*/%<>=!(){};])
""", re.VERBOSE)
KEYWORDS = {"print", "putc", "prints", "read", "getc", "if", "else", "while", "and", "or", "not"}
ESC = {"n": "\n", "t": "\t", "\\": "\\", "'": "'", '"': '"', "0": "\0"}


def unescape(s):
    return re.sub(r"\\(.)", lambda m: ESC.get(m.group(1), m.group(1)), s)


def tokenize(src):
    toks, pos, line = [], 0, 1
    while pos < len(src):
        m = TOKEN_RE.match(src, pos)
        if not m:
            raise SyntaxError(f"{line}行目: 読めない文字 {src[pos]!r}")
        kind = m.lastgroup
        text = m.group()
        if kind == "num":
            toks.append(("num", int(text), line))
        elif kind == "chr":
            toks.append(("num", ord(unescape(text[1:-1])), line))
        elif kind == "str":
            toks.append(("str", unescape(text[1:-1]), line))
        elif kind == "id":
            toks.append(("kw" if text in KEYWORDS else "id", text, line))
        elif kind == "op":
            toks.append(("op", text, line))
        line += text.count("\n")
        pos = m.end()
    toks.append(("eof", None, line))
    return toks


# ------------------------------------------------------------------ 構文解析（再帰下降）
class Parser:
    def __init__(self, toks):
        self.toks, self.i = toks, 0

    def peek(self):
        return self.toks[self.i]

    def take(self, value=None):
        t = self.toks[self.i]
        if value is not None and t[1] != value:
            raise SyntaxError(f"{t[2]}行目: {value!r} が必要ですが {t[1]!r} がありました")
        self.i += 1
        return t

    def at(self, value):
        return self.peek()[1] == value

    def program(self):
        body = []
        while self.peek()[0] != "eof":
            body.append(self.stmt())
        return ("block", body)

    def stmt(self):
        kind, val, line = self.peek()
        if val == "{":
            self.take("{")
            body = []
            while not self.at("}"):
                body.append(self.stmt())
            self.take("}")
            return ("block", body)
        if val == "if":
            self.take(); self.take("(")
            cond = self.expr()
            self.take(")")
            then = self.stmt()
            other = None
            if self.at("else"):
                self.take()
                other = self.stmt()
            return ("if", cond, then, other)
        if val == "while":
            self.take(); self.take("(")
            cond = self.expr()
            self.take(")")
            return ("while", cond, self.stmt())
        if val in ("print", "putc"):
            self.take()
            e = self.expr()
            self.take(";")
            return (val, e)
        if val == "prints":
            self.take()
            s = self.take()
            if s[0] != "str":
                raise SyntaxError(f"{line}行目: prints には文字列が必要です")
            self.take(";")
            return ("prints", s[1])
        if val in ("read", "getc"):
            self.take()
            name = self.take()
            if name[0] != "id":
                raise SyntaxError(f"{line}行目: 変数名が必要です")
            self.take(";")
            return (val, name[1])
        if kind == "id":
            self.take()
            self.take("=")
            e = self.expr()
            self.take(";")
            return ("assign", val, e)
        raise SyntaxError(f"{line}行目: 文として読めません: {val!r}")

    # 優先順位の低い順に
    def expr(self):
        return self.or_()

    def or_(self):
        e = self.and_()
        while self.at("or") or self.at("||"):
            self.take()
            e = ("or", e, self.and_())
        return e

    def and_(self):
        e = self.not_()
        while self.at("and") or self.at("&&"):
            self.take()
            e = ("and", e, self.not_())
        return e

    def not_(self):
        if self.at("not") or self.at("!"):
            self.take()
            return ("not", self.not_())
        return self.cmp()

    def cmp(self):
        e = self.add()
        if self.peek()[1] in ("<", ">", "<=", ">=", "==", "!="):
            op = self.take()[1]
            e = (op, e, self.add())
        return e

    def add(self):
        e = self.mul()
        while self.peek()[1] in ("+", "-"):
            op = self.take()[1]
            e = (op, e, self.mul())
        return e

    def mul(self):
        e = self.unary()
        while self.peek()[1] in ("*", "/", "%"):
            op = self.take()[1]
            e = (op, e, self.unary())
        return e

    def unary(self):
        if self.at("-"):
            self.take()
            e = self.unary()
            if e[0] == "num":
                return ("num", -e[1])
            return ("-", ("num", 0), e)
        return self.primary()

    def primary(self):
        kind, val, line = self.take()
        if kind == "num":
            return ("num", val)
        if kind == "id":
            return ("var", val)
        if val == "(":
            e = self.expr()
            self.take(")")
            return e
        raise SyntaxError(f"{line}行目: 式として読めません: {val!r}")


# ------------------------------------------------------------------ 定数畳み込み
def fold(e):
    if e[0] in ("num", "var"):
        return e
    if e[0] == "not":
        a = fold(e[1])
        return ("num", int(a[1] == 0)) if a[0] == "num" else ("not", a)
    op, a, b = e[0], fold(e[1]), fold(e[2])
    if a[0] == "num" and b[0] == "num":
        x, y = a[1], b[1]
        f = {"+": lambda: x + y, "-": lambda: x - y, "*": lambda: x * y,
             "/": lambda: x // y if y else None, "%": lambda: x % y if y else None,
             "<": lambda: int(x < y), ">": lambda: int(x > y), "<=": lambda: int(x <= y),
             ">=": lambda: int(x >= y), "==": lambda: int(x == y), "!=": lambda: int(x != y),
             "and": lambda: int(bool(x) and bool(y)), "or": lambda: int(bool(x) or bool(y))}[op]()
        if f is not None:
            return ("num", f)
    return (op, a, b)


# ------------------------------------------------------------------ コード生成
class CodeGen:
    def __init__(self):
        self.vars = []      # スタックの底から順に並ぶ変数
        self.temps = 0      # 変数の上に積まれている一時値の数
        self.out = []
        self.nlabel = 0

    def label(self, hint):
        self.nlabel += 1
        return f"{hint}{self.nlabel}"

    def emit(self, line, delta=0):
        self.out.append("  " + line)
        self.temps += delta

    def depth(self, name):
        """変数 name の、現在のスタック先頭からの深さ（0 = 先頭）"""
        i = self.vars.index(name)
        return (len(self.vars) - 1 - i) + self.temps

    # --- 変数の収集
    def collect(self, node):
        if not isinstance(node, tuple):
            return
        if node[0] in ("assign", "read", "getc"):
            if node[1] not in self.vars:
                self.vars.append(node[1])
        if node[0] == "var" and node[1] not in self.vars:
            self.vars.append(node[1])
        for ch in node[1:]:
            if isinstance(ch, tuple):
                self.collect(ch)
            elif isinstance(ch, list):
                for c in ch:
                    self.collect(c)

    # --- 式（結果を 1 つスタックに積む）
    def expr(self, e):
        k = e[0]
        if k == "num":
            self.emit(f"push {e[1]}", +1)
        elif k == "var":
            self.emit(f"pick {self.depth(e[1])}     ; {e[1]}", +1)
        elif k == "not":
            self.expr(e[1])
            self.emit("not")
        elif k in ("+", "-", "*", "/", "%"):
            self.expr(e[1]); self.expr(e[2])
            self.emit({"+": "add", "-": "sub", "*": "mul", "/": "div", "%": "mod"}[k], -1)
        elif k == ">":
            self.expr(e[1]); self.expr(e[2]); self.emit("gt", -1)
        elif k == "<":                       # a < b  ⇔  b > a
            self.expr(e[2]); self.expr(e[1]); self.emit("gt", -1)
        elif k == "<=":                      # a <= b ⇔ not (a > b)
            self.expr(e[1]); self.expr(e[2]); self.emit("gt", -1); self.emit("not")
        elif k == ">=":                      # a >= b ⇔ not (b > a)
            self.expr(e[2]); self.expr(e[1]); self.emit("gt", -1); self.emit("not")
        elif k == "==":
            self.expr(e[1]); self.expr(e[2]); self.emit("sub", -1); self.emit("not")
        elif k == "!=":
            self.expr(e[1]); self.expr(e[2]); self.emit("sub", -1); self.emit("not"); self.emit("not")
        elif k == "and":                     # 両方を 0/1 にしてから掛ける
            self.bool(e[1]); self.bool(e[2]); self.emit("mul", -1)
        elif k == "or":                      # 0/1 にして足し、もう一度 0/1 に
            self.bool(e[1]); self.bool(e[2]); self.emit("add", -1); self.emit("not"); self.emit("not")
        else:
            raise ValueError(e)

    def bool(self, e):
        """式を計算し、結果を 0 か 1 にする"""
        self.expr(e)
        if e[0] not in ("not", "<", ">", "<=", ">=", "==", "!=", "and", "or"):
            self.emit("not"); self.emit("not")

    def store(self, name):
        """スタック先頭の値を変数 name に書き込み、先頭から取り除く"""
        d = self.depth(name)          # 先頭の値を含めた深さ
        if d == 1:
            self.emit("swap")
            self.emit("pop", -1)
        else:
            self.emit(f"bury {d}")      # 新しい値を変数の位置へ。古い値は深さ d-1 に上がる
            self.emit(f"push {d}")
            self.emit(f"push {d - 1}")
            self.emit("roll")           # 古い値を先頭へ
            self.emit("pop", -1)        # 捨てる
        self.out[-1] += f"     ; → {name}"

    # --- 文
    def stmt(self, s):
        k = s[0]
        if k == "block":
            for c in s[1]:
                self.stmt(c)
        elif k == "assign":
            self.out.append(f"; {s[1]} = ...")
            self.expr(fold(s[2]))
            self.store(s[1])
        elif k == "print":
            self.expr(fold(s[1])); self.emit("outn", -1)
        elif k == "putc":
            self.expr(fold(s[1])); self.emit("outc", -1)
        elif k == "prints":
            esc = s[1].replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\t", "\\t")
            self.emit(f'prints "{esc}"')
        elif k in ("read", "getc"):
            # 番兵 -1 を積んでから読む。読めなければ -1 だけが残る
            done = self.label("in_done")
            self.out.append(f"; {k} {s[1]}")
            self.emit("push -1", +1)
            self.emit("inn" if k == "read" else "inc")
            self.emit("dup")
            self.emit("push -1")
            self.emit("gt")             # 読めた値 > -1 なら 1
            self.emit(f"jz {done}")
            self.emit("swap")
            self.emit("pop")            # 番兵を取り除く
            self.out.append(f"{done}:")
            self.store(s[1])
        elif k == "if":
            cond, then, other = fold(s[1]), s[2], s[3]
            l_else, l_end = self.label("else"), self.label("endif")
            self.out.append("; if")
            self.expr(cond)
            self.emit(f"jz {l_else if other else l_end}", -1)
            self.stmt(then)
            if other:
                self.emit(f"jmp {l_end}")
                self.out.append(f"{l_else}:")
                self.stmt(other)
            self.out.append(f"{l_end}:")
        elif k == "while":
            l_top, l_end = self.label("while"), self.label("wend")
            self.out.append(f"{l_top}:")
            self.expr(fold(s[1]))
            self.emit(f"jz {l_end}", -1)
            self.stmt(s[2])
            self.emit(f"jmp {l_top}")
            self.out.append(f"{l_end}:")
        else:
            raise ValueError(s)
        assert self.temps == 0, s


def compile_src(src):
    tree = Parser(tokenize(src)).program()
    g = CodeGen()
    g.collect(tree)
    g.out.append("; 変数: " + (", ".join(g.vars) if g.vars else "なし"))
    for v in g.vars:
        g.out.append(f"  push 0     ; {v}")
    g.stmt(tree)
    g.out.append("  halt")
    return "\n".join(g.out) + "\n"


def main(argv):
    import argparse
    ap = argparse.ArgumentParser(prog="minic.py")
    ap.add_argument("src")
    ap.add_argument("-o", "--out", help="Piet 画像の出力先")
    ap.add_argument("-cs", type=int, default=1)
    a = ap.parse_args(argv)
    code = compile_src(open(a.src, encoding="utf-8").read())
    if a.out:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import pasm
        prog = pasm.assemble(code)
        prog.save_png(a.out, a.cs)
        print(f"{a.out}: {prog.w}x{prog.h} codels", file=sys.stderr)
    else:
        sys.stdout.write(code)


if __name__ == "__main__":
    main(sys.argv[1:])
