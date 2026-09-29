# Karma — DIN fastener product data

- `data/raw/` — source workbooks (DIN part 1–3, one sheet per standard, by sales priority)
- `scripts/extract_skus.py` — builds the unique size-level SKU list from the source tables
- `output/DIN_SKU_list.xlsx` — result: `راهنما` (guide), `SKUs`, `Review`, `Standards`

```
pip install openpyxl
python3 scripts/extract_skus.py
```
