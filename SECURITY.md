# Security notice · development MVP

Do not host this project on the public internet yet. The FastAPI endpoints have **no authentication or authorization**; the dashboard has no accounts, tenant isolation, CSRF protection or rate limiting. Keep API bound to localhost; never expose it with a public tunnel until fixed.

Google OAuth tokens, API credentials, LLM logs, source stories and generated videos may be sensitive. `.gitignore` excludes `secrets`, `outputs`, `data` and `.env`; verify with `git status` before every push. Do not commit copyrighted stories or model weights. Use dedicated service accounts only for services that support them; YouTube video uploads use owner OAuth, not a generic service account.

Before allowing users or public hosting, implement HTTPS, authentication, least-privilege roles, per-tenant database access policies, encrypted token storage, token revocation, audit logs, upload consent and privacy controls, idempotent job execution, API rate limits, user data deletion and abuse reporting. Provide YouTube Terms and your own accessible privacy policy and data-deletion instructions.

Report issues privately to the maintainers. Never include tokens or raw private story data in issue descriptions.
