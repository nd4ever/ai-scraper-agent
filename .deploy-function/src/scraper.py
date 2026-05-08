import requests
from bs4 import BeautifulSoup
from dateutil import parser
from datetime import datetime, timedelta, date as date_type
from urllib.parse import urljoin
from typing import List, Dict, Optional, Tuple
import json
import re
import warnings

try:
    from bs4 import XMLParsedAsHTMLWarning
except Exception:  # pragma: no cover
    XMLParsedAsHTMLWarning = None

try:
    from dateutil.parser import UnknownTimezoneWarning
except Exception:  # pragma: no cover
    UnknownTimezoneWarning = Warning

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible)"}

AZURE_BLOG_CATEGORY_BY_SLUG = {
    'azurearcblog': 'Azure Arc Blog',
    'azurearchitectureblog': 'Azure Architecture Blog',
    'azurecomputeblog': 'Azure Compute Blog',
    'azuregovernanceandmanagement': 'Azure Governance and Management Blog',
    'azureinfrastructureblog': 'Azure Infrastructure Blog',
    'azureintegrationservicesblog': 'Azure Integration Services Blog',
    'azuremigrationandmodernization': 'Azure Migration and Modernization Blog',
    'azurenetworkingblog': 'Azure Networking Blog',
    'azureobservabilityblog': 'Azure Observability Blog',
    'azurestorageblog': 'Azure Storage Blog',
    'azuretoolsblog': 'Azure Tools Blog',
    'azurevirtualdesktopblog': 'Azure Virtual Desktop Blog',
    'finopsblog': 'FinOps Blog',
    'linuxandopensourceblog': 'Linux and Open Source Blog',
}

AZURE_BLOG_BOARD_ID_BY_SLUG = {
    'azurearcblog': 'AzureArcBlog',
    'azurearchitectureblog': 'AzureArchitectureBlog',
    'azurecomputeblog': 'AzureComputeBlog',
    'azuregovernanceandmanagement': 'AzureGovernanceandManagement',
    'azureinfrastructureblog': 'AzureInfrastructureBlog',
    'azureintegrationservicesblog': 'AzureIntegrationServicesBlog',
    'azuremigrationandmodernization': 'AzureMigrationandModernization',
    'azurenetworkingblog': 'AzureNetworkingBlog',
    'azureobservabilityblog': 'AzureObservabilityBlog',
    'azurestorageblog': 'AzureStorageBlog',
    'azuretoolsblog': 'AzureToolsBlog',
    'azurevirtualdesktopblog': 'AzureVirtualDesktopBlog',
    'finopsblog': 'FinOpsBlog',
    'linuxandopensourceblog': 'LinuxandOpenSourceBlog',
}

YOUTUBE_VIDEO_CHANNELS = [
    {
        'name': 'NTFAQGuy',
        'page_url': 'https://www.youtube.com/@NTFAQGuy/videos',
    },
    {
        'name': 'MicrosoftAzure',
        'page_url': 'https://www.youtube.com/@MicrosoftAzure/videos',
    },
    {
        'name': 'MSFTMechanics',
        'page_url': 'https://www.youtube.com/@MSFTMechanics/videos',
    },
    {
        'name': 'MicrosoftSecurityCommunity',
        'page_url': 'https://www.youtube.com/@MicrosoftSecurityCommunity/videos',
    },
    {
        'name': 'AzureArcServerForum',
        'page_url': 'https://www.youtube.com/@AzureArcServerForum/videos',
    },
]

AZURE_VIDEO_TITLE_KEYWORDS = [
    'azure',
    'aks',
    'app service',
    'api management',
    'arc',
    'bicep',
    'container apps',
    'cosmos db',
    'data factory',
    'devops',
    'entra',
    'foundry',
    'function app',
    'functions',
    'key vault',
    'landing zone',
    'logic apps',
    'microsoft fabric',
    'openai',
    'power platform',
    'sentinel',
    'service bus',
    'sql mi',
    'virtual desktop',
    'vnet',
]


def fetch_url(url: str) -> str:
    resp = requests.get(url, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    return resp.text


def parse_date(text: str) -> Optional[datetime]:
    if not text:
        return None
    try:
        with warnings.catch_warnings():
            warnings.filterwarnings('ignore', category=UnknownTimezoneWarning)
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


def _normalize_azure_update_title(title: str) -> str:
    title = re.sub(r'\s+', ' ', (title or '')).strip()

    # Azure update feed items often include "[Launched] Generally Available: ...".
    # Prefer the release ring from the announcement body for clearer labeling.
    m = re.match(r'^\[[^\]]+\]\s*Generally Available:\s*(.+)$', title, re.I)
    if m:
        return f"[Generally Available] {m.group(1).strip()}"

    m = re.match(r'^Generally Available:\s*(.+)$', title, re.I)
    if m:
        return f"[Generally Available] {m.group(1).strip()}"

    return title


def _extract_azure_update_status_and_title(title: str) -> Tuple[Optional[str], str]:
    title = _normalize_azure_update_title(title)
    if not title:
        return None, ''

    bracket_status = None
    body = title

    m = re.match(r'^\[([^\]]+)\]\s*(.+)$', title)
    if m:
        bracket_status = m.group(1).strip()
        body = m.group(2).strip()

    # Prefer the explicit release ring that appears before the announcement title.
    # Example: "[Launched] Generally Available: ..." -> status="Generally Available".
    m = re.match(r'^(Generally Available|Public Preview|Private Preview|Retirement):\s*(.+)$', body, re.I)
    if m:
        return m.group(1).strip(), m.group(2).strip()

    return bracket_status, body


def _normalize_item(title: str, href: str, date_iso: str, base_url: str) -> Optional[Dict]:
    status, clean_title = _extract_azure_update_status_and_title(title)
    title = clean_title
    if not title or len(title) < 4:
        return None
    if title.lower() in {'read more', 'learn more', 'details'}:
        return None
    if not href:
        return None
    item = {
        'title': re.sub(r'\s+', ' ', title),
        'url': urljoin(base_url, href),
        'date': date_iso,
    }
    if status:
        item['status'] = status
    else:
        item['status'] = None
    return item


MRC_API_BASE = 'https://www.microsoft.com/releasecommunications/api/v2/azure'


def _extract_update_id(update_url: str) -> Optional[str]:
    m = re.search(r'[?&]id=(\d+)', update_url or '', re.I)
    return m.group(1) if m else None


def _fetch_mrc_update_details(update_url: str) -> Optional[Dict]:
    """Fetch the MRC JSON API for one update and extract metadata.

    URL pattern: https://www.microsoft.com/releasecommunications/api/v2/azure/{id}
    Returns product names and all documentation links found in description HTML.
    """
    update_id = _extract_update_id(update_url)
    if not update_id:
        return None
    api_url = f'{MRC_API_BASE}/{update_id}'
    try:
        resp = requests.get(api_url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        return None

    description_html = data.get('description') or ''
    products = data.get('products') or []
    product_categories = data.get('productCategories') or []
    product_names = [str(p).strip() for p in products if str(p).strip()]
    category_names = [str(c).strip() for c in product_categories if str(c).strip()]

    documentation_links: List[str] = []
    learn_more_url: Optional[str] = None
    if description_html:
        soup = BeautifulSoup(description_html, 'html.parser')
        for a in soup.find_all('a', href=True):
            href = (a.get('href') or '').strip()
            if not href.startswith('http'):
                continue
            if href not in documentation_links:
                documentation_links.append(href)

            text = re.sub(r'\s+', ' ', a.get_text(' ', strip=True)).strip().lower()
            if learn_more_url is None and 'learn' in text and 'more' in text:
                learn_more_url = href

        if learn_more_url is None and documentation_links:
            learn_more_url = documentation_links[0]

    product_name = product_names[0] if product_names else (category_names[0] if category_names else None)
    return {
        'product': product_name,
        'products': product_names,
        'product_categories': category_names,
        'documentation_links': documentation_links,
        'learn_more_url': learn_more_url,
    }


def _infer_product_from_title(title: str) -> Optional[str]:
    text = re.sub(r'\s+', ' ', (title or '')).strip()
    if not text:
        return None

    stop_words = {'in', 'for', 'on', 'with', 'from', 'and', 'to', 'at'}

    patterns = [
        r'(Azure [A-Za-z0-9\- ]{2,60}?)\s+(?:supports|support|is|are|now|for|from|in|on|with)\b',
        r'\b(?:in|for|on|with|from)\s+(Azure [A-Za-z0-9\- ]{2,60}?)\b',
    ]
    for pattern in patterns:
        m = re.search(pattern, text, re.I)
        if m:
            candidate = re.sub(r'\s+', ' ', m.group(1)).strip(' :-')
            words = candidate.split()
            while words and words[-1].lower() in stop_words:
                words.pop()
            candidate = ' '.join(words).strip()

            if not candidate or candidate.lower() == 'azure':
                continue
            if len(words) >= 2 and words[0].lower() == 'azure' and words[1].lower() in stop_words:
                continue

            if candidate and candidate.lower() != 'azure':
                return candidate
    return None


def _enrich_azure_update_item(item: Dict) -> Dict:
    details = _fetch_mrc_update_details(item.get('url', ''))
    if details:
        item['product'] = details.get('product')
        item['products'] = details.get('products') or []
        item['product_categories'] = details.get('product_categories') or []
        item['documentation_links'] = details.get('documentation_links') or []
        item['learn_more_url'] = details.get('learn_more_url')
    else:
        item.setdefault('product', None)
        item.setdefault('products', [])
        item.setdefault('product_categories', [])
        item.setdefault('documentation_links', [])
        item.setdefault('learn_more_url', None)

    if not item.get('product'):
        inferred = _infer_product_from_title(item.get('title', ''))
        if inferred:
            item['product'] = inferred

    return item


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


def _extract_youtube_feed_url(channel_page_url: str) -> Optional[str]:
    try:
        html = fetch_url(channel_page_url)
    except Exception:
        return None

    soup = BeautifulSoup(html, 'html.parser')
    for link in soup.find_all('link', href=True):
        rel = link.get('rel') or []
        rel_values = [str(value).lower() for value in rel]
        link_type = str(link.get('type') or '').lower()
        if 'alternate' in rel_values and link_type == 'application/rss+xml':
            return str(link.get('href') or '').strip() or None

    canonical = soup.find('link', rel='canonical', href=True)
    canonical_href = str(canonical.get('href') or '').strip() if canonical else ''
    m = re.search(r'/channel/(UC[\w-]+)', canonical_href)
    if m:
        return f'https://www.youtube.com/feeds/videos.xml?channel_id={m.group(1)}'

    m = re.search(r'channelId\":\"(UC[\w-]+)', html)
    if m:
        return f'https://www.youtube.com/feeds/videos.xml?channel_id={m.group(1)}'

    return None


def _is_azure_related_video_title(title: str) -> bool:
    normalized = re.sub(r'\s+', ' ', (title or '')).strip().lower()
    if not normalized:
        return False
    return any(keyword in normalized for keyword in AZURE_VIDEO_TITLE_KEYWORDS)


def fetch_youtube_channel_videos(
    channel_name: str,
    channel_page_url: str,
    start_date: date_type,
    end_date: date_type,
) -> List[Dict]:
    feed_url = _extract_youtube_feed_url(channel_page_url)
    if not feed_url:
        return []

    try:
        feed_xml = fetch_url(feed_url)
    except Exception:
        return []

    if XMLParsedAsHTMLWarning is not None:
        warnings.filterwarnings('ignore', category=XMLParsedAsHTMLWarning)

    feed_soup = BeautifulSoup(feed_xml, 'html.parser')
    items: List[Dict] = []

    for entry in feed_soup.find_all(['entry', 'item']):
        title_tag = entry.find('title')
        link_tag = entry.find('link')
        date_tag = entry.find(['published', 'updated', 'pubdate'])

        title = re.sub(r'\s+', ' ', title_tag.get_text(' ', strip=True) if title_tag else '').strip()
        href = ''
        if link_tag:
            href = (link_tag.get('href') or link_tag.get_text(strip=True) or '').strip()
        if not href:
            m = re.search(r'https?://www\.youtube\.com/watch\?v=[^\s<\"]+', str(entry), re.I)
            if m:
                href = m.group(0)

        date_iso = _parse_date_to_iso(date_tag.get_text(strip=True) if date_tag else '')
        if not title or not href or not date_iso or not _is_azure_related_video_title(title):
            continue

        items.append({
            'channel': channel_name,
            'channel_url': channel_page_url,
            'title': title,
            'url': href,
            'date': date_iso,
        })

    recent = filter_date_range(_dedupe_items(items), start_date, end_date)
    return sorted(recent, key=lambda it: it.get('date', ''), reverse=True)


def fetch_azure_youtube_videos(start_date: date_type, end_date: date_type) -> List[Dict]:
    items: List[Dict] = []
    for channel in YOUTUBE_VIDEO_CHANNELS:
        items.extend(
            fetch_youtube_channel_videos(
                channel_name=channel['name'],
                channel_page_url=channel['page_url'],
                start_date=start_date,
                end_date=end_date,
            )
        )

    deduped = _dedupe_items(items)
    return sorted(deduped, key=lambda it: it.get('date', ''), reverse=True)


def _extract_blog_category_slug(href: str) -> Optional[str]:
    if not href:
        return None
    m = re.search(r'/category/azure/blog/([^/?#]+)', href, re.I)
    if not m:
        return None
    return m.group(1).strip().lower()


def _find_blog_category_for_link(anchor) -> Optional[str]:
    # Walk a few ancestors and look for the parent category link in the same card.
    current = anchor
    for _ in range(6):
        if current is None:
            break
        try:
            links = current.find_all('a', href=True)
        except Exception:
            links = []
        for link in links:
            slug = _extract_blog_category_slug(link.get('href', ''))
            if slug and slug in AZURE_BLOG_CATEGORY_BY_SLUG:
                return AZURE_BLOG_CATEGORY_BY_SLUG[slug]
        current = current.parent
    return None


def _find_date_near(node) -> Optional[datetime]:
    def _parse_from_tag_date_attrs(tag) -> Optional[datetime]:
        for attr in ('datetime', 'title', 'data-date', 'data-time', 'data-timestamp'):
            try:
                val = tag.get(attr) if hasattr(tag, 'get') else None
            except Exception:
                val = None
            if not val:
                continue
            d = parse_date(str(val))
            if d:
                return d
        return None

    # search inside node
    time_tag = node.find('time') if hasattr(node, 'find') else None
    if time_tag:
        if time_tag.has_attr('datetime'):
            d = parse_date(time_tag['datetime'])
        else:
            d = parse_date(time_tag.get_text(strip=True))
        if d:
            return d

    # Tech Community cards often carry publish date in a title attribute.
    if hasattr(node, 'find_all'):
        for tag in node.find_all(attrs={'title': True}, limit=15):
            d = _parse_from_tag_date_attrs(tag)
            if d:
                return d

        # Generic fallback for explicit date attributes.
        for tag in node.find_all(limit=20):
            d = _parse_from_tag_date_attrs(tag)
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

            # Parent cards may hold the publish date in attributes.
            d = _parse_from_tag_date_attrs(anc)
            if d:
                return d

            if hasattr(anc, 'find_all'):
                for tag in anc.find_all(attrs={'title': True}, limit=6):
                    d = _parse_from_tag_date_attrs(tag)
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


def get_previous_week_range() -> Tuple[date_type, date_type]:
    """Return (monday, sunday) of the most recently completed Mon–Sun week."""
    today = date_type.today()
    current_monday = today - timedelta(days=today.weekday())
    prev_monday = current_monday - timedelta(weeks=1)
    prev_sunday = current_monday - timedelta(days=1)
    return prev_monday, prev_sunday


def filter_date_range(
    items: List[Dict],
    start_date: date_type,
    end_date: date_type,
) -> List[Dict]:
    """Keep only items whose date falls within [start_date, end_date] inclusive."""
    filtered: List[Dict] = []
    for it in items:
        try:
            dt = parser.parse(it['date']).date()
        except Exception:
            continue
        if start_date <= dt <= end_date:
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
                items.append(_enrich_azure_update_item(item))

        if items:
            return _dedupe_items(items)

    return []


def fetch_techcommunity(start_date: date_type, end_date: date_type) -> List[Dict]:
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

    return filter_date_range(items, start_date, end_date)


def fetch_azure_community_blog_headlines(start_date: date_type, end_date: date_type) -> List[Dict]:
    """Fetch blog posts from multiple Azure blog sources."""
    items: List[Dict] = []
    
    # Blog slugs to fetch (in order of display)
    blog_slugs = [
        'azurearcblog',
        'azurearchitectureblog',
        'azurecomputeblog',
        'azuregovernanceandmanagement',
        'azureinfrastructureblog',
        'azureintegrationservicesblog',
        'azuremigrationandmodernization',
        'azurenetworkingblog',
        'azureobservabilityblog',
        'azurestorageblog',
        'azuretoolsblog',
        'azurevirtualdesktopblog',
        'finopsblog',
        'linuxandopensourceblog',
    ]
    
    if XMLParsedAsHTMLWarning is not None:
        warnings.filterwarnings('ignore', category=XMLParsedAsHTMLWarning)
    
    for slug in blog_slugs:
        category_name = AZURE_BLOG_CATEGORY_BY_SLUG.get(slug, slug)
        board_id = AZURE_BLOG_BOARD_ID_BY_SLUG.get(slug, slug)
        rss_url = f'https://techcommunity.microsoft.com/t5/s/gxcuf89792/rss/board?board.id={board_id}'
        
        try:
            feed_xml = fetch_url(rss_url)
        except Exception:
            continue
        
        feed_soup = BeautifulSoup(feed_xml, 'html.parser')
        
        for entry in feed_soup.find_all('item'):
            title_tag = entry.find('title')
            link_tag = entry.find('link')
            date_tag = entry.find(['pubdate', 'published', 'updated', 'dc:date'])

            title = re.sub(r'\s+', ' ', title_tag.get_text(' ', strip=True) if title_tag else '').strip()
            href = ''
            if link_tag:
                href = (link_tag.get('href') or link_tag.get_text(strip=True) or '').strip()
            if not href:
                # TechCommunity RSS has malformed <link/> tags; extract URL from raw entry XML
                # URLs can be /blog/... or /t5/.../...  format
                m = re.search(r'https?://techcommunity\.microsoft\.com/[^\s<]+', str(entry), re.I)
                if m:
                    href = m.group(0)
            date_iso = _parse_date_to_iso(date_tag.get_text(strip=True) if date_tag else '')

            if not title or not href or not date_iso:
                continue

            items.append({
                'category': category_name,
                'title': title,
                'url': urljoin(rss_url, href),
                'date': date_iso,
            })

    deduped = _dedupe_items(items)
    recent = filter_date_range(deduped, start_date, end_date)
    return sorted(recent, key=lambda it: it.get('date', ''), reverse=True)


def fetch_azure_updates(start_date: date_type, end_date: date_type) -> List[Dict]:
    url = 'https://azure.microsoft.com/en-us/updates/'
    # Primary: official release communications RSS feed.
    feed_items = _fetch_azure_updates_from_feed(url)
    if feed_items:
        return filter_date_range(feed_items, start_date, end_date)

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
                items.append(_enrich_azure_update_item(item))

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
                items.append(_enrich_azure_update_item(item))

    items = _dedupe_items(items)
    return filter_date_range(items, start_date, end_date)
