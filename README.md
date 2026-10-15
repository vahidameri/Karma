# Karma — DIN fastener product data

- `data/raw/` — source workbooks (DIN part 1–3, one sheet per standard, by sales priority)
- `scripts/extract_skus.py` — builds the unique size-level SKU list from the source tables
- `data/drawings/reyher/` — REYHER catalogue drawings (`images/`, `images_index.csv`, `articles_index.csv`)
- `scripts/drawings.py` — matches each parent (standard + form) to its drawing and embeds it
- `output/DIN_SKU_list.xlsx` — result: `راهنما` (guide), `Parents` (index, with `نقشه` drawing column), `SKUs`, `Review`

```
pip install openpyxl pillow
python3 scripts/extract_skus.py
```
