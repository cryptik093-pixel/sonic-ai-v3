# Security Policy

## Scope

Sonic AI V3 is an application repository. Security-sensitive configuration must remain outside Git history and be supplied through local environment files, deployment secrets, or CI/CD secret stores.

## Supported Branch

- `main` is the canonical integration branch.
- Feature and Codex branches must be treated as disposable implementation branches until reviewed and merged.

## Secrets

Never commit:

- API keys
- OAuth/client secrets
- database credentials
- JWT/signing secrets
- cloud credentials
- private keys or certificates
- production `.env` files

Use `.env.example` for documentation only. It must contain placeholders or local-development-only defaults and must never contain production credentials.

If a secret is suspected to have been committed or exposed:

1. Revoke or rotate the credential at its provider immediately.
2. Record the incident in the project security log/issue.
3. Remove the secret from the current tree.
4. Determine whether historical Git history must also be rewritten.
5. Verify that the replacement credential is stored only in an approved secret store.

Deleting a secret from the latest commit does **not** make a previously committed secret safe.

## Reporting a Vulnerability

For a private vulnerability report, contact the repository owner through GitHub rather than opening a public issue containing sensitive details.

Include:

- affected component or path
- reproduction steps
- impact
- suspected exposure window
- relevant logs or evidence with secrets/redacted credentials removed

## Security Baseline

Gate 1 of the Omega House Command Center establishes repository security and source-control hygiene before Revenue Intelligence work begins. The baseline should be re-verified before production deployment and whenever credentials, deployment workflows, or external integrations change.
