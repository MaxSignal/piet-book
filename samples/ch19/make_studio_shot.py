# 第19章の Piet スタジオのスクリーンショットを作る。
# 実行: . ext/tkenv.sh && xvfb-run -a -s "-screen 0 1200x800x24" python3 samples/ch19/make_studio_shot.py
import os as _os
ROOT = _os.path.abspath(_os.path.join(_os.path.dirname(__file__), "..", ".."))
import sys, os
sys.path.insert(0, os.path.join(ROOT, "tools"))
import tkinter as tk, pietstudio as S
root = tk.Tk(); root.geometry("1180x740+0+0")
app = S.Studio(root, os.path.join(ROOT, "site/img/ch19/loop_fix-big.png"))
root.geometry("1180x740+0+0")
app.breaks.add((7, 7))
def go():
    app.set_zoom(11); app.reset()
    app.run(); app.run(); app.run()
    app.draw_marks()
    root.after(500, lambda: (os.system("import -window root -crop 1180x740+0+0 " + os.path.join(ROOT, "site/img/ch19/studio-break.png")), root.destroy()))
root.after(600, go)
root.mainloop()
