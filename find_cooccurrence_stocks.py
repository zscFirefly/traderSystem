import pandas as pd
from collections import defaultdict
import os

class StockCorrelationAnalyzer:
    """
    股票关联关系分析器
    用于分析Excel文件中股票的共现关系（基于同一天涨停）
    """
    
    def __init__(self, file_path, sheet_name='股票维度'):
        """
        初始化股票关联关系分析器
        
        参数：
        file_path: Excel文件路径
        sheet_name: 工作表名称，默认为'股票维度'
        """
        self.file_path = file_path
        self.sheet_name = sheet_name
        self.df = None
        self.daily_stocks = None
        self.co_occurrence_dates = None
        self.stock_set = None
        self.stock_to_concepts = None  # 新增：股票到概念的映射
        
        # 初始化时读取数据
        self.read_data()
        self.analyze_correlation()
    
    def read_data(self):
        """
        读取Excel文件中的股票数据
        """
        try:
            self.df = pd.read_excel(self.file_path, sheet_name=self.sheet_name)
        except FileNotFoundError:
            raise Exception(f"文件未找到 - {self.file_path}")
        except ValueError as e:
            if "No sheet named" in str(e):
                raise Exception(f"未找到名为【{self.sheet_name}】的工作表")
            else:
                raise Exception(f"读取Excel文件时发生值错误 - {e}")
        except Exception as e:
            raise Exception(f"读取文件时发生未知错误 - {e}")
    
    def analyze_correlation(self):
        """
        分析股票之间的关联关系（基于同一天同板块概念或同概念标签涨停）
        """
        if self.df is None:
            raise Exception("数据未加载")
        
        # 按日期分组
        grouped_by_date = self.df.groupby('日期')
        
        # 构建共现矩阵（记录每对股票在同一天同板块概念或同概念标签涨停的具体日期）
        self.co_occurrence_dates = defaultdict(set)
        self.stock_set = set()
        self.stock_to_concepts = defaultdict(set)  # 初始化股票到概念的映射
        self.stock_to_code = {}  # 初始化股票简称到代码的映射
        
        # 遍历每个日期
        for date, date_data in grouped_by_date:
            # 构建股票到所有概念的映射（包括板块概念和概念标签）
            stock_to_all_concepts = {}
            # 新增：构建股票到当天板块概念的映射
            stock_to_plate_concept = {}
            
            for _, row in date_data.iterrows():
                stock = row['股票简称']
                # 确保股票代码显示为6位数字格式，包括前导零
                if pd.notna(row['股票代码']):
                    stock_code = f"{int(row['股票代码']):06d}"
                else:
                    stock_code = ""
                self.stock_set.add(stock)
                
                # 记录股票简称到代码的映射
                if stock not in self.stock_to_code:
                    self.stock_to_code[stock] = stock_code
                
                # 收集所有概念（板块概念 + 概念标签）
                all_concepts = []
                
                # 处理板块概念（单个概念）
                plate_concept = row['板块概念']
                if pd.notna(plate_concept) and plate_concept.strip():
                    plate_concept = plate_concept.strip()
                    all_concepts.append(plate_concept)
                    # 记录股票当天的板块概念
                    stock_to_plate_concept[stock] = plate_concept
                
                # 处理概念标签（多个概念，逗号分隔）
                concepts_str = row['概念标签']
                if pd.notna(concepts_str) and concepts_str.strip():
                    concept_tags = [c.strip() for c in concepts_str.split('、') if c.strip()]
                    all_concepts.extend(concept_tags)
                
                stock_to_all_concepts[stock] = all_concepts
                
                # 将所有概念添加到股票到概念的映射中
                for concept in all_concepts:
                    self.stock_to_concepts[stock].add(concept)
            
            # 构建概念到股票的映射
            concept_to_stocks = defaultdict(list)
            for stock, concepts in stock_to_all_concepts.items():
                for concept in concepts:
                    concept_to_stocks[concept].append(stock)
            
            # 在每个概念内统计股票共现关系
            for concept, stocks in concept_to_stocks.items():
                if len(stocks) >= 2:  # 至少需要两只股票才会有共现
                    # 记录每对股票的共现日期
                    for i in range(len(stocks)):
                        for j in range(i+1, len(stocks)):
                            # 获取两只股票
                            stock1 = stocks[i]
                            stock2 = stocks[j]
                            
                            # 检查两只股票是否都有板块概念记录
                            if stock1 in stock_to_plate_concept and stock2 in stock_to_plate_concept:
                                # 新增条件：只有当两只股票当天的板块概念相同时，才记录共现关系
                                if stock_to_plate_concept[stock1] == stock_to_plate_concept[stock2]:
                                    # 确保股票对的顺序一致，避免重复计数
                                    stock_pair = tuple(sorted([stock1, stock2]))
                                    self.co_occurrence_dates[stock_pair].add(date)
    
    def get_topk_related_stocks(self, target_stock, topk=10, match_300=False):
        """
        获取与目标股票关联性最高的topk股票
        
        参数：
        target_stock: 目标股票简称
        topk: 返回的相关股票数量
        match_300: 是否仅匹配股票代码以30开头的股票
        
        返回：
        list: 包含(top_stock, 共现次数, 共现日期列表, 概念列表)的列表
        """
        if self.stock_set is None or self.co_occurrence_dates is None:
            raise Exception("尚未进行关联关系分析")
        
        if target_stock not in self.stock_set:
            raise Exception(f"未找到股票 '{target_stock}'")
        
        # 收集与目标股票相关的所有股票及其共现信息
        related_stocks = []
        for (stock1, stock2), dates in self.co_occurrence_dates.items():
            if stock1 == target_stock:
                # 获取相关股票的概念信息和股票代码
                concepts = list(self.stock_to_concepts.get(stock2, []))
                stock_code = self.stock_to_code.get(stock2, '')
                
                # 应用股票代码过滤
                if not match_300 or (stock_code and stock_code.startswith('30')):
                    related_stocks.append((stock2, stock_code, len(dates), sorted(list(dates)), concepts))
            elif stock2 == target_stock:
                # 获取相关股票的概念信息和股票代码
                concepts = list(self.stock_to_concepts.get(stock1, []))
                stock_code = self.stock_to_code.get(stock1, '')
                
                # 应用股票代码过滤
                if not match_300 or (stock_code and stock_code.startswith('30')):
                    related_stocks.append((stock1, stock_code, len(dates), sorted(list(dates)), concepts))
        
        # 按共现次数降序排序，取前topk
        related_stocks.sort(key=lambda x: x[2], reverse=True)
        return related_stocks[:topk]
    
    def get_stocks_with_min_cooccurrence(self, target_stock, min_cooccurrence=2):
        """
        获取与目标股票共现次数大于等于指定阈值的股票
        
        参数：
        target_stock: 目标股票简称
        min_cooccurrence: 最小共现次数阈值
        
        返回：
        list: 包含(top_stock, 股票代码, 共现次数, 共现日期列表, 概念列表)的列表
        """
        if self.stock_set is None or self.co_occurrence_dates is None:
            raise Exception("尚未进行关联关系分析")
        
        if target_stock not in self.stock_set:
            raise Exception(f"未找到股票 '{target_stock}'")
        
        # 收集与目标股票相关的所有股票及其共现信息
        related_stocks = []
        for (stock1, stock2), dates in self.co_occurrence_dates.items():
            co_occurrence_count = len(dates)
            if co_occurrence_count >= min_cooccurrence:
                if stock1 == target_stock:
                    # 获取相关股票的概念信息和股票代码
                    concepts = list(self.stock_to_concepts.get(stock2, []))
                    stock_code = self.stock_to_code.get(stock2, '')
                    related_stocks.append((stock2, stock_code, co_occurrence_count, sorted(list(dates)), concepts))
                elif stock2 == target_stock:
                    # 获取相关股票的概念信息和股票代码
                    concepts = list(self.stock_to_concepts.get(stock1, []))
                    stock_code = self.stock_to_code.get(stock1, '')
                    related_stocks.append((stock1, stock_code, co_occurrence_count, sorted(list(dates)), concepts))
        
        # 按共现次数降序排序
        related_stocks.sort(key=lambda x: x[2], reverse=True)
        return related_stocks


def main():
    """
    主函数，用于运行股票共现查询脚本
    """
    print("=== 股票共现关系查询工具 ===")
    
    # 初始化分析器
    try:
        file_path = os.path.join(os.path.dirname(__file__), '板块涨停_关系型_全量.xlsx')
        analyzer = StockCorrelationAnalyzer(file_path)
        print("股票关联分析器初始化成功")
    except Exception as e:
        print(f"初始化失败: {e}")
        return
    
    # 获取用户输入的股票名称
    target_stock = input("请输入要查询的股票名称: ").strip()
    
    if not target_stock:
        print("错误：股票名称不能为空")
        return
    
    # 查询共现次数大于等于2的股票
    try:
        results = analyzer.get_stocks_with_min_cooccurrence(target_stock, min_cooccurrence=2)
        
        if not results:
            print(f"未找到与 '{target_stock}' 共现次数大于等于2的股票")
        else:
            print(f"\n与 '{target_stock}' 共现次数大于等于2的股票（共 {len(results)} 只）：")
            print("-" * 80)
            print("股票名称\t股票代码\t共现次数\t共现日期\t\t\t\t\t\t\t\t\t\t\t\t相关概念")
            print("-" * 80)
            
            # 收集股票代码和名称，用于日志输出
            stock_code_name_list = []
            
            for stock_name, stock_code, count, dates, concepts in results:
                # 格式化日期
                formatted_dates = [date.strftime('%Y-%m-%d') if hasattr(date, 'strftime') else str(date) for date in dates]
                dates_str = ', '.join(formatted_dates[:5])  # 只显示前5个日期
                if len(dates) > 5:
                    dates_str += f"...等共{len(dates)}个日期"
                
                # 格式化概念
                concepts_str = ', '.join(concepts[:5])  # 只显示前5个概念
                if len(concepts) > 5:
                    concepts_str += f"...等共{len(concepts)}个概念"
                
                print(f"{stock_name}\t{stock_code}\t{count}\t{dates_str}\t{concepts_str}")
                
                # 添加到股票代码和名称列表
                if stock_code:
                    stock_code_name_list.append(f"{stock_code}:{stock_name}")
            
            print("-" * 80)
            
            # 新增日志：以指定格式打印股票代码和名称
            if stock_code_name_list:
                print("\n股票代码:股票名称格式输出：")
                print(' '.join(stock_code_name_list))
    except Exception as e:
        print(f"查询失败: {e}")


if __name__ == "__main__":
    main()