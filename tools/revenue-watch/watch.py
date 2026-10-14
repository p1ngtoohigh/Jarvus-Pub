#!/usr/bin/env python3
"""HYDRA public paid-work monitor; reports candidate links, never applies or pays."""
import datetime as dt
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

API = "https://api.github.com"
REPO = os.getenv("GITHUB_REPOSITORY", "")
TOKEN = os.getenv("GITHUB_TOKEN", "")
TITLE = "[HYDRA] Paid work lead watch"

def request(url, method="GET", payload=None):
    data = json.dumps(payload).encode() if payload is not None else None
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "hydra-revenue-watch/1.0"}
    if TOKEN:
        headers["Authorization"] = "Bearer " + TOKEN
    if data is not None:
        headers["Content-Type"] = "application/json"
    with urllib.request.urlopen(urllib.request.Request(url, data=data, headers=headers, method=method), timeout=20) as response:
        return json.load(response)

def search():
    since = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=3)).date().isoformat()
    queries = [
        f"is:issue is:open label:bounty updated:>={since}",
        f'is:issue is:open "bounty" created:>={since}',
        f'is:issue is:open "paid" "Shopify" created:>={since}',
    ]
    found = {}
    for query in queries:
        url = API + "/search/issues?" + urllib.parse.urlencode({"q": query, "sort": "updated", "order": "desc", "per_page": 30})
        try:
            for item in request(url).get("items", []):
                if item.get("pull_request"):
                    continue
                title = item.get("title", "")
                body = (item.get("body") or "")[:3000]
                if not re.search(r"\$\s*\d{1,5}|\b(?:usd|paid bounty|cash bounty|payment)\b", title + "\n" + body, re.I):
                    continue
                if re.search(r"\b(?:bounty watcher|bounty plaza|leaderboard|bounty close)\b", title, re.I):
                    continue
                if item.get("user", {}).get("type") == "Bot":
                    continue
                found[item["html_url"]] = {"title": title[:160], "url": item["html_url"], "updated": item.get("updated_at", "")}
        except (urllib.error.URLError, TimeoutError, ValueError) as exc:
            print("Search failed:", query, str(exc), file=sys.stderr)
    return list(found.values())

def main():
    leads = search()
    print(json.dumps({"candidate_count": len(leads), "candidates": leads[:20]}, indent=2))
    if not (REPO and TOKEN):
        print("Read-only mode: no repository token.")
        return
    url = f"{API}/repos/{REPO}/issues"
    issues = request(url + "?state=open&per_page=100")
    issue = next((x for x in issues if x.get("title") == TITLE and not x.get("pull_request")), None)
    seen = set(re.findall(r"<!-- seen:(https://github\.com/[^ ]+) -->", (issue or {}).get("body") or ""))
    fresh = [x for x in leads if x["url"] not in seen][:5]
    if not fresh:
        print("No new candidates.")
        return
    lines = [f'- [{x["title"]}]({x["url"]}) — updated {x["updated"]}' for x in fresh]
    note = "\n\n**Unverified leads, not contracts.** Confirm funding, eligibility, and AI-use rules. No proposal was submitted."
    markers = "\n".join(f'<!-- seen:{x["url"]} -->' for x in fresh)
    if issue:
        request(issue["url"], "PATCH", {"body": (issue.get("body") or "") + "\n" + markers})
        request(issue["comments_url"], "POST", {"body": "New paid-work candidates:\n\n" + "\n".join(lines) + note})
        print("Updated", issue["html_url"])
    else:
        body = "HYDRA lead watch. Public candidate links only; no automatic proposals, purchases, or contracts.\n\n" + "\n".join(lines) + note + "\n" + markers
        created = request(url, "POST", {"title": TITLE, "body": body})
        print("Created", created["html_url"])

if __name__ == "__main__":
    main()
