import requests
from bs4 import BeautifulSoup
from dateutil import parser
from datetime import datetime, timedelta
from urllib.parse import urljoin
from typing import List, Dict, Optional

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible)"}


def fetch_url(url: str) -> str:
    resp = requests.get(url, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    return resp.text


def parse_date(text: str) -> Optional[datetime]:
    try:
        return parser.parse(text)
    except Exception:
        return None


def _find_date_near(node) -> Optional[datetime]:
    # search inside node
    time_tag = node.find('time') if hasattr(node, 'find') else None
    if time_tag:
        if time_tag.has_attr('datetime'):
            d = parse_date(time_tag['datetime'])
        else:
            d = parse_date(time_tag.get_text(strip=True))
        if d:
            return d

    # search for common date spans
    for cls in ('date', 'posted', 'published', 'timestamp'):
        span = node.find(attrs={'class': lambda v: v and cls in v}) if hasattr(node, 'find') else None
        if span:
            d = parse_date(span.get_text(strip=True))
            if d:
                return d

    # search ancestors and immediate siblings
    for anc in getattr(node, 'parents', [])[:5]:
        time_tag = anc.find('time')
        if time_tag:
            if time_tag.has_attr('datetime'):
                d = parse_date(time_tag['datetime'])
            else:
                d = parse_date(time_tag.get_text(strip=True))
            if d:
                return d
    return None


def filter_recent(items: List[Dict], days: int = 7) -> List[Dict]:
    cutoff = (datetime.utcnow() - timedelta(days=days)).date()
    filtered: List[Dict] = []
    for it in items:
        dt = None
        try:
            dt = parser.parse(it['date'])
        except Exception:
            continue
        if dt.date() >= cutoff:
            filtered.append(it)
    return filtered


def fetch_techcommunity(days: int = 7) -> List[Dict]:
    url = 'https://techcommunity.microsoft.com/category/azure'
    html = fetch_url(url)
    soup = BeautifulSoup(html, 'html.parser')
    items: List[Dict] = []

    # Primary strategy: article-like containers
    candidates = soup.select('article, .node, .card, .search-result, .post, .listing')
    for c in candidates:
        a = c.find('a', href=True)
        if not a or not a.get_text(strip=True):
            continue
        title = a.get_text(strip=True)
        href = urljoin(url, a['href'])
        d = _find_date_near(c)
        if not d:
            # fallback: look for time near the anchor specifically
            d = _find_date_near(a)
        if d:
            items.append({'title': title, 'url': href, 'date': d.isoformat()})

    # Secondary strategy: anchors that look like TechCommunity threads
    if not items:
        for a in soup.find_all('a', href=True):
            href = a['href']
            if '/t5/' in href or '/community/' in href:
                title = a.get_text(strip=True)
                if not title:
                    continue
                d = _find_date_near(a)
                if d:
                    items.append({'title': title, 'url': urljoin(url, href), 'date': d.isoformat()})

    return filter_recent(items, days)


def fetch_azure_updates(days: int = 7) -> List[Dict]:
    url = 'https://azure.microsoft.com/en-us/updates/'
    html = fetch_url(url)
    soup = BeautifulSoup(html, 'html.parser')
    items: List[Dict] = []

    # Azure updates site commonly lists updates in list items or cards
    candidates = soup.select('article, li, .update, .update-item, .card')
    for c in candidates:
        a = c.find('a', href=True)
        if not a or not a.get_text(strip=True):
            continue
        title = a.get_text(strip=True)
        href = urljoin(url, a['href'])
        d = _find_date_near(c)
        if not d:
            d = _find_date_near(a)
        if d:
            items.append({'title': title, 'url': href, 'date': d.isoformat()})

    # Fallback: anchors that include '/updates/'
    if not items:
        for a in soup.find_all('a', href=True):
            href = a['href']
            if '/updates/' in href:
                title = a.get_text(strip=True)
                if not title:
                    continue
                d = _find_date_near(a)
                if d:
                    items.append({'title': title, 'url': urljoin(url, href), 'date': d.isoformat()})

    return filter_recent(items, days)
