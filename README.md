# Awesome DeepSeek Harness

A curated and ranked collection of popular DeepSeek Harness plugins, tools, projects and resources.

> **Discover → Track → Rank → Explore**

This repository is the open data and community layer for the DeepSeek Harness ecosystem.

## 🔥 Popular

The ranking is based primarily on GitHub community signals such as stars and star growth.

<!-- POPULAR_START -->
Run the GitHub Action once to populate this section.
<!-- POPULAR_END -->

## 🚀 Trending

Projects with the strongest recent star growth.

<!-- TRENDING_START -->
Run the GitHub Action once to populate this section.
<!-- TRENDING_END -->

## 🆕 New & Rising

New projects that are gaining attention.

<!-- RISING_START -->
Run the GitHub Action once to populate this section.
<!-- RISING_END -->

## Methodology

The first version intentionally focuses on **community popularity**, not subjective quality scores.

- Stars are the strongest signal.
- Recent star growth is the second major signal.
- Forks and contributor count are supporting signals.
- Repository activity is shown as context, not as a substitute for popularity.
- Every daily run stores a snapshot so growth can be measured over time.
- Candidate discovery is automated; false positives can be excluded through `config/overrides.json`.

As the dataset grows, the ranking model can be versioned without rewriting historical snapshots.

## Automation

A GitHub Actions workflow runs daily and can also be triggered manually.

It:
1. discovers candidate repositories from several GitHub searches;
2. deduplicates repositories;
3. records current GitHub metrics;
4. stores a dated snapshot;
5. calculates Popular / Trending / Rising;
6. updates this README;
7. commits the generated data back to the repository.

## License

CC0 1.0
