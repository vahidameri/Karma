# Karma — DIN fastener product data

- `data/raw/` — source workbooks (DIN part 1–3, one sheet per standard, by sales priority)
- `scripts/extract_skus.py` — builds the unique size-level SKU list from the source tables
- `output/DIN_SKU_list.xlsx` — result: `راهنما` (guide), `Parents`, `SKUs`, `Review`

```
pip install openpyxl
python3 scripts/extract_skus.py
```

## Karma Platform 2.0 alpha

The executable rewrite is in [`platform/`](platform/README.fa.md). This is a development alpha; see its [delivery status](platform/docs/RELEASE-2.0.0-alpha.1.md) for implemented workflows and remaining work.
