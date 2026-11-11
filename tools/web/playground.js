/* playground.js — Piet エディタ兼デバッガ */
(function () {
  "use strict";
  const P = window.Piet;
  const $ = id => document.getElementById(id);
  const KEY = "piet-book-playground-v1";

  // 初期状態: 第1章の「5 を出力する」プログラム
  const DEMO = "RRRRR1m#....\n....#mm#....\n.....##.....";
  let W = 12, H = 8, grid = new Int8Array(W * H).fill(P.WHITE);
  let brush = 1;          // 赤
  let tool = "paint";
  let zoom = 28;
  let prog = null, m = null, timer = null;

  function loadText(t) {
    const p = P.Program.fromText(t);
    setGrid(p.w, p.h, p.grid);
  }
  function setGrid(w, h, g) {
    W = w; H = h; grid = Int8Array.from(g);
    $("pg-w").value = W; $("pg-h").value = H;
    changed();
  }
  function resizeGrid(w, h) {
    const ng = new Int8Array(w * h).fill(P.WHITE);
    for (let y = 0; y < Math.min(h, H); y++) for (let x = 0; x < Math.min(w, W); x++) ng[y * w + x] = grid[y * W + x];
    W = w; H = h; grid = ng; changed();
  }

  // ---------------------------------------------------------------- パレット
  const pal = $("pg-palette");
  const order = [];
  for (let l = 0; l < 3; l++) for (let h = 0; h < 6; h++) order.push(h * 3 + l);
  order.push(P.WHITE, P.BLACK);
  const palButtons = new Map();
  order.forEach(c => {
    const b = document.createElement("button");
    b.type = "button";
    b.style.background = P.colHex(c);
    if (c === P.BLACK || (c >= 0 && (c % 3 === 2 || (c % 3 === 1 && [0, 4, 5].includes((c / 3) | 0))))) b.classList.add("dk");
    if (c < 0) b.classList.add("wide");
    if (c === P.WHITE) b.classList.add("wh");
    b.addEventListener("click", () => { brush = c; if (tool === "pick") setTool("paint"); updatePalette(); });
    pal.appendChild(b);
    palButtons.set(c, b);
  });
  function updatePalette() {
    palButtons.forEach((b, c) => {
      let label = P.colName(c);
      if (brush >= 0 && c >= 0) {
        const cmd = P.commandBetween(brush, c);
        label = cmd ? cmd : "（同じ色）";
      }
      b.textContent = label;
      b.title = P.colName(c) + " " + P.colHex(c);
      b.setAttribute("aria-label", P.colName(c) + (brush >= 0 && c >= 0 ? "：" + (P.commandBetween(brush, c) || "命令なし") : ""));
      b.classList.toggle("sel", c === brush);
    });
    $("pg-cur").textContent = "選択中: " + P.colName(brush) + (brush >= 0 ? "（各マスはこの色からの命令）" : "");
  }

  // ---------------------------------------------------------------- 道具
  function setTool(t) {
    tool = t;
    ["paint", "fill", "pick"].forEach(k => { const b = $("tool-" + k); b.classList.toggle("on", k === t); b.setAttribute("aria-pressed", k === t); });
  }
  $("tool-paint").onclick = () => setTool("paint");
  $("tool-fill").onclick = () => setTool("fill");
  $("tool-pick").onclick = () => setTool("pick");

  const cv = $("pg-canvas");
  let drawing = false;
  function cellAt(ev) {
    const r = cv.getBoundingClientRect();
    const x = Math.floor((ev.clientX - r.left) / zoom), y = Math.floor((ev.clientY - r.top) / zoom);
    return (x >= 0 && y >= 0 && x < W && y < H) ? [x, y] : null;
  }
  function apply(ev) {
    const c = cellAt(ev); if (!c) return;
    const [x, y] = c, i = y * W + x;
    if (tool === "pick") { brush = grid[i]; updatePalette(); setTool("paint"); return; }
    if (tool === "fill") { flood(x, y, brush); changed(); return; }
    if (grid[i] !== brush) { grid[i] = brush; changed(); }
  }
  function flood(x, y, c) {
    const from = grid[y * W + x]; if (from === c) return;
    const st = [[x, y]];
    while (st.length) {
      const [a, b] = st.pop();
      if (a < 0 || b < 0 || a >= W || b >= H || grid[b * W + a] !== from) continue;
      grid[b * W + a] = c;
      st.push([a + 1, b], [a - 1, b], [a, b + 1], [a, b - 1]);
    }
  }
  cv.addEventListener("pointerdown", ev => { drawing = tool === "paint"; cv.setPointerCapture(ev.pointerId); apply(ev); });
  cv.addEventListener("pointermove", ev => {
    if (drawing) apply(ev);
    const c = cellAt(ev);
    if (c && prog) {
      const col = prog.color(c[0], c[1]);
      const size = col >= 0 ? prog.block(c[0], c[1]).size : null;
      $("pg-hover").textContent = `(${c[0]}, ${c[1]})  ${P.colName(col)}` + (size ? `  ブロックの大きさ ${size}` : "");
    }
  });
  cv.addEventListener("pointerup", () => { drawing = false; });
  cv.addEventListener("pointercancel", () => { drawing = false; });

  // ---------------------------------------------------------------- 変更と描画
  function changed() {
    prog = new P.Program(W, H, Int8Array.from(grid));
    prog.analyze();
    resetRun();
    save();
    exportViews();
  }
  function draw() { P.drawProgram(cv, prog, zoom, m); }
  function exportViews() {
    $("pg-text").value = prog.toText();
    const c = document.createElement("canvas");
    c.width = W * 10; c.height = H * 10;
    const ctx = c.getContext("2d");
    for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) { ctx.fillStyle = P.colHex(grid[y * W + x]); ctx.fillRect(x * 10, y * 10, 10, 10); }
    $("pg-png").src = c.toDataURL("image/png");
  }
  function save() { try { localStorage.setItem(KEY, JSON.stringify({ W, H, g: Array.from(grid), input: $("pg-input").value })); } catch (e) { } }
  function restore() {
    try {
      const s = JSON.parse(localStorage.getItem(KEY) || "null");
      if (s && s.W && s.H && s.g && s.g.length === s.W * s.H) { $("pg-input").value = s.input || ""; setGrid(s.W, s.H, s.g); return true; }
    } catch (e) { }
    return false;
  }

  // ---------------------------------------------------------------- 実行
  function inputText() { return $("pg-input").value.replace(/\\n/g, "\n").replace(/\\0/g, "\0"); }
  function stop() { if (timer) { clearTimeout(timer); timer = null; } $("pg-play").textContent = "再生"; }
  function resetRun() { stop(); m = new P.Machine(prog, inputText()); show(); }
  function show() {
    const out = $("pg-out");
    out.textContent = m.out; out.classList.toggle("empty", !m.out.length);
    const last = m.last ? (m.last.cmd + (m.last.ok ? "" : "（無視）")) : "—";
    $("pg-state").innerHTML = `<span><b>ステップ</b> ${m.steps}</span><span><b>DP</b> ${P.DP_JA[m.dp]}</span><span><b>CC</b> ${P.CC_JA[m.cc]}</span>` +
      `<span><b>直前の命令</b> ${P.escapeHtml(last)}</span><span class="pv-stack"><b>スタック</b> ${P.escapeHtml(P.fmtStack(m.stack))}</span>` +
      (m.halted ? `<span class="pv-halt">停止しました</span>` : "");
    draw();
  }
  $("pg-run").onclick = () => {
    stop(); if (m.halted || m.steps) m = new P.Machine(prog, inputText());
    const t0 = performance.now();
    const chunk = () => {
      let i = 0; while (i < 20000 && m.step()) i++;
      if (!m.halted && m.steps < 5_000_000 && performance.now() - t0 < 20000) { show(); timer = setTimeout(chunk, 0); }
      else { timer = null; show(); if (!m.halted) $("pg-state").insertAdjacentHTML("beforeend", "<span class='pv-halt'>上限に達したので止めました（無限ループの可能性）</span>"); }
    };
    chunk();
  };
  $("pg-step").onclick = () => { stop(); if (m.halted) m = new P.Machine(prog, inputText()); m.step(); show(); };
  $("pg-reset").onclick = resetRun;
  $("pg-play").onclick = () => {
    if (timer) { stop(); return; }
    if (m.halted) m = new P.Machine(prog, inputText());
    $("pg-play").textContent = "一時停止";
    const tick = () => { if (!m.step()) { stop(); show(); return; } show(); timer = setTimeout(tick, 220); };
    tick();
  };
  $("pg-input").addEventListener("input", () => { save(); resetRun(); });

  // ---------------------------------------------------------------- 寸法・表示
  $("pg-w").addEventListener("change", () => resizeGrid(clamp(+$("pg-w").value), H));
  $("pg-h").addEventListener("change", () => resizeGrid(W, clamp(+$("pg-h").value)));
  const clamp = v => Math.max(1, Math.min(160, v | 0 || 1));
  $("pg-zoom").addEventListener("input", () => { zoom = +$("pg-zoom").value; draw(); });
  let armed = false;
  $("pg-clear").onclick = () => {
    if (!armed) { armed = true; $("pg-clear").textContent = "もう一度押すと消去"; setTimeout(() => { armed = false; $("pg-clear").textContent = "全消去"; }, 2500); return; }
    armed = false; $("pg-clear").textContent = "全消去"; grid.fill(P.WHITE); changed();
  };

  // ---------------------------------------------------------------- 読み込み・書き出し
  $("pg-text-load").onclick = () => { try { loadText($("pg-text").value); } catch (e) { $("pg-hover").textContent = "テキストを読み込めませんでした: " + e.message; } };
  $("pg-text-copy").onclick = () => {
    const t = $("pg-text");
    navigator.clipboard.writeText(t.value).then(() => { $("pg-text-copy").textContent = "コピーしました"; }, () => { t.select(); });
  };
  $("pg-file").addEventListener("change", ev => {
    const f = ev.target.files[0]; if (!f) return;
    const url = URL.createObjectURL(f);
    const img = new Image();
    img.onload = () => {
      const c = document.createElement("canvas"); c.width = img.naturalWidth; c.height = img.naturalHeight;
      const ctx = c.getContext("2d"); ctx.drawImage(img, 0, 0);
      const p = P.Program.fromImageData(ctx.getImageData(0, 0, c.width, c.height));
      if (p.w > 160 || p.h > 160) { $("pg-hover").textContent = `大きすぎます（${p.w}×${p.h} コーデル）。160×160 までの画像を開けます。`; return; }
      setGrid(p.w, p.h, p.grid); URL.revokeObjectURL(url);
    };
    img.src = url;
  });
  fetch("samples.json").then(r => r.json()).then(list => {
    const sel = $("pg-sample");
    list.forEach((s, i) => {
      const o = document.createElement("option");
      o.value = i; o.textContent = `図 ${s.no}  ${s.caption.replace(/`/g, "")}`.slice(0, 80);
      sel.appendChild(o);
    });
    sel.addEventListener("change", () => {
      const s = list[+sel.value]; if (!s) return;
      if (!s.grid) { $("pg-hover").textContent = "この図は大きすぎるため開けません。"; return; }
      Promise.resolve(P.Program.fromText(s.grid)).then(p => {
        if (p.w > 160 || p.h > 160) { $("pg-hover").textContent = "この図は大きすぎるため開けません。"; return; }
        $("pg-input").value = s.input || ""; setGrid(p.w, p.h, p.grid);
        zoom = Math.max(6, Math.min(28, Math.floor(640 / p.w))); $("pg-zoom").value = zoom; draw();
      });
    });
  }).catch(() => { });

  // ---------------------------------------------------------------- 開始
  if (!restore()) loadText(DEMO);
  updatePalette();
})();
