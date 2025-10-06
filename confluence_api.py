import requests, urllib.parse
from typing import Optional, Dict, Any, List

class ConfluenceAPI:
    def __init__(self, base_url: str, email: str, api_token: str, space_key: str):
        self.base_url = base_url.rstrip('/')
        self.email = email
        self.api_token = api_token
        self.space_key = space_key
        self.session = requests.Session()
        self.session.auth = (email, api_token)
        self.session.headers.update({'Content-Type': 'application/json'})
    
    def _url(self, path: str) -> str:
        return f"{self.base_url}{path}"

    def find_page_by_title(self, title: str) -> Optional[Dict[str, Any]]:
        if not title:
            return None
        url = self._url(f"/rest/api/content?spaceKey={self.space_key}&title={urllib.parse.quote(title)}&expand=ancestors,version")
        resp = self.session.get(url)
        resp.raise_for_status()
        data = resp.json()
        if data.get('size', 0) > 0:
            return data['results'][0]
        return None

    def find_page_by_id(self, page_id: str) -> Optional[Dict[str, Any]]:
        if not page_id:
            return None
        resp = self.session.get(self._url(f"/rest/api/content/{page_id}?expand=ancestors,version"))
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return resp.json()

    def find_page_relaxed(self, title: str) -> Optional[Dict[str, Any]]:
        t = (title or '').strip()
        if not t:
            return None
        variants = {t, t.replace('\\u2013','-'), t.replace('-','\\u2013'), ' '.join(t.split())}
        for v in variants:
            p = self.find_page_by_title(v)
            if p: return p
        cql = f'space="{self.space_key}" and type="page" and title ~ "{t}"'
        resp = self.session.get(self._url(f"/rest/api/content/search?cql={urllib.parse.quote(cql)}&limit=25&expand=version"))
        if resp.status_code == 200:
            hits = resp.json().get('results', [])
            for r in hits:
                if r.get('title','').lower() == t.lower():
                    return r
            return hits[0] if hits else None
        return None

    def create_page(self, title: str, body_html: str, parent_id: str = None, labels: list = None) -> Dict[str, Any]:
        payload = {
            "type": "page",
            "title": title,
            "space": {"key": self.space_key},
            "body": {"storage": {"value": body_html, "representation": "storage"}}
        }
        if parent_id:
            payload["ancestors"] = [{"id": parent_id}]
        resp = self.session.post(self._url("/rest/api/content"), json=payload)
        resp.raise_for_status()
        page = resp.json()
        if labels:
            self.set_labels(page['id'], labels)
        return page

    def update_page_body(self, page_id: str, title: str, body_html: str):
        r = self.session.get(self._url(f"/rest/api/content/{page_id}?expand=version"))
        r.raise_for_status()
        ver = r.json()['version']['number']
        payload = {
            "id": page_id,
            "type": "page",
            "title": title,
            "version": {"number": ver + 1},
            "body": {"storage": {"value": body_html, "representation": "storage"}}
        }
        resp = self.session.put(self._url(f"/rest/api/content/{page_id}"), json=payload)
        resp.raise_for_status()
        return resp.json()

    def set_labels(self, page_id: str, labels: list):
        items = [{"prefix": "global", "name": l} for l in (labels or []) if l]
        if not items: return
        resp = self.session.post(self._url(f"/rest/api/content/{page_id}/label"), json=items)
        try:
            resp.raise_for_status()
        except Exception:
            pass
