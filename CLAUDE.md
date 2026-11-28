# FPV Uhyliant: notes for AI-assisted development

- Read `DEVELOPMENT_GUIDE.md`, `PRODUCT_UX.md`, `DELIVERY_ROADMAP.md` and `docs/REMOTE_OPERATIONS_CONCEPT.md` before changing code.
- **Maximum automation is an owner directive for the whole project.** Before adding any field, button or step, apply the
  maximum-automation checklist in `DEVELOPMENT_GUIDE.md`: the station detects, configures and verifies by itself, and asks
  the operator only for what it cannot know.
- The product owner is not a programmer: explain results in simple Ukrainian, show screenshots of UI changes.
- Work on branch `automation/copilot-autopilot`, open PRs to `main`; merge your own PR only when CI is fully green.
- Checks before a PR: `ruff format src tools && ruff check src tools`, `cd src/app && python -m pytest -q -p no:cacheprovider .`,
  `python tools/project_doctor.py` (READY), and the QML smoke tests under xvfb.
