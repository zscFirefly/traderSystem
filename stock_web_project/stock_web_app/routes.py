from collections import defaultdict

from flask import Blueprint, current_app, jsonify, render_template, request
import networkx as nx

from .services import (
    BaoStockClient,
    calculate_correlation_matrix,
    calculate_significance_matrix,
    create_returns_matrix,
    get_stock_data,
    plot_correlation_heatmap_base64,
    plot_correlation_matrix_base64,
    plot_significance_heatmap_base64,
)


web_bp = Blueprint("web", __name__)


def _get_analyzer():
    return current_app.config.get("ANALYZER")


def _get_alert_store():
    return current_app.config.get("ALERT_STORE")


def _get_rule_store():
    return current_app.config.get("RULE_STORE")


def _get_lesson_store():
    return current_app.config.get("LESSON_STORE")


def _get_analyzer_error():
    error = current_app.config.get("ANALYZER_INIT_ERROR")
    if error:
        return f"分析器未初始化: {error}"
    return "分析器未初始化"


@web_bp.route("/")
def index():
    return render_template("index.html")


@web_bp.route("/api/search_stocks", methods=["GET"])
def search_stocks():
    query = request.args.get("query", "").strip()
    analyzer = _get_analyzer()
    if not query or not analyzer or analyzer.df.empty:
        return jsonify([])

    stocks = analyzer.df["股票简称"].unique()
    results = [stock for stock in stocks if query in stock]
    return jsonify(results[:10])


@web_bp.route("/api/related_stocks", methods=["GET"])
def related_stocks():
    analyzer = _get_analyzer()
    stock = request.args.get("stock", "").strip()
    topk = request.args.get("topk", "10")
    match_300 = request.args.get("match_300", "false").lower() == "true"

    try:
        topk = int(topk) if topk else 10
        if not stock:
            return jsonify({"error": "参数错误"}), 400
        if not analyzer:
            return jsonify({"success": False, "error": _get_analyzer_error()}), 400

        results = analyzer.get_topk_related_stocks(stock, topk, match_300)
        formatted_results = []
        for stock_name, stock_code, count, dates, concepts in results:
            formatted_dates = [
                date.strftime("%Y-%m-%d") if hasattr(date, "strftime") else str(date)
                for date in dates
            ]
            formatted_results.append(
                {
                    "stock_name": stock_name,
                    "stock_code": stock_code,
                    "count": count,
                    "dates": formatted_dates,
                    "concepts": concepts,
                }
            )

        return jsonify(
            {
                "success": True,
                "target_stock": stock,
                "target_stock_code": analyzer.stock_to_code.get(stock, ""),
                "results": formatted_results,
            }
        )
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 400


@web_bp.route("/api/concept_stocks", methods=["GET"])
def concept_stocks():
    analyzer = _get_analyzer()
    concept = request.args.get("concept", "").strip()
    topk = request.args.get("topk", "20")
    min_weight = request.args.get("min_weight", "1")

    try:
        topk = int(topk) if topk else 20
        min_weight = int(min_weight) if min_weight else 1
        if not concept:
            return jsonify({"error": "参数错误"}), 400
        if not analyzer:
            return jsonify({"success": False, "error": _get_analyzer_error()}), 400

        concept_to_stocks = defaultdict(list)
        for stock_name, concepts_list in analyzer.stock_to_concepts.items():
            for stock_concept in concepts_list:
                concept_to_stocks[stock_concept].append(stock_name)

        if concept not in concept_to_stocks:
            return jsonify(
                {
                    "success": True,
                    "concept": concept,
                    "results": [],
                    "message": f'未找到与概念 "{concept}" 相关的股票',
                }
            )

        concept_stocks_list = concept_to_stocks[concept]
        linkage_data = []
        for stock_pair, dates in analyzer.co_occurrence_dates.items():
            stock1, stock2 = stock_pair
            if (stock1 in concept_stocks_list or stock2 in concept_stocks_list) and len(dates) >= min_weight:
                linkage_data.append(
                    {
                        "股票简称_A": stock1,
                        "股票简称_B": stock2,
                        "共现频次": len(dates),
                        "共现日期": sorted(list(dates)),
                    }
                )

        graph = nx.Graph()
        for item in linkage_data:
            graph.add_edge(item["股票简称_A"], item["股票简称_B"], weight=item["共现频次"])

        centrality = nx.degree_centrality(graph) if graph.number_of_nodes() > 0 else {}

        results = []
        for stock_name in concept_stocks_list:
            stock_code = analyzer.stock_to_code.get(stock_name, "")
            all_concepts = list(analyzer.stock_to_concepts.get(stock_name, []))

            related = []
            if stock_name in graph:
                neighbors = sorted(
                    graph.neighbors(stock_name),
                    key=lambda item: graph[stock_name][item]["weight"],
                    reverse=True,
                )
                related = neighbors[:5]

            results.append(
                {
                    "stock_name": stock_name,
                    "stock_code": stock_code,
                    "concepts": all_concepts,
                    "centrality": round(centrality.get(stock_name, 0), 4),
                    "related_stocks": related,
                }
            )

        results.sort(key=lambda item: item["centrality"], reverse=True)
        return jsonify(
            {
                "success": True,
                "concept": concept,
                "total_count": len(concept_stocks_list),
                "graph_stats": {
                    "nodes": graph.number_of_nodes(),
                    "edges": graph.number_of_edges(),
                },
                "results": results[:topk],
            }
        )
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 400


@web_bp.route("/api/debug_data", methods=["GET"])
def debug_data():
    analyzer = _get_analyzer()
    if not analyzer:
        return jsonify({"error": _get_analyzer_error()}), 400

    try:
        result = {
            "stock_count": len(analyzer.stock_set) if analyzer.stock_set else 0,
            "concept_count": len(
                set(
                    concept
                    for concepts in analyzer.stock_to_concepts.values()
                    for concept in concepts
                )
            ),
            "sample_stocks": list(analyzer.stock_set)[:10] if analyzer.stock_set else [],
            "sample_concepts": [],
        }

        all_concepts = set()
        for concepts in analyzer.stock_to_concepts.values():
            all_concepts.update(concepts)
            if len(all_concepts) >= 10:
                break
        result["sample_concepts"] = list(all_concepts)[:10]

        return jsonify({"success": True, "data": result})
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 400


@web_bp.route("/api/alerts", methods=["GET", "POST"])
def alerts():
    alert_store = _get_alert_store()
    if not alert_store:
        return jsonify({"success": False, "error": "事件提醒存储未初始化"}), 500

    if request.method == "GET":
        try:
            limit = request.args.get("limit", "").strip()
            limit_value = int(limit) if limit else None
            all_results = alert_store.list_alerts()
            results = all_results[:limit_value] if limit_value else all_results
            return jsonify(
                {
                    "success": True,
                    "total": len(all_results),
                    "results": results,
                }
            )
        except Exception as exc:
            return jsonify({"success": False, "error": str(exc)}), 400

    try:
        payload = request.get_json() or {}
        created = alert_store.create_alert(payload)
        return jsonify({"success": True, "item": created}), 201
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 400


@web_bp.route("/api/alerts/<alert_id>", methods=["PUT", "DELETE"])
def alert_detail(alert_id):
    alert_store = _get_alert_store()
    if not alert_store:
        return jsonify({"success": False, "error": "事件提醒存储未初始化"}), 500

    if request.method == "PUT":
        try:
            payload = request.get_json() or {}
            updated = alert_store.update_alert(alert_id, payload)
            return jsonify({"success": True, "item": updated})
        except Exception as exc:
            return jsonify({"success": False, "error": str(exc)}), 400

    try:
        payload = request.get_json(silent=True) or {}
        operator = payload.get("updated_by", "").strip() or payload.get("created_by", "").strip() or "system"
        deleted = alert_store.delete_alert(alert_id, operator=operator)
        return jsonify({"success": True, "item": deleted})
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 400


@web_bp.route("/api/discipline/rules", methods=["GET", "POST"])
def discipline_rules():
    rule_store = _get_rule_store()
    if not rule_store:
        return jsonify({"success": False, "error": "交易纪律规则存储未初始化"}), 500

    if request.method == "GET":
        try:
            limit = request.args.get("limit", "").strip()
            limit_value = int(limit) if limit else None
            results = rule_store.list_rules(limit=limit_value)
            return jsonify({"success": True, "total": len(results), "results": results})
        except Exception as exc:
            return jsonify({"success": False, "error": str(exc)}), 400

    try:
        payload = request.get_json() or {}
        created = rule_store.create_rule(payload)
        return jsonify({"success": True, "item": created}), 201
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 400


@web_bp.route("/api/discipline/rules/<rule_id>", methods=["PUT", "DELETE"])
def discipline_rule_detail(rule_id):
    rule_store = _get_rule_store()
    if not rule_store:
        return jsonify({"success": False, "error": "交易纪律规则存储未初始化"}), 500

    if request.method == "PUT":
        try:
            payload = request.get_json() or {}
            updated = rule_store.update_rule(rule_id, payload)
            return jsonify({"success": True, "item": updated})
        except Exception as exc:
            return jsonify({"success": False, "error": str(exc)}), 400

    try:
        payload = request.get_json(silent=True) or {}
        operator = payload.get("updated_by", "").strip() or payload.get("created_by", "").strip() or "system"
        deleted = rule_store.delete_rule(rule_id, operator=operator)
        return jsonify({"success": True, "item": deleted})
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 400


@web_bp.route("/api/discipline/lessons", methods=["GET", "POST"])
def discipline_lessons():
    lesson_store = _get_lesson_store()
    if not lesson_store:
        return jsonify({"success": False, "error": "交易纪律教训存储未初始化"}), 500

    if request.method == "GET":
        try:
            limit = request.args.get("limit", "").strip()
            limit_value = int(limit) if limit else None
            dashboard_only = request.args.get("dashboard_only", "false").lower() == "true"
            results = lesson_store.list_lessons(limit=limit_value, dashboard_only=dashboard_only)
            return jsonify({"success": True, "total": len(results), "results": results})
        except Exception as exc:
            return jsonify({"success": False, "error": str(exc)}), 400

    try:
        payload = request.get_json() or {}
        created = lesson_store.create_lesson(payload)
        return jsonify({"success": True, "item": created}), 201
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 400


@web_bp.route("/api/discipline/lessons/<lesson_id>", methods=["PUT", "DELETE"])
def discipline_lesson_detail(lesson_id):
    lesson_store = _get_lesson_store()
    if not lesson_store:
        return jsonify({"success": False, "error": "交易纪律教训存储未初始化"}), 500

    if request.method == "PUT":
        try:
            payload = request.get_json() or {}
            updated = lesson_store.update_lesson(lesson_id, payload)
            return jsonify({"success": True, "item": updated})
        except Exception as exc:
            return jsonify({"success": False, "error": str(exc)}), 400

    try:
        payload = request.get_json(silent=True) or {}
        operator = payload.get("updated_by", "").strip() or payload.get("created_by", "").strip() or "system"
        deleted = lesson_store.delete_lesson(lesson_id, operator=operator)
        return jsonify({"success": True, "item": deleted})
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 400


@web_bp.route("/api/multi_stock_correlation", methods=["POST"])
def multi_stock_correlation():
    baostock_client = BaoStockClient()
    request_summary = {
        "stocks": [],
        "start_date": None,
        "end_date": None,
        "trading_days": None,
        "period": None,
    }
    try:
        payload = request.get_json()
        if not payload:
            return jsonify({"success": False, "error": "请求参数为空"}), 400

        stocks = payload.get("stocks", [])
        start_date = payload.get("start_date")
        end_date = payload.get("end_date")
        trading_days = int(payload.get("trading_days", 10))
        period = payload.get("period", "5")
        include_heatmap = payload.get(
            "include_heatmap",
            payload.get("include_heatmaps", False),
        )
        request_summary.update(
            {
                "start_date": start_date,
                "end_date": end_date,
                "trading_days": trading_days,
                "period": period,
            }
        )

        if not stocks:
            return jsonify({"success": False, "error": "请至少提供一只股票"}), 400

        valid_stocks = []
        for stock in stocks:
            stock_code = stock.get("stock_code") or stock.get("symbol")
            stock_name = stock.get("stock_name") or stock.get("name")
            if stock_code and stock_name:
                valid_stocks.append((stock_code, stock_name))
            else:
                return jsonify(
                    {
                        "success": False,
                        "error": "股票参数格式错误，需要包含 stock_code/stock_name",
                    }
                ), 400
        request_summary["stocks"] = valid_stocks
        current_app.logger.info(
            "multi_stock_correlation request stocks=%s trading_days=%s period=%s start_date=%s end_date=%s include_heatmap=%s",
            valid_stocks,
            trading_days,
            period,
            start_date,
            end_date,
            include_heatmap,
        )

        stock_datas = []
        stock_names = []
        valid_stocks_list = []
        failed_stocks = []
        baostock_client.login()
        if not start_date or not end_date:
            start_date, end_date = baostock_client.get_recent_trading_window(trading_days)
            current_app.logger.info(
                "multi_stock_correlation resolved trading window start=%s end=%s",
                start_date,
                end_date,
            )
        for symbol, name in valid_stocks:
            stock_data = get_stock_data(
                symbol,
                start_date,
                end_date,
                period,
                client=baostock_client,
            )
            if stock_data is None:
                failed_stocks.append({"symbol": symbol, "name": name, "reason": "没有返回分钟数据"})
                current_app.logger.warning(
                    "multi_stock_correlation stock data missing symbol=%s name=%s start=%s end=%s period=%s",
                    symbol,
                    name,
                    start_date,
                    end_date,
                    period,
                )
                continue
            stock_datas.append(stock_data)
            stock_names.append(name)
            valid_stocks_list.append((symbol, name))
            current_app.logger.info(
                "multi_stock_correlation stock data loaded symbol=%s name=%s rows=%s",
                symbol,
                name,
                len(stock_data),
            )

        if not valid_stocks_list:
            current_app.logger.warning(
                "multi_stock_correlation no stock data available failed_stocks=%s",
                failed_stocks,
            )
            return jsonify(
                {
                    "success": False,
                    "error": "没有成功获取任何股票数据",
                    "failed_stocks": failed_stocks,
                    "time_range": {"start_date": start_date, "end_date": end_date},
                }
            ), 400

        returns_matrix = create_returns_matrix(stock_datas, stock_names)
        if returns_matrix is None:
            current_app.logger.warning(
                "multi_stock_correlation failed to build returns matrix valid_stocks=%s failed_stocks=%s",
                valid_stocks_list,
                failed_stocks,
            )
            return jsonify(
                {
                    "success": False,
                    "error": "无法创建收益率矩阵",
                    "valid_stocks": [
                        {"symbol": symbol, "name": name} for symbol, name in valid_stocks_list
                    ],
                    "failed_stocks": failed_stocks,
                    "time_range": {"start_date": start_date, "end_date": end_date},
                }
            ), 400
        current_app.logger.info(
            "multi_stock_correlation returns matrix created rows=%s columns=%s valid_stocks=%s failed_stocks=%s",
            len(returns_matrix),
            list(returns_matrix.columns),
            valid_stocks_list,
            failed_stocks,
        )

        correlation_results = {}
        for method in ["pearson", "spearman", "kendall"]:
            correlation_matrix = calculate_correlation_matrix(returns_matrix, method)
            if correlation_matrix is None:
                continue
            correlation_results[method] = {
                "matrix": correlation_matrix.round(4).to_dict(),
                "heatmap_base64": (
                    plot_correlation_heatmap_base64(correlation_matrix, method)
                    if include_heatmap
                    else None
                ),
                "matrix_image_base64": (
                    plot_correlation_matrix_base64(correlation_matrix, method)
                    if include_heatmap
                    else None
                ),
            }

        significance_matrix = calculate_significance_matrix(returns_matrix)
        significance_result = None
        if significance_matrix is not None:
            significance_result = {
                "matrix": significance_matrix.round(4).to_dict(),
                "heatmap_base64": (
                    plot_significance_heatmap_base64(significance_matrix)
                    if include_heatmap
                    else None
                ),
            }

        return jsonify(
            {
                "success": True,
                "target_stocks": [
                    {"symbol": symbol, "name": name}
                    for symbol, name in valid_stocks_list
                ],
                "time_range": {"start_date": start_date, "end_date": end_date},
                "trading_days": trading_days,
                "period": period,
                "returns_count": len(returns_matrix),
                "correlation_results": correlation_results,
                "significance_result": significance_result,
                "failed_stocks": failed_stocks,
            }
        )
    except Exception as exc:
        current_app.logger.exception(
            "multi_stock_correlation failed stocks=%s start_date=%s end_date=%s trading_days=%s period=%s",
            request_summary["stocks"],
            request_summary["start_date"],
            request_summary["end_date"],
            request_summary["trading_days"],
            request_summary["period"],
        )
        return jsonify({"success": False, "error": str(exc)}), 400
    finally:
        baostock_client.logout()
