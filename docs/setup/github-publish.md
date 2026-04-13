# GitHub Publishing Guide

## Current state

This local repository currently has:

- no Git remote configured
- no commits yet

That means you can create a local branch immediately, but you cannot push until you connect a GitHub repository as `origin`.

## Recommended branch name

Use:

`hra-dashboard-deliverables`

## Local branch creation

```bash
git switch -c hra-dashboard-deliverables
```

## Stage and commit

```bash
git add .
git commit -m "Add HRA dashboard, deliverables, and documentation"
```

## Connect a new GitHub repo

Create an empty repository on GitHub first, then run:

```bash
git remote add origin <YOUR_GITHUB_REPO_URL>
```

Examples:

```bash
git remote add origin git@github.com:YOUR_USERNAME/YOUR_REPO.git
```

or

```bash
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
```

## Push the branch

```bash
git push -u origin hra-dashboard-deliverables
```

## Open a pull request

After pushing, open GitHub and create a pull request from:

- head branch: `hra-dashboard-deliverables`
- base branch: usually `main`

## If you want to keep the repo clean

Before pushing, confirm that you want to include only the HRA dashboard project content. This repo also contains local non-project material that has now been ignored, but you should still review `git status` before committing.
