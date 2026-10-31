# Karma prototype — source

Recovered on 1405-08 from the installed Google Sheets build (1.4.0) after the work container was reset.

- `src/app.html` — the whole app (sales, accounting, catalogue, IAM, search). Runs against the
  Apps Script server when opened by `Code.gs`; opened on its own (no `google.script.run`) it runs
  offline with the built-in sample data, which is what the standalone prototype is.
- `src/loader.html` — the loading page served by `doGet()`; it fetches `app.html` in pieces.
- `src/img/` — product photos, drawings and banners referenced by file name (`KSU({...})`).
- `gas/` — server (`Code.gs`), manifest and the Persian install guide.
- `tools/` — build, package and test scripts.
