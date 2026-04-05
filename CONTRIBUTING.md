# Contributing to data-layer-manager

We follow a structured development workflow to ensure high code quality and consistent releases.

## 🛠️ Setup

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd data-layer-manager
    ```
2.  **Synchronize dependencies**:
    ```bash
    uv sync
    ```
3.  **Install pre-commit hooks**:
    ```bash
    uv run pre-commit install
    ```

## 🚥 Standards

-   **Linting/Formatting**: Handled by **Ruff**. It is recommended to use the VS Code extension for real-time feedback.
-   **Types**: Strict **Mypy** checking is enforced. All public APIs must have type hints.
-   **Commits**: We use **Conventional Commits**.
    -   `feat`: New features
    -   `fix`: Bug fixes
    -   `docs`: Documentation only
    -   `refactor`: Code changes that neither fix a bug nor add a feature
    -   `chore`: Tooling, versioning, etc.

## 🚀 Versioning Workflow

We use **`bump-my-version`** to automate semantic versioning. This updates version strings across the project and creates a Git tag and commit automatically.

### Commands

Avoid manual version changes in `pyproject.toml`. Instead, use one of the following commands:

-   **Patch Release** (Bug fixes, backward compatible):
    ```bash
    uv run bump-my-version bump patch
    ```
    *Example: 0.1.0 -> 0.1.1*

-   **Minor Release** (New features, backward compatible):
    ```bash
    uv run bump-my-version bump minor
    ```
    *Example: 0.1.1 -> 0.2.0*

-   **Major Release** (Breaking changes):
    ```bash
    uv run bump-my-version bump major
    ```
    *Example: 0.2.1 -> 1.0.0*

### Git Integration
By default, these commands will:
1.  Search and replace the version number in all configured files.
2.  Commit the change with: `chore(version): bump <old> -> <new>`.
3.  Tag the commit with: `v<new>`.

*Note: You must have a clean git state (no uncommitted changes) to run these commands.*

### Changelog Updates

All contributors MUST update the `CHANGELOG.md` for any changes that land in the main branch. You must follow the instructions provided in the **`changelog-update`** skill before submitting any changes.

**Skill Location**: [/.agent/skills/changelog-update/SKILL.md](file://./.agent/skills/changelog-update/SKILL.md)
