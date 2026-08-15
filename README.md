# Awesome DeepSeek Harness

A curated and ranked collection of popular DeepSeek Harness plugins, tools, projects and resources.

> **Discover → Track → Rank → Explore**

This repository is building an open, historical dataset of the DeepSeek Harness ecosystem.

## 🔥 Popular

Popularity is primarily based on GitHub Stars, with recent star growth becoming a secondary signal once enough history exists.

<!-- POPULAR_START -->
Run **Actions → Update DSH Rankings → Run workflow** to populate this section.
<!-- POPULAR_END -->

## 🚀 Trending

Projects gaining stars fastest recently.

<!-- TRENDING_START -->
Run the workflow to populate this section.
<!-- TRENDING_END -->

## 📈 Rising

Lower-base projects showing unusually strong recent growth.

<!-- RISING_START -->
Run the workflow to populate this section.
<!-- RISING_END -->

## 📊 What we collect

### GitHub
- Stars and historical star snapshots
- Forks and watchers
- Issues and repository activity timestamps
- Topics, language and license
- Repository size, default branch, archive/fork status
- Discovery source

### Packages
When detectable without credentials:
- npm package name/version/weekly downloads
- PyPI package name/version

### Discovery sources
- GitHub repository search
- GitHub `dsh-plugin` topic
- Public DSH ecosystem catalogs
- Public competitor catalogs as additional discovery seeds

The project is **data-first**: ranking formulas can change later without losing historical observations.

## Methodology

### Popularity
Current version:
- **70%** normalized GitHub Stars
- **30%** normalized 7-day star gain, once enough history exists
- before 7 days of history, ranking falls back to Stars

### Trending
Trending emphasizes recent absolute star gain plus growth rate.

### Rising
Rising favors projects with a smaller existing audience but unusually strong recent growth.

No subjective AI quality score is used in the popularity ranking.

## Automation

GitHub Actions runs daily and can be triggered manually.

The pipeline:
1. discovers repositories from multiple public sources;
2. deduplicates candidates;
3. fetches repository metadata;
4. detects npm/PyPI packages where practical;
5. saves a daily immutable snapshot;
6. computes Popular / Trending / Rising;
7. updates the README;
8. commits generated data.

## Data

- `data/projects.json` — latest normalized dataset
- `data/history/YYYY-MM-DD.json` — daily snapshots
- `config/sources.json` — discovery sources
- `config/overrides.json` — explicit include/exclude controls

## License

CC0 1.0
