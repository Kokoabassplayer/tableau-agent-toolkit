# Security Policy

## Supported Versions

| Version | Supported |
| ------- | --------- |
| 0.1.x   | Yes       |

## Reporting a Vulnerability

If you discover a security vulnerability in this project, please report it by:

1. **Email**: Open a private security advisory on GitHub at
   `https://github.com/tableau-agent-toolkit/tableau-agent-toolkit/security/advisories/new`
2. **Do not** file a public issue for security vulnerabilities.

We aim to acknowledge reports within 48 hours and provide a fix within 7 days for
confirmed vulnerabilities.

## Security Policy

- **No secrets in YAML specs, templates, or plugin manifests.** All credentials
  (PAT tokens, JWT secrets) must be provided via environment variables or a
  secrets manager.
- **Environment variable prefix**: All Tableau-related settings use the `TABLEAU_`
  prefix (e.g., `TABLEAU_SERVER_URL`, `TABLEAU_PAT_SECRET`).
- **YAML loading**: This project uses `yaml.safe_load()` exclusively to prevent
  arbitrary code execution from untrusted spec files.
