# CLAUDE.md

Guidance for Claude Code when working in this repo.

## What this repo is

A collection of small, unrelated side projects. Each folder under `projects/` is independent.

## Rules

- New projects go in `projects/<kebab-case-name>/`, started by copying `projects/_template/`.
- Keep each project self-contained: its own dependencies, config, and README with setup/run steps.
- Don't add dependencies or tooling at the repo root — put them inside the project folder.
- When creating a project, add a row to the **Projects** table in the root `README.md`.
- Never commit secrets; use `.env` (gitignored) plus a committed `.env.example`.
- Environment is Windows; give run commands in PowerShell.
