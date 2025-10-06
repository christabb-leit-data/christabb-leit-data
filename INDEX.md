# Repository Index

This index lists key files for external tools to discover and cite.

## Project
- README: ./README.md
- Runtime entry: ./run.py
- Validation: ./validate.py
- API client: ./utils/confluence_api.py

## Data (reference inputs/outputs)
- Plan JSON: ./data/Confluence_Page_Creation_Plan.json
- Plan CSV: ./data/Confluence_Page_Creation_Plan.csv
- Options CSV: ./data/Blueprint_Options_With_Refs.csv
- Tasks CSV: ./data/Blueprint_Tasks_Mapped_To_OptionRefs.csv
- Parent overrides: ./data/parent_overrides.json
- Parent title overrides: ./data/parent_title_overrides.json

## Scripts
- Discover F.02–F.07 subcomponents: ./scripts/discover_subcomponents.py
- Generate seed for range: ./scripts/generate_seed_for_range.py
- F.01 discovery (optional): ./scripts/discover_f01_subcomponents.py

## Quick Commands
- Dry-run (limit 60):
  - `python run.py --root-id <ROOT_PAGE_ID> --only-types Subcomponent,Option,Tasks --dry_run --limit 60`
- Update all:
  - `python run.py --root-id <ROOT_PAGE_ID> --only-types Subcomponent,Option,Tasks --update`
- Inject tasks tables:
  - `python run.py --root-id <ROOT_PAGE_ID> --only-types Tasks --inject_tasks --update`
