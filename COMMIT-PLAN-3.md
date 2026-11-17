# Commit Plan — Deliverable 3

Blood Bank Management System · Organisation [SE-miniproject1](https://github.com/SE-miniproject1)

Source: `SE_Mini_Project_Delivereables_Part-3.pdf`. It asks for updated test cases, completed testing with four reports in `docs/`, and an optional Sprint 3. The dates in the PDF (2 to 6 November) have passed, so do this as fast as you can and tell the faculty the submission is late.

## 1. What is already done (Aadish, branch `test/aadish-cases`)

Review and merge this first. Everything else depends on it.

- `pyproject.toml`: `branch = true`, so coverage now measures branches. Needed for the Branch Coverage Report.
- 8 new tests in `src/core/tests/test_security_validation.py` for IT-06, SV-04, SV-06 and SV-07. The suite is now **584 tests, all pass**, 98 percent line and branch coverage, ruff clean.
- Test IDs added to existing tests for SV-04, SV-07 and SV-08.
- Test Plan: all 16 collection cases (UT-10 to UT-16, IT-05 to IT-09, ST-05 to ST-08) and all 8 security cases (SV-01 to SV-08) now have an Actual Result and Test Result. Section 6 (environment) is corrected.
- `docs/DEVIATIONS.md`: D-84 to D-89 added.
- `planning/BACKLOG.md`: Sprint 3 note. No Sprint 3 was needed.
- `tools/system_validation_report.py` and `docs/test-reports/System-Validation-Report.md`. The report is generated from the Test Plan, so it fills itself in as you merge your results. Aadish regenerates it at the end.

## 2. Order of work

| Step | Who | What | Needs |
|---|---|---|---|
| 0 | Aadish | Open the PR for `test/aadish-cases`, get it approved and merged | |
| 1 | Balaraj, Dhanya, Niveditha | Branch from the new `main`. Update and run your cases, fill the results in `docs/Test-Plan.md` | Step 0 |
| 2 | Balaraj, Dhanya, Niveditha | Write your report in `docs/test-reports/` | Step 0 |
| 3 | Everyone | Review one PR each (section 5) | |
| 4 | Aadish | Regenerate the System Validation Report | Steps 1 to 3 merged |
| 5 | Balaraj | Sections 7 and 14 of the Test Plan, Test Summary, Word rebuild | Step 4 |

Steps 1 and 2 can run in parallel. Do not wait for each other. Only Balaraj's step 5 has to be last.

## 3. Rules that apply to everyone

1. **Branch from current `main`:** `git checkout main && git pull && git checkout -b test/<yourname>-cases`.
2. **One PR per report, one per case group.** Small PRs merge faster and conflict less.
3. **Edit only your own rows** in `docs/Test-Plan.md`. Never reformat the file. Never touch another person's rows. Git then merges your rows cleanly.
4. **Deviation numbers.** Use your own range so nobody collides. Aadish used D-84 to D-89.
   - Balaraj: D-90 to D-95
   - Dhanya: D-96 to D-101
   - Niveditha: D-102 to D-107
   When two PRs both append to `DEVIATIONS.md` you will get a conflict at the end of the file. Keep both sets of rows.
5. **Filling a result.** Actual Result says what really happened and names the test file, as UT-40 does. Test Result is one of `Passed`, `Failed`, `Passed with deviation`, `Partly executed`, `Not executed`. If the system differs from the plan, write the difference in `DEVIATIONS.md` and refer to it in the case. Never edit an expected result to hide a difference.
6. **Never mark a case Passed that did not run.** A case that needs a person (a browser, a deployed server) must be run by a person, with the date.
7. **Tagging a test.** Put the case ID in the test's docstring, for example `"""UT-22 (REQ-21)."""`. A range such as `UT-13 to UT-15` counts as tagging all three. A case with no matching test needs a new test or a manual run.
8. **Before every push**, run from `Deliverable-1/`:
   ```bash
   export BBMS_ENV=test DJANGO_SECRET_KEY=local-test
   ruff check src && ruff format --check src
   python src/manage.py makemigrations --check --dry-run
   python src/manage.py test src
   python3 tools/check_traceability.py
   ```
   All five must pass. CI runs the same.
9. **Commit from your own account** with your own name. Message format: `<type>(<area>): <what>`. Types used so far: `docs`, `test`, `build`, `fix`.
10. **Do not merge your own PR.** Someone else approves it (section 5).

## 4. Tasks per person

### Aadish
Done (section 1). Remaining:
- Open the PR. Suggested split into three commits on the branch:
  1. `test(security): add IT-06, SV-04, SV-06 and SV-07 validation tests` (the new test file and the three docstring tags)
  2. `build(coverage): measure branch coverage` (`pyproject.toml`)
  3. `docs(test-plan): record collection and security results, fix environment section, add D-84 to D-89 and Sprint 3 note` (Test Plan, DEVIATIONS, BACKLOG, report script and report)
- After the others merge, run `python3 tools/system_validation_report.py`, commit `docs(test-reports): regenerate the System Validation Report`.
- Review Niveditha's PRs.

### Balaraj — A.1 donor registration and A.7 nonfunctional. Unit Test Report. Final step.
Branch `test/balaraj-cases`.
1. **Cases (17 + 6).** UT-01 to UT-09, IT-01 to IT-04, ST-01 to ST-04 are tagged. Run them, read each test to confirm it matches the case, record the results. ST-25 to ST-29 are tagged in `core/tests`. ST-30 Quality has no test: its evidence is CI's 70 percent gate (actual 98 percent) and the ruff check. Say so in the Actual Result.
   Commit: `docs(test-plan): record results for donor registration and nonfunctional cases`
2. **Unit Test Report.**
   ```bash
   mkdir -p docs/test-reports
   python src/manage.py test src --verbosity 2 > docs/test-reports/unit-test-output.txt 2>&1
   ```
   Write `docs/test-reports/Unit-Test-Report.md`: environment, command, 584 tests with 1 skipped (name it and say why), a table of UT-01 to UT-48 with results, any failures. Take the UT results from the Test Plan after Dhanya and Niveditha merge, or list their UT cases as pending until then.
   Commit: `docs(test-reports): add the Unit Test Report`
3. **Last, after step 4 above:** update section 7 (real dates instead of "to be confirmed", and delete the line saying no test was executed) and section 14 (executed, passed, failed, pending per level, copied from the final Test Plan). Write a short Test Summary Report (section 8 of the plan lists it). Run `python3 tools/check_traceability.py`, then `pip install -r tools/requirements.txt && python3 tools/build_docx.py` and commit the regenerated Word file in `submission/`.
   Commit: `docs(test-plan): update schedule and metrics` then `build: regenerate the Word copy of the Test Plan`

### Dhanya — A.3 inventory, A.4 requests. Code Coverage Report.
Branch `test/dhanya-cases`.
1. **Cases (16 + 17).** UT-17 UT-18 UT-20 UT-21 UT-24, IT-10 IT-11 IT-13, ST-09 ST-10 ST-11 and all of A.4 (UT-25 to UT-33, IT-14 to IT-17, ST-13 to ST-16) are tagged in `inventory/tests`, `audit/tests` and `bloodrequests/tests`. Not tagged: **UT-19 inventory query, UT-22 transfer, UT-23 discard, IT-12 transfer and discard audit, ST-12 inventory console.** US-14 built those features, so look in `inventory/tests/test_actions.py` and `test_console.py`, tag the right tests, and update the case wording to the built behaviour. For allocation, confirm the tests assert the refusal of expired, wrong-group and untested units, not only the success path.
   Commits: `test(inventory): tag the US-14 tests with their Test Plan cases` and `docs(test-plan): record results for inventory and request cases`
2. **Code Coverage Report** (after Aadish's PR merges).
   ```bash
   coverage run src/manage.py test src
   coverage report > docs/test-reports/coverage-summary.txt
   coverage html -d docs/test-reports/coverage-html
   ```
   Write `docs/test-reports/Code-Coverage-Report.md`: date, commit, tool and version, TOTAL (98 percent, 7,668 statements, 111 missed when checked, rerun to confirm), a per-app table, the least covered files and why, the NFR-Q5 70 percent threshold. Do not change the omit rules to raise the number. If `coverage-html` is large, commit only the summary and the Markdown and say how to regenerate.
   Commit: `docs(test-reports): add the Code Coverage Report`

### Niveditha — A.5 camps, A.6 search, notifications, reports. Branch Coverage Report.
Branch `test/niveditha-cases`.
1. **Cases (12 + 20).** A.5 is tagged except **IT-20 camp collection to inventory** (look in `camps/tests/test_collection_link.py`). In A.6, UT-40, IT-21 and ST-20 already have results but the test file `core/tests/test_availability.py` carries no tag: add it. UT-41 to UT-46, IT-22 to IT-25, ST-21 and ST-23 are tagged. Not tagged: **UT-47 user administration, UT-48 configuration store, IT-26, ST-24 administration, ST-22 reporting.** The tests exist in `accounts/tests/test_admin.py`, `core/tests/test_config.py` and `reports/tests/`. Read them, tag them, record. Notification cases run against stubbed SMS and email: say so (D-73 to D-78).
   Commits: `test(search): tag availability tests with UT-40, IT-21 and ST-20`, `test: tag admin, configuration and report tests with their cases`, `docs(test-plan): record results for camp, search, notification and report cases`
2. **Branch Coverage Report** (after Aadish's PR merges).
   ```bash
   coverage run src/manage.py test src
   coverage report --show-missing > docs/test-reports/branch-coverage-summary.txt
   coverage json -o docs/test-reports/branch-coverage.json
   ```
   Write `docs/test-reports/Branch-Coverage-Report.md`: date, commit, tool, total branches and partial branches (884 and 47 when checked, rerun to confirm), a per-app table with the Branch and BrPart columns, the ten files with the most partial branches and why each is uncovered. State clearly that this report counts branches and Code Coverage counts lines.
   Commit: `docs(test-reports): add the Branch Coverage Report`

## 5. Who reviews whom

| PR author | Reviewer |
|---|---|
| Aadish | Balaraj |
| Balaraj | Dhanya |
| Dhanya | Niveditha |
| Niveditha | Aadish |

A reviewer checks: the results are true (rerun two or three cases), nothing outside the author's own rows changed, the five checks in rule 8 pass, and no case is marked Passed without a test or a recorded manual run.

## 6. Done means

- [ ] `docs/Test-Plan.md`: no case reads `Not executed` / `Pending` unless a deviation explains why.
- [ ] `docs/test-reports/` holds the four reports: Unit Test, System Validation, Code Coverage, Branch Coverage.
- [ ] Section 14 metrics, section 7 schedule and section 6 environment match the real results.
- [ ] `submission/Test-Plan-Blood-Bank-Management-System.docx` rebuilt.
- [ ] CI is green on `main`.
- [ ] `CONTRIBUTIONS.md` refreshed by Aadish after the merges (`python3 tools/contribution_report.py`).
