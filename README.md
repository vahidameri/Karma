# Karma — DIN fastener product data

- `data/raw/` — source workbooks (DIN part 1–3, one sheet per standard, by sales priority)
- `scripts/extract_skus.py` — builds the unique size-level SKU list from the source tables
- `scripts/parse_mechtool.py` — parses cached mechtool.cn GB/T pages into length x weight matrices (`data/external/mechtool/`)
- `data/din_to_gb.csv` — DIN → ISO → GB/T equivalents used to fill missing lengths and weights
- `output/DIN_SKU_list.xlsx` — result: `راهنما` (guide), `SKUs`, `Review`, `Standards`

```
pip install openpyxl
python3 scripts/extract_skus.py
```
