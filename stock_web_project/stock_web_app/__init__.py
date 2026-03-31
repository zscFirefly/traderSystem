def create_app(config_overrides=None):
    from flask import Flask

    from .alerts_store import CsvAlertStore
    from .config import Config
    from .correlation_store import CsvCorrelationPresetStore
    from .discipline_store import CsvLessonStore, CsvRuleStore
    from .routes import web_bp
    from .services import StockCorrelationAnalyzer, configure_matplotlib

    app = Flask(__name__)
    app.config.from_object(Config)
    if config_overrides:
        app.config.update(config_overrides)

    configure_matplotlib()

    try:
        analyzer = StockCorrelationAnalyzer(
            file_path=app.config["DATA_FILE"],
            sheet_name=app.config["DATA_SHEET"],
        )
        app.config["ANALYZER_INIT_ERROR"] = None
        app.logger.info("股票关联分析器初始化成功: %s", app.config["DATA_FILE"])
    except Exception as exc:
        analyzer = None
        app.config["ANALYZER_INIT_ERROR"] = str(exc)
        app.logger.warning("股票关联分析器初始化失败: %s", exc)

    app.config["ANALYZER"] = analyzer
    app.config["ALERT_STORE"] = CsvAlertStore(app.config["ALERTS_FILE"])
    app.config["RULE_STORE"] = CsvRuleStore(app.config["TRADING_RULES_FILE"])
    app.config["LESSON_STORE"] = CsvLessonStore(app.config["TRADING_LESSONS_FILE"])
    app.config["CORRELATION_PRESET_STORE"] = CsvCorrelationPresetStore(app.config["CORRELATION_PRESETS_FILE"])
    app.register_blueprint(web_bp)
    return app
