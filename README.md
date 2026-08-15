# Awesome DeepSeek Harness

A curated and ranked collection of popular DeepSeek Harness plugins, tools, projects and resources.

> **Discover → Track → Rank → Explore**

This repository is the open data and community layer for the DeepSeek Harness ecosystem.

## 🔥 Popular

The ranking is based primarily on GitHub community signals such as stars and star growth.

<!-- POPULAR_START -->
| Rank | Project | Stars | 7d Growth | Description |
|---:|---|---:|---:|---|
| 1 | [deepseek-ai/deepseek-harness](https://github.com/deepseek-ai/deepseek-harness) | 97,081 | — | DeepSeek Harness: Everything is a Plugin. |
| 2 | [nexu-io/open-design](https://github.com/nexu-io/open-design) | 86,365 | — | 🎨 The open-source Claude Design alternative. 🖥️ Local-first desktop app. 🖼️ Your coding... |
| 3 | [CherryHQ/cherry-studio](https://github.com/CherryHQ/cherry-studio) | 50,480 | — | AI productivity studio with smart chat, autonomous agents, and 300+ assistants. Unified... |
| 4 | [zhayujie/CowAgent](https://github.com/zhayujie/CowAgent) | 46,511 | — | Open-source super AI assistant & Agent Harness. Plans tasks, runs tools and skills, sel... |
| 5 | [Hmbown/CodeWhale](https://github.com/Hmbown/CodeWhale) | 40,776 | — | Open-source, community-driven agent harness |
| 6 | [titanwings/colleague-skill](https://github.com/titanwings/colleague-skill) | 22,066 | — | 将冰冷的离别化为温暖的 Skill，欢迎加入数字生命1.0！Transforming cold farewells into warm skills? It's giving... |
| 7 | [liyupi/ai-guide](https://github.com/liyupi/ai-guide) | 18,377 | — | 程序员鱼皮的 AI 资源大全 + Vibe Coding 零基础教程，分享 OpenClaw 保姆级教程、大模型玩法（DeepSeek / GPT / Gemini / Cl... |
| 8 | [tt-a1i/archify](https://github.com/tt-a1i/archify) | 12,578 | — | Agent skill for beautiful, verifiable architecture, workflow, sequence, data-flow, and ... |
| 9 | [Devin-AXIS/iPolloWork](https://github.com/Devin-AXIS/iPolloWork) | 4,017 | — | A next-generation, source-available AI workspace with a self-evolving agent runtime for... |
| 10 | [crafter-station/petdex](https://github.com/crafter-station/petdex) | 3,793 | — | A public gallery of animated pets for Codex, Claude Code, DeepSeek Harness, Hermes, Ope... |
<!-- POPULAR_END -->

## 🚀 Trending

Projects with the strongest recent star growth.

<!-- TRENDING_START -->
_No data yet._
<!-- TRENDING_END -->

## 🆕 New & Rising

New projects that are gaining attention.

<!-- RISING_START -->
| Rank | Project | Stars | 7d Growth | Description |
|---:|---|---:|---:|---|
| 1 | [deepseek-ai/deepseek-harness](https://github.com/deepseek-ai/deepseek-harness) | 97,081 | — | DeepSeek Harness: Everything is a Plugin. |
| 2 | [nexu-io/open-design](https://github.com/nexu-io/open-design) | 86,365 | — | 🎨 The open-source Claude Design alternative. 🖥️ Local-first desktop app. 🖼️ Your coding... |
| 3 | [CherryHQ/cherry-studio](https://github.com/CherryHQ/cherry-studio) | 50,480 | — | AI productivity studio with smart chat, autonomous agents, and 300+ assistants. Unified... |
| 4 | [zhayujie/CowAgent](https://github.com/zhayujie/CowAgent) | 46,511 | — | Open-source super AI assistant & Agent Harness. Plans tasks, runs tools and skills, sel... |
| 5 | [Hmbown/CodeWhale](https://github.com/Hmbown/CodeWhale) | 40,776 | — | Open-source, community-driven agent harness |
| 6 | [titanwings/colleague-skill](https://github.com/titanwings/colleague-skill) | 22,066 | — | 将冰冷的离别化为温暖的 Skill，欢迎加入数字生命1.0！Transforming cold farewells into warm skills? It's giving... |
| 7 | [liyupi/ai-guide](https://github.com/liyupi/ai-guide) | 18,377 | — | 程序员鱼皮的 AI 资源大全 + Vibe Coding 零基础教程，分享 OpenClaw 保姆级教程、大模型玩法（DeepSeek / GPT / Gemini / Cl... |
| 8 | [tt-a1i/archify](https://github.com/tt-a1i/archify) | 12,578 | — | Agent skill for beautiful, verifiable architecture, workflow, sequence, data-flow, and ... |
| 9 | [Devin-AXIS/iPolloWork](https://github.com/Devin-AXIS/iPolloWork) | 4,017 | — | A next-generation, source-available AI workspace with a self-evolving agent runtime for... |
| 10 | [crafter-station/petdex](https://github.com/crafter-station/petdex) | 3,793 | — | A public gallery of animated pets for Codex, Claude Code, DeepSeek Harness, Hermes, Ope... |
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
