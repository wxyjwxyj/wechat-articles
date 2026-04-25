"""GitHub Trending HTML 解析测试。"""
from unittest.mock import patch, MagicMock

from collectors.github_trending import GitHubTrendingCollector, _is_ai_related, _TrendingParser


SAMPLE_HTML = """
<html><body>
<article class="Box-row">
  <h2 class="h3 lh-condensed">
    <a href="/owner/llm-awesome">owner / llm-awesome</a>
  </h2>
  <p class="col-9 color-fg-muted my-1 pr-4">
    A curated list of LLM tools and resources
  </p>
  <span class="d-inline-block float-sm-right">
    <svg></svg>
    343 stars today
  </span>
</article>
<article class="Box-row">
  <h2 class="h3 lh-condensed">
    <a href="/owner/game-engine">owner / game-engine</a>
  </h2>
  <p class="col-9 color-fg-muted my-1 pr-4">
    A fast 2D game engine
  </p>
  <span>
    50 stars today
  </span>
</article>
</body></html>
"""


def test_is_ai_related():
    assert _is_ai_related("llm-tools", "")
    assert _is_ai_related("", "A curated list of LLM resources")
    assert not _is_ai_related("game-engine", "A fast 2D game engine")


def test_parser_extracts_repos():
    parser = _TrendingParser()
    parser.feed(SAMPLE_HTML)

    assert len(parser.repos) == 2
    ai_repo = parser.repos[0]
    assert ai_repo["name"] == "owner/llm-awesome"
    assert ai_repo["url"] == "https://github.com/owner/llm-awesome"
    assert "LLM" in ai_repo["description"]
    assert ai_repo["stars_today"] == 343


def test_fetch_filters_ai_repos():
    collector = GitHubTrendingCollector(max_repos=10)
    mock_resp = MagicMock()
    mock_resp.text = SAMPLE_HTML
    mock_resp.raise_for_status = MagicMock()

    with patch.object(collector._session, "get", return_value=mock_resp):
        repos = collector.fetch_trending_repos()

    # 只有 llm-awesome 是 AI 相关
    assert len(repos) == 1
    assert repos[0]["name"] == "owner/llm-awesome"
    assert "fetched_at" in repos[0]
