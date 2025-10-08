def adf_text(s: str): 
    return {"type":"text","text": s}

def adf_p(s: str):    
    return {"type":"paragraph","content":[adf_text(s)]}

def adf_th(text: str, width_px: int):
    # width hint must live on the HEADER cell
    return {
        "type":"tableHeader",
        "attrs":{"colspan":1,"rowspan":1,"colwidth":[int(width_px)]},
        "content":[adf_p(text)]
    }

def adf_td(text: str):
    return {"type":"tableCell","attrs":{"colspan":1,"rowspan":1},"content":[adf_p(text)]}

def build_tasks_table_adf(rows: list[dict]) -> dict:
    # Tune these numbers as you like — they are pixel hints
    # Confluence Cloud resizes columns based on header cell colwidth
    # If any column still squeezes, bump its header width px (e.g., Desc 460→520)
    headers = [
        ("ID",80), ("Title",190), ("Desc",520), ("CX",48),  # Increased Desc width for better readability
        ("Role",78), ("Dep",120), ("Client Deps",180), ("Deliverables",160), ("Acceptance",160),
    ]
    table = {"type":"table","attrs":{"isNumberColumnEnabled":False,"layout":"wide"},"content":[]}
    # header row with colwidth
    table["content"].append({
        "type":"tableRow",
        "content":[adf_th(h, w) for (h, w) in headers]
    })
    # data rows
    for r in rows:
        table["content"].append({
            "type":"tableRow",
            "content":[
                adf_td(r.get("ID","")), adf_td(r.get("Title","")), adf_td(r.get("Desc","")),
                adf_td(r.get("CX","")), adf_td(r.get("Role","")), adf_td(r.get("Dep","")),
                adf_td(r.get("Client Deps","")), adf_td(r.get("Deliverables","")), adf_td(r.get("Acceptance","")),
            ]
        })
    return table

def build_tasks_page_doc(option_ref: str, rows: list[dict]) -> dict:
    """
    Build ADF document for tasks page.
    
    Note: After publishing, flip the page to Full width once in Confluence UI 
    (page toolbar → Page width). That affects the canvas, while layout:"wide" 
    affects the table element itself.
    """
    return {
        "version": 1,
        "type": "doc",
        "content": [
            {"type":"paragraph","content":[adf_text(f"Legend: CX=L/M/H; Role=DE/SDE/SDA/PDA; Dep=Task IDs")]},
            build_tasks_table_adf(rows)
        ]
    }
