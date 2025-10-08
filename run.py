import os, json, argparse, html
import pandas as pd
from dotenv import load_dotenv
from utils.confluence_api import ConfluenceAPI

REQ_PLAN_COLS = ["Parent Page","Page Title","Page Type","Code / Ref","Description / Notes","Complexity","Mode Applicability","Validation / Cleanup Flag","Labels","Recommended Action"]

def esc(s): return html.escape(str(s) if s is not None else "")

def render_tasks_table(tasks_df: pd.DataFrame, option_ref: str) -> str:
    preferred = ["Task ID","Task Title","Task Description","Complexity","Primary Role","Notes"]
    # Handle both "OptionRef" and "Option Ref" column names
    option_col = "OptionRef" if "OptionRef" in tasks_df.columns else "Option Ref"
    df = tasks_df[tasks_df[option_col] == option_ref].copy()
    if df.empty:
        return f"<p><em>No tasks found for OptionRef {esc(option_ref)}.</em></p>"
    # Derive columns dynamically from what's actually in the CSV
    cols = [c for c in preferred if c in df.columns] or preferred
    # Backfill any missing preferred columns
    for c in preferred:
        if c not in df.columns:
            df[c] = ""
    th = "".join(f"<th>{esc(c)}</th>" for c in cols)
    trs = []
    for _, r in df.iterrows():
        tds = "".join(f"<td>{esc(r.get(c,''))}</td>" for c in cols)
        trs.append(f"<tr>{tds}</tr>")
    return f"""<table>
  <colgroup>
    <col/> <col/> <col style="width:40%"/> <col/> <col/> <col/> <col/> <col/> <col/>
  </colgroup>
  <tbody>
    <tr>{th}</tr>
    {''.join(trs)}
  </tbody>
</table>"""

def build_body(row, tasks_df: pd.DataFrame = None):
    page_type = row.get("Page Type","")
    desc = row.get("Description / Notes","")
    complexity = row.get("Complexity","")
    modes = row.get("Mode Applicability","")
    flag = row.get("Validation / Cleanup Flag","")
    code = row.get("Code / Ref","")

    if page_type == "Subcomponent":
        body = f"""
<h2>Overview</h2>
<p>{esc(desc)}</p>
<h3>Options</h3>
<p>Child pages list the implementation options for this subcomponent.</p>
"""
    elif page_type == "Option":
        body = f"""
<h2>Option Overview</h2>
<p>{esc(desc)}</p>
<table>
  <tr><th>Option Ref</th><td>{esc(code)}</td></tr>
  <tr><th>Complexity</th><td>{esc(complexity)}</td></tr>
  <tr><th>Mode Applicability</th><td>{esc(modes)}</td></tr>
  <tr><th>Validation / Cleanup</th><td>{esc(flag)}</td></tr>
</table>
<p>See child page <strong>Tasks – {esc(code)}</strong> for task breakdown.</p>
"""
    else:
        if tasks_df is not None and not tasks_df.empty:
            tasks_html = render_tasks_table(tasks_df, code)
            body = f"""
<h2>Tasks for {esc(code)}</h2>
<p>{esc(desc)}</p>
{tasks_html}
"""
        else:
            body = f"""
<h2>Tasks for {esc(code)}</h2>
<p>{esc(desc)}</p>
<table>
  <tr>
    <th>Task</th><th>Role</th><th>Complexity</th><th>MVP</th><th>Production</th><th>Enterprise</th>
  </tr>
  <tr><td colspan="6"><em>Populate from 'Blueprint_Tasks_Mapped_To_OptionRefs.csv' filtered by OptionRef = {esc(code)}.</em></td></tr>
</table>
"""
    return body

def main():
    load_dotenv()
    p = argparse.ArgumentParser(description="Create/Update Confluence pages with optional Tasks injection.")
    p.add_argument("--plan", default="data/Confluence_Page_Creation_Plan.json")
    p.add_argument("--tasks", default="data/Blueprint_Tasks_Mapped_To_OptionRefs.csv")
    p.add_argument("--space", default=os.getenv("CONFLUENCE_SPACE_KEY","LDPB"))
    p.add_argument("--root", default=os.getenv("CONFLUENCE_ROOT_PARENT","LEIT Data Platform Blueprint"))
    p.add_argument("--root-id", default="", help="Explicit Confluence page ID for root parent")
    p.add_argument("--dry_run", action="store_true")
    p.add_argument("--update", action="store_true")
    p.add_argument("--only-types", default="", help="Comma list: Subcomponent,Option,Tasks")
    p.add_argument("--limit", type=int, default=0)
    p.add_argument("--inject_tasks", action="store_true", help="Inject tasks table into Tasks pages from CSV")
    args = p.parse_args()

    api = ConfluenceAPI(
        base_url=os.getenv("CONFLUENCE_BASE_URL","").strip(),
        email=os.getenv("CONFLUENCE_EMAIL","").strip(),
        api_token=os.getenv("CONFLUENCE_API_TOKEN","").strip(),
        space_key=args.space.strip()
    )

    with open(args.plan) as f:
        rows = json.load(f)
    tasks_df = pd.read_csv(args.tasks) if args.inject_tasks and os.path.exists(args.tasks) else pd.DataFrame()

    only_types = [t.strip() for t in args.only_types.split(",") if t.strip()]
    if only_types:
        rows = [r for r in rows if r.get("Page Type") in only_types]

    order_map = {"Subcomponent":0,"Option":1,"Tasks":2}
    rows.sort(key=lambda r: order_map.get(r.get("Page Type"), 99))

    def resolve_parent_id(parent_title):
        if args.root_id and (not parent_title or parent_title == args.root):
            return args.root_id
        p = api.find_page_by_title(parent_title) or api.find_page_relaxed(parent_title)
        if p: return p["id"]
        if args.root_id: return args.root_id
        root = api.find_page_by_title(args.root) or api.find_page_relaxed(args.root)
        return root["id"] if root else None

    created = updated = skipped = 0
    for i, row in enumerate(rows, 1):
        if args.limit and i > args.limit:
            break
        title = (row.get("Page Title") or "").strip()
        parent_title = (row.get("Parent Page") or "").strip()
        labels = [l.strip() for l in (row.get("Labels","") or "").split(";") if l.strip()]
        if not title: continue

        existing = api.find_page_by_title(title) or api.find_page_relaxed(title)
        body_html = build_body(row, tasks_df if args.inject_tasks else pd.DataFrame())

        if existing:
            if args.update:
                if args.dry_run:
                    print(f"[DRY][UPDATE] {title}")
                else:
                    api.update_page_body(existing["id"], title, body_html)
                    if labels: api.set_labels(existing["id"], labels)
                updated += 1
            else:
                skipped += 1
            continue

        parent_id = resolve_parent_id(parent_title)
        if args.dry_run:
            print(f"[DRY][CREATE] '{title}' under '{parent_title}' (parent_id={parent_id})")
            continue
        api.create_page(title, body_html, parent_id=parent_id, labels=labels)
        created += 1

    print(f"Done. Created={created} Updated={updated} Skipped={skipped}")

if __name__ == "__main__":
    main()
