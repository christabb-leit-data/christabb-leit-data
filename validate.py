import os, json, argparse, csv
from collections import Counter

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--plan', default='data/Confluence_Page_Creation_Plan.json')
    args = ap.parse_args()

    with open(args.plan) as f:
        rows = json.load(f)

    # Basic checks
    errors = []
    titles = Counter()
    parents = Counter()
    bad = []

    for r in rows:
        t = (r.get('Page Title') or '').strip()
        p = (r.get('Parent Page') or '').strip()
        k = (r.get('Page Type') or '').strip()
        if not t: bad.append(('Missing Title', r))
        titles[t] += 1
        parents[p] += 1

    print('=== Title Dupes (should generally be unique) ===')
    for t, c in titles.most_common():
        if c > 1:
            print(f'  {c}x: {t}')

    print('\n=== Parent Titles (ensure these exist in Confluence) ===')
    for p, c in parents.items():
        if p:
            print(f'  {c} children -> {p}')

    if bad:
        print('\n=== Rows with issues ===')
        for why, r in bad[:10]:
            print(why, r)

    print('\nCheck complete. If parent titles differ in Confluence, either:')
    print(' - bulk find/replace in the JSON to match, or')
    print(' - pass --root "LEIT Data Platform Blueprint" to run.py for fallback.')

if __name__ == '__main__':
    main()
