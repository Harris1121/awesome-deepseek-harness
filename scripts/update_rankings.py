#!/usr/bin/env python3
import datetime as dt
import json
import math
import os
import re
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOKEN = os.environ.get("GITHUB_TOKEN", "")
HEADERS = {
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
    "User-Agent": "awesome-deepseek-harness-ranking",
}
if TOKEN:
    HEADERS["Authorization"] = f"Bearer {TOKEN}"

def api_repo(full_name):
    req = urllib.request.Request("https://api.github.com/repos/" + full_name, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=15) as response:
        return json.loads(response.read().decode("utf-8"))

def load_snapshots():
    snapshots = []
    history_dir = ROOT / "data/history"
    if not history_dir.exists():
        return snapshots
    for path in sorted(history_dir.glob("*.json")):
        try:
            snapshots.append(json.loads(path.read_text(encoding="utf-8")))
        except Exception:
            pass
    return snapshots

def prior(snapshots, name, days):
    target = dt.date.today() - dt.timedelta(days=days)
    candidates = []
    for snapshot in snapshots:
        try:
            snapshot_date = dt.date.fromisoformat(snapshot["date"])
        except Exception:
            continue
        item = snapshot.get("projects", {}).get(name)
        if item:
            candidates.append((abs((snapshot_date - target).days), item))
    if not candidates:
        return None
    candidates.sort(key=lambda x: x[0])
    distance, item = candidates[0]
    return item if distance <= max(2, days // 2) else None

def pct(now, before):
    if not before:
        return None
    old = before.get("stars", 0)
    if old <= 0:
        return None
    return (now - old) / old * 100.0

def gain(now, before):
    if not before:
        return None
    return now - before.get("stars", 0)

def table(items):
    if not items:
        return "_Not enough history yet._"
    lines = [
        "| Rank | Project | Stars | 7d Gain | 7d Growth |",
        "|---:|---|---:|---:|---:|",
    ]
    for i, project in enumerate(items[:10], 1):
        gain_7d = project.get("gain_7d")
        growth_7d = project.get("growth_7d")
        gain_text = "—" if gain_7d is None else f"{gain_7d:+,}"
        growth_text = "—" if growth_7d is None else f"{growth_7d:+.1f}%"
        lines.append(
            f"| {i} | [{project['full_name']}]({project['html_url']}) | "
            f"{project['stars']:,} | {gain_text} | {growth_text} |"
        )
    return "\n".join(lines)

def update_readme(projects):
    popular = sorted(projects, key=lambda p: (-p["popularity_score"], -p["stars"]))
    trending = [p for p in projects if (p.get("gain_7d") or 0) > 0]
    trending.sort(key=lambda p: (-p["gain_7d"], -(p.get("growth_7d") or 0), -p["stars"]))
    rising = [p for p in projects if (p.get("growth_7d") or 0) > 0]
    rising.sort(key=lambda p: (-p["rising_score"], -p["stars"]))

    readme_path = ROOT / "README.md"
    text = readme_path.read_text(encoding="utf-8")
    for key, value in [("POPULAR", table(popular)), ("TRENDING", table(trending)), ("RISING", table(rising))]:
        pattern = rf"(<!-- {key}_START -->)(.*?)(<!-- {key}_END -->)"
        text = re.sub(pattern, rf"\1\n{value}\n\3", text, flags=re.S)
    readme_path.write_text(text, encoding="utf-8")

def main():
    repositories_path = ROOT / "data/repositories.json"
    pool = json.loads(repositories_path.read_text(encoding="utf-8")).get("repositories", [])
    snapshots = load_snapshots()
    print(f"[1/4] Updating GitHub metrics for {len(pool)} repositories...", flush=True)

    projects = []
    failures = []
    for index, entry in enumerate(pool, 1):
        name = entry["full_name"]
        try:
            repo = api_repo(name)
            stars = int(repo.get("stargazers_count", 0))
            previous_7d = prior(snapshots, name, 7)
            previous_30d = prior(snapshots, name, 30)
            projects.append({
                "full_name": name,
                "html_url": repo.get("html_url"),
                "description": repo.get("description") or "",
                "stars": stars,
                "forks": int(repo.get("forks_count", 0)),
                "watchers": int(repo.get("subscribers_count", 0)),
                "open_issues": int(repo.get("open_issues_count", 0)),
                "language": repo.get("language"),
                "license": (repo.get("license") or {}).get("spdx_id"),
                "created_at": repo.get("created_at"),
                "updated_at": repo.get("updated_at"),
                "pushed_at": repo.get("pushed_at"),
                "topics": repo.get("topics") or [],
                "sources": entry.get("sources", []),
                "first_seen": entry.get("first_seen"),
                "gain_7d": gain(stars, previous_7d),
                "growth_7d": pct(stars, previous_7d),
                "gain_30d": gain(stars, previous_30d),
                "growth_30d": pct(stars, previous_30d),
            })
        except Exception as error:
            failures.append({"repo": name, "error": str(error)})
        if index % 25 == 0 or index == len(pool):
            print(f"  {index}/{len(pool)} complete; failures={len(failures)}", flush=True)

    print("[2/4] Computing popularity scores...", flush=True)
    max_stars = max([p["stars"] for p in projects] or [1])
    max_gain = max([max(p.get("gain_7d") or 0, 0) for p in projects] or [1])
    for project in projects:
        star_score = math.log1p(project["stars"]) / math.log1p(max_stars)
        if project.get("gain_7d") is None:
            popularity = star_score
        else:
            gain_score = math.log1p(max(project["gain_7d"], 0)) / math.log1p(max_gain) if max_gain > 0 else 0
            popularity = 0.70 * star_score + 0.30 * gain_score
        project["popularity_score"] = round(popularity * 100, 2)
        growth = max(project.get("growth_7d") or 0, 0)
        star_gain = max(project.get("gain_7d") or 0, 0)
        project["rising_score"] = round(math.log1p(star_gain) * growth, 3)

    print("[3/4] Saving snapshot/data...", flush=True)
    data_dir = ROOT / "data"
    history_dir = ROOT / "data/history"
    data_dir.mkdir(parents=True, exist_ok=True)
    history_dir.mkdir(parents=True, exist_ok=True)

    now = dt.datetime.now(dt.timezone.utc).isoformat()
    today = dt.date.today().isoformat()
    (data_dir / "projects.json").write_text(
        json.dumps({"generated_at": now, "projects": projects, "failures": failures}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    snapshot = {
        "date": today,
        "generated_at": now,
        "projects": {p["full_name"]: {"stars": p["stars"], "forks": p["forks"]} for p in projects},
    }
    (history_dir / f"{today}.json").write_text(
        json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    print("[4/4] Updating README...", flush=True)
    update_readme(projects)
    print(f"Done. Updated {len(projects)} repositories; failures={len(failures)}.", flush=True)

if __name__ == "__main__":
    main()
