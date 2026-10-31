# Karma prototype — source

Recovered on 1405-08 from the installed Google Sheets build (1.4.0) after the work container was reset.

- `src/app.html` — the whole app (sales, accounting, catalogue, IAM, search). Runs against the
  Apps Script server when opened by `Code.gs`; opened on its own (no `google.script.run`) it runs
  offline with the built-in sample data, which is what the standalone prototype is.
- `src/loader.html` — the loading page served by `doGet()`; it fetches `app.html` in pieces.
- `src/img/` — product photos, drawings and banners referenced by file name (`KSU({...})`).
- `gas/` — server (`Code.gs`), manifest and the Persian install guide.
- `tools/` — build, package and test scripts.

## Build and test

From `prototype/tools` (needs Node with Playwright and Python 3):

| Command | What it does |
|---|---|
| `python3 build.py` | builds `dist/Karma-prototype.html` (one file, images inside) and `dist/Karma-GoogleSheets-v<ver>.zip` |
| `node e2e_gas.js` | installs the built bundle on a simulated Apps Script runtime (`mock.js`) and drives the app against it |
| `node smoke_all.js ../src/app.html` | every staff user opens every page in their menu |
| `node t_r8.js ../src/app.html` | quote numbers on send, follow-up box, archive, admin-only delete, header position |
| `node t_work.js ../src/app.html` | workspace: assign, complete with a note, visibility by role, settings |
| `node gold.js ../src/app.html` | smart-search test set |
| `python3 astm_r8.py app.html` | one-off: rebuilt the ASTM section from the owner's workbook (already applied) |

`dist/` is not committed.
