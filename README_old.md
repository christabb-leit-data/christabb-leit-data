# Confluence Blueprint Import (Option 1B – Native REST API)

This toolkit creates the **Subcomponent → Option → Tasks** page hierarchy in **Confluence Cloud** using only the **native REST API** (no paid apps).

## What it does
- Reads `data/Confluence_Page_Creation_Plan.json` (already generated from your model).
- Creates pages under the **LDPB** space using the **Parent Page** and **Page Title** fields.
- Applies labels and writes a minimal, structured body based on your plan:
  - **Subcomponent** pages: overview shell
  - **Option** pages: summary (complexity, applicability, notes, validation flags)
  - **Tasks** pages: a ready-to-fill table shell for tasks of that option

## Quick Start (Cursor IDE)

1) **Copy the folder** `confluence_import/` into your Cursor workspace.
2) In a terminal:
```bash
cd confluence_import
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```
3) Edit `.env`:
```
CONFLUENCE_BASE_URL=https://leit-data.atlassian.net/wiki
CONFLUENCE_EMAIL=your_email@leit-data.com
CONFLUENCE_API_TOKEN=your_api_token_here
CONFLUENCE_SPACE_KEY=LDPB
CONFLUENCE_ROOT_PARENT=LEIT Data Platform Blueprint
```
4) Dry-run first:
```bash
python run.py --dry-run --limit 20
```
5) Create pages for real:
```bash
python run.py
```

### Useful flags
- `--root "LEIT Data Platform Blueprint"`: fallback parent when a listed parent title isn’t found
- `--space LDPB`: override space key
- `--update`: update body/labels if page already exists
- `--only-types Option,Tasks`: limit creation to certain page types
- `--limit 50`: process first N rows for a quick test

## Notes
- The script first **looks for the exact parent page title** in the space. If not found, it **falls back** to the `--root` page.
- If a page with the same title already exists in the space, the script **skips** creating a duplicate (unless `--update` is set).
- You can safely re-run to fill gaps or after correcting titles.


---

## 🔎 Validate alignment to Confluence structure

1) Inspect parent titles expected by the plan:
```bash
python validate.py
```
Ensure pages like **LEIT Data Platform Blueprint**, **F.01 – Ingest**, and each **F.xx.y – <Subcomponent>**
already exist (or set `--root` to a guaranteed parent).

2) If needed, adjust *Parent Page* titles in `data/Confluence_Page_Creation_Plan.json`
   or set a fallback with:
```bash
python run.py --root "LEIT Data Platform Blueprint" --dry-run --limit 20
```

3) When dry-run looks good, run without `--dry-run` to create pages.
