
# F.01 Alignment & OpenFlow Correction

## 1) Discover exact subcomponent titles from Confluence
```bash
cd confluence_import_aligned
python scripts/discover_f01_subcomponents.py --parent-id <F01_INGEST_PAGE_ID>
# or, if you don't know the id:
python scripts/discover_f01_subcomponents.py --parent-title "F.01 – Ingest"
```

## 2) Generate F.01 seed metadata (OpenFlow native CDC fix applied)
```bash
python scripts/generate_f01_seed.py
```

This writes:
- data/Confluence_Page_Creation_Plan.json (F.01 only)
- data/Confluence_Page_Creation_Plan.csv
- data/Blueprint_Options_With_Refs.csv
- data/Blueprint_Tasks_Mapped_To_OptionRefs.csv

## 3) Dry-run creation then apply
```bash
python validate.py
python run.py --root-id <ROOT_PAGE_ID> --only-types Subcomponent,Option,Tasks --dry-run --limit 30
python run.py --root-id <ROOT_PAGE_ID> --only-types Subcomponent,Option,Tasks --update
```
