#!/usr/bin/env python3
"""
Discover DeepSeek Harness-related GitHub repositories, snapshot metrics,
calculate popularity/trending/rising rankings, and update README.md.

No third-party Python packages are required.
"""

import datetime as dt
import json
import math
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config"
DATA = ROOT / "data"
HISTORY = DATA / "history"
README = ROOT / "README.md"

API = "https://api.github.com"
TOKEN = os.environ.get("GITHUB_TOKEN", "")

HEADERS = {
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
    "User-Agent": "awesome-deepseek-harness-radar",
}
if TOKEN:
    HEADERS["Authorization"] = f"Bearer {TOKEN}"


def api_get(path, params=None):
    url = API + path
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers=HEADERS)
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as exc:
            if attempt == 4:
                raise
            time.sleep(2 ** attempt)


def load_json(path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def discover():
    sources = load_json(CONFIG / "sources.json", {})
    overrides = load_json(CONFIG / "overrides.json", {})
    excluded = set(overrides.get("exclude", []))
    forced = set(overrides.get("include", []))

    repos = {}
    for query in sources.get("searches", []):
        data = api_get("/search/repositories", {
            "q": query,
            "sort": sources.get("sort", "stars"),
            "order": sources.get("order", "desc"),
            "per_page": min(int(sources.get("per_query", 100)), 100),
        })
        for item in data.get("items", []):
            full_name = item["full_name"]
            if full_name in excluded:
                continue
            repos[full_name] = item

    # Explicit inclusions are fetched even if they do not match discovery queries.
    for full_name in forced:
        if full_name not in repos:
            owner, repo = full_name.split("/", 1)
            repos[full_name] = api_get(f"/repos/{owner}/{repo}")

    return list(repos.values())


def history_files():
    return sorted(HISTORY.glob("*.json"))


def load_history():
    snapshots = []
    for path in history_files():
        try:
            snapshots.append(json.loads(path.read_text(encoding="utf-8")))
        except Exception:
            pass
    return snapshots


def metric_at(snapshots, full_name, days):
    if not snapshots:
        return None
    target = dt.date.today() - dt.timedelta(days=days)
    best = None
    best_distance = 10**9
    for snap in snapshots:
        try:
            d = dt.date.fromisoformat(snap["date"])
        except Exception:
            continue
        distance = abs((d - target).days)
        if distance < best_distance and distance <= max(days * 2, 3):
            item = snap.get("projects", {}).get(full_name)
            if item:
                best = item
                best_distance = distance
    return best


def growth_pct(now, before):
    if before is None:
        return None
    old = before.get("stars", 0)
    if old <= 0:
        return None
    return (now - old) / old * 100.0


def log_norm(value, max_value):
    if max_value <= 0:
        return 0.0
    return math.log1p(value) / math.log1p(max_value)


def classify(repo):
    text = " ".join([
        repo.get("name", ""),
        repo.get("description") or "",
        " ".join(repo.get("topics") or []),
    ]).lower()

    if any(k in text for k in ["plugin", "dsh-plugin"]):
        return "Plugins"
    if any(k in text for k in ["desktop", "electron"]):
        return "Desktop"
    if any(k in text for k in ["tui", "terminal ui", "terminal"]):
        return "TUI"
    if any(k in text for k in ["mcp", "model context protocol"]):
        return "MCP"
    if any(k in text for k in ["guide", "handbook", "tutorial", "awesome"]):
        return "Guides & Resources"
    if any(k in text for k in ["web", "frontend", "ui"]):
        return "Web"
    return "Projects"


def build_projects(raw, snapshots):
    projects = []
    max_stars = max([r.get("stargazers_count", 0) for r in raw] or [1])

    for r in raw:
        name = r["full_name"]
        stars = int(r.get("stargazers_count", 0))
        forks = int(r.get("forks_count", 0))
        contributors = None
        # We deliberately do not make an extra API call per repository.
        # Contributor count can be added later through a batched/GraphQL collector.

        prev1 = metric_at(snapshots, name, 1)
        prev7 = metric_at(snapshots, name, 7)
        prev30 = metric_at(snapshots, name, 30)

        g1 = growth_pct(stars, prev1)
        g7 = growth_pct(stars, prev7)
        g30 = growth_pct(stars, prev30)

        popularity_base = log_norm(stars, max_stars)
        growth_signal = min(max((g7 or 0.0) / 100.0, 0.0), 2.0) / 2.0
        # Version 1: stars 70%, 7d growth 30%.
        # If there is no 7d history yet, fall back to stars only.
        score = popularity_base * 100.0
        if g7 is not None:
            score = (popularity_base * 0.70 + growth_signal * 0.30) * 100.0

        projects.append({
            "full_name": name,
            "name": r.get("name"),
            "html_url": r.get("html_url"),
            "description": r.get("description") or "",
            "stars": stars,
            "forks": forks,
            "open_issues": int(r.get("open_issues_count", 0)),
            "language": r.get("language"),
            "license": (r.get("license") or {}).get("spdx_id"),
            "topics": r.get("topics") or [],
            "default_branch": r.get("default_branch"),
            "created_at": r.get("created_at"),
            "updated_at": r.get("updated_at"),
            "pushed_at": r.get("pushed_at"),
            "category": classify(r),
            "stars_1d_growth_pct": g1,
            "stars_7d_growth_pct": g7,
            "stars_30d_growth_pct": g30,
            "popularity_score": round(score, 2),
        })

    projects.sort(key=lambda x: (-x["popularity_score"], -x["stars"], x["full_name"].lower()))
    for i, p in enumerate(projects, 1):
        p["rank"] = i

    return projects


def ranking_table(items, limit=10, growth_key="stars_7d_growth_pct"):
    rows = []
    for i, p in enumerate(items[:limit], 1):
        growth = p.get(growth_key)
        growth_text = "—" if growth is None else f"{growth:+.1f}%"
        desc = re.sub(r"\s+", " ", p["description"]).strip()
        if len(desc) > 90:
            desc = desc[:87] + "..."
        rows.append(
            f"| {i} | [{p['full_name']}]({p['html_url']}) | "
            f"{p['stars']:,} | {growth_text} | {desc or '—'} |"
        )
    if not rows:
        return "_No data yet._"
    return "\n".join([
        "| Rank | Project | Stars | 7d Growth | Description |",
        "|---:|---|---:|---:|---|",
        *rows,
    ])


def update_readme(projects):
    popular = sorted(projects, key=lambda x: (-x["popularity_score"], -x["stars"]))
    with_growth = [p for p in projects if p.get("stars_7d_growth_pct") is not None and p["stars_7d_growth_pct"] > 0]
    trending = sorted(with_growth, key=lambda x: (-x["stars_7d_growth_pct"], -x["stars"]))
    rising = sorted(
        projects,
        key=lambda x: (
            -(x["stars_7d_growth_pct"] if x.get("stars_7d_growth_pct") is not None else -999),
            -x["stars"],
        ),
    )

    text = README.read_text(encoding="utf-8")

    replacements = {
        "POPULAR": ranking_table(popular, 10),
        "TRENDING": ranking_table(trending, 10),
        "RISING": ranking_table(rising, 10),
    }

    for key, value in replacements.items():
        pattern = rf"(<!-- {key}_START -->)(.*?)(<!-- {key}_END -->)"
        text, count = re.subn(pattern, rf"\1\n{value}\n\3", text, flags=re.S)
        if count == 0:
            raise RuntimeError(f"README marker missing: {key}")

    README.write_text(text, encoding="utf-8")


def save_snapshot(projects):
    today = dt.date.today().isoformat()
    snapshot = {
        "date": today,
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "projects": {
            p["full_name"]: {
                "stars": p["stars"],
                "forks": p["forks"],
                "updated_at": p["updated_at"],
                "pushed_at": p["pushed_at"],
            }
            for p in projects
        },
    }
    HISTORY.mkdir(parents=True, exist_ok=True)
    (HISTORY / f"{today}.json").write_text(
        json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (DATA / "projects.json").write_text(
        json.dumps({
            "generated_at": snapshot["generated_at"],
            "projects": projects,
        }, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def main():
    print("Discovering repositories...")
    raw = discover()
    print(f"Discovered {len(raw)} unique repositories.")

    snapshots = load_history()
    projects = build_projects(raw, snapshots)

    save_snapshot(projects)
    update_readme(projects)

    print("Updated rankings.")
    for p in projects[:10]:
        print(f"{p['rank']:>2}. {p['full_name']:<45} stars={p['stars']:<6} score={p['popularity_score']}")


if __name__ == "__main__":
    main()
