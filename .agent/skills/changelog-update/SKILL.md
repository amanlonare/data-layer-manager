---
name: changelog-update
description: Systematic workflow for updating CHANGELOG.md with automated delta identification.
---

# Changelog Update Skill

Follow this checklist and protocol every time you need to update the `CHANGELOG.md` file. The goal is to ensure that each entry accurately reflects everything **added or changed** relative to the previous version.

## Phase 1: Delta Identification

1.  **Check Current Version**: Read the top of `CHANGELOG.md` to identify the most recent documented version.
2.  **Inspect Git History**: Run `git log <last_tag_or_version>..HEAD --oneline` to see precisely what commits have landed since the last release.
3.  **Review GSD Artifacts**:
    *   Read the most recent `PLAN.md` and `CONTEXT.md` for the currently active phase.
    *   Check for any completed tasks or implemented features that aren't yet in the log.

## Phase 2: Categorization

Filter the identified deltas into the following standard categories (based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)):

*   `### Added`: For new features or capabilities.
*   `### Changed`: For changes in existing functionality.
*   `### Deprecated`: For soon-to-be removed features.
*   `### Removed`: For now removed features.
*   `### Fixed`: For any bug fixes.
*   `### Security`: In case of vulnerabilities.

## Phase 3: Writing the Update

1.  **Format Version Header**: Ensure it follows the `## [x.y.z] - YYYY-MM-DD` format.
2.  **Focus on the "What"**: Write concise, value-oriented summaries of each change.
    *   *Bad*: "Updated retriever.py"
    *   *Good*: "Implemented HybridRetrievalService using RRF fusion logic."
3.  **Maintain Chronological Order**: The newest version must **always** be at the top of the file under the `# Changelog` header.
4.  **Verify Links**: If the project uses version-comparison links at the bottom of the file, ensure those are updated to include the new version range.

## Phase 4: Final Verification

*   [ ] Does the update only list items added or changed *since* the previous version?
*   [ ] Is the date accurate for the current release?
*   [ ] Does the summary use the same voice and level of detail as previous entries?
*   [ ] Are there any duplicate entries from previous versions? (Remove them if found).
