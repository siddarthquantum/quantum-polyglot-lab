# Contributing

Thanks for your interest in Quantum Polyglot Lab. Every contribution follows the project's core loop:

> **One mathematical problem → one algorithm → Python, Java, C and Rust → shared tests → analysis → documentation**

## What a complete contribution includes

1. **Math and intuition** — the concept behind the problem, in plain language.
2. **Algorithm** — described independently of any language.
3. **Implementations** — in as many of Python, Java, C and Rust as you can. Partial is fine; say which are missing.
4. **Tests** — shared input/output cases that every implementation must pass, including boundary and invalid inputs.
5. **Analysis** — time and space complexity, edge cases and limitations.
6. **Security notes** — input validation, overflow, memory safety, where they apply.
7. **References** — books, papers or standards you relied on.

## Workflow

1. Fork the repo and create a branch: `feature/<topic>` or `fix/<topic>`.
2. Keep each pull request focused on one problem or one fix.
3. Make sure CI passes locally before opening the PR:
   ```bash
   # C
   gcc -std=c11 -Wall -Wextra -Werror -fsanitize=address,undefined -o graph c/graph_lab/graph_traversals.c
   c/graph_lab/tests/run_tests.sh ./graph
   gcc -std=c11 -Wall -Wextra -Werror -fsanitize=address,undefined -o array_ops c/array_lab/solution/array_ops.c
   c/array_lab/tests/run_tests.sh ./array_ops
   # Python
   ruff check python/ && ruff format --check python/
   ```
4. Open a pull request describing what changed and how you tested it.

## Ground rules

- Never commit secrets, credentials, datasets with personal data, or compiled binaries.
- Prefer clear code over clever code; this is a learning repository.
- Be kind in reviews. See the [Code of Conduct](CODE_OF_CONDUCT.md).
