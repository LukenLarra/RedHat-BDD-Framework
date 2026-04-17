---
description: Analyzes BDD .feature files and implements missing step definitions in tests/features/steps/.
---

# BDD Feature Implementation Skill

This prompt automates the discovery and implementation of missing Behavior-Driven Development (BDD) steps using the `behave` framework.

## Instructions

When the user asks to implement steps for a specific feature, follow this workflow:

1. **Read the Feature File**: Use `read_file` to read the target `.feature` file in `tests/features/`.
2. **Extract Steps**: Identify all `Given`, `When`, `Then`, `And`, and `But` clauses in the scenarios.
3. **Scan Existing Steps**: Search `tests/features/steps/` using `grep_search` or `semantic_search` to find which of these steps are already implemented.
4. **Draft Missing Steps**:
   - Write the missing implementations in Python using `behave` decorators (`@given`, `@when`, `@then`).
   - Group related steps into specific files (e.g., `tests/features/steps/movies_steps.py`).
   - **Crucial**: Ensure all code, docstrings, and comments are fully in **English**, following the repository's `copilot-instructions.md`.
   - Adhere to the repository's formatting (compatible with `rufff` and `python>=3.8`).
5. **Implement**: Use file creation or string replacement tools to add the new functions into the codebase.
6. **Validate**: Remind the user they can run `python tests/run_bdd_tests.py` to verify that the steps were successfully linked.
