# Misc Claude Projects

A grab-bag repo for small, one-off, and experimental projects.

## Layout

```
projects/
  _template/        # copy this to start a new project
  <project-name>/   # one folder per project, self-contained
```

## Starting a new project

```powershell
Copy-Item -Recurse projects/_template projects/my-new-project
```

Then fill in `projects/my-new-project/README.md`.

## Conventions

- Each project lives in its own folder under `projects/` using `kebab-case` names.
- Projects are self-contained: their own dependencies, README, and run instructions.
- No secrets in the repo — use a local `.env` (ignored by git) and commit a `.env.example`.

## Projects

| Project | Description | Status |
|---------|-------------|--------|
| _(none yet)_ | | |
