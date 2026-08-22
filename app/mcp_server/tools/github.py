"""
GitHub tool — search repositories and get repository stats,
using GitHub's official REST API.
"""

import os
import httpx

GITHUB_API_BASE = "https://api.github.com"


def _headers() -> dict:
    token = os.environ.get("GITHUB_TOKEN")
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def search_repositories(query: str, limit: int = 5) -> list[dict]:
    """
    Search GitHub repositories by keyword, sorted by star count (most popular first).
    Returns a list of repos with name, description, stars, url, and language.
    """
    if limit > 20:
        limit = 20  # keep responses reasonable in size

    response = httpx.get(
        f"{GITHUB_API_BASE}/search/repositories",
        params={"q": query, "sort": "stars", "order": "desc", "per_page": limit},
        headers=_headers(),
        timeout=10.0,
    )
    response.raise_for_status()
    data = response.json()

    results = []
    for repo in data.get("items", []):
        results.append(
            {
                "full_name": repo["full_name"],
                "description": repo.get("description"),
                "stars": repo["stargazers_count"],
                "language": repo.get("language"),
                "url": repo["html_url"],
            }
        )
    return results


def get_repository_stats(owner: str, repo: str) -> dict:
    """Get statistics for a specific repository (owner/repo), e.g. stars, forks, open issues."""
    response = httpx.get(
        f"{GITHUB_API_BASE}/repos/{owner}/{repo}",
        headers=_headers(),
        timeout=10.0,
    )
    response.raise_for_status()
    data = response.json()

    return {
        "full_name": data["full_name"],
        "description": data.get("description"),
        "stars": data["stargazers_count"],
        "forks": data["forks_count"],
        "open_issues": data["open_issues_count"],
        "language": data.get("language"),
        "url": data["html_url"],
    }