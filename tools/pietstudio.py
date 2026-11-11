#!/usr/bin/env python3
"""pietstudio.py -- Piet スタジオ（本書付属の Piet エディタ兼デバッガ）

  python3 pietstudio.py [画像ファイル]

Python の標準ライブラリ（tkinter）だけで動きます。同じフォルダに piet.py を置いてください。
  - パレットで色を選び、格子をクリック／ドラッグして塗る
  - パレットの各色には「選んでいる色からその色へ移ったときの命令」が表示される
  - 実行・1 ステップ実行・再生、ブレークポイント（右クリック）、スタックとトレースの表示
  - PNG / GIF / PPM の読み書き（コーデルサイズ指定可）、本書のテキスト記法の読み書き
"""
import os, sys, math
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import piet
from piet import Program, Machine, RGB, WHITE, BLACK, command_between, color_name, DP_VEC, DP_NAMES, CC_NAMES, fmt_stack

APP = "Piet スタジオ"
COLORS = [(h, l) for l in range(3) for h in range(6)] + [WHITE, BLACK]
CMD_JA = {None: "（同じ色）"}


def hexcolor(c):
    if c == WHITE:
        return "#ffffff"
    if c == BLACK:
        return "#000000"
    return "#%06x" % RGB[c]


def text_on(c):
    if c == BLACK:
        return "#ffffff"
    if c == WHITE:
        return "#000000"
    h, l = c
    return "#ffffff" if l == 2 or (l == 1 and h in (0, 4, 5)) else "#000000"


# ---------------------------------------------------------------- 画像の入出力（PIL を使わない）
def load_image(root, path, codel_size=None):
    img = tk.PhotoImage(master=root, file=path)
    W, H = img.width(), img.height()
    rows = root.tk.splitlist(root.tk.call(img.name, "data"))
    px = []
    for r in rows:
        px.append([int(v[1:], 16) for v in root.tk.splitlist(r)])
    if codel_size is None:
        g = 0
        for y in range(H):
            run = 1
            for x in range(1, W + 1):
                if x < W and px[y][x] == px[y][x - 1]:
                    run += 1
                else:
                    g = math.gcd(g, run); run = 1
        for x in range(W):
            run = 1
            for y in range(1, H + 1):
                if y < H and px[y][x] == px[y - 1][x]:
                    run += 1
                else:
                    g = math.gcd(g, run); run = 1
        codel_size = g or 1
    cs = codel_size
    grid = []
    for y in range(H // cs):
        row = []
        for x in range(W // cs):
            row.append(piet.RGB2COL.get(px[y * cs][x * cs], WHITE))
        grid.append(row)
    return grid, cs


def save_image(root, grid, path, cs):
    h, w = len(grid), len(grid[0])
    img = tk.PhotoImage(master=root, width=w * cs, height=h * cs)
    for y in range(h):
        line = []
        for x in range(w):
            line += [hexcolor(grid[y][x])] * cs
        row = "{" + " ".join(line) + "}"
        img.put(" ".join([row] * cs), to=(0, y * cs))
    ext = os.path.splitext(path)[1].lower()
    fmt = {".gif": "gif", ".ppm": "ppm"}.get(ext, "png")
    img.write(path, format=fmt)


# ---------------------------------------------------------------- アプリ本体
class Studio:
    def __init__(self, root, path=None):
        self.root = root
        self.W, self.H = 16, 10
        self.grid = [[WHITE] * self.W for _ in range(self.H)]
        self.zoom = 32
        self.brush = (0, 1)      # 赤
        self.tool = tk.StringVar(value="paint")
        self.path = None
        self.codel_size = 10
        self.undo, self.redo = [], []
        self.breaks = set()      # ブレークポイント（コーデル座標。そのコーデルを含むブロックに入ったら止まる）
        self.machine = None
        self.prog = None
        self.running = None
        self.log_pos = 0
        self.dirty = False
        self._build_ui()
        if path:
            self.open_path(path)
        else:
            self.load_text("RRRRR1m#\n....#mm#\n.....##.")
            self.dirty = False
            self._title()

    # ------------------------------------------------------------ UI
    def _build_ui(self):
        r = self.root
        r.title(APP)
        r.geometry("1200x780")
        self._menus()
        main = ttk.PanedWindow(r, orient="horizontal")
        main.pack(fill="both", expand=True)

        # 左: キャンバス
        left = ttk.Frame(main)
        tb = ttk.Frame(left)
        tb.pack(fill="x", padx=6, pady=4)
        for val, lab in (("paint", "塗る"), ("fill", "塗りつぶし"), ("pick", "スポイト")):
            ttk.Radiobutton(tb, text=lab, value=val, variable=self.tool).pack(side="left", padx=2)
        ttk.Label(tb, text="  表示倍率").pack(side="left")
        self.zoom_var = tk.IntVar(value=self.zoom)
        ttk.Scale(tb, from_=4, to=48, variable=self.zoom_var, command=lambda e: self.set_zoom(int(float(e)))).pack(side="left")
        ttk.Label(tb, text="  右クリック: ブレークポイント").pack(side="left")
        cf = ttk.Frame(left)
        cf.pack(fill="both", expand=True)
        self.cv = tk.Canvas(cf, background="#e9ecf1", highlightthickness=0)
        xs = ttk.Scrollbar(cf, orient="horizontal", command=self.cv.xview)
        ys = ttk.Scrollbar(cf, orient="vertical", command=self.cv.yview)
        self.cv.configure(xscrollcommand=xs.set, yscrollcommand=ys.set)
        self.cv.grid(row=0, column=0, sticky="nsew")
        ys.grid(row=0, column=1, sticky="ns")
        xs.grid(row=1, column=0, sticky="ew")
        cf.rowconfigure(0, weight=1)
        cf.columnconfigure(0, weight=1)
        self.status = ttk.Label(left, text="", anchor="w")
        self.status.pack(fill="x", padx=6, pady=3)
        self.cv.bind("<Button-1>", self.on_press)
        self.cv.bind("<B1-Motion>", self.on_drag)
        self.cv.bind("<ButtonRelease-1>", lambda e: self._end_stroke())
        self.cv.bind("<Button-3>", self.on_break)
        self.cv.bind("<Motion>", self.on_motion)
        main.add(left, weight=3)

        # 右: パレットと実行
        right = ttk.Frame(main, padding=6)
        ttk.Label(right, text="パレット（各マスは選択中の色からの命令）").pack(anchor="w")
        self.cur_label = ttk.Label(right, text="")
        self.cur_label.pack(anchor="w", pady=(0, 3))
        pal = tk.Frame(right)
        pal.pack(fill="x")
        self.pal_buttons = {}
        for i, c in enumerate(COLORS):
            b = tk.Label(pal, text="", width=11, height=2, bg=hexcolor(c), fg=text_on(c),
                         relief="flat", bd=0, highlightthickness=3, highlightbackground="#ffffff",
                         font=("TkDefaultFont", 9, "bold"))
            if i < 18:
                b.grid(row=i // 6, column=i % 6, padx=1, pady=1, sticky="nsew")
            else:
                b.grid(row=3, column=(i - 18) * 3, columnspan=3, padx=1, pady=1, sticky="nsew")
            b.bind("<Button-1>", lambda e, c=c: self.set_brush(c))
            self.pal_buttons[c] = b
        for k in range(6):
            pal.columnconfigure(k, weight=1)

        runf = ttk.LabelFrame(right, text="実行", padding=6)
        runf.pack(fill="x", pady=(10, 4))
        bf = ttk.Frame(runf)
        bf.pack(fill="x")
        ttk.Button(bf, text="実行 (F5)", command=self.run).pack(side="left")
        self.play_btn = ttk.Button(bf, text="再生 (F6)", command=self.toggle_play)
        self.play_btn.pack(side="left", padx=3)
        ttk.Button(bf, text="1 ステップ (F10)", command=self.step).pack(side="left")
        ttk.Button(bf, text="リセット (F2)", command=self.reset).pack(side="left", padx=3)
        sf = ttk.Frame(runf)
        sf.pack(fill="x", pady=(4, 0))
        ttk.Label(sf, text="再生の速さ").pack(side="left")
        self.speed = tk.IntVar(value=5)
        ttk.Scale(sf, from_=1, to=10, variable=self.speed).pack(side="left", fill="x", expand=True)
        ttk.Label(runf, text="入力（標準入力として読まれます）").pack(anchor="w", pady=(6, 0))
        self.inp = tk.Text(runf, height=2, font=("TkFixedFont", 10))
        self.inp.pack(fill="x")
        self.inp.bind("<<Modified>>", self._inp_changed)
        ttk.Label(runf, text="出力").pack(anchor="w", pady=(6, 0))
        self.out = tk.Text(runf, height=4, font=("TkFixedFont", 10), state="disabled", background="#f2f4f7")
        self.out.pack(fill="x")
        self.state = ttk.Label(runf, text="", font=("TkFixedFont", 10), justify="left")
        self.state.pack(anchor="w", pady=(6, 0))

        lf = ttk.LabelFrame(right, text="トレース", padding=4)
        lf.pack(fill="both", expand=True, pady=(4, 0))
        self.trace = tk.Text(lf, height=10, font=("TkFixedFont", 9), state="disabled", wrap="none")
        tys = ttk.Scrollbar(lf, orient="vertical", command=self.trace.yview)
        self.trace.configure(yscrollcommand=tys.set)
        self.trace.pack(side="left", fill="both", expand=True)
        tys.pack(side="right", fill="y")
        main.add(right, weight=2)

        for key, fn in (("<F5>", self.run), ("<F6>", self.toggle_play), ("<F10>", self.step), ("<F2>", self.reset),
                        ("<Control-z>", self.do_undo), ("<Control-y>", self.do_redo), ("<Control-s>", self.save),
                        ("<Control-o>", self.open_dialog), ("<Control-n>", self.new_dialog)):
            r.bind(key, lambda e, fn=fn: fn())
        r.protocol("WM_DELETE_WINDOW", self.quit)

    def _menus(self):
        m = tk.Menu(self.root)
        f = tk.Menu(m, tearoff=False)
        f.add_command(label="新規…", accelerator="Ctrl+N", command=self.new_dialog)
        f.add_command(label="開く…", accelerator="Ctrl+O", command=self.open_dialog)
        f.add_command(label="保存", accelerator="Ctrl+S", command=self.save)
        f.add_command(label="名前を付けて保存…", command=self.save_as)
        f.add_separator()
        f.add_command(label="テキスト記法を開く…", command=self.open_text)
        f.add_command(label="テキスト記法で保存…", command=self.save_text)
        f.add_separator()
        f.add_command(label="終了", command=self.quit)
        m.add_cascade(label="ファイル", menu=f)
        e = tk.Menu(m, tearoff=False)
        e.add_command(label="元に戻す", accelerator="Ctrl+Z", command=self.do_undo)
        e.add_command(label="やり直し", accelerator="Ctrl+Y", command=self.do_redo)
        e.add_separator()
        e.add_command(label="サイズ変更…", command=self.resize_dialog)
        e.add_command(label="すべて白にする", command=self.clear_all)
        e.add_command(label="ブレークポイントをすべて解除", command=self.clear_breaks)
        m.add_cascade(label="編集", menu=e)
        r = tk.Menu(m, tearoff=False)
        r.add_command(label="実行", accelerator="F5", command=self.run)
        r.add_command(label="再生／一時停止", accelerator="F6", command=self.toggle_play)
        r.add_command(label="1 ステップ", accelerator="F10", command=self.step)
        r.add_command(label="リセット", accelerator="F2", command=self.reset)
        m.add_cascade(label="実行", menu=r)
        h = tk.Menu(m, tearoff=False)
        h.add_command(label="使い方", command=self.help)
        m.add_cascade(label="ヘルプ", menu=h)
        self.root.config(menu=m)

    # ------------------------------------------------------------ 描画
    def redraw(self):
        cv, z = self.cv, self.zoom
        cv.delete("all")
        self.rects = {}
        for y in range(self.H):
            for x in range(self.W):
                c = self.grid[y][x]
                self.rects[(x, y)] = cv.create_rectangle(x * z, y * z, (x + 1) * z, (y + 1) * z, fill=hexcolor(c),
                                                         outline="#c8ccd4" if z >= 8 else "")
        cv.configure(scrollregion=(0, 0, self.W * z, self.H * z))
        self.draw_marks()

    def draw_marks(self):
        cv, z = self.cv, self.zoom
        cv.delete("mark")
        for (x, y) in self.breaks:
            cv.create_oval(x * z + z * 0.3, y * z + z * 0.3, x * z + z * 0.7, y * z + z * 0.7, fill="#d00000", outline="#ffffff",
                           width=2, tags="mark")
        m = self.machine
        if not m or (m.steps == 0 and not m.halted):
            return
        c = self.prog.color(m.x, m.y)
        if c is not None and c != WHITE:
            blk = self.prog.block(m.x, m.y)
            for (x, y) in blk:
                for (dx, dy, x0, y0, x1, y1) in ((0, -1, x, y, x + 1, y), (0, 1, x, y + 1, x + 1, y + 1),
                                                 (-1, 0, x, y, x, y + 1), (1, 0, x + 1, y, x + 1, y + 1)):
                    if (x + dx, y + dy) not in blk:
                        cv.create_line(x0 * z, y0 * z, x1 * z, y1 * z, fill="#000000", width=max(3, z // 6), tags="mark")
                        cv.create_line(x0 * z, y0 * z, x1 * z, y1 * z, fill="#ffffff", width=max(1, z // 14), tags="mark")
        cx, cy, r = (m.x + 0.5) * z, (m.y + 0.5) * z, max(4, z * 0.32)
        dx, dy = DP_VEC[m.dp]
        pts = [cx + dx * r, cy + dy * r,
               cx - dx * r * 0.7 - dy * r * 0.75, cy - dy * r * 0.7 + dx * r * 0.75,
               cx - dx * r * 0.7 + dy * r * 0.75, cy - dy * r * 0.7 - dx * r * 0.75]
        cv.create_polygon(pts, fill="#000000", outline="#ffffff", width=2, tags="mark")

    def set_zoom(self, z):
        if z != self.zoom:
            self.zoom = z
            self.redraw()

    def update_palette(self):
        for c, b in self.pal_buttons.items():
            if isinstance(self.brush, tuple) and isinstance(c, tuple):
                cmd = command_between(self.brush, c)
                lab = CMD_JA.get(cmd, cmd).replace("_number", "(number)").replace("_char", "(char)")
            else:
                lab = color_name(c, True)
            b.configure(text=lab, highlightbackground="#16181d" if c == self.brush else "#ffffff")
        self.cur_label.configure(text=f"選択中: {color_name(self.brush, True)}  {hexcolor(self.brush).upper()}")

    # ------------------------------------------------------------ 編集
    def set_brush(self, c):
        self.brush = c
        if self.tool.get() == "pick":
            self.tool.set("paint")
        self.update_palette()

    def cell(self, ev):
        x = int(self.cv.canvasx(ev.x) // self.zoom)
        y = int(self.cv.canvasy(ev.y) // self.zoom)
        return (x, y) if 0 <= x < self.W and 0 <= y < self.H else None

    def snapshot(self):
        return (self.W, self.H, [row[:] for row in self.grid])

    def _begin_stroke(self):
        if not getattr(self, "_stroke", False):
            self.undo.append(self.snapshot())
            self.undo = self.undo[-200:]
            self.redo.clear()
            self._stroke = True

    def _end_stroke(self):
        if getattr(self, "_stroke", False):
            self._stroke = False
            self.changed()

    def on_press(self, ev):
        c = self.cell(ev)
        if not c:
            return
        x, y = c
        t = self.tool.get()
        if t == "pick":
            self.set_brush(self.grid[y][x])
            return
        if t == "fill":
            self._begin_stroke()
            self.flood(x, y, self.brush)
            self._end_stroke()
            self.redraw()
            return
        self._begin_stroke()
        self.paint(x, y)

    def on_drag(self, ev):
        if self.tool.get() == "paint":
            c = self.cell(ev)
            if c:
                self.paint(*c)

    def paint(self, x, y):
        if self.grid[y][x] != self.brush:
            self.grid[y][x] = self.brush
            self.cv.itemconfigure(self.rects[(x, y)], fill=hexcolor(self.brush))

    def flood(self, x, y, c):
        frm = self.grid[y][x]
        if frm == c:
            return
        st = [(x, y)]
        while st:
            a, b = st.pop()
            if 0 <= a < self.W and 0 <= b < self.H and self.grid[b][a] == frm:
                self.grid[b][a] = c
                st += [(a + 1, b), (a - 1, b), (a, b + 1), (a, b - 1)]

    def on_break(self, ev):
        c = self.cell(ev)
        if c:
            self.breaks ^= {c}
            self.draw_marks()

    def clear_breaks(self):
        self.breaks.clear()
        self.draw_marks()

    def on_motion(self, ev):
        c = self.cell(ev)
        if not c or not self.prog:
            return
        x, y = c
        col = self.grid[y][x]
        s = f"({x}, {y})  {color_name(col, True)}"
        if col not in (WHITE, BLACK):
            s += f"  ブロックの大きさ {len(self.prog.block(x, y))}"
            if isinstance(self.brush, tuple):
                cmd = command_between(col, self.brush) if col != self.brush else None
                if cmd:
                    s += f"  ／ この色 → 選択中の色: {cmd}"
        self.status.configure(text=s)

    def do_undo(self):
        if self.undo:
            self.redo.append(self.snapshot())
            self.W, self.H, self.grid = self.undo.pop()
            self.changed(); self.redraw()

    def do_redo(self):
        if self.redo:
            self.undo.append(self.snapshot())
            self.W, self.H, self.grid = self.redo.pop()
            self.changed(); self.redraw()

    def changed(self):
        self.prog = Program([row[:] for row in self.grid])
        self.dirty = True
        self._title()
        self.reset()

    def set_grid(self, grid):
        self.grid = grid
        self.H, self.W = len(grid), len(grid[0])
        self.breaks = {b for b in self.breaks if b[0] < self.W and b[1] < self.H}
        self.prog = Program([row[:] for row in self.grid])
        self.redraw()
        self.update_palette()
        self.reset()

    def resize(self, w, h):
        self.undo.append(self.snapshot())
        ng = [[self.grid[y][x] if y < self.H and x < self.W else WHITE for x in range(w)] for y in range(h)]
        self.set_grid(ng)
        self.changed()

    def clear_all(self):
        self.undo.append(self.snapshot())
        self.set_grid([[WHITE] * self.W for _ in range(self.H)])
        self.changed()

    # ------------------------------------------------------------ 実行
    def input_text(self):
        return self.inp.get("1.0", "end-1c")

    def _inp_changed(self, ev):
        if self.inp.edit_modified():
            self.inp.edit_modified(False)
            self.reset()

    def reset(self):
        self.stop()
        if self.prog is None:
            self.prog = Program([row[:] for row in self.grid])
        self.machine = Machine(self.prog, self.input_text(), trace=True)
        self.log_pos = 0
        self._set_text(self.trace, "")
        self.show()

    def _set_text(self, w, s, append=False):
        w.configure(state="normal")
        if not append:
            w.delete("1.0", "end")
        w.insert("end", s)
        w.configure(state="disabled")
        w.see("end")

    def show(self):
        m = self.machine
        self._set_text(self.out, "".join(m.out))
        new = m.log[self.log_pos:]
        if new:
            if len(m.log) > 4000:   # トレースは最新部分だけ保持
                del m.log[:-2000]
                self._set_text(self.trace, "\n".join(m.log[-2000:]) + "\n")
            else:
                self._set_text(self.trace, "\n".join(new) + "\n", append=True)
        self.log_pos = len(m.log)
        st = fmt_stack(m.stack)
        if len(st) > 120:
            st = "… " + st[-120:]
        state = f"ステップ {m.steps}   DP {DP_NAMES[m.dp]}   CC {CC_NAMES[m.cc]}   位置 ({m.x},{m.y})"
        if m.halted:
            state += "   ― 停止しました"
        self.state.configure(text=state + f"\nスタック {st}")
        self.draw_marks()

    def _hit_break(self, before):
        m = self.machine
        if not self.breaks or m.halted:
            return False
        c = self.prog.color(m.x, m.y)
        if c in (WHITE, BLACK, None):
            return False
        blk = self.prog.block(m.x, m.y)
        return blk is not before and any(b in blk for b in self.breaks)

    def step(self):
        self.stop()
        if self.machine.halted:
            self.reset()
        self.machine.step()
        self.show()

    def run(self):
        self.stop()
        if self.machine.halted:
            self.reset()
        self.running = "run"
        self._run_chunk(0)

    def _run_chunk(self, total):
        m = self.machine
        n = 0
        while n < 5000 and not m.halted:
            before = self.prog.block(m.x, m.y) if self.prog.color(m.x, m.y) not in (WHITE, BLACK, None) else None
            if not m.step():
                break
            n += 1
            if self._hit_break(before):
                self.running = None
                self.show()
                self.status.configure(text="ブレークポイントで止まりました")
                return
        total += n
        if len(m.log) > 4000:
            del m.log[:-1000]
            self.log_pos = 0
        if m.halted or total >= 3_000_000:
            self.running = None
            self.show()
            if not m.halted:
                self.status.configure(text="300 万ステップで止めました（無限ループの可能性）")
            return
        if self.running == "run":
            self.show()
            self.root.after(1, lambda: self._run_chunk(total))

    def toggle_play(self):
        if self.running == "play":
            self.stop()
            return
        self.stop()
        if self.machine.halted:
            self.reset()
        self.running = "play"
        self.play_btn.configure(text="一時停止 (F6)")
        self._tick()

    def _tick(self):
        if self.running != "play":
            return
        m = self.machine
        before = self.prog.block(m.x, m.y) if self.prog.color(m.x, m.y) not in (WHITE, BLACK, None) else None
        ok = m.step()
        self.show()
        if not ok or self._hit_break(before):
            self.stop()
            return
        delay = int(900 / (self.speed.get() ** 1.6))
        self.root.after(max(5, delay), self._tick)

    def stop(self):
        self.running = None
        if hasattr(self, "play_btn"):
            self.play_btn.configure(text="再生 (F6)")

    # ------------------------------------------------------------ ファイル
    def _title(self):
        name = os.path.basename(self.path) if self.path else "無題"
        self.root.title(f"{'*' if self.dirty else ''}{name} ― {APP}")

    def confirm_discard(self):
        if not self.dirty:
            return True
        return messagebox.askyesno(APP, "変更が保存されていません。破棄してよいですか？")

    def new_dialog(self):
        if not self.confirm_discard():
            return
        w = simpledialog.askinteger(APP, "幅（コーデル数）", initialvalue=16, minvalue=1, maxvalue=400)
        h = w and simpledialog.askinteger(APP, "高さ（コーデル数）", initialvalue=10, minvalue=1, maxvalue=400)
        if w and h:
            self.path = None
            self.undo.clear(); self.breaks.clear()
            self.set_grid([[WHITE] * w for _ in range(h)])
            self.dirty = False
            self._title()

    def resize_dialog(self):
        w = simpledialog.askinteger(APP, "新しい幅", initialvalue=self.W, minvalue=1, maxvalue=400)
        h = w and simpledialog.askinteger(APP, "新しい高さ", initialvalue=self.H, minvalue=1, maxvalue=400)
        if w and h:
            self.resize(w, h)

    def open_dialog(self):
        if not self.confirm_discard():
            return
        p = filedialog.askopenfilename(title="Piet プログラムを開く",
                                       filetypes=[("画像", "*.png *.gif *.ppm"), ("テキスト記法", "*.txt"), ("すべて", "*")])
        if p:
            self.open_path(p)

    def open_path(self, p):
        try:
            if p.endswith(".txt"):
                self.load_text(open(p, encoding="utf-8").read())
                self.path = None
            else:
                grid, cs = load_image(self.root, p)
                self.codel_size = cs
                self.set_grid(grid)
                self.path = p
                self.status.configure(text=f"{os.path.basename(p)} を開きました（コーデルサイズ {cs}、{self.W}×{self.H} コーデル）")
        except Exception as e:
            messagebox.showerror(APP, f"開けませんでした: {e}")
            return
        self.undo.clear(); self.redo.clear(); self.breaks.clear()
        self.dirty = False
        self._title()
        self.zoom = max(4, min(40, 900 // max(self.W, 1)))
        self.zoom_var.set(self.zoom)
        self.redraw()

    def load_text(self, t):
        prog = Program.from_text(t)
        self.set_grid(prog.grid)

    def open_text(self):
        if not self.confirm_discard():
            return
        p = filedialog.askopenfilename(filetypes=[("テキスト記法", "*.txt"), ("すべて", "*")])
        if p:
            self.open_path(p)

    def save(self):
        if not self.path:
            return self.save_as()
        try:
            save_image(self.root, self.grid, self.path, self.codel_size)
        except Exception as e:
            messagebox.showerror(APP, f"保存できませんでした: {e}")
            return
        self.dirty = False
        self._title()
        self.status.configure(text=f"保存しました（コーデルサイズ {self.codel_size}）")

    def save_as(self):
        p = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG", "*.png"), ("GIF", "*.gif"), ("PPM", "*.ppm")])
        if not p:
            return
        cs = simpledialog.askinteger(APP, "コーデルサイズ（1 コーデルを何ピクセルにするか）", initialvalue=self.codel_size, minvalue=1, maxvalue=64)
        if not cs:
            return
        self.codel_size = cs
        self.path = p
        self.save()

    def save_text(self):
        p = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("テキスト記法", "*.txt")])
        if p:
            with open(p, "w", encoding="utf-8") as f:
                f.write(Program(self.grid).to_text() + "\n")

    def help(self):
        messagebox.showinfo(APP, __doc__)

    def quit(self):
        if self.confirm_discard():
            self.root.destroy()


def main():
    root = tk.Tk()
    try:
        ttk.Style().theme_use("clam")
    except tk.TclError:
        pass
    Studio(root, sys.argv[1] if len(sys.argv) > 1 else None)
    root.mainloop()


if __name__ == "__main__":
    main()
