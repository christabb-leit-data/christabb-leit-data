def adf_text(s: str):
    return {"type": "text", "text": s}

def adf_p(*texts: str):
    return {"type": "paragraph", "content": [adf_text(t) for t in texts if t]}

def adf_cell(*texts: str):
    return {"type": "tableCell", "attrs": {"colspan": 1, "rowspan": 1}, "content": [adf_p(*texts)]}

def adf_header(text: str):
    return {"type": "tableHeader", "attrs": {"colspan": 1, "rowspan": 1}, "content": [adf_p(text)]}

def _trim_text(text: str, max_length: int = 100) -> str:
    """Trim ultra-long text to reasonable length for better readability."""
    if not text or len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."

def build_tasks_table_adf(rows, compact=True):
    """
    rows: iterable of dicts with keys:
      ID, Title, Desc, CX, Role, Dep, Client Deps, Deliverables, Acceptance
    Returns ADF node for a compact, full-width table with trimmed text.
    """
    headers = ["ID","Title","Desc","CX","Role","Dep","Client Deps","Deliverables","Acceptance"]
    colwidth = [80,170,360,40,70,110,140,140,160]

    table = {
        "type": "table",
        "attrs": {"isNumberColumnEnabled": False, "layout": "full-width", "colwidth": colwidth},
        "content": []
    }
    # header row
    table["content"].append({
        "type": "tableRow",
        "content": [adf_header(h) for h in headers]
    })
    # data rows
    for r in rows:
        table["content"].append({
            "type": "tableRow",
            "content": [
                adf_cell(r.get("ID","")),
                adf_cell(_trim_text(r.get("Title",""), 80)),  # Trim long titles
                adf_cell(_trim_text(r.get("Desc",""), 150)),  # Trim long descriptions
                adf_cell(r.get("CX","")),              # Expect L/M/H
                adf_cell(r.get("Role","")),            # DE/SDE/SDA/PDA
                adf_cell(r.get("Dep","")),
                adf_cell(_trim_text(r.get("Client Deps",""), 80)),  # Trim client deps
                adf_cell(_trim_text(r.get("Deliverables",""), 100)),  # Keep deliverables concise
                adf_cell(_trim_text(r.get("Acceptance",""), 100)),  # Keep acceptance concise
            ]
        })
    return table

def build_tasks_page_doc(option_ref: str, rows: list[dict]):
    table = build_tasks_table_adf(rows, compact=True)
    return {
        "version": 1,
        "type": "doc",
        "content": [
            {"type":"paragraph","content":[adf_text(f"Tasks filtered by OptionRef={option_ref}.")]},
            {"type":"paragraph","content":[adf_text("Legend: CX=L/M/H; Role=DE/SDE/SDA/PDA; Dep=Task IDs")]},
            table
        ]
    }
