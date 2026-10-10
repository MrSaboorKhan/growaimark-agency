"""
tool_seo.py - Asli SEO Analyzer.

Ye tool diye gaye website ko khol kar uska HTML parhta hai aur 17 asli checks karta hai
(title, meta description, H1, images alt, mobile, HTTPS, speed, robots.txt, sitemap waghera).
Koi number random nahi hai, har score asli check se aata hai.

SAFETY: user ki di hui URL server se kholi jati hai, is liye private/internal addresses
(localhost, 10.x.x.x, 169.254.x.x waghera) block hain, redirects har baar dobara check hote hain,
aur page ka size aur waqt limited hai.
"""

import html
import ipaddress
import re
import socket
import time
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from flask import Blueprint, jsonify, request

from ai_helper import get_client_ip

seo_bp = Blueprint("seo", __name__)

USER_AGENT = "Mozilla/5.0 (compatible; GrowAIMarkBot/1.0; +https://growaimark.com)"
MAX_BYTES = 2_000_000       # page ka max size (2 MB)
MAX_REDIRECTS = 5
REQUEST_TIMEOUT = 8         # har network step ka timeout (seconds)
MAIN_DEADLINE = 15          # poore page fetch ka max waqt
EXTRA_DEADLINE = 8          # robots.txt / sitemap.xml ka max waqt


class FetchError(Exception):
    def __init__(self, message, status=400):
        super().__init__(message)
        self.message = message
        self.status = status


# ---------------------------------------------------------------- safe fetching
def normalize_url(raw):
    raw = (raw or "").strip()
    if not raw:
        raise FetchError("Please enter a website address.")
    if len(raw) > 500:
        raise FetchError("That address is too long.")
    if not re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", raw):
        raw = "https://" + raw
    parsed = urlparse(raw)
    if parsed.scheme not in ("http", "https"):
        raise FetchError("Only http and https website addresses are supported.")
    if not parsed.hostname:
        raise FetchError("That does not look like a valid website address.")
    if parsed.username or parsed.password:
        raise FetchError("Addresses with a username or password are not allowed.")
    try:
        port = parsed.port
    except ValueError:
        raise FetchError("That does not look like a valid website address.")
    if port not in (None, 80, 443):
        raise FetchError("Only standard web ports (80 and 443) are allowed.")
    return raw


def assert_public_host(hostname):
    """Sirf public internet addresses ki ijazat hai."""
    try:
        infos = socket.getaddrinfo(hostname, None)
    except socket.gaierror:
        raise FetchError("We could not find this website. Please check the address.")
    if not infos:
        raise FetchError("We could not find this website. Please check the address.")
    for info in infos:
        ip = ipaddress.ip_address(info[4][0].split("%")[0])
        if ip.version == 6 and ip.ipv4_mapped:
            ip = ip.ipv4_mapped
        if not ip.is_global:
            raise FetchError("This address is not allowed.")


def safe_get(url, max_bytes=MAX_BYTES, deadline_s=MAIN_DEADLINE):
    """Page laata hai. Returns (response, body_bytes, final_url, redirects, truncated)."""
    started = time.time()
    current = url
    redirects = 0

    while True:
        if time.time() - started > deadline_s:
            raise FetchError("The website took too long to respond.", 504)

        parsed = urlparse(current)
        if parsed.scheme not in ("http", "https") or not parsed.hostname:
            raise FetchError("The website redirected to an unsupported address.")
        if parsed.port not in (None, 80, 443):
            raise FetchError("The website redirected to a port that is not allowed.")
        assert_public_host(parsed.hostname)

        try:
            resp = requests.get(
                current,
                headers={
                    "User-Agent": USER_AGENT,
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.8",
                },
                timeout=REQUEST_TIMEOUT,
                allow_redirects=False,
                stream=True,
            )
        except requests.exceptions.SSLError:
            raise FetchError("This website has an invalid or expired SSL certificate.", 502)
        except requests.exceptions.Timeout:
            raise FetchError("The website took too long to respond.", 504)
        except requests.exceptions.RequestException:
            raise FetchError("We could not connect to this website.", 502)

        if resp.status_code in (301, 302, 303, 307, 308) and resp.headers.get("Location"):
            resp.close()
            redirects += 1
            if redirects > MAX_REDIRECTS:
                raise FetchError("The website redirects too many times.")
            current = urljoin(current, resp.headers["Location"])
            continue

        chunks, size, truncated = [], 0, False
        try:
            for chunk in resp.iter_content(16384):
                chunks.append(chunk)
                size += len(chunk)
                if size > max_bytes:
                    truncated = True
                    break
                if time.time() - started > deadline_s:
                    raise FetchError("The website took too long to respond.", 504)
        except requests.exceptions.RequestException:
            resp.close()
            raise FetchError("The connection to the website was interrupted.", 502)
        resp.close()

        body = b"".join(chunks)[:max_bytes]
        return resp, body, current, redirects, truncated


def check_extra(origin, path, kind):
    """robots.txt / sitemap.xml maujood hai ya nahi."""
    try:
        resp, body, _, _, _ = safe_get(urljoin(origin, path), max_bytes=300_000, deadline_s=EXTRA_DEADLINE)
    except Exception:
        return False
    if resp.status_code != 200:
        return False
    ctype = resp.headers.get("Content-Type", "").lower()
    text = body[:8000].decode("utf-8", errors="ignore").lower()
    if kind == "robots":
        return "html" not in ctype and any(k in text for k in ("user-agent", "disallow", "allow:", "sitemap:"))
    return "<urlset" in text or "<sitemapindex" in text


# ---------------------------------------------------------------- analysis
def make_check(check_id, label, status, earned, maximum, detail, fix=""):
    return {
        "id": check_id,
        "label": label,
        "status": status,        # pass / warn / fail
        "points": earned,
        "max_points": maximum,
        "detail": detail,
        "fix": fix,
    }


def strip_www(host):
    return host[4:] if host.startswith("www.") else host


def grade_for(score):
    if score >= 90:
        return "A"
    if score >= 80:
        return "B"
    if score >= 65:
        return "C"
    if score >= 50:
        return "D"
    return "F"


def analyze_html(final_url, resp, body, redirects, truncated, robots_ok, sitemap_ok):
    soup = BeautifulSoup(body, "html.parser")
    checks = []

    # ---- elements nikalna (script/style hatane se pehle)
    title_tag = soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else ""

    meta_desc_tag = soup.find("meta", attrs={"name": re.compile(r"^description$", re.I)})
    meta_desc = (meta_desc_tag.get("content") or "").strip() if meta_desc_tag else ""

    robots_tag = soup.find("meta", attrs={"name": re.compile(r"^robots$", re.I)})
    robots_content = ((robots_tag.get("content") or "") if robots_tag else "").lower()
    header_robots = resp.headers.get("X-Robots-Tag", "").lower()
    noindex = "noindex" in robots_content or "noindex" in header_robots

    viewport = soup.find("meta", attrs={"name": re.compile(r"^viewport$", re.I)})
    canonical = soup.find("link", rel="canonical")
    html_tag = soup.find("html")
    lang = (html_tag.get("lang") or "").strip() if html_tag else ""

    og_found = [p for p in ("og:title", "og:description", "og:image")
                if soup.find("meta", attrs={"property": p})]
    json_ld = soup.find("script", attrs={"type": "application/ld+json"})

    h1_texts = [h.get_text(strip=True) for h in soup.find_all("h1")]
    h1_texts = [t for t in h1_texts if t]
    h2_count = len(soup.find_all("h2"))

    images = [i for i in soup.find_all("img") if i.get("src") or i.get("data-src")]
    images_missing_alt = [i for i in images if i.get("alt") is None]

    base_host = strip_www((urlparse(final_url).hostname or "").lower())
    internal_links, external_links = 0, 0
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if not href or href.startswith(("#", "mailto:", "tel:", "javascript:")):
            continue
        host = strip_www((urlparse(urljoin(final_url, href)).hostname or "").lower())
        if host == base_host:
            internal_links += 1
        else:
            external_links += 1

    for tag in soup(["script", "style", "noscript", "template"]):
        tag.decompose()
    word_count = len(re.findall(r"\w+", soup.get_text(" ", strip=True)))

    response_ms = int(resp.elapsed.total_seconds() * 1000)
    size_kb = round(len(body) / 1024)

    # ---- 1. HTTPS
    if urlparse(final_url).scheme == "https":
        checks.append(make_check("https", "HTTPS (secure connection)", "pass", 8, 8, "The site uses HTTPS."))
    else:
        checks.append(make_check("https", "HTTPS (secure connection)", "fail", 0, 8,
                                 "The site is not using HTTPS.",
                                 "Install an SSL certificate and redirect all pages to HTTPS."))

    # ---- 2. Title
    n = len(title)
    if not title:
        checks.append(make_check("title", "Title tag", "fail", 0, 12, "No title tag found.",
                                 "Add a unique title of 30-60 characters that includes your main keyword."))
    elif 30 <= n <= 60:
        checks.append(make_check("title", "Title tag", "pass", 12, 12, f"Title length is good ({n} characters)."))
    else:
        fix = ("Make the title more descriptive, around 30-60 characters." if n < 30
               else "Shorten the title to 60 characters or less so Google does not cut it off.")
        checks.append(make_check("title", "Title tag", "warn", 6, 12, f"Title is {n} characters (ideal 30-60).", fix))

    # ---- 3. Meta description
    n = len(meta_desc)
    if not meta_desc:
        checks.append(make_check("meta_description", "Meta description", "fail", 0, 10,
                                 "No meta description found.",
                                 "Write a meta description of 70-160 characters that makes people want to click."))
    elif 70 <= n <= 160:
        checks.append(make_check("meta_description", "Meta description", "pass", 10, 10,
                                 f"Meta description length is good ({n} characters)."))
    else:
        fix = ("Expand the meta description to at least 70 characters." if n < 70
               else "Shorten the meta description to 160 characters or less.")
        checks.append(make_check("meta_description", "Meta description", "warn", 5, 10,
                                 f"Meta description is {n} characters (ideal 70-160).", fix))

    # ---- 4. H1
    if len(h1_texts) == 1:
        checks.append(make_check("h1", "H1 heading", "pass", 10, 10, "The page has exactly one H1 heading."))
    elif len(h1_texts) == 0:
        checks.append(make_check("h1", "H1 heading", "fail", 0, 10, "No H1 heading found.",
                                 "Add one clear H1 heading that describes what the page is about."))
    else:
        checks.append(make_check("h1", "H1 heading", "warn", 5, 10, f"Found {len(h1_texts)} H1 headings.",
                                 "Use a single H1 per page and use H2/H3 for the sub-sections."))

    # ---- 5. H2
    if h2_count >= 1:
        checks.append(make_check("h2", "Sub-headings (H2)", "pass", 4, 4, f"Found {h2_count} H2 sub-headings."))
    else:
        checks.append(make_check("h2", "Sub-headings (H2)", "warn", 2, 4, "No H2 sub-headings found.",
                                 "Break your content into sections with H2 headings."))

    # ---- 6. Content length
    if word_count >= 300:
        checks.append(make_check("content", "Content length", "pass", 10, 10,
                                 f"About {word_count} words of text found."))
    elif word_count >= 100:
        checks.append(make_check("content", "Content length", "warn", 5, 10,
                                 f"Only about {word_count} words of text found.",
                                 "Add more helpful content, ideally 300 words or more."))
    else:
        checks.append(make_check("content", "Content length", "fail", 0, 10,
                                 f"Very little text found ({word_count} words).",
                                 "Add more helpful written content. Pages built mainly with JavaScript may also hide text from search engines."))

    # ---- 7. Image alt text
    if not images:
        checks.append(make_check("image_alt", "Image alt text", "pass", 8, 8, "No images found on the page."))
    else:
        missing, total = len(images_missing_alt), len(images)
        if missing == 0:
            checks.append(make_check("image_alt", "Image alt text", "pass", 8, 8,
                                     f"All {total} images have alt text."))
        elif missing / total <= 0.2:
            checks.append(make_check("image_alt", "Image alt text", "warn", 4, 8,
                                     f"{missing} of {total} images have no alt text.",
                                     "Add short descriptive alt text to every image."))
        else:
            checks.append(make_check("image_alt", "Image alt text", "fail", 0, 8,
                                     f"{missing} of {total} images have no alt text.",
                                     "Add short descriptive alt text to every image."))

    # ---- 8. Mobile viewport
    if viewport:
        checks.append(make_check("viewport", "Mobile friendly setup", "pass", 8, 8, "Viewport meta tag is present."))
    else:
        checks.append(make_check("viewport", "Mobile friendly setup", "fail", 0, 8,
                                 "No viewport meta tag found.",
                                 'Add <meta name="viewport" content="width=device-width, initial-scale=1"> so the page works on phones.'))

    # ---- 9. Canonical
    if canonical:
        checks.append(make_check("canonical", "Canonical link", "pass", 4, 4, "A canonical link is set."))
    else:
        checks.append(make_check("canonical", "Canonical link", "warn", 2, 4, "No canonical link found.",
                                 "Add a canonical link to avoid duplicate-content problems."))

    # ---- 10. Language
    if lang:
        checks.append(make_check("lang", "Page language", "pass", 3, 3, f"Language is set ({lang})."))
    else:
        checks.append(make_check("lang", "Page language", "warn", 1, 3, "No lang attribute on the <html> tag.",
                                 'Add a language, for example <html lang="en">.'))

    # ---- 11. Indexable
    if noindex:
        checks.append(make_check("indexable", "Search engines allowed", "fail", 0, 7,
                                 "The page tells search engines NOT to index it (noindex).",
                                 "Remove the noindex instruction if you want this page to appear on Google."))
    else:
        checks.append(make_check("indexable", "Search engines allowed", "pass", 7, 7,
                                 "The page can be indexed by search engines."))

    # ---- 12. Open Graph
    if len(og_found) == 3:
        checks.append(make_check("open_graph", "Social sharing tags (Open Graph)", "pass", 5, 5,
                                 "og:title, og:description and og:image are all set."))
    elif og_found:
        checks.append(make_check("open_graph", "Social sharing tags (Open Graph)", "warn", 2, 5,
                                 f"Only some tags found ({', '.join(og_found)}).",
                                 "Add og:title, og:description and og:image so links look good when shared."))
    else:
        checks.append(make_check("open_graph", "Social sharing tags (Open Graph)", "warn", 0, 5,
                                 "No Open Graph tags found.",
                                 "Add og:title, og:description and og:image so links look good when shared."))

    # ---- 13. Structured data
    if json_ld:
        checks.append(make_check("schema", "Structured data (JSON-LD)", "pass", 3, 3, "Structured data found."))
    else:
        checks.append(make_check("schema", "Structured data (JSON-LD)", "warn", 0, 3, "No structured data found.",
                                 "Add JSON-LD schema markup (for example Organization or Article) to help Google understand the page."))

    # ---- 14. Server speed
    if response_ms < 800:
        checks.append(make_check("speed", "Server response time", "pass", 6, 6,
                                 f"Server responded in {response_ms} ms."))
    elif response_ms < 2000:
        checks.append(make_check("speed", "Server response time", "warn", 3, 6,
                                 f"Server responded in {response_ms} ms (ideal under 800 ms).",
                                 "Use caching or a faster hosting plan to speed up the server."))
    else:
        checks.append(make_check("speed", "Server response time", "fail", 0, 6,
                                 f"Server took {response_ms} ms to respond.",
                                 "Use caching, a CDN or a faster hosting plan. Slow sites rank lower."))

    # ---- 15. Page size
    if truncated:
        checks.append(make_check("size", "Page size", "fail", 0, 4, "The page HTML is larger than 2 MB.",
                                 "Reduce the page size by removing unneeded code and inline data."))
    elif size_kb <= 300:
        checks.append(make_check("size", "Page size", "pass", 4, 4, f"HTML size is {size_kb} KB."))
    elif size_kb <= 1000:
        checks.append(make_check("size", "Page size", "warn", 2, 4, f"HTML size is {size_kb} KB (ideal under 300 KB).",
                                 "Reduce page size by removing unneeded code."))
    else:
        checks.append(make_check("size", "Page size", "fail", 0, 4, f"HTML size is {size_kb} KB.",
                                 "Reduce page size by removing unneeded code and inline data."))

    # ---- 16. robots.txt
    if robots_ok:
        checks.append(make_check("robots_txt", "robots.txt file", "pass", 3, 3, "robots.txt found."))
    else:
        checks.append(make_check("robots_txt", "robots.txt file", "warn", 0, 3, "No robots.txt found.",
                                 "Add a robots.txt file at the root of your website."))

    # ---- 17. sitemap.xml
    if sitemap_ok:
        checks.append(make_check("sitemap", "XML sitemap", "pass", 3, 3, "sitemap.xml found."))
    else:
        checks.append(make_check("sitemap", "XML sitemap", "warn", 0, 3,
                                 "No sitemap.xml found at the usual location.",
                                 "Create an XML sitemap and submit it in Google Search Console."))

    earned = sum(c["points"] for c in checks)
    maximum = sum(c["max_points"] for c in checks)
    score = round(earned / maximum * 100)

    problems = [c for c in checks if c["status"] != "pass"]
    problems.sort(key=lambda c: c["max_points"] - c["points"], reverse=True)

    return {
        "score": score,
        "grade": grade_for(score),
        "title": title or "(no title found)",
        "meta_description": meta_desc,
        "word_count": word_count,
        "issues": [c["detail"] for c in problems],
        "recommendations": [c["fix"] for c in problems if c["fix"]][:8],
        "checks": checks,
        "stats": {
            "response_ms": response_ms,
            "page_size_kb": size_kb,
            "redirects": redirects,
            "images": len(images),
            "images_missing_alt": len(images_missing_alt),
            "internal_links": internal_links,
            "external_links": external_links,
            "h1_count": len(h1_texts),
            "h2_count": h2_count,
            "passed": sum(1 for c in checks if c["status"] == "pass"),
            "warnings": sum(1 for c in checks if c["status"] == "warn"),
            "failed": sum(1 for c in checks if c["status"] == "fail"),
        },
    }


def escape_all(obj):
    """Third-party website ka text page par safely dikhane ke liye."""
    if isinstance(obj, str):
        return html.escape(obj)
    if isinstance(obj, list):
        return [escape_all(x) for x in obj]
    if isinstance(obj, dict):
        return {k: escape_all(v) for k, v in obj.items()}
    return obj


# ---------------------------------------------------------------- rate limit
_seo_hits = {}
SEO_MAX_REQUESTS = 6
SEO_WINDOW = 60


def seo_rate_limited(ip):
    now = time.time()
    recent = [t for t in _seo_hits.get(ip, []) if now - t < SEO_WINDOW]
    if len(recent) >= SEO_MAX_REQUESTS:
        _seo_hits[ip] = recent
        return True
    recent.append(now)
    _seo_hits[ip] = recent
    if len(_seo_hits) > 5000:
        for key in list(_seo_hits.keys()):
            if not any(now - t < SEO_WINDOW for t in _seo_hits[key]):
                _seo_hits.pop(key, None)
    return False


# ---------------------------------------------------------------- route
def error_response(message, status):
    # Purani dashboard in fields ko parhti hai, is liye ye sab bharte hain
    return jsonify({
        "success": False,
        "error": message,
        "score": 0,
        "title": message,
        "issues": [message],
        "recommendations": ["Check the website address and try again."],
        "message": message,
    }), status


@seo_bp.route("/api/seo/analyze", methods=["POST"])
def analyze_seo():
    data = request.get_json(silent=True) or {}

    if seo_rate_limited(get_client_ip(request)):
        return error_response("You are sending requests too fast. Please wait a minute and try again.", 429)

    try:
        url = normalize_url(str(data.get("url", "")))
        resp, body, final_url, redirects, truncated = safe_get(url)

        if resp.status_code >= 400:
            raise FetchError(f"The website returned an error (HTTP {resp.status_code}).", 502)
        ctype = resp.headers.get("Content-Type", "").lower()
        if ctype and "html" not in ctype:
            raise FetchError("This address is not a web page.", 400)

        parsed = urlparse(final_url)
        origin = f"{parsed.scheme}://{parsed.netloc}"
        robots_ok = sitemap_ok = False
        try:
            with ThreadPoolExecutor(max_workers=2) as pool:
                f_robots = pool.submit(check_extra, origin, "/robots.txt", "robots")
                f_sitemap = pool.submit(check_extra, origin, "/sitemap.xml", "sitemap")
                robots_ok = f_robots.result(timeout=EXTRA_DEADLINE + 5)
                sitemap_ok = f_sitemap.result(timeout=EXTRA_DEADLINE + 5)
        except Exception:
            pass

        report = analyze_html(final_url, resp, body, redirects, truncated, robots_ok, sitemap_ok)
    except FetchError as e:
        return error_response(e.message, e.status)
    except Exception as e:
        print(f"[SEO] Unexpected error: {e}")
        return error_response("Something went wrong while analyzing this website. Please try again.", 500)

    report.update({
        "success": True,
        "url": final_url,
        "message": "SEO analysis complete",
    })
    return jsonify(escape_all(report))