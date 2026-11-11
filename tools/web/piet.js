/* piet.js — 『Piet プログラミング入門』ブラウザ版ビューア / 実行エンジン
 * 実行エンジンは tools/piet.py と同じ規則で動く（仕様準拠、整数は BigInt）。
 */
(function () {
  "use strict";

  // ---------------------------------------------------------------- 色
  const RGB = [
    [0xFFC0C0, 0xFF0000, 0xC00000], [0xFFFFC0, 0xFFFF00, 0xC0C000], [0xC0FFC0, 0x00FF00, 0x00C000],
    [0xC0FFFF, 0x00FFFF, 0x00C0C0], [0xC0C0FF, 0x0000FF, 0x0000C0], [0xFFC0FF, 0xFF00FF, 0xC000C0],
  ];
  const WHITE = -1, BLACK = -2;            // 色番号: hue*3+light (0..17), 白 -1, 黒 -2
  const RGB2COL = new Map();
  for (let h = 0; h < 6; h++) for (let l = 0; l < 3; l++) RGB2COL.set(RGB[h][l], h * 3 + l);
  RGB2COL.set(0xFFFFFF, WHITE); RGB2COL.set(0x000000, BLACK);
  const HUE_JA = ["赤", "黄", "緑", "シアン", "青", "マゼンタ"];
  const LIGHT_JA = ["淡", "", "濃"];
  const colName = c => c === WHITE ? "白" : c === BLACK ? "黒" : LIGHT_JA[c % 3] + HUE_JA[(c / 3) | 0];
  const colHex = c => c === WHITE ? "#FFFFFF" : c === BLACK ? "#000000" : "#" + RGB[(c / 3) | 0][c % 3].toString(16).padStart(6, "0").toUpperCase();
  const CMDS = [
    [null, "push", "pop"], ["add", "subtract", "multiply"], ["divide", "mod", "not"],
    ["greater", "pointer", "switch"], ["duplicate", "roll", "in(number)"], ["in(char)", "out(number)", "out(char)"],
  ];
  function commandBetween(a, b) {
    const dh = (((b / 3) | 0) - ((a / 3) | 0) + 6) % 6;
    const dl = (b % 3 - a % 3 + 3) % 3;
    return CMDS[dh][dl];
  }
  const TEXT_CH = "rRy1"; // unused placeholder
  const CHARS = {};
  "rygcbm".split("").forEach((ch, h) => CHARS[ch] = h * 3);
  "RYGCBM".split("").forEach((ch, h) => CHARS[ch] = h * 3 + 1);
  "123456".split("").forEach((ch, h) => CHARS[ch] = h * 3 + 2);
  CHARS["."] = WHITE; CHARS["#"] = BLACK;
  const COL2CHAR = {};
  Object.keys(CHARS).forEach(k => COL2CHAR[CHARS[k]] = k);

  // ---------------------------------------------------------------- プログラム
  class Program {
    constructor(w, h, grid) { this.w = w; this.h = h; this.grid = grid; this.blockOf = null; this.blocks = null; }
    static fromImageData(img, cs) {
      const W = img.width, H = img.height, d = img.data;
      const px = (x, y) => { const i = (y * W + x) * 4; return (d[i] << 16) | (d[i + 1] << 8) | d[i + 2]; };
      if (!cs) cs = guessCodelSize(W, H, px);
      const w = Math.floor(W / cs), h = Math.floor(H / cs);
      const grid = new Int8Array(w * h);
      for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
        const v = px(x * cs, y * cs);
        const c = RGB2COL.get(v);
        grid[y * w + x] = c === undefined ? WHITE : c;
      }
      return new Program(w, h, grid);
    }
    static fromText(text) {
      const rows = text.replace(/\r/g, "").split("\n").map(r => r.split(";")[0].replace(/\s/g, "")).filter(r => r.length);
      const w = Math.max(...rows.map(r => r.length)), h = rows.length;
      const grid = new Int8Array(w * h).fill(WHITE);
      rows.forEach((r, y) => r.split("").forEach((ch, x) => { if (ch in CHARS) grid[y * w + x] = CHARS[ch]; }));
      return new Program(w, h, grid);
    }
    toText() {
      let s = "";
      for (let y = 0; y < this.h; y++) {
        for (let x = 0; x < this.w; x++) s += COL2CHAR[this.grid[y * this.w + x]];
        s += "\n";
      }
      return s;
    }
    color(x, y) { return (x >= 0 && y >= 0 && x < this.w && y < this.h) ? this.grid[y * this.w + x] : null; }
    analyze() {   // 全ブロックを求める
      const { w, h, grid } = this;
      const blockOf = new Int32Array(w * h).fill(-1);
      const blocks = [];
      for (let i = 0; i < w * h; i++) {
        if (blockOf[i] >= 0) continue;
        const c = grid[i], id = blocks.length, cells = [];
        const stack = [i]; blockOf[i] = id;
        let minx = 1e9, maxx = -1, miny = 1e9, maxy = -1;
        while (stack.length) {
          const j = stack.pop(), x = j % w, y = (j / w) | 0;
          cells.push(j);
          if (x < minx) minx = x; if (x > maxx) maxx = x; if (y < miny) miny = y; if (y > maxy) maxy = y;
          const nb = [[x + 1, y], [x - 1, y], [x, y + 1], [x, y - 1]];
          for (const [nx, ny] of nb) {
            if (nx < 0 || ny < 0 || nx >= w || ny >= h) continue;
            const k = ny * w + nx;
            if (blockOf[k] < 0 && grid[k] === c) { blockOf[k] = id; stack.push(k); }
          }
        }
        const b = { id, color: c, cells, size: cells.length, exits: null };
        if (c >= 0) b.exits = computeExits(cells, w, minx, maxx, miny, maxy);
        blocks.push(b);
      }
      this.blockOf = blockOf; this.blocks = blocks;
    }
    block(x, y) { if (!this.blocks) this.analyze(); return this.blocks[this.blockOf[y * this.w + x]]; }
  }

  function computeExits(cells, w, minx, maxx, miny, maxy) {
    // exits[dp*2+cc] = [x, y]
    const pts = cells.map(j => [j % w, (j / w) | 0]);
    const pick = (filter, cmp) => pts.filter(filter).reduce((a, b) => cmp(b, a) ? b : a);
    const R = p => p[0] === maxx, D = p => p[1] === maxy, L = p => p[0] === minx, U = p => p[1] === miny;
    return [
      pick(R, (a, b) => a[1] < b[1]), pick(R, (a, b) => a[1] > b[1]),   // 右: CC左=上, CC右=下
      pick(D, (a, b) => a[0] > b[0]), pick(D, (a, b) => a[0] < b[0]),   // 下: CC左=右(東), CC右=左
      pick(L, (a, b) => a[1] > b[1]), pick(L, (a, b) => a[1] < b[1]),   // 左: CC左=下, CC右=上
      pick(U, (a, b) => a[0] < b[0]), pick(U, (a, b) => a[0] > b[0]),   // 上: CC左=左(西), CC右=右
    ];
  }

  function gcd(a, b) { while (b) { [a, b] = [b, a % b]; } return a; }
  function guessCodelSize(W, H, px) {
    let g = 0;
    for (let y = 0; y < H; y++) {
      let run = 1;
      for (let x = 1; x <= W; x++) {
        if (x < W && px(x, y) === px(x - 1, y)) run++;
        else { g = gcd(g, run); run = 1; if (g === 1) return 1; }
      }
    }
    for (let x = 0; x < W; x++) {
      let run = 1;
      for (let y = 1; y <= H; y++) {
        if (y < H && px(x, y) === px(x, y - 1)) run++;
        else { g = gcd(g, run); run = 1; if (g === 1) return 1; }
      }
    }
    return g || 1;
  }

  // ---------------------------------------------------------------- 実行機械
  const DPV = [[1, 0], [0, 1], [-1, 0], [0, -1]];
  const DP_JA = ["右", "下", "左", "上"], CC_JA = ["左", "右"];
  const floorDiv = (a, b) => { let q = a / b; if ((a % b !== 0n) && ((a < 0n) !== (b < 0n))) q -= 1n; return q; };
  const floorMod = (a, b) => ((a % b) + b) % b;

  class Machine {
    constructor(prog, input) {
      this.p = prog; if (!prog.blocks) prog.analyze();
      this.reset(input || "");
    }
    reset(input) {
      this.x = 0; this.y = 0; this.dp = 0; this.cc = 0; this.stack = []; this.out = "";
      this.input = Array.from(input || ""); this.ip = 0;
      this.steps = 0; this.halted = false; this.last = null; this.prev = null;
    }
    readChar() { return this.ip < this.input.length ? BigInt(this.input[this.ip++].codePointAt(0)) : null; }
    readNumber() {
      let i = this.ip; const s = this.input;
      while (i < s.length && /\s/.test(s[i])) i++;
      let j = i; if (j < s.length && (s[j] === "+" || s[j] === "-")) j++;
      let k = j; while (k < s.length && s[k] >= "0" && s[k] <= "9") k++;
      if (k === j) return null;
      this.ip = k; return BigInt(s.slice(i, k).join(""));
    }
    exec(cmd, size) {
      const st = this.stack, n = st.length;
      const bin = f => { if (n < 2) return false; const b = st.pop(), a = st.pop(); const r = f(a, b); if (r === null) { st.push(a, b); return false; } st.push(r); return true; };
      switch (cmd) {
        case "push": st.push(BigInt(size)); return true;
        case "pop": if (!n) return false; st.pop(); return true;
        case "add": return bin((a, b) => a + b);
        case "subtract": return bin((a, b) => a - b);
        case "multiply": return bin((a, b) => a * b);
        case "divide": return bin((a, b) => b === 0n ? null : floorDiv(a, b));
        case "mod": return bin((a, b) => b === 0n ? null : floorMod(a, b));
        case "greater": return bin((a, b) => a > b ? 1n : 0n);
        case "not": if (!n) return false; st[n - 1] = st[n - 1] === 0n ? 1n : 0n; return true;
        case "pointer": { if (!n) return false; const v = st.pop(); this.dp = Number(((BigInt(this.dp) + v) % 4n + 4n) % 4n); return true; }
        case "switch": { if (!n) return false; let v = st.pop(); if (v < 0n) v = -v; this.cc = Number((BigInt(this.cc) + v) % 2n); return true; }
        case "duplicate": if (!n) return false; st.push(st[n - 1]); return true;
        case "roll": {
          if (n < 2) return false;
          const depth = st[n - 2], cnt = st[n - 1];
          if (depth < 0n || depth > BigInt(n - 2)) return false;
          st.pop(); st.pop();
          const d = Number(depth);
          if (d > 0) {
            const r = Number(((cnt % depth) + depth) % depth);
            if (r) { const seg = st.splice(st.length - d, d); st.push(...seg.slice(d - r), ...seg.slice(0, d - r)); }
          }
          return true;
        }
        case "in(number)": { const v = this.readNumber(); if (v === null) return false; st.push(v); return true; }
        case "in(char)": { const v = this.readChar(); if (v === null) return false; st.push(v); return true; }
        case "out(number)": if (!n) return false; this.out += st.pop().toString(); return true;
        case "out(char)": {
          if (!n) return false; const v = st[n - 1];
          if (v < 0n || v > 0x10FFFFn) return false;
          st.pop(); this.out += String.fromCodePoint(Number(v)); return true;
        }
      }
      return false;
    }
    step() {
      if (this.halted) return false;
      const p = this.p;
      const cur = p.color(this.x, this.y);
      this.prev = { x: this.x, y: this.y };
      if (cur === WHITE) return this.slide(this.x, this.y, null);
      const blk = p.block(this.x, this.y);
      for (let attempt = 0; attempt < 8; attempt++) {
        const [ex, ey] = blk.exits[this.dp * 2 + this.cc];
        const nx = ex + DPV[this.dp][0], ny = ey + DPV[this.dp][1];
        const nc = p.color(nx, ny);
        if (nc !== null && nc !== BLACK) {
          if (nc === WHITE) return this.slide(nx, ny, blk);
          const cmd = commandBetween(cur, nc);
          const ok = this.exec(cmd, blk.size);
          this.steps++;
          this.last = { cmd: cmd === "push" ? "push " + blk.size : cmd, ok, from: cur, to: nc, exit: [ex, ey] };
          this.x = nx; this.y = ny;
          return true;
        }
        if (attempt % 2 === 0) this.cc ^= 1; else this.dp = (this.dp + 1) % 4;
      }
      this.halted = true; this.last = { cmd: "停止", ok: true };
      return false;
    }
    slide(x, y, blk) {
      const p = this.p, seen = new Set();
      for (;;) {
        const [dx, dy] = DPV[this.dp];
        while (p.color(x + dx, y + dy) === WHITE) { x += dx; y += dy; }
        const nc = p.color(x + dx, y + dy);
        if (nc !== null && nc !== BLACK) {
          this.x = x + dx; this.y = y + dy; this.steps++;
          this.last = { cmd: "白を通過（命令なし）", ok: true };
          return true;
        }
        const key = x + "," + y + "," + this.dp + "," + this.cc;
        if (seen.has(key)) { this.halted = true; this.last = { cmd: "停止（白の中で行き止まり）", ok: true }; return false; }
        seen.add(key);
        this.cc ^= 1; this.dp = (this.dp + 1) % 4;
      }
    }
  }

  // ---------------------------------------------------------------- 画像の読み込み
  const cache = new Map();
  function loadProgram(src) {
    if (cache.has(src)) return cache.get(src);
    const pr = new Promise((resolve, reject) => {
      const img = new Image();
      img.onload = () => {
        const c = document.createElement("canvas");
        c.width = img.naturalWidth; c.height = img.naturalHeight;
        const ctx = c.getContext("2d");
        ctx.drawImage(img, 0, 0);
        try { resolve(Program.fromImageData(ctx.getImageData(0, 0, c.width, c.height))); }
        catch (e) { reject(e); }
      };
      img.onerror = () => reject(new Error("画像を読み込めません: " + src));
      img.src = src;
    });
    cache.set(src, pr);
    return pr;
  }

  // ---------------------------------------------------------------- 描画
  function cssVar(el, name, fb) { const v = getComputedStyle(el).getPropertyValue(name).trim(); return v || fb; }

  function drawProgram(canvas, prog, zoom, m) {
    const w = prog.w * zoom, h = prog.h * zoom;
    const dpr = window.devicePixelRatio || 1;
    if (canvas.width !== Math.round(w * dpr)) { canvas.width = Math.round(w * dpr); canvas.height = Math.round(h * dpr); }
    canvas.style.width = w + "px"; canvas.style.aspectRatio = prog.w + " / " + prog.h;
    const ctx = canvas.getContext("2d");
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    for (let y = 0; y < prog.h; y++) for (let x = 0; x < prog.w; x++) {
      ctx.fillStyle = colHex(prog.grid[y * prog.w + x]);
      ctx.fillRect(x * zoom, y * zoom, zoom, zoom);
    }
    if (zoom >= 8) {
      ctx.strokeStyle = "rgba(128,128,128,0.35)"; ctx.lineWidth = 1 / dpr;
      ctx.beginPath();
      for (let x = 0; x <= prog.w; x++) { ctx.moveTo(x * zoom, 0); ctx.lineTo(x * zoom, h); }
      for (let y = 0; y <= prog.h; y++) { ctx.moveTo(0, y * zoom); ctx.lineTo(w, y * zoom); }
      ctx.stroke();
    }
    if (m && m.steps > 0 || m && m.halted) {
      const c = prog.color(m.x, m.y);
      // 現在のブロックを縁取り
      if (c !== WHITE && c !== null) {
        const b = prog.block(m.x, m.y);
        const set = new Set(b.cells);
        ctx.lineWidth = Math.max(2, zoom / 6);
        ctx.strokeStyle = "#000"; drawOutline(ctx, prog, set, zoom, 0);
        ctx.strokeStyle = "#fff"; ctx.lineWidth = Math.max(1, zoom / 12); drawOutline(ctx, prog, set, zoom, 0);
      }
      // 現在のコーデルに DP の矢印
      const cx = (m.x + 0.5) * zoom, cy = (m.y + 0.5) * zoom, r = Math.max(3, zoom * 0.32);
      const [dx, dy] = DPV[m.dp];
      ctx.fillStyle = "#000"; ctx.strokeStyle = "#fff"; ctx.lineWidth = Math.max(1, zoom / 14);
      ctx.beginPath();
      ctx.moveTo(cx + dx * r, cy + dy * r);
      ctx.lineTo(cx - dx * r * 0.7 - dy * r * 0.75, cy - dy * r * 0.7 + dx * r * 0.75);
      ctx.lineTo(cx - dx * r * 0.7 + dy * r * 0.75, cy - dy * r * 0.7 - dx * r * 0.75);
      ctx.closePath(); ctx.fill(); ctx.stroke();
    }
  }
  function drawOutline(ctx, prog, set, z, _) {
    ctx.beginPath();
    for (const j of set) {
      const x = j % prog.w, y = (j / prog.w) | 0;
      const has = (xx, yy) => xx >= 0 && yy >= 0 && xx < prog.w && yy < prog.h && set.has(yy * prog.w + xx);
      if (!has(x, y - 1)) { ctx.moveTo(x * z, y * z); ctx.lineTo((x + 1) * z, y * z); }
      if (!has(x, y + 1)) { ctx.moveTo(x * z, (y + 1) * z); ctx.lineTo((x + 1) * z, (y + 1) * z); }
      if (!has(x - 1, y)) { ctx.moveTo(x * z, y * z); ctx.lineTo(x * z, (y + 1) * z); }
      if (!has(x + 1, y)) { ctx.moveTo((x + 1) * z, y * z); ctx.lineTo((x + 1) * z, (y + 1) * z); }
    }
    ctx.stroke();
  }

  function fmtStack(st) {
    if (!st.length) return "（空）";
    const s = st.slice(-24).map(v => v.toString());
    return (st.length > 24 ? "… " : "") + "[" + s.join(" ") + "]";
  }
  function showChars(s) { return s.replace(/\n/g, "↵\n"); }

  // ---------------------------------------------------------------- ビューア（本文の図）
  function autoZoom(prog, avail) {
    const z = Math.floor(avail / prog.w);
    return Math.max(2, Math.min(28, z));
  }

  class Viewer {
    constructor(root, prog) {
      this.root = root; this.prog = prog;
      this.canvas = root.querySelector("canvas");
      this.inputEl = root.querySelector("textarea.pv-input");
      this.outEl = root.querySelector(".pv-out");
      this.stateEl = root.querySelector(".pv-state");
      this.zoomFixed = parseInt(root.dataset.zoom || "0", 10);
      this.m = new Machine(prog, this.inputEl ? this.inputEl.value : "");
      this.timer = null;
      root.querySelector(".pv-run").addEventListener("click", () => this.run());
      root.querySelector(".pv-step").addEventListener("click", () => this.stepOnce());
      root.querySelector(".pv-play").addEventListener("click", () => this.togglePlay());
      root.querySelector(".pv-reset").addEventListener("click", () => this.reset());
      if (this.inputEl) this.inputEl.addEventListener("input", () => this.reset());
      this.resize();
      new ResizeObserver(() => this.resize()).observe(root.querySelector(".pv-stage"));
      this.update();
    }
    resize() {
      const stage = this.root.querySelector(".pv-stage");
      const avail = Math.max(120, stage.clientWidth - 2);
      this.zoom = this.zoomFixed ? Math.min(this.zoomFixed, autoZoom(this.prog, avail)) : autoZoom(this.prog, Math.min(avail, 640));
      this.draw();
    }
    draw() { drawProgram(this.canvas, this.prog, this.zoom, this.m); }
    reset() {
      this.stop();
      this.m.reset(this.inputEl ? this.inputEl.value.replace(/\\n/g, "\n").replace(/\\0/g, "\0") : "");
      this.update();
    }
    stop() { if (this.timer) { clearTimeout(this.timer); this.timer = null; this.root.querySelector(".pv-play").textContent = "再生"; } }
    stepOnce() { this.stop(); if (this.m.halted) this.reset(); this.m.step(); this.update(); }
    run() {
      this.stop();
      if (this.m.halted) this.m.reset(this.inputEl ? this.inputEl.value.replace(/\\n/g, "\n").replace(/\\0/g, "\0") : "");
      const t0 = performance.now();
      const chunk = () => {
        let i = 0;
        while (i < 20000 && this.m.step()) i++;
        if (!this.m.halted && this.m.steps < 5_000_000 && performance.now() - t0 < 20000) { this.update(); this.timer = setTimeout(chunk, 0); }
        else { this.timer = null; this.update(); }
      };
      chunk();
    }
    togglePlay() {
      if (this.timer) { this.stop(); return; }
      if (this.m.halted) this.m.reset(this.inputEl ? this.inputEl.value.replace(/\\n/g, "\n").replace(/\\0/g, "\0") : "");
      this.root.querySelector(".pv-play").textContent = "一時停止";
      const tick = () => {
        if (!this.m.step()) { this.stop(); this.update(); return; }
        this.update();
        this.timer = setTimeout(tick, this.prog.w * this.prog.h > 600 ? 60 : 260);
      };
      tick();
    }
    update() {
      const m = this.m;
      this.outEl.textContent = m.out.length ? m.out : "";
      this.outEl.classList.toggle("empty", !m.out.length);
      const last = m.last ? (m.last.cmd + (m.last.ok ? "" : "（無視）")) : "—";
      this.stateEl.innerHTML =
        `<span><b>ステップ</b> ${m.steps}</span><span><b>DP</b> ${DP_JA[m.dp]}</span><span><b>CC</b> ${CC_JA[m.cc]}</span>` +
        `<span class="pv-last"><b>直前の命令</b> ${escapeHtml(last)}</span><span class="pv-stack"><b>スタック</b> ${escapeHtml(fmtStack(m.stack))}</span>` +
        (m.halted ? `<span class="pv-halt">停止しました</span>` : "");
      this.draw();
    }
  }
  function escapeHtml(s) { return String(s).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c])); }

  function initFigures() {
    const progOf = el => el.dataset.grid ? Promise.resolve(Program.fromText(el.dataset.grid.replace(/\//g, "\n"))) : loadProgram(el.dataset.src);
    document.querySelectorAll("figure.pv").forEach(fig => {
      progOf(fig).then(prog => new Viewer(fig, prog)).catch(err => {
        const st = fig.querySelector(".pv-state"); if (st) st.textContent = String(err.message || err);
      });
    });
    // 章扉の帯（クリックで実行）
    document.querySelectorAll(".strip[data-grid], .strip[data-src]").forEach(el => {
      progOf(el).then(prog => {
        const cv = el.querySelector("canvas"), out = el.querySelector(".strip-out");
        const z = parseInt(el.dataset.zoom || "8", 10);
        drawProgram(cv, prog, z, null);
        el.querySelector("button").addEventListener("click", () => {
          const m = new Machine(prog, ""); let i = 0;
          while (i++ < 200000 && m.step()) { }
          out.textContent = "出力: " + m.out;
          drawProgram(cv, prog, z, m);
        });
      }).catch(() => {});
    });
  }

  // ---------------------------------------------------------------- 長いコードにコピーボタン
  function initCopy() {
    document.querySelectorAll(".prose pre").forEach(pre => {
      if (pre.classList.contains("trace") || pre.classList.contains("grid")) return;
      if ((pre.textContent.match(/\n/g) || []).length < 12) return;
      const wrap = document.createElement("div"); wrap.className = "code-wrap";
      pre.parentNode.insertBefore(wrap, pre); wrap.appendChild(pre);
      const b = document.createElement("button"); b.type = "button"; b.className = "copy-btn"; b.textContent = "コピー";
      b.addEventListener("click", () => {
        const done = () => { b.textContent = "コピーしました"; setTimeout(() => b.textContent = "コピー", 2000); };
        const fallback = () => { const r = document.createRange(); r.selectNodeContents(pre); const sel = getSelection(); sel.removeAllRanges(); sel.addRange(r); b.textContent = "選択しました（Ctrl+C でコピー）"; };
        if (navigator.clipboard) navigator.clipboard.writeText(pre.textContent).then(done, fallback); else fallback();
      });
      wrap.appendChild(b);
    });
  }

  // ---------------------------------------------------------------- 公開
  window.Piet = { Program, Machine, loadProgram, drawProgram, commandBetween, colName, colHex, CMDS, WHITE, BLACK, RGB, DP_JA, CC_JA, fmtStack, escapeHtml, autoZoom, CHARS, COL2CHAR };
  const boot = () => { initFigures(); initCopy(); };
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot); else boot();
})();
