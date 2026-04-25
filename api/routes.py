"""小程序只读 API 路由。所有路由均为 GET，不做写操作。"""
from datetime import date

from flask import current_app, jsonify

from storage.repository import BundleRepository, ItemRepository, SourceRepository
from api.research_routes import register_research_routes


def register_routes(app) -> None:
    """注册所有只读路由到 Flask app。"""

    @app.get("/api/bundles/today")
    def get_today_bundle():
        """获取今日 bundle。未生成时返回 404。"""
        today = date.today().isoformat()
        return _get_bundle_by_date(today)

    @app.get("/api/bundles/<bundle_date>")
    def get_bundle_by_date(bundle_date: str):
        """获取指定日期的 bundle。bundle_date 格式：YYYY-MM-DD。"""
        return _get_bundle_by_date(bundle_date)

    @app.get("/api/sources")
    def list_sources():
        """列出所有 source。"""
        db_path = current_app.config["DB_PATH"]
        repo = SourceRepository(db_path)
        sources = repo.list_sources()
        return jsonify(sources)

    @app.get("/api/sources/<source_name>/items")
    def get_source_items(source_name: str):
        """获取指定来源今日的所有 item。"""
        db_path = current_app.config["DB_PATH"]
        today = date.today().isoformat()
        repo = ItemRepository(db_path)
        items = repo.list_items_by_date(today)
        filtered = [
            item for item in items
            if item.get("author") == source_name
        ]
        return jsonify(filtered)

    @app.get("/api/topics")
    def list_topics():
        """列出今日 bundle 的话题列表。"""
        today = date.today().isoformat()
        db_path = current_app.config["DB_PATH"]
        repo = BundleRepository(db_path)
        bundle = repo.get_bundle_by_date(today)
        if bundle is None:
            return jsonify([])
        # 话题从 bundle_topics 关联表获取（暂时返回空列表，待后续完善）
        return jsonify(bundle.get("topics", []))

    # 注册研究功能路由
    register_research_routes(app)


def _get_bundle_by_date(bundle_date: str):
    """内部辅助：按日期获取 bundle，不存在时返回 404。"""
    db_path = current_app.config["DB_PATH"]
    repo = BundleRepository(db_path)
    bundle = repo.get_bundle_by_date(bundle_date)
    if bundle is None:
        return jsonify({"error": "bundle not found", "date": bundle_date}), 404
    return jsonify(bundle)
