from collections import defaultdict
from datetime import datetime
import base64
import io
import logging
import os
import tempfile

os.environ.setdefault("MPLCONFIGDIR", os.path.join(tempfile.gettempdir(), "matplotlib"))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats
import seaborn as sns


def configure_matplotlib() -> None:
    plt.rcParams["font.sans-serif"] = ["SimHei", "Arial Unicode MS"]
    plt.rcParams["axes.unicode_minus"] = False


def default_intraday_range() -> tuple[str, str]:
    today = datetime.now().strftime("%Y-%m-%d")
    return f"{today} 09:30:00", f"{today} 15:00:00"


class BaoStockClient:
    def __init__(self):
        self._bs = None
        self._logged_in = False

    def login(self) -> None:
        if self._logged_in:
            return

        try:
            import baostock as bs
        except ModuleNotFoundError as exc:
            raise Exception("未安装 baostock，请先执行 `pip install baostock`") from exc

        result = bs.login()
        if result.error_code != "0":
            raise Exception(f"登录 baostock 失败: {result.error_msg}")

        self._bs = bs
        self._logged_in = True

    def logout(self) -> None:
        if self._logged_in and self._bs is not None:
            self._bs.logout()
        self._logged_in = False
        self._bs = None

    @staticmethod
    def normalize_symbol(symbol: str) -> str:
        symbol = str(symbol).strip().lower()
        if symbol.startswith(("sh.", "sz.")):
            return symbol

        if len(symbol) != 6 or not symbol.isdigit():
            raise Exception(f"不支持的股票代码格式: {symbol}")

        if symbol.startswith(("5", "6", "9")):
            return f"sh.{symbol}"
        return f"sz.{symbol}"

    def get_stock_data(self, symbol: str, start_date: str, end_date: str, period: str = "5"):
        self.login()

        normalized_symbol = self.normalize_symbol(symbol)
        start_datetime = pd.to_datetime(start_date)
        end_datetime = pd.to_datetime(end_date)

        result_set = self._bs.query_history_k_data_plus(
            normalized_symbol,
            "date,time,code,open,high,low,close,volume,amount,adjustflag",
            start_date=start_datetime.strftime("%Y-%m-%d"),
            end_date=end_datetime.strftime("%Y-%m-%d"),
            frequency=str(period),
            adjustflag="3",
        )
        if result_set.error_code != "0":
            raise Exception(f"获取 {normalized_symbol} 数据失败: {result_set.error_msg}")

        rows = []
        while result_set.error_code == "0" and result_set.next():
            rows.append(result_set.get_row_data())

        if not rows:
            logging.warning("股票 %s 在指定时间范围内没有返回分钟数据", normalized_symbol)
            return None

        result = pd.DataFrame(rows, columns=result_set.fields)
        result["time_part"] = result["time"].astype(str).str[8:14]
        result["datetime"] = (
            result["date"]
            + " "
            + result["time_part"].str[:2]
            + ":"
            + result["time_part"].str[2:4]
            + ":"
            + result["time_part"].str[4:6]
        )
        result["时间"] = pd.to_datetime(
            result["datetime"],
            format="%Y-%m-%d %H:%M:%S",
            errors="coerce",
        )

        numeric_cols = ["open", "high", "low", "close", "volume", "amount"]
        for col in numeric_cols:
            result[col] = pd.to_numeric(result[col], errors="coerce")

        result = result.rename(
            columns={
                "open": "开盘",
                "close": "收盘",
                "high": "最高",
                "low": "最低",
                "volume": "成交量",
                "amount": "成交额",
            }
        )

        filtered = result[
            (result["时间"] >= start_datetime) & (result["时间"] <= end_datetime)
        ]
        if filtered.empty:
            logging.warning("股票 %s 在过滤后的时间范围内没有可用数据", normalized_symbol)
            return None

        return filtered[["时间", "开盘", "收盘", "最高", "最低", "成交量", "成交额"]].copy()

    def get_recent_trading_window(self, trading_days: int = 10, end_date: str | None = None):
        self.login()

        if trading_days <= 0:
            raise Exception("trading_days 必须是正整数")

        end_ts = pd.to_datetime(end_date).normalize() if end_date else pd.Timestamp.now().normalize()
        start_probe = end_ts - pd.Timedelta(days=max(45, trading_days * 8))

        result_set = self._bs.query_trade_dates(
            start_date=start_probe.strftime("%Y-%m-%d"),
            end_date=end_ts.strftime("%Y-%m-%d"),
        )
        if result_set.error_code != "0":
            raise Exception(f"查询交易日历失败: {result_set.error_msg}")

        rows = []
        while result_set.error_code == "0" and result_set.next():
            rows.append(result_set.get_row_data())

        if not rows:
            raise Exception("未获取到交易日历数据")

        trade_dates = pd.DataFrame(rows, columns=result_set.fields)
        if "calendar_date" not in trade_dates.columns or "is_trading_day" not in trade_dates.columns:
            raise Exception("交易日历返回字段不完整")

        trading_days_df = trade_dates[trade_dates["is_trading_day"] == "1"].copy()
        if trading_days_df.empty:
            raise Exception("最近区间内没有可用交易日")

        trading_days_df["calendar_date"] = pd.to_datetime(trading_days_df["calendar_date"])
        recent_days = trading_days_df.sort_values("calendar_date").tail(trading_days)
        if recent_days.empty:
            raise Exception("无法确定最近交易日窗口")

        start_day = recent_days.iloc[0]["calendar_date"].strftime("%Y-%m-%d")
        end_day = recent_days.iloc[-1]["calendar_date"].strftime("%Y-%m-%d")
        return f"{start_day} 09:30:00", f"{end_day} 15:00:00"


def get_stock_data(
    symbol: str,
    start_date: str,
    end_date: str,
    period: str = "5",
    client: BaoStockClient | None = None,
):
    own_client = client is None
    client = client or BaoStockClient()

    try:
        return client.get_stock_data(symbol, start_date, end_date, period)
    finally:
        if own_client:
            client.logout()


def calculate_returns(stock_data, price_col: str = "收盘"):
    if stock_data is None:
        return None

    stock_data = stock_data.sort_values("时间").copy()
    stock_data["收益率"] = stock_data[price_col].pct_change()
    return stock_data[["时间", "收益率"]]


def create_returns_matrix(stock_datas, stock_names):
    if not stock_datas or not stock_names:
        return None

    returns_list = []
    for stock_data, stock_name in zip(stock_datas, stock_names):
        if stock_data is None:
            continue

        returns = calculate_returns(stock_data)
        if returns is None:
            continue

        returns = returns.rename(columns={"收益率": f"收益率_{stock_name}"})
        returns_list.append(returns)

    if not returns_list:
        return None

    merged_returns = returns_list[0]
    for returns in returns_list[1:]:
        merged_returns = pd.merge(merged_returns, returns, on="时间", how="inner")

    return merged_returns.dropna()


def calculate_correlation_matrix(returns_matrix, method: str = "pearson"):
    if returns_matrix is None:
        return None

    return_cols = [col for col in returns_matrix.columns if col.startswith("收益率_")]
    if not return_cols:
        return None

    correlation_matrix = returns_matrix[return_cols].corr(method=method)
    correlation_matrix.columns = [
        col.replace("收益率_", "") for col in correlation_matrix.columns
    ]
    correlation_matrix.index = [
        idx.replace("收益率_", "") for idx in correlation_matrix.index
    ]
    return correlation_matrix


def calculate_significance_matrix(returns_matrix):
    if returns_matrix is None:
        return None

    return_cols = [col for col in returns_matrix.columns if col.startswith("收益率_")]
    if not return_cols:
        return None

    pvalue_matrix = pd.DataFrame(
        np.ones((len(return_cols), len(return_cols))),
        columns=return_cols,
        index=return_cols,
    )

    for i in range(len(return_cols)):
        for j in range(i + 1, len(return_cols)):
            col1 = return_cols[i]
            col2 = return_cols[j]
            _, pvalue = stats.pearsonr(returns_matrix[col1], returns_matrix[col2])
            pvalue_matrix.loc[col1, col2] = pvalue
            pvalue_matrix.loc[col2, col1] = pvalue

    pvalue_matrix.columns = [col.replace("收益率_", "") for col in pvalue_matrix.columns]
    pvalue_matrix.index = [idx.replace("收益率_", "") for idx in pvalue_matrix.index]
    return pvalue_matrix


def _figure_to_base64() -> str:
    img = io.BytesIO()
    plt.savefig(img, format="png", dpi=300, bbox_inches="tight")
    img.seek(0)
    encoded = base64.b64encode(img.getvalue()).decode("utf-8")
    plt.close()
    return encoded


def plot_correlation_heatmap_base64(correlation_matrix, method: str = "pearson"):
    if correlation_matrix is None:
        return None

    plt.figure(figsize=(12, 10))
    sns.heatmap(
        correlation_matrix,
        annot=True,
        cmap="coolwarm",
        center=0,
        fmt=".4f",
        square=True,
        linewidths=0.5,
        cbar_kws={"shrink": 0.8},
    )
    plt.title(f"股票相关性矩阵（{method} 相关系数）", fontsize=16, pad=20)
    plt.xticks(rotation=45, ha="right", fontsize=12)
    plt.yticks(rotation=0, fontsize=12)
    plt.tight_layout()
    return _figure_to_base64()


def plot_correlation_matrix_base64(correlation_matrix, method: str = "pearson"):
    if correlation_matrix is None:
        return None

    plt.figure(figsize=(12, 10))
    sns.heatmap(
        correlation_matrix,
        annot=True,
        cmap="YlGnBu",
        fmt=".2f",
        square=True,
        linewidths=0.5,
        cbar_kws={"shrink": 0.8},
    )
    plt.title(f"相关性系数矩阵（{method}）", fontsize=16, pad=20)
    plt.xticks(rotation=45, ha="right", fontsize=12)
    plt.yticks(rotation=0, fontsize=12)
    plt.tight_layout()
    return _figure_to_base64()


def plot_significance_heatmap_base64(pvalue_matrix):
    if pvalue_matrix is None:
        return None

    plt.figure(figsize=(12, 10))
    significance_matrix = pvalue_matrix < 0.05
    sns.heatmap(
        pvalue_matrix,
        annot=significance_matrix,
        cmap="Reds",
        center=0.05,
        fmt=".4f",
        square=True,
        linewidths=0.5,
        cbar_kws={"shrink": 0.8},
        mask=np.eye(len(pvalue_matrix)),
        annot_kws={"ha": "center", "va": "center", "color": "black"},
    )
    plt.title("相关性显著性矩阵（p值，True表示p<0.05）", fontsize=16, pad=20)
    plt.xticks(rotation=45, ha="right", fontsize=12)
    plt.yticks(rotation=0, fontsize=12)
    plt.tight_layout()
    return _figure_to_base64()


class StockCorrelationAnalyzer:
    def __init__(self, file_path: str, sheet_name: str = "股票维度"):
        self.file_path = file_path
        self.sheet_name = sheet_name
        self.df = None
        self.co_occurrence_dates = None
        self.stock_set = None
        self.stock_to_concepts = None
        self.stock_to_code = {}
        self.read_data()
        self._resolve_columns()
        self.analyze_correlation()

    def read_data(self) -> None:
        try:
            self.df = pd.read_excel(self.file_path, sheet_name=self.sheet_name)
        except FileNotFoundError as exc:
            raise Exception(f"文件未找到 - {self.file_path}") from exc
        except ValueError as exc:
            if "No sheet named" in str(exc):
                raise Exception(f"未找到名为【{self.sheet_name}】的工作表") from exc
            raise Exception(f"读取 Excel 文件失败 - {exc}") from exc
        except Exception as exc:
            raise Exception(f"读取文件时发生错误 - {exc}") from exc

    def _pick_column(self, *candidates: str) -> str:
        for candidate in candidates:
            if candidate in self.df.columns:
                return candidate
        raise Exception(
            f"缺少必要字段，期望字段之一: {', '.join(candidates)}；实际字段: {', '.join(map(str, self.df.columns))}"
        )

    def _resolve_columns(self) -> None:
        self.date_col = self._pick_column("日期")
        self.stock_name_col = self._pick_column("股票简称")
        self.stock_code_col = self._pick_column("股票代码")
        self.plate_concept_col = self._pick_column("板块概念", "板块名称")
        self.concept_tags_col = self._pick_column("概念标签")

    def analyze_correlation(self) -> None:
        if self.df is None:
            raise Exception("数据未加载")

        grouped_by_date = self.df.groupby(self.date_col)
        self.co_occurrence_dates = defaultdict(set)
        self.stock_set = set()
        self.stock_to_concepts = defaultdict(set)

        for date, date_data in grouped_by_date:
            stock_to_all_concepts = {}

            for _, row in date_data.iterrows():
                stock = row[self.stock_name_col]
                stock_code = ""
                if pd.notna(row[self.stock_code_col]):
                    stock_code = f"{int(row[self.stock_code_col]):06d}"

                self.stock_set.add(stock)
                self.stock_to_code.setdefault(stock, stock_code)

                all_concepts = []
                plate_concept = row[self.plate_concept_col]
                if pd.notna(plate_concept) and plate_concept.strip():
                    all_concepts.append(plate_concept.strip())

                concepts_str = row[self.concept_tags_col]
                if pd.notna(concepts_str) and concepts_str.strip():
                    concept_tags = [
                        concept.strip()
                        for concept in concepts_str.split("、")
                        if concept.strip()
                    ]
                    all_concepts.extend(concept_tags)

                stock_to_all_concepts[stock] = all_concepts
                for concept in all_concepts:
                    self.stock_to_concepts[stock].add(concept)

            concept_to_stocks = defaultdict(list)
            for stock, concepts in stock_to_all_concepts.items():
                for concept in concepts:
                    concept_to_stocks[concept].append(stock)

            for stocks in concept_to_stocks.values():
                if len(stocks) < 2:
                    continue
                for i in range(len(stocks)):
                    for j in range(i + 1, len(stocks)):
                        stock_pair = tuple(sorted([stocks[i], stocks[j]]))
                        self.co_occurrence_dates[stock_pair].add(date)

    def get_topk_related_stocks(self, target_stock: str, topk: int = 10, match_300: bool = False):
        if self.stock_set is None or self.co_occurrence_dates is None:
            raise Exception("尚未进行关联关系分析")

        if target_stock not in self.stock_set:
            raise Exception(f"未找到股票 '{target_stock}'")

        related_stocks = []
        for (stock1, stock2), dates in self.co_occurrence_dates.items():
            if stock1 == target_stock:
                concepts = list(self.stock_to_concepts.get(stock2, []))
                stock_code = self.stock_to_code.get(stock2, "")
                if not match_300 or (stock_code and stock_code.startswith("30")):
                    related_stocks.append(
                        (stock2, stock_code, len(dates), sorted(list(dates)), concepts)
                    )
            elif stock2 == target_stock:
                concepts = list(self.stock_to_concepts.get(stock1, []))
                stock_code = self.stock_to_code.get(stock1, "")
                if not match_300 or (stock_code and stock_code.startswith("30")):
                    related_stocks.append(
                        (stock1, stock_code, len(dates), sorted(list(dates)), concepts)
                    )

        related_stocks.sort(key=lambda item: item[2], reverse=True)
        return related_stocks[:topk]
