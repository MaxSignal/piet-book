// node tools/web/jstest.js cases.json  -- JS エンジンを Python 版の結果と照合
global.window = {}; global.document = { readyState: "complete", querySelectorAll: () => [] };
require("./piet.js");
const P = window.Piet, cases = JSON.parse(require("fs").readFileSync(process.argv[2], "utf8"));
let ok = 0, ng = 0;
for (const c of cases) {
  const m = new P.Machine(P.Program.fromText(c.text), c.input);
  let i = 0; while (i++ < c.steps + 10 && m.step()) { }
  if (m.out === c.out && m.steps === c.steps) ok++; else { ng++; console.log("NG", c.id, JSON.stringify(m.out.slice(0, 60)), JSON.stringify(c.out.slice(0, 60)), m.steps, c.steps); }
}
console.log(`js: ${ok} ok, ${ng} NG`);
