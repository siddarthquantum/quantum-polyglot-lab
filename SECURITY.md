# Security Policy

## Scope

This is an educational repository. Its code is not intended for production use, but security is part of the learning method, so reports are welcome and taken seriously.

Examples of useful reports:

- Memory-safety bugs in C code (buffer overflows, out-of-bounds access, use-after-free)
- Incorrect or unsafe cryptographic implementations
- Unsafe input handling in any language
- Secrets or sensitive data accidentally committed

## Reporting a vulnerability

Please **do not** open a public issue for security problems.

Use GitHub's private reporting instead: go to the **Security** tab of this repository and choose **Report a vulnerability**.

Include what you found, the file and line, and steps or input to reproduce it. You can expect an acknowledgement within 7 days.

## How this repo protects itself

Every push and pull request runs:

- C builds with `-Wall -Wextra -Werror` and tests under AddressSanitizer and UndefinedBehaviorSanitizer
- CodeQL static analysis (`security-extended` queries) for C and Python
- Ruff linting including bandit-style security rules for Python
- Gitleaks secret scanning across the full history
