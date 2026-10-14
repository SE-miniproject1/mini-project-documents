# Backlog setup: step-by-step

Files: `create_backlog.sh` (does everything), `backlog.csv` (same data, for review or manual import), `BACKLOG.md` (readable plan).

## Option A: automatic (recommended, about 5 minutes)

One person with admin rights on the org/repo runs this (Aadish as project lead is the natural choice).

```bash
# 1. Install tools: GitHub CLI (https://cli.github.com) and jq. Then log in:
gh auth login
gh auth refresh -s project        # needed for GitHub Projects

# 2. Clone the repo and add the files
git clone https://github.com/SE-miniproject1/mini-project-documents.git
cd mini-project-documents
git checkout -b docs/backlog
mkdir -p planning
# copy create_backlog.sh, backlog.csv, BACKLOG.md into planning/

# 3. Create labels, sprint milestones, the Project board and 29 issues
bash planning/create_backlog.sh
```

If your code lives in a different repo, run `REPO=SE-miniproject1/<code-repo> bash planning/create_backlog.sh` so issues and the project are linked to that repo.

The script is safe to re-run for labels, milestones and the project, but it creates the issues again, so run it once only.

## Commit the planning files (via PR, as your working agreement requires)

```bash
git add planning/
git commit -m "docs: add product backlog, story points and sprint plan"
git push -u origin docs/backlog
gh pr create --title "Add product backlog and sprint plan" \
  --body "Backlog derived from SRS v1.0. 29 stories, 2 sprints, story points and owners assigned." \
  --reviewer Sonuaadi0706
```

A repo owner then reviews and merges the PR.

## Option B: manual, in the GitHub UI

1. Org page > Projects > New project > Board. Name it "BBMS Product Backlog".
2. Project > Settings: link it to the repo. Add a number field "Story Points" and a single-select field "Sprint" (Sprint 1, Sprint 2, Stretch).
3. Repo > Issues > Milestones: create "Sprint 1" (due 23 Oct), "Sprint 2" (due 30 Oct).
4. Create one issue per row of `backlog.csv`, set assignee and milestone, add to the project, fill the two fields.

## Checklist against the deliverable sheet

| Item | Where |
|---|---|
| 1a Project linked to repo | Script step "Project board" |
| 1b Backlog from FR and NFR | 29 issues covering REQ-1 to REQ-46 plus NFRs |
| 1c Story points | `Story Points` field and `SP-n` label |
| 1d Assign to members | Issue assignees |
| 1e Plan two sprints | Milestones "Sprint 1" and "Sprint 2" |
| 1f Dry run 12-16 Oct | Move 1-2 small stories (for example US-03) through branch, PR, review, merge |
| 2b Enable GitHub Actions | US-01 adds the workflow; also enable in repo Settings > Actions |

## Sprint 1 reminders (19-23 Oct)

- Each assignee raises the PR from a branch such as `feature/us-04-donor-registration`; a repo owner reviews and merges.
- Record the 1-minute demo video and upload it to the repo.
- Note any deviation from SRS, SAD or Test Plan as you go.
