"""
GitHub API service for managing Issues used by utteranc.es comments.
Each published article gets a corresponding GitHub Issue for comments.
"""

import logging
from github import Github, GithubException

logger = logging.getLogger(__name__)


class GitHubService:
    """Manages GitHub Issues for blog article comments."""

    def __init__(self, token: str, repo_name: str):
        self.token = token
        self.repo_name = repo_name
        self._gh = None
        self._repo = None

    @property
    def gh(self):
        if self._gh is None:
            if not self.token:
                raise ValueError('GITHUB_TOKEN is not configured')
            self._gh = Github(self.token)
        return self._gh

    @property
    def repo(self):
        if self._repo is None:
            if not self.repo_name:
                raise ValueError('GITHUB_REPO is not configured')
            self._repo = self.gh.get_repo(self.repo_name)
        return self._repo

    def is_configured(self) -> bool:
        return bool(self.token and self.repo_name)

    def create_issue(self, title: str, body: str, labels: list[str] | None = None) -> int | None:
        """Create a GitHub Issue for article comments. Returns issue number or None."""
        if not self.is_configured():
            logger.warning('GitHub not configured, skipping issue creation')
            return None

        try:
            issue = self.repo.create_issue(
                title=title,
                body=body,
                labels=labels or ['blog-post'],
            )
            logger.info(f'Created issue #{issue.number} for article: {title}')
            return issue.number
        except GithubException as e:
            logger.error(f'Failed to create issue: {e}')
            return None

    def update_issue(self, issue_number: int, title: str, body: str) -> bool:
        """Update an existing Issue when article is edited."""
        if not self.is_configured():
            return False

        try:
            issue = self.repo.get_issue(number=issue_number)
            issue.edit(title=title, body=body)
            logger.info(f'Updated issue #{issue_number}')
            return True
        except GithubException as e:
            logger.error(f'Failed to update issue #{issue_number}: {e}')
            return False

    def close_issue(self, issue_number: int) -> bool:
        """Close an Issue when article is deleted or unpublished."""
        if not self.is_configured():
            return False

        try:
            issue = self.repo.get_issue(number=issue_number)
            issue.edit(state='closed')
            logger.info(f'Closed issue #{issue_number}')
            return True
        except GithubException as e:
            logger.error(f'Failed to close issue #{issue_number}: {e}')
            return False

    def build_issue_body(self, article_url: str, summary: str) -> str:
        """Build the Issue body that links back to the article."""
        return f"""> This issue is for blog comments on: [{article_url}]({article_url})

{summary}

---
*Comments on this issue will appear on the blog post via utteranc.es.*
"""
