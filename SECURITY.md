# Sonic AI V3 Security Policy

**Status:** Active
**Canonical branch:** `main`

## Supported State

Sonic AI V3 is under active development and recovery. There is no production release version to declare as supported yet.

| State | Support |
|---|---|
| `main` | Active development / security fixes as discovered |
| Feature/recovery branches | Experimental; not production baselines |
| Historical snapshots | Not supported |

## Security Rules

- Never commit API keys, access tokens, passwords, private keys, or production credentials.
- Keep local secrets in `.env`; document required variables in `.env.example`.
- Do not expose secrets through frontend bundles, logs, test fixtures, screenshots, or documentation.
- Treat authentication, authorization, user ownership, file uploads, tool execution, MCP boundaries, and agent permissions as security-sensitive surfaces.
- Do not allow agents to bypass application/domain authorization or mutate arbitrary state.
- Validate external input at application boundaries.
- Keep CORS, cookies, tokens, storage paths, and database access explicitly scoped.

## Reporting a Vulnerability

For a security issue, do not publish exploit details in a public issue first. Contact the repository owner privately through the security/contact mechanism available on the GitHub repository.

Include:

1. A concise description of the vulnerability.
2. Affected component/path.
3. Reproduction steps or proof of concept, when safe to provide.
4. Potential impact.
5. Suggested mitigation, if known.

## Security Verification Before Release

A release candidate must verify at minimum:

- Authentication and session handling.
- Authorization and user ownership.
- Secret/configuration hygiene.
- File upload validation and path safety.
- API input validation.
- CORS and security headers.
- Agent/tool/MCP permission boundaries.
- Dependency vulnerabilities.
- Logging does not leak secrets or sensitive user data.

Production readiness must be established from executable tests and runtime evidence, not from historical audit documents alone.
