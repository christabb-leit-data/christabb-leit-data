import os, json, argparse, requests
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from utils.confluence_api import ConfluenceAPI


def list_child_pages(session: requests.Session, base_url: str, parent_id: str) -> List[Dict[str, Any]]:
    """List all child pages under a parent page ID."""
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


def find_component_pages(api: ConfluenceAPI, component_patterns: List[str]) -> Dict[str, Dict[str, Any]]:
    """Find component pages by title patterns."""
    components = {}
    for pattern in component_patterns:
        # Try exact match first
        page = api.find_page_by_title(pattern)
        if page:
            components[pattern] = page
            continue
        
        # Try with different dash variations
        variations = [
            pattern.replace(' – ', ' - '),
            pattern.replace(' - ', ' – '),
            pattern.replace(' – ', ' - ').replace('F.', 'F.0'),
            pattern.replace(' - ', ' – ').replace('F.', 'F.0')
        ]
        
        for variation in variations:
            if variation != pattern:
                page = api.find_page_by_title(variation)
                if page:
                    components[pattern] = page
                    break
    
    return components


def main():
    load_dotenv()
    ap = argparse.ArgumentParser(description="Discover subcomponents for F.02-F.07 components")
    ap.add_argument('--out', default='data/components_F02_F07_subcomponents.json', 
                   help='Output file for discovered subcomponents')
    ap.add_argument('--parent-overrides', default='data/parent_overrides.json',
                   help='JSON file with parent page ID overrides')
    args = ap.parse_args()

    base_url = (os.getenv('CONFLUENCE_BASE_URL') or '').rstrip('/')
    email = os.getenv('CONFLUENCE_EMAIL') or ''
    token = os.getenv('CONFLUENCE_API_TOKEN') or ''
    space_key = os.getenv('CONFLUENCE_SPACE_KEY', 'LDPB')

    if not base_url or not email or not token:
        raise SystemExit('Missing CONFLUENCE_BASE_URL, CONFLUENCE_EMAIL, or CONFLUENCE_API_TOKEN in .env')

    api = ConfluenceAPI(base_url=base_url, email=email, api_token=token, space_key=space_key)

    # Load parent overrides if available
    parent_overrides = {}
    if args.parent_overrides and os.path.isfile(args.parent_overrides):
        try:
            with open(args.parent_overrides) as f:
                parent_overrides = json.load(f)
        except Exception as e:
            print(f"Warning: Could not load parent overrides: {e}")

    # Component patterns to discover
    component_patterns = [
        "F.02 – Data Processing and Transformation",
        "F.03 – Data Quality and Governance", 
        "F.04 – Storage and Compute",
        "F.05 – Data Modelling and Data Model Management",
        "F.06 – Analytics and Reporting",
        "F.07 – Data Security and Privacy"
    ]

    # Find component pages
    components = find_component_pages(api, component_patterns)
    
    all_subcomponents = []
    
    for pattern, component_page in components.items():
        print(f"Processing {pattern}...")
        
        # Use override ID if available, otherwise use discovered page ID
        parent_id = parent_overrides.get(pattern, {}).get('id', component_page['id'])
        parent_title = component_page.get('title', pattern)
        
        # Get child pages
        children = list_child_pages(api.session, api.base_url, parent_id)
        
        for child in children:
            title = (child.get('title') or '').strip()
            if not title:
                continue
                
            all_subcomponents.append({
                'component_pattern': pattern,
                'component_title': parent_title,
                'component_id': parent_id,
                'subcomponent_title': title,
                'subcomponent_id': child.get('id', ''),
                'subcomponent_code': title.split(' ')[0] if ' ' in title else title
            })
    
    # Sort by component and subcomponent code
    all_subcomponents.sort(key=lambda x: (x['component_pattern'], x['subcomponent_code']))
    
    # Write output
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, 'w') as f:
        json.dump(all_subcomponents, f, indent=2)
    
    print(f"Discovered {len(all_subcomponents)} subcomponents across {len(components)} components")
    print(f"Output written to {args.out}")
    
    # Print summary
    for pattern in component_patterns:
        count = len([s for s in all_subcomponents if s['component_pattern'] == pattern])
        status = "✓" if pattern in components else "✗"
        print(f"  {status} {pattern}: {count} subcomponents")


if __name__ == '__main__':
    main()