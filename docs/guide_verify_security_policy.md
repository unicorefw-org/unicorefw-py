# `verify_security_policy.py` guide

Source: [`scripts/verify_security_policy.py`](../scripts/verify_security_policy.py)

## Purpose

Use this script to enforce two security controls:

1. Every inline scanner suppression must have an exact scope, a future expiry,
   and a specific rationale.
2. SARIF reports must contain no unsuppressed finding at or above the configured
   severity threshold.

The command fails closed on malformed policy data rather than ignoring it.

## Requirements

- Run the command from the repository root unless paths are explicit.
- Use a valid directory for suppression scanning.
- Supply SARIF 2.1.0 files for report verification.
- Keep the SARIF suppression registry at schema version `1`. The repository
  default is `security/suppressions.json`.
- Use UTC dates when reviewing expiry behavior.

## Commands

Verify inline suppressions in the repository:

```bash
python3 scripts/verify_security_policy.py suppressions --root .
```

Verify every `.sarif` file under a directory with the default medium threshold:

```bash
python3 scripts/verify_security_policy.py sarif \
  --input build/sarif \
  --suppressions security/suppressions.json \
  --minimum-severity 4.0
```

Valid Bandit suppression metadata must appear within the preceding two lines
and use the same exact codes:

```python
# Security suppression: codes=B608; expires=2099-12-31; rationale=Query shape is fixed and values remain parameterized.
execute(query)  # nosec B608
```

Replace the example expiry with the shortest reviewed period appropriate for
the exception.

## Options

| Command or option | Default | Contract |
|---|---:|---|
| `suppressions` | n/a | Scan source comments for governed inline suppressions. |
| `suppressions --root PATH` | `.` | Existing directory to scan recursively. |
| `sarif` | n/a | Validate SARIF findings against the suppression registry. |
| `sarif --input PATH` | required | One SARIF file or a directory searched recursively for `*.sarif`. |
| `sarif --suppressions PATH` | `security/suppressions.json` | Schema version 1 suppression registry. |
| `sarif --minimum-severity VALUE` | `4.0` | Finite threshold from 0 through 10, inclusive. |
| `-h`, `--help` | n/a | Print help for the root command or selected subcommand. |

## Output and exit status

Successful suppression validation prints the number of scoped inline
suppressions. Successful SARIF validation prints the number of examined
results, including findings below the threshold.

Exit status `0` means the selected policy passed. Exit status `1` means policy
input was invalid, a suppression was missing required governance, or an
unsuppressed finding met the threshold. Argparse uses status `2` for malformed
command syntax. Policy diagnostics are written to standard error.

## Safety and operational notes

Blanket `# nosec` comments are forbidden. Codes must use the exact `B123`
shape and match adjacent `Security suppression` metadata. One metadata comment
cannot govern multiple suppressions. Expiry must be later than the current UTC
date, and rationale text must contain at least 20 characters.

Secret allowlist comments also require an expiry and rationale:

```text
# pragma: allowlist secret; expires=2099-12-31; rationale=Public test fixture contains no production credential.
```

The source scan skips symlinks, non-files, build outputs, coverage output,
virtual environments, caches, and Git metadata. It scans Python files plus
supported shell, configuration, JavaScript, TypeScript, and YAML suffixes.

JSON inputs are limited to 64 MiB each. SARIF severity prefers numeric
`security-severity` metadata. Otherwise `error` maps to 7, `warning` to 4, and
`note` or `none` to 0. Unknown levels fail conservatively at severity 7.

SARIF suppression entries require exact `tool`, `rule_id`, and `fingerprint`
values plus future `expires` and a rationale. Duplicate entries are rejected.
Fingerprint selection prefers `primaryLocationLineHash`, then the first sorted
partial fingerprint, then a deterministic SHA-256 fallback.

## Troubleshooting

For an inline failure, use the reported file and line. Confirm the suppression
lists explicit codes, its metadata is no more than two lines earlier, and both
code sets match exactly.

For an SARIF finding, copy the reported normalized tool, rule ID, and
fingerprint into a reviewed registry entry. Do not suppress by rule alone.
Resolve the finding instead when no narrow, temporary exception is justified.

If a report is not found, pass either the SARIF file itself or a directory that
contains files ending in `.sarif`. Other JSON extensions are not discovered.
