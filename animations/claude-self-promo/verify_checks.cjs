// Runs the exact code shown in the film and the checks the film displays.
// Expected: the first version fails check 3, the fixed version passes all three.
// Usage: node verify_checks.cjs
const fs = require('fs');
const path = require('path');
const vm = require('vm');

const sandbox = { window: {} };
vm.runInNewContext(fs.readFileSync(path.join(__dirname, 'cues.js'), 'utf8'), sandbox);
const { CODE_BEFORE, CODE_AFTER } = sandbox.window.CUE;

const before = CODE_BEFORE.split('\n');
const after = CODE_AFTER.split('\n');
const diffs = before.map((l, i) => (l !== after[i] ? i : -1)).filter(i => i >= 0);
if (before.length !== after.length || diffs.length !== 1) {
  throw new Error(`BEFORE and AFTER must differ on exactly one line, got lines ${diffs}`);
}

function runChecks(code) {
  const { bars, layout } = new Function(code + '\nreturn { bars, layout };')();
  const L = layout(bars, 600);
  const tallest = bars.reduce((a, b) => (b.value > a.value ? b : a)).day;
  const last = L[L.length - 1];
  const right = last.x + last.w;
  return [
    { label: 'three bars', ok: L.length === 3, detail: `${L.length} bars` },
    { label: 'Tue is the tallest', ok: tallest === 'Tue', detail: `tallest: ${tallest}` },
    { label: 'last bar stays inside the chart', ok: right <= 600 + 1e-6, detail: `right edge ${Math.round(right)} px, chart is 600 px` },
  ];
}

const b = runChecks(CODE_BEFORE);
const a = runChecks(CODE_AFTER);
for (const [name, rows] of [['before', b], ['after', a]]) {
  console.log(`--- ${name}`);
  for (const r of rows) console.log(`${r.ok ? 'PASS' : 'FAIL'}  ${r.label}  (${r.detail})`);
}
const ok =
  b.map(r => r.ok).join() === 'true,true,false' && a.every(r => r.ok);
if (!ok) {
  console.error('unexpected check results');
  process.exit(1);
}
console.log('OK: first version fails one check, fixed version passes all three');
