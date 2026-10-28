# Contributing

This repository is an educational local-first starter. Ask the owner for project access and the intended source license before redistributing or contributing substantial code. This project deliberately ships without a license until the owner selects a business model.

## Developer workflow
1. Open an issue describing the desired behavior and its testing plan.
2. Create a feature branch (e.g., `feat/forced-alignment`).
3. Keep credentials and licensed content out of the repository.
4. Run `PYTHONPATH=backend pytest backend/tests -q` and `cd frontend && npm run build`.
5. Open a pull request with screenshot(s), test notes and policy impact.

Contributions involving Reddit, YouTube, external media or voice models must document the API terms, content rights and relevant licenses. Avoid engagement manipulation, credential scraping and policy circumvention.
