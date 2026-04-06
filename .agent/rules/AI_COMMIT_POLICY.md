# AI Commit Policy

## ⚠️ MANDATORY RULE
The AI assistant **MUST NOT** execute `git commit` or any automated commit tools (e.g., `gsd-ship`, `git commit --amend`) unless specifically and explicitly instructed to do so by the user in the current conversation.

### Guidelines
1.  **Wait for Consent**: Even if a task (like updating a changelog or fixing linting) is traditionally followed by a commit, wait for the user to say "commit this" or "save changes".
2.  **No "Implicit" Commits**: Do not assume that a successful "make test" or "make lint" implies a green light to commit.
3.  **Explicit Requests Only**: Only proceed when the user gives a clear directive to finalize the work in the repository history.

## When Committing
If explicitly asked to commit, the AI assistant **MUST** reference and follow the conventions defined in the **`git-commit-formatter`** skill (`.agent/skills/git-commit-formatter/SKILL.md`) to structure the commit message appropriately.
