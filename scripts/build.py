"""Build the portfolio page from GitHub.

Every public repo of GITHUB_USER with the `portfolio` topic becomes one or more project
cards. A repo describes its card(s) in a `portfolio.json` file at its root (one object, or a
list of objects for a repo that holds several projects). Repos without that file still get a
card from their GitHub description, language and topics. Projects that have no repo live in
data/manual-projects.json.

    python scripts/build.py          # writes _site/index.html

Set GITHUB_TOKEN to avoid the unauthenticated API rate limit.
"""
import html
import json
import os
import re
import sys
import urllib.error
import urllib.request

GITHUB_USER = "WeeKen99"
TOPIC = "portfolio"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Category used when a repo has no portfolio.json, picked from its topics
TOPIC_CATEGORIES = {
    "data-engineering": "Data Engineering",
    "machine-learning": "Machine Learning",
    "nlp": "NLP & RAG",
    "rag": "NLP & RAG",
    "automation": "Automation",
    "software-engineering": "Software Engineering",
    "java": "Software Engineering",
    "research": "Research",
}


def api(url):
    req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json", "User-Agent": "portfolio-build"})
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def fetch_portfolio_json(repo):
    url = f"https://raw.githubusercontent.com/{repo['full_name']}/{repo['default_branch']}/portfolio.json"
    try:
        with urllib.request.urlopen(url, timeout=30) as r:
            data = json.load(r)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise
    return data if isinstance(data, list) else [data]


def fallback_entry(repo):
    topics = repo.get("topics", [])
    category = next((TOPIC_CATEGORIES[t] for t in topics if t in TOPIC_CATEGORIES), "Other")
    tags = ([repo["language"]] if repo.get("language") else []) + [
        t.replace("-", " ").title() for t in topics if t != TOPIC and t not in TOPIC_CATEGORIES
    ]
    return {
        "title": repo["name"].replace("-", " ").replace("_", " ").title(),
        "category": category,
        "summary": repo.get("description") or "",
        "tags": tags[:5],
    }


def repo_projects():
    repos = api(f"https://api.github.com/users/{GITHUB_USER}/repos?per_page=100&type=owner")
    projects = []
    for repo in repos:
        if repo["private"] or repo.get("archived") or TOPIC not in repo.get("topics", []):
            continue
        entries = fetch_portfolio_json(repo) or [fallback_entry(repo)]
        branch = repo["default_branch"]
        for e in entries:
            path = e.get("path", "").strip("/")
            e["link"] = f"{repo['html_url']}/tree/{branch}/{path}" if path else repo["html_url"]
            e["_pushed"] = repo["pushed_at"]
            feat = e.get("featured")
            if feat and feat.get("image") and not feat["image"].startswith("http"):
                feat["image"] = f"https://raw.githubusercontent.com/{repo['full_name']}/{branch}/{feat['image'].lstrip('/')}"
            projects.append(e)
        print(f"  {repo['name']}: {len(entries)} card(s)")
    return projects


def manual_projects():
    with open(os.path.join(ROOT, "data", "manual-projects.json"), encoding="utf-8") as f:
        return json.load(f)


def esc(s):
    return html.escape(str(s), quote=True)


def tags_html(tags):
    return "".join(f"<span>{esc(t)}</span>" for t in tags)


def category_html(p):
    badge = f' · <span class="kaggle">{esc(p["badge"])}</span>' if p.get("badge") else ""
    return f"{esc(p['category'])}{badge}"


def result_html(result, indent):
    return f'{indent}<div><span class="result">{esc(result)}</span></div>\n' if result else ""


def grid_card(p):
    return (
        f'      <article class="pcard" data-cat="{esc(p["category"])}">\n'
        f'        <span class="cat">{category_html(p)}</span>\n'
        f'        <h3>{esc(p["title"])}</h3>\n'
        f'        <p>{esc(p["summary"])}</p>\n'
        + result_html(p.get("result"), "        ")
        + f'        <div class="tags">{tags_html(p.get("tags", []))}</div>\n'
        f'        <a class="link" href="{esc(p["link"])}" target="_blank" rel="noopener">View on GitHub →</a>\n'
        f'      </article>\n'
    )


def featured_card(p):
    f = p["featured"]
    return (
        f'      <article class="fcard reveal">\n'
        f'        <div class="fcard-img"><img src="{esc(f["image"])}" alt="{esc(f.get("imageAlt", p["title"]))}" loading="lazy"></div>\n'
        f'        <div class="fcard-body">\n'
        f'          <span class="cat">{category_html(p)}</span>\n'
        f'          <h3>{esc(p["title"])}</h3>\n'
        f'          <p>{esc(f.get("summary", p["summary"]))}</p>\n'
        + result_html(f.get("result", p.get("result")), "          ")
        + f'          <div class="tags">{tags_html(f.get("tags", p.get("tags", [])))}</div>\n'
        f'          <a class="link" href="{esc(p["link"])}" target="_blank" rel="noopener">View project →</a>\n'
        f'        </div>\n'
        f'      </article>\n'
    )


def sort_projects(projects):
    # New projects without an explicit "order" go first, most recently pushed first;
    # the rest follow in their "order".
    new = sorted((p for p in projects if "order" not in p), key=lambda p: p.get("_pushed", ""), reverse=True)
    ordered = sorted((p for p in projects if "order" in p), key=lambda p: p["order"])
    return new + ordered


def main():
    print("Reading repos tagged '%s'..." % TOPIC)
    projects = repo_projects() + manual_projects()
    required = ("title", "category", "summary", "link")
    for p in projects:
        missing = [k for k in required if not p.get(k)]
        if missing:
            sys.exit(f"Project {p.get('title', '?')} is missing {missing}")
    if len(projects) < 3:
        sys.exit(f"Only {len(projects)} projects found; refusing to publish a near-empty page.")

    projects = sort_projects(projects)
    featured = [p for p in projects if p.get("featured") and p["featured"].get("image")][:3]

    with open(os.path.join(ROOT, "src", "index.template.html"), encoding="utf-8") as f:
        page = f.read()
    for marker in ("<!-- @FEATURED -->", "<!-- @PROJECTS -->", "@PROJECT_COUNT"):
        if page.count(marker) != 1:
            sys.exit(f"Template must contain {marker} exactly once")
    page = page.replace("<!-- @FEATURED -->", "".join(featured_card(p) for p in featured).rstrip("\n"))
    page = page.replace("<!-- @PROJECTS -->", "\n".join(grid_card(p) for p in projects).rstrip("\n"))
    page = page.replace("@PROJECT_COUNT", str(len(projects)))

    out = os.path.join(ROOT, "_site")
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, "index.html"), "w", encoding="utf-8", newline="\n") as f:
        f.write(page)
    print(f"Built _site/index.html: {len(projects)} projects, {len(featured)} featured")


if __name__ == "__main__":
    main()
