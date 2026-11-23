/**
 * CHERRY AIR FLT# ALLOCATOR — v6.1 (multi-editor: hub managers have write access)
 * Install: Extensions → Apps Script → paste this file → Save → run setup() ONCE as the
 * sheet owner (authorize when prompted). setup() installs the edit trigger (runs with
 * OWNER authority, so it can write cells hub managers cannot) and locks down:
 *   - FLT# columns (C) on all three sheets   - Ledger sheet
 *   - Registry / NextFree / ThruSeg          - Network Plan / Change Log
 * Hub managers keep full write on pairing columns, notes, and the lookup inputs.
 *
 * What it does:
 *  - Watches Flights!B (pairing), 'Thru Flights'!D:F (origin/stop/dest), HubFlights!B.
 *  - When a route appears and its FLT# cell is empty, assigns the lowest never-used
 *    even/odd pair in the correct hub block, writes it as a PERMANENT VALUE, and
 *    records both numbers in the Ledger sheet.
 *  - Numbers are never reissued (RECYCLE=false): deleting a route retires its numbers forever.
 *  - Multi-editor safe via LockService.
 *  - Menu: Cherry Air → "Allocate missing numbers" for bulk pastes/imports.
 */

const CFG = {
  RECYCLE: false, // true = deleted routes' numbers may be reissued (ledger ignored)
  SPOKE_LO: { KTVC: 100, KTEB: 300, KBJC: 500, KAFW: 700, KPDK: 900, KVGT: 1100, KLMT: 1300, KLUK: 1500 },
  BLOCK_W: 200,
  THRU_OFFSET: 3000,
  HUB_LO: 0, HUB_HI: 99,   // connectors: pairs 2/1 .. 98/97
  SHEETS: { FLIGHTS: 'Flights', THRU: 'Thru Flights', HUB: 'HubFlights', LEDGER: 'Ledger' },
};

function onOpen() {
  SpreadsheetApp.getUi().createMenu('Cherry Air')
    .addItem('Allocate missing numbers', 'allocateAllMissing')
    .addItem('Run setup (owner only, once)', 'setup')
    .addToUi();
}

function handleEdit(e) {
  if (!e || !e.range) return;
  const sh = e.range.getSheet(), name = sh.getName();
  const r1 = e.range.getRow(), r2 = r1 + e.range.getNumRows() - 1;
  if (r1 < 2) return;
  const touches = (c) => e.range.getColumn() <= c && c <= e.range.getLastColumn();

  if (name === CFG.SHEETS.FLIGHTS && touches(2)) allocateRows(sh, 'spoke', r1, r2);
  else if (name === CFG.SHEETS.THRU && (touches(4) || touches(5) || touches(6))) allocateRows(sh, 'thru', r1, r2);
  else if (name === CFG.SHEETS.HUB && touches(2)) allocateRows(sh, 'hub', r1, r2);
}

function allocateRows(sh, kind, r1, r2) {
  const lock = LockService.getScriptLock();
  lock.waitLock(20000); // serialize concurrent hub-manager edits
  try {
    const used = loadUsed();
    for (let r = r1; r <= r2; r++) {
      const numCell = sh.getRange(r, 3);
      if (numCell.getValue() !== '') continue; // numbers are permanent — never overwrite

      let origin = null;
      if (kind === 'spoke') {
        const pairing = String(sh.getRange(r, 2).getValue() || '').trim().toUpperCase();
        if (pairing.length < 9) continue;
        origin = pairing.slice(0, 4);
      } else if (kind === 'thru') {
        const o = String(sh.getRange(r, 4).getValue() || '').trim().toUpperCase();
        const s = String(sh.getRange(r, 5).getValue() || '').trim().toUpperCase();
        const d = String(sh.getRange(r, 6).getValue() || '').trim().toUpperCase();
        if (!(o && s && d)) continue; // wait until all three typed
        origin = o;
      } else {
        const pairing = String(sh.getRange(r, 2).getValue() || '').trim().toUpperCase();
        if (pairing.length < 9) continue;
      }

      let lo, hi;
      if (kind === 'hub') { lo = CFG.HUB_LO; hi = CFG.HUB_HI; }
      else {
        const base = CFG.SPOKE_LO[origin];
        if (base === undefined) { toast(`Unknown hub "${origin}" — no number assigned (row ${r})`); continue; }
        lo = kind === 'thru' ? base + CFG.THRU_OFFSET : base;
        hi = lo + CFG.BLOCK_W - 1;
      }

      let out = null;
      for (let cand = lo + 2; cand <= hi; cand += 2) {
        if (!used.has(cand) && !used.has(cand - 1)) { out = cand; break; }
      }
      if (out === null) { toast(`BLOCK FULL for ${origin || 'hub connectors'} (row ${r})`); continue; }

      numCell.setValue(out).setFontColor('#7030A0').setFontWeight('bold');
      recordLedger([out, out - 1]);
      used.add(out); used.add(out - 1);
      toast(`CHY${out}/${out - 1} assigned (row ${r})`);
    }
  } finally {
    lock.releaseLock();
  }
}

/** Union of Ledger (unless recycling) and all live FLT# cells (belt and braces). */
function loadUsed() {
  const ss = SpreadsheetApp.getActive();
  const used = new Set();
  if (!CFG.RECYCLE) {
    const lg = ss.getSheetByName(CFG.SHEETS.LEDGER);
    if (lg && lg.getLastRow() > 1)
      lg.getRange(2, 1, lg.getLastRow() - 1, 1).getValues().forEach(v => { if (v[0] !== '') used.add(Number(v[0])); });
  }
  [CFG.SHEETS.HUB, CFG.SHEETS.FLIGHTS, CFG.SHEETS.THRU].forEach(name => {
    const sh = ss.getSheetByName(name);
    if (!sh || sh.getLastRow() < 2) return;
    sh.getRange(2, 3, sh.getLastRow() - 1, 1).getValues().forEach(v => {
      const n = Number(v[0]);
      if (Number.isInteger(n) && n > 0) { used.add(n); used.add(n - 1); }
    });
  });
  return used;
}

function recordLedger(nums) {
  const ss = SpreadsheetApp.getActive();
  let lg = ss.getSheetByName(CFG.SHEETS.LEDGER);
  if (!lg) {
    lg = ss.insertSheet(CFG.SHEETS.LEDGER);
    lg.getRange(1, 1).setValue('EVER-ASSIGNED FLT #s — allocator memory. Do not edit.');
  }
  const start = lg.getLastRow() + 1;
  lg.getRange(start, 1, nums.length, 1).setValues(nums.map(n => [n]));
}

/** Bulk repair: assign numbers to every route row missing one (for pasted imports). */
function allocateAllMissing() {
  const ss = SpreadsheetApp.getActive();
  const jobs = [
    [ss.getSheetByName(CFG.SHEETS.HUB), 'hub'],
    [ss.getSheetByName(CFG.SHEETS.FLIGHTS), 'spoke'],
    [ss.getSheetByName(CFG.SHEETS.THRU), 'thru'],
  ];
  jobs.forEach(([sh, kind]) => { if (sh && sh.getLastRow() >= 2) allocateRows(sh, kind, 2, sh.getLastRow()); });
  toast('Allocation sweep complete.');
}

function toast(msg) { SpreadsheetApp.getActive().toast(msg, 'Cherry Air Allocator', 6); }


/** ONE-TIME, run as sheet owner: installable trigger + protections. Safe to re-run. */
function setup() {
  const ss = SpreadsheetApp.getActive();

  // 1) Installable edit trigger running as owner (remove stale copies first)
  ScriptApp.getProjectTriggers()
    .filter(t => t.getHandlerFunction() === 'handleEdit')
    .forEach(t => ScriptApp.deleteTrigger(t));
  ScriptApp.newTrigger('handleEdit').forSpreadsheet(ss).onEdit().create();

  // 2) Protect FLT# columns: hub managers type pairings, never numbers
  [CFG.SHEETS.HUB, CFG.SHEETS.FLIGHTS, CFG.SHEETS.THRU].forEach(name => {
    const sh = ss.getSheetByName(name);
    if (!sh) return;
    const p = sh.getRange('C2:C').protect().setDescription('FLT# — allocator only');
    p.removeEditors(p.getEditors());
  });

  // 3) Protect system sheets whole
  ['Ledger', 'Registry', 'NextFree', 'ThruSeg', 'Network Plan', 'Change Log'].forEach(name => {
    const sh = ss.getSheetByName(name);
    if (!sh) return;
    const p = sh.protect().setDescription(name + ' — system sheet');
    p.removeEditors(p.getEditors());
  });

  toast('Setup complete: trigger installed, system cells locked.');
}
