import requests
from bs4 import BeautifulSoup
from dateutil import parser
from datetime import datetime, timedelta
from urllib.parse import urljoin
from typing import List, Dict, Optional
import json
import re
import warnings

try:
    from bs4 import XMLParsedAsHTMLWarning
except Exception:  # pragma: no cover
    XMLParsedAsHTMLWarning = None

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible)"}


def fetch_url(url: str) -> str:
    resp = requests.get(url, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    return resp.text


def parse_date(text: str) -> Optional[datetime]:
    if not text:
        return None
    try:
        return parser.parse(text, fuzzy=True)
    except Exception:
        return None


def _parse_date_to_iso(text: str) -> Optional[str]:
    dt = parse_date(text)
    if not dt:
        return None
    # Keep consistent ISO strings and avoid timezone/naive compare issues later.
    try:
        if dt.tzinfo:
            dt = dt.astimezone().replace(tzinfo=None)
    except Exception:
        pass
    return dt.isoformat()


def _looks_like_azure_update_url(href: str) -> bool:
    if not href:
        return False
    href_l = href.lower()
    return '/updates' in href_l and ('azure.microsoft.com' in href_l or href_l.startswith('/'))


def _normalize_item(title: str, href: str, date_iso: str, base_url: str) -> Optional[Dict]:
    title = (title or '').strip()
    if not title or len(title) < 4:
        return None
    if title.lower() in {'read more', 'learn more', 'details'}:
        return None
    if not href:
        return None
    return {
        'title': re.sub(r'\s+', ' ', title),
        'url': urljoin(base_url, href),
        'date': date_iso,
    }


def _dedupe_items(items: List[Dict]) -> List[Dict]:
    seen = set()
    out: List[Dict] = []
    for it in items:
        key = (it.get('url', '').strip(), it.get('title', '').strip().lower())
        if not key[0] or key in seen:
            continue
        seen.add(key)
        out.append(it)
    return out


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

    # search ancestors and immediate siblings (limit to a few parents)
    parents = getattr(node, 'parents', None)
    if parents is not None:
        count = 0
        for anc in parents:
            if count >= 5:
                break
            count += 1
            try:
                time_tag = anc.find('time')
            except Exception:
                time_tag = None
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


def _walk_json(obj):
    if isinstance(obj, dict):
        yield obj
        for v in obj.values():
            yield from _walk_json(v)
    elif isinstance(obj, list):
        for i in obj:
            yield from _walk_json(i)


def _fetch_azure_updates_from_feed(base_url: str) -> List[Dict]:
    feed_urls = [
        'https://www.microsoft.com/releasecommunications/api/v2/azure/rss',
        'https://azure.microsoft.com/en-us/updates/feed/',
        'https://azure.microsoft.com/en-us/updates/rss/',
    ]
    items: List[Dict] = []
    for feed in feed_urls:
        try:
            feed_xml = fetch_url(feed)
        except Exception:
            continue

        if XMLParsedAsHTMLWarning is not None:
            warnings.filterwarnings('ignore', category=XMLParsedAsHTMLWarning)
        feed_soup = BeautifulSoup(feed_xml, 'html.parser')
        for entry in feed_soup.find_all(['item', 'entry']):
            title_tag = entry.find('title')
            link_tag = entry.find('link')
            date_tag = entry.find(['pubdate', 'updated', 'published', 'dc:date'])

            title = title_tag.get_text(strip=True) if title_tag else ''
            href = ''
            if link_tag:
                href = link_tag.get('href') or link_tag.get_text(strip=True)
            if not href:
                # The feed sometimes uses malformed <link/> tags followed by plain text URL.
                m = re.search(r'https?://azure\.microsoft\.com/updates\?id=\d+', str(entry), re.I)
                if m:
                    href = m.group(0)

            date_iso = _parse_date_to_iso(date_tag.get_text(strip=True) if date_tag else '')
            if not _looks_like_azure_update_url(href) or not date_iso:
                continue

            item = _normalize_item(title, href, date_iso, base_url)
            if item:
                items.append(item)

        if items:
            return _dedupe_items(items)

    return []


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
    # Primary: official release communications RSS feed.
    feed_items = _fetch_azure_updates_from_feed(url)
    if feed_items:
        return filter_recent(feed_items, days)

    try:
        html = fetch_url(url)
    except Exception:
        return []
    soup = BeautifulSoup(html, 'html.parser')
    items: List[Dict] = []

    # Strategy 1: parse JSON-LD blocks, which are usually more stable than CSS class names.
    for s in soup.find_all('script', attrs={'type': 'application/ld+json'}):
        raw = (s.string or s.get_text() or '').strip()
        if not raw:
            continue
        try:
            payload = json.loads(raw)
        except Exception:
            continue
        for obj in _walk_json(payload):
            title = obj.get('headline') or obj.get('name') or ''
            href = obj.get('url') or ''
            date_text = (
                obj.get('datePublished')
                or obj.get('dateModified')
                or obj.get('dateCreated')
                or ''
            )
            if not _looks_like_azure_update_url(str(href)):
                continue
            date_iso = _parse_date_to_iso(str(date_text))
            if not date_iso:
                continue
            item = _normalize_item(str(title), str(href), date_iso, url)
            if item:
                items.append(item)

    # Strategy 2: robust HTML card extraction with broader date fallbacks.
    candidates = soup.select(
        'article, li, .update, .update-item, .card, [data-bi-name], [data-testid]'
    )
    for c in candidates:
        anchors = c.find_all('a', href=True)
        for a in anchors[:3]:
            href = a['href']
            if not _looks_like_azure_update_url(href):
                continue
            title = a.get_text(strip=True)
            d = _find_date_near(c) or _find_date_near(a)
            date_iso = d.isoformat() if d else None
            if not date_iso:
                # Try common date attributes when no nearby visible date exists.
                for attr in ('data-date', 'datetime', 'data-published', 'data-publish-date'):
                    val = c.get(attr) or a.get(attr)
                    if val:
                        date_iso = _parse_date_to_iso(str(val))
                        if date_iso:
                            break
            if not date_iso:
                continue
            item = _normalize_item(title, href, date_iso, url)
            if item:
                items.append(item)

    items = _dedupe_items(items)
    return filter_recent(items, days)
