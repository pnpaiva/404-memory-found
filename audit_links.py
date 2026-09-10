#!/usr/bin/env python3
"""Link health report for 404memoryfound.com.

  python3 audit_links.py            -> prints the report
  python3 audit_links.py --external -> also HEAD-checks every external link (slow, polite)
  python3 audit_links.py --write    -> writes docs/link-report.md as well

Reports: internal links in post bodies that point at missing pages; posts with fewer than two inbound links
from other posts' bodies (explicit links plus the automatic linkPhrases links build.py inserts); dead external
links when --external is given. Nothing here modifies posts.json.
"""
import json
import re
import sys
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

import build  # reuse the site's own link rules

EXTERNAL = "--external" in sys.argv
WRITE = "--write" in sys.argv
UA = "Mozilla/5.0 (compatible; 404MemoryFound-linkcheck/1.0; +https://404memoryfound.com)"


def main():
    data = json.load(open("posts.json", encoding="utf-8"))
    posts = data["posts"]
    ids = {p["id"] for p in posts}
    for p in posts:
        p.setdefault("slug", p["id"])
    index = sorted(((ph, p["slug"]) for p in posts for ph in build.link_phrases(p)), key=lambda t: -len(t[0]))
    bodies = {p["id"]: build.add_internal_links(p["body"], p, index) for p in posts}

    broken_internal = []
    inbound = Counter()
    external = defaultdict(list)
    for pid, body in bodies.items():
        for href in re.findall(r'href="([^"]+)"', body):
            if href.startswith("/posts/"):
                target = href[len("/posts/"):].split("#")[0].removesuffix(".html")
                if target in ids:
                    if target != pid:
                        inbound[target] += 1
                else:
                    broken_internal.append((pid, href))
            elif href.startswith("http"):
                external[href].append(pid)
    for p in posts:
        for s in p.get("sources") or []:
            external[s["url"]].append(p["id"])

    orphans = sorted((inbound[p["id"]], p["id"]) for p in posts if inbound[p["id"]] < 2)

    dead = []
    if EXTERNAL:
        def check(url):
            req = Request(url, headers={"User-Agent": UA}, method="HEAD")
            try:
                with urlopen(req, timeout=20) as r:
                    return url, r.status
            except HTTPError as e:
                if e.code in (403, 405, 429):  # bots refused, not dead
                    return url, e.code
                return url, e.code
            except URLError as e:
                return url, f"ERR {e.reason}"
            except Exception as e:  # noqa: BLE001
                return url, f"ERR {e}"
        with ThreadPoolExecutor(max_workers=6) as ex:
            for url, status in ex.map(check, sorted(external)):
                if status in (404, 410, 500, 502, 503) or str(status).startswith("ERR"):
                    dead.append((status, url, sorted(set(external[url]))))

    lines = [f"# Link report, {date.today().isoformat()}", "",
             f"{len(posts)} posts, {sum(inbound.values())} internal body links, {len(external)} distinct external URLs.", ""]
    lines += ["## Broken internal links", ""] + ([f"- {pid}: `{href}`" for pid, href in broken_internal] or ["None."]) + [""]
    lines += [f"## Posts with fewer than two inbound body links ({len(orphans)})", ""]
    lines += [f"- {n} inbound: {pid}" for n, pid in orphans] + [""]
    if EXTERNAL:
        lines += [f"## Dead external links ({len(dead)})", ""]
        lines += [f"- {status} {url}  (in {', '.join(pids)})" for status, url, pids in dead] or ["None."]
    report = "\n".join(lines) + "\n"
    print(report)
    if WRITE:
        import os
        os.makedirs("docs", exist_ok=True)
        open("docs/link-report.md", "w", encoding="utf-8").write(report)
    return 1 if broken_internal else 0


if __name__ == "__main__":
    sys.exit(main())
