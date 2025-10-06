[See INDEX.md for a concise entry-point to all files.](./INDEX.md)


# F.02–F.07 Discovery + Seed Generator

This package discovers **subcomponents** for components F.02..F.07 from your Confluence space,
then builds aligned metadata files (Plan JSON/CSV, Options CSV, Tasks CSV) — ready for your importer
and the Tasks injection runner.

## 0) Prereqs
- `.env` with CONFLUENCE_* vars (same as your importer)
- Space key (e.g., LDPB)

## 1) Discover subcomponents (pulls exact titles from Confluence)

```bash
cd confluence_import_aligned
# Optionally create a small JSON for parent overrides (page IDs) if titles vary:
# data/parent_overrides.json:
# { "F.02 – Orchestration": {"id": "123"}, "F.03 – Transformation": {"id":"456"} }

python scripts/discover_subcomponents.py --out data/components_F02_F07_subcomponents.json --parent-overrides data/parent_overrides.json
```

This writes `data/components_F02_F07_subcomponents.json` like:
```json
[
  {"component":"F.02","component_title":"F.02 – Orchestration","subcomponents":[{"code":"F.02.1","title":"F.02.1 – ..."}]},
  ...
]
```

## 2) Generate reference metadata (Options/Tasks scaffolds)

```bash
python scripts/generate_seed_for_range.py --discovered data/components_F02_F07_subcomponents.json --out-dir data
```

This writes:
- `data/Confluence_Page_Creation_Plan.json`
- `data/Confluence_Page_Creation_Plan.csv`
- `data/Blueprint_Options_With_Refs.csv`
- `data/Blueprint_Tasks_Mapped_To_OptionRefs.csv`

> Options & tasks are **reference defaults** per component (A/B/C pattern). Review and adjust to match your blueprint specifics after import.

## 3) Import pages and inject tasks

```bash
# validate + dry-run
python validate.py
python run.py --root-id <ROOT_PAGE_ID> --only-types Subcomponent,Option,Tasks --dry-run --limit 60

# create/update pages
python run.py --root-id <ROOT_PAGE_ID> --only-types Subcomponent,Option,Tasks --update

# inject task tables from CSV into the Tasks pages (if you installed the patch from earlier):
python run.py --root-id <ROOT_PAGE_ID> --only-types Tasks --inject-tasks --update
```

## Notes
- Titles use en-dash; the discovery script tolerates hyphen variants.
- If Confluence component titles differ (e.g., “F.04 – Storage & Compute” vs “Storage and Compute”), add their page IDs in `data/parent_overrides.json`.
- Edit the generated CSVs to replace reference defaults with **your exact options & tasks** where the blueprint defines them. Add info.
