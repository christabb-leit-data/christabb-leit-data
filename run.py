import os, json, argparse, html
import pandas as pd
from dotenv import load_dotenv
from utils.confluence_api import ConfluenceAPI

REQ_PLAN_COLS = ["Parent Page","Page Title","Page Type","Code / Ref","Description / Notes","Complexity","Mode Applicability","Validation / Cleanup Flag","Labels","Recommended Action"]

HEADER_ALIASES = {
    "Task ID": "ID",
    "Task Title": "Title",
    "Task Description": "Description",
    "Primary Role": "Role",
    "Client Dependencies": "Client Deps",
    "Acceptance Criteria": "Acceptance",
    "Predecessors": "Pre-reqs",
}

DROP_COLS = {
    "Orchestration Integration",
    "Monitoring & Alerting",
    "Schedule / Frequency",
}

WIDTHS = {  # percentage hints; Confluence will respect colgroup without inline CSS
    "Task ID": 8,
    "Task Title": 18,
    "Task Description": 34,
    "Primary Role": 8,
    "Complexity": 6,
    "Predecessors": 8,
    "Client Dependencies": 10,
    "Deliverables": 8,
    "Acceptance Criteria": 10,
}

def _esc(s) -> str:
    return html.escape("" if s is None else str(s))

def _complexity_code(val: str) -> str:
    """Normalize complexity to codes: L, M, H (fallback to original)."""
    m = (val or "").strip().lower()
    return {
        "low": "L", "l": "L",
        "medium": "M", "m": "M",
        "high": "H", "h": "H",
    }.get(m, (val or "").strip())

def esc(s): return _esc(s)

def _as_storage_html(value: str) -> str:
    """
    Accepts plain text, markdown-ish, or HTML.
    If it *looks* like HTML (starts with '<'), pass through.
    Otherwise, wrap lines in <p> and bullets into <ul>/<li> so it renders nicely.
    Returns XHTML suitable for Confluence 'storage' representation.
    """
    txt = (value or "").strip()
    if txt.startswith("<"):  # treat as HTML already
        return txt
    # very small markdown-to-HTML for bullets/headings
    lines = [l.rstrip() for l in txt.splitlines() if l.strip() != ""]
    out = []
    in_ul = False
    for line in lines:
        if line.lstrip().startswith(("-", "*")):
            if not in_ul:
                out.append("<ul>")
                in_ul = True
            out.append(f"<li>{html.escape(line.lstrip('-* ').strip())}</li>")
        else:
            if in_ul:
                out.append("</ul>")
                in_ul = False
            out.append(f"<p>{html.escape(line)}</p>")
    if in_ul:
        out.append("</ul>")
    return "".join(out)

def render_tasks_table(tasks_df: pd.DataFrame, option_ref: str) -> str:
    df = tasks_df[tasks_df.get("OptionRef") == option_ref].copy()
    if df.empty:
        return f"<p><em>No tasks found for OptionRef {html.escape(option_ref)}.</em></p>"

    preferred = [
        "Task ID","Task Title","Task Description","Complexity","Primary Role","Notes",
        "Predecessors","Client Dependencies","Deliverables","Acceptance Criteria",
        # legacy/optional columns (kept only if present and not in DROP_COLS)
        "MVP","Production","Enterprise",
    ]
    cols = [c for c in preferred if c in df.columns and c not in DROP_COLS]
    df = df[cols].replace({pd.NA: "", None: ""}).fillna("")

    # Build colgroup with width hints for present columns
    colgroup = "<colgroup>" + "".join(
        f'<col width="{WIDTHS.get(c, 8)}%"/>'
        for c in df.columns
    ) + "</colgroup>"

    # Header row with short labels
    thead = "".join(
        f"<th>{_esc(HEADER_ALIASES.get(c, c))}</th>"
        for c in df.columns
    )

    # Body
    trs = []
    for _, r in df.iterrows():
        tds = []
        for c in df.columns:
            v = r[c]
            if c == "Complexity":
                code = _complexity_code(v)
                long = {"L":"Low","M":"Medium","H":"High"}.get(code, str(v or ""))
                tds.append(f'<td><span title="{_esc(long)}">{_esc(code)}</span></td>')
            else:
                tds.append(f"<td>{_esc(v)}</td>")
        trs.append("<tr>" + "".join(tds) + "</tr>")

    # No inline styles; pure storage HTML
    return (
        "<table>"
        f"{colgroup}"
        f"<thead><tr>{thead}</tr></thead>"
        f"<tbody>{''.join(trs)}</tbody>"
        "</table>"
    )

def build_body(row, tasks_df: pd.DataFrame = None):
    page_type = row.get("Page Type","")
    desc = _as_storage_html(row.get("Description / Notes",""))
    complexity = row.get("Complexity","")
    modes = row.get("Mode Applicability","")
    flag = row.get("Validation / Cleanup Flag","")
    code = row.get("Code / Ref","")

    if page_type == "Subcomponent":
        body = f"""
<h2>Overview</h2>
{desc}
<h3>Options</h3>
<p>Child pages list the implementation options for this subcomponent.</p>
"""
    elif page_type == "Option":
        # Format complexity with code tags
        complexity_formatted = f"<code>{_complexity_code(complexity)}</code>"
        
        body = f"""
<h2>Option Overview</h2>
<div style="margin-bottom: 15px;">
  <div style="font-size: 12px; line-height: 1.4; margin-bottom: 10px;">{desc}</div>
</div>

<table class="confluenceTable" style="width: 100%; margin-bottom: 15px; font-size: 11px;">
  <colgroup>
    <col style="width: 25%;"/>
    <col style="width: 75%;"/>
  </colgroup>
  <tbody>
    <tr>
      <th style="background-color: #f8f9fa; font-size: 10px; font-weight: bold; padding: 6px; border: 1px solid #ddd;">Option Ref</th>
      <td style="font-size: 10px; padding: 6px; border: 1px solid #ddd;"><code>{esc(code)}</code></td>
    </tr>
    <tr>
      <th style="background-color: #f8f9fa; font-size: 10px; font-weight: bold; padding: 6px; border: 1px solid #ddd;">Complexity</th>
      <td style="font-size: 10px; padding: 6px; border: 1px solid #ddd;">{complexity_formatted}</td>
    </tr>
    <tr>
      <th style="background-color: #f8f9fa; font-size: 10px; font-weight: bold; padding: 6px; border: 1px solid #ddd;">Mode Applicability</th>
      <td style="font-size: 10px; padding: 6px; border: 1px solid #ddd;">{esc(modes)}</td>
    </tr>
    <tr>
      <th style="background-color: #f8f9fa; font-size: 10px; font-weight: bold; padding: 6px; border: 1px solid #ddd;">Validation / Cleanup</th>
      <td style="font-size: 10px; padding: 6px; border: 1px solid #ddd;">{esc(flag)}</td>
    </tr>
  </tbody>
</table>

<div style="background-color: #e3f2fd; border-left: 4px solid #2196f3; padding: 8px; margin-top: 15px;">
  <p style="font-size: 11px; margin: 0; color: #1565c0;">
    <strong>Next Steps:</strong> See child page <strong>Tasks – {esc(code)}</strong> for detailed task breakdown and implementation guidance.
  </p>
</div>
"""
    else:
        if tasks_df is not None and not tasks_df.empty:
            tasks_html = render_tasks_table(tasks_df, code)
            body = f"""
<h2>Tasks for {esc(code)}</h2>
<div style="margin-bottom: 15px;">
  <p style="font-size: 12px; line-height: 1.4; margin-bottom: 10px;">{esc(desc)}</p>
</div>
{tasks_html}
"""
        else:
            body = f"""
<h2>Tasks for {esc(code)}</h2>
<div style="margin-bottom: 15px;">
  <p style="font-size: 12px; line-height: 1.4; margin-bottom: 10px;">{esc(desc)}</p>
</div>
<table class="confluenceTable" style="width: 100%; font-size: 11px;">
  <thead>
    <tr>
      <th style="background-color: #f8f9fa; font-size: 10px; font-weight: bold; padding: 6px; border: 1px solid #ddd;">Task</th>
      <th style="background-color: #f8f9fa; font-size: 10px; font-weight: bold; padding: 6px; border: 1px solid #ddd;">Role</th>
      <th style="background-color: #f8f9fa; font-size: 10px; font-weight: bold; padding: 6px; border: 1px solid #ddd;">Complexity</th>
      <th style="background-color: #f8f9fa; font-size: 10px; font-weight: bold; padding: 6px; border: 1px solid #ddd;">MVP</th>
      <th style="background-color: #f8f9fa; font-size: 10px; font-weight: bold; padding: 6px; border: 1px solid #ddd;">Production</th>
      <th style="background-color: #f8f9fa; font-size: 10px; font-weight: bold; padding: 6px; border: 1px solid #ddd;">Enterprise</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td colspan="6" style="font-size: 10px; padding: 8px; border: 1px solid #ddd; text-align: center; font-style: italic;">
        Populate from 'Blueprint_Tasks_Mapped_To_OptionRefs.csv' filtered by OptionRef = <code>{esc(code)}</code>.
      </td>
    </tr>
  </tbody>
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
