"""Flask 只读 API 入口。"""
from pathlib import Path

from flask import Flask

from api.routes import register_routes
from storage.db import init_db

DEFAULT_DB_PATH = Path(__file__).parent.parent / "content.db"


def create_app(config: dict | None = None) -> Flask:
    """创建并配置 Flask 应用。config 可覆盖 DB_PATH 等配置项。"""
    app = Flask(__name__)
    app.config["DB_PATH"] = str(DEFAULT_DB_PATH)
    if config:
        app.config.update(config)

    # 确保 DB 已初始化
    init_db(app.config["DB_PATH"])

    register_routes(app)
    return app
