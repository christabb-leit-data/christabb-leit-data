import os, json, argparse
from typing import List, Dict, Any, Optional
import requests
from dotenv import load_dotenv
from utils.confluence_api import ConfluenceAPI


def list_child_pages(session: requests.Session, base_url: str, parent_id: str) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    start = 0
    limit = 100
    while True:
        url = f"{base_url}/rest/api/content/{parent_id}/child/page?start={start}&limit={limit}"
        r = session.get(url, timeout=30)
        r.raise_for_status()
        data = r.json()
        values = data.get('results', [])
        for v in values:
            results.append(v)
        if data.get('_links', {}).get('next'):
            start += limit
            continue
        break
    return results


def main():
    load_dotenv()
    ap = argparse.ArgumentParser(description="Discover Subcomponent pages under F.01 – Ingest and write plan JSON")
    ap.add_argument('--parent-id', default='', help='Parent page ID for F.01 – Ingest')
    ap.add_argument('--parent-title', default='', help='Parent page title if ID not known (e.g., F.01 – Ingest)')
    ap.add_argument('--output', default='data/Confluence_Page_Creation_Plan.json', help='Path to write plan JSON')
    args = ap.parse_args()

    base_url = (os.getenv('CONFLUENCE_BASE_URL') or '').rstrip('/')
    email = os.getenv('CONFLUENCE_EMAIL') or ''
    token = os.getenv('CONFLUENCE_API_TOKEN') or ''
    space_key = os.getenv('CONFLUENCE_SPACE_KEY', 'LDPB')

    if not base_url or not email or not token:
        raise SystemExit('Missing CONFLUENCE_BASE_URL, CONFLUENCE_EMAIL, or CONFLUENCE_API_TOKEN in .env')

    api = ConfluenceAPI(base_url=base_url, email=email, api_token=token, space_key=space_key)

    parent_title: Optional[str] = None
    parent_id = (args.parent_id or '').strip()
    if not parent_id:
        title = (args.parent_title or '').strip()
        if not title:
            raise SystemExit('Provide --parent-id or --parent-title')
        parent = api.find_page_by_title(title)
        if not parent:
            raise SystemExit(f"Parent title not found in space: {title}")
        parent_id = parent['id']
        parent_title = parent.get('title') or title
    else:
        # Resolve title for readability
        p = api.session.get(f"{api.base_url}/rest/api/content/{parent_id}")
        try:
            p.raise_for_status()
            parent_title = p.json().get('title')
        except Exception:
            parent_title = args.parent_title or ''

    children = list_child_pages(api.session, api.base_url, parent_id)

    plan_rows: List[Dict[str, Any]] = []
    for child in children:
        title = (child.get('title') or '').strip()
        if not title:
            continue
        plan_rows.append({
            'Page Title': title,
            'Parent Page': parent_title or '',
            'Page Type': 'Subcomponent',
            'Labels': 'blueprint;subcomponent',
            'Description / Notes': '',
            'Complexity': '',
            'Mode Applicability': '',
            'Validation / Cleanup Flag': '',
            'Code / Ref': ''
        })

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, 'w') as f:
        json.dump(plan_rows, f, indent=2)

    print(f"Wrote {len(plan_rows)} Subcomponent rows to {args.output}")


if __name__ == '__main__':
    main()
