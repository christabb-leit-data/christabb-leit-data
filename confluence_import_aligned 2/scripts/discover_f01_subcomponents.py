import os, re, json, argparse
from dotenv import load_dotenv
from utils.confluence_api import ConfluenceAPI

def main():
    load_dotenv()
    ap = argparse.ArgumentParser(description="Discover F.01 subcomponents from Confluence.")
    ap.add_argument("--parent-id", default="", help="Page ID for 'F.01 – Ingest' (recommended).")
    ap.add_argument("--parent-title", default="F.01 – Ingest", help="Fallback if no ID is given.")
    ap.add_argument("--out", default="data/F01_subcomponents.json")
    ap.add_argument("--space", default=os.getenv("CONFLUENCE_SPACE_KEY","LDPB"))
    base = os.getenv("CONFLUENCE_BASE_URL","").strip()
    email = os.getenv("CONFLUENCE_EMAIL","").strip()
    token = os.getenv("CONFLUENCE_API_TOKEN","").strip()
    args = ap.parse_args()

    api = ConfluenceAPI(base, email, token, args.space)

    parent = None
    if args.parent_id:
        parent = api.find_page_by_id(args.parent_id)
    if not parent:
        parent = api.find_page_by_title(args.parent_title) or api.find_page_relaxed(args.parent_title)
    if not parent:
        raise SystemExit("Could not resolve 'F.01 – Ingest' parent. Provide --parent-id.")

    kids = api.list_children(parent["id"])
    pat = re.compile(r"^F\.01\.\d+\s+[–-]\s+.+")
    out = []
    for k in kids:
        title = k.get("title","")
        if pat.match(title):
            code = title.split(" ")[0]  # F.01.x
            out.append({"code": code, "title": title})

    out.sort(key=lambda r: r["code"])
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w") as f:
        json.dump(out, f, indent=2)
    print(f"Wrote {len(out)} subcomponents -> {args.out}")

if __name__ == "__main__":
    main()
