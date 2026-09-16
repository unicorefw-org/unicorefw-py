# Security Policy

## Supported versions

Security fixes are applied to the latest patch release on the current minor
line and to the default branch.

| Version | Security support |
|---|---|
| 1.1.x | Supported |
| Earlier releases | Unsupported |

Users should upgrade to the latest available patch release before reporting a
problem that may already be fixed.

## Privately reporting a vulnerability

Do not disclose suspected vulnerabilities in a public issue, discussion, pull
request, test fixture, or log.

Email `kenny@unicorefw.org` with the subject
`[SECURITY] UniCoreFW vulnerability report`. Include:

- the affected version and Python/runtime environment;
- the vulnerable API and required configuration;
- minimal reproduction steps or a proof of concept;
- the security impact and any known mitigations;
- whether the issue is already public.

Email is not an encrypted secret-management channel. Remove live credentials,
tokens, personal data, production database contents, and other unrelated
secrets from the report. If those details are essential, first request a safer
transfer method with a summary that contains no exploit details.

The maintainer will validate the report, determine affected versions, prepare
tests and a fix, and coordinate disclosure with the reporter. No fixed response
or remediation time is promised.

## Threat model

UniCoreFW is a utility library that runs with the privileges of its host Python
process. Its security objectives are:

- preserve the confidentiality and integrity of caller data, credentials,
  database contents, audit records, and cryptographic material;
- prevent untrusted values from becoming executable SQL, HTML, spreadsheet
  formulas, templates, paths, or log records through documented safe APIs;
- place explicit memory, time, row, and nesting budgets around
  caller-controlled work;
- fail closed at authentication, validation, database, and distributed
  rate-limit boundaries without exposing secrets in public exception messages;
- preserve the integrity of release artifacts and dependency metadata.

Assume an attacker can supply malformed and oversized values, repeat requests,
race concurrent calls, control imported files, and observe public return values
and exceptions. Application code, deployment configuration, secret storage,
database permissions, Redis permissions, the Python interpreter, and the
operating system remain separate trust boundaries.

The following inputs are trusted by contract and must not be attacker
controlled:

- Python callables and objects that application code executes;
- template source, raw SQL/CSS/regex escape hatches, and migration scripts;
- encryption keys, database credentials, backend clients, and audit-log
  destinations;
- configuration that relaxes a safe default or enables destructive behavior.

The local `RateLimiter`/`LocalRateLimiter` protects only one Python process.
Multiprocess or multi-host services must use `DistributedRateLimiter` with an
atomic shared backend and must also enforce network- and infrastructure-level
abuse controls. `strip_html_tags()` and `strip_tags()` are text
transformations, not HTML sanitizers. `require_callable()` and
`validate_callable()` establish callability only, not trust or code safety.

Compromise of the host, interpreter, maintainer account, application-supplied
trusted code, or a third-party service is outside the library's defensive
boundary. Reports showing that a documented safe API crosses one of the
boundaries above are in scope; general hardening suggestions may use the public
issue tracker when they contain no vulnerability details.

## Security gates and suppressions

Required CI runs Bandit, dependency auditing, tracked-file secret scanning, and
CodeQL `security-extended` queries. Medium and high findings fail their gate.
CodeQL findings use a minimum security severity of 4.0; SARIF results without a
numeric security severity fail conservatively when their level is `warning` or
`error`.

Security suppressions are temporary reviewed exceptions, not permanent
allowlists:

- Bandit `# nosec` comments must name exact rule identifiers and have an
  adjacent rationale and future expiry date.
- Intentional secret-scanner fixtures must carry an inline rationale and future
  expiry date.
- CodeQL exceptions must match the tool, rule, and SARIF fingerprint in
  `security/suppressions.json`, with a rationale and future expiry date.

`scripts/verify_security_policy.py` rejects blanket, mismatched, malformed,
duplicate, and expired exceptions. The current expiry date is evaluated in UTC.
Remove a suppression when its finding is repaired; do not extend an expiry
without repeating the security review.

Secret scanning is heuristic and scans the current repository snapshot. It
does not prove that secrets are absent, inspect unreferenced Git history, revoke
exposed credentials, or replace provider-side secret scanning and push
protection. The CI scan disables online secret verification so repository
content is not sent to third-party verification endpoints.
