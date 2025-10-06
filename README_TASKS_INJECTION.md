
# Tasks Injection Patch

Injects tasks tables from `data/Blueprint_Tasks_Mapped_To_OptionRefs.csv` into
each Tasks page (`Tasks – <OptionRef>`).

## Commands
```bash
cd confluence_import_aligned
python run.py --root-id <ROOT_PAGE_ID> --only-types Tasks --inject-tasks --dry-run --update
python run.py --root-id <ROOT_PAGE_ID> --only-types Tasks --inject-tasks --update
# Or re-render all, including Options/Subcomponents
python run.py --root-id <ROOT_PAGE_ID> --only-types Subcomponent,Option,Tasks --inject-tasks --update
```
