import pandas as pd
from collections import defaultdict


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
        self.stock_to_code = None  # 新增：股票简称到代码的映射
        
        # 初始化时读取数据
        self.read_data()
    
    def read_data(self):
        """
        读取Excel文件中的股票数据
        """
        try:
            self.df = pd.read_excel(self.file_path, sheet_name=self.sheet_name)
            print(f"成功读取文件: {self.file_path}")
            print(f"工作表: {self.sheet_name}")
        except FileNotFoundError:
            print(f"错误：文件未找到 - {self.file_path}")
            raise
        except ValueError as e:
            if "No sheet named" in str(e):
                print(f"错误：未找到名为【{self.sheet_name}】的工作表")
            else:
                print(f"错误：读取Excel文件时发生值错误 - {e}")
            raise
        except Exception as e:
            print(f"错误：读取文件时发生未知错误 - {e}")
            raise
    
    def show_data_info(self):
        """
        显示数据的基本信息
        """
        if self.df is None:
            print("错误：数据未加载")
            return
        
        print("\n=== 数据基本信息 ===")
        self.df.info()
        
        print("\n数据前5行：")
        print(self.df.head())
        
        print(f"\n数据总行数：{len(self.df)}")
        print(f"数据总列数：{len(self.df.columns)}")
        
        print("\n所有列名：")
        print(self.df.columns.tolist())
    
    def analyze_correlation(self):
        """
        分析股票之间的关联关系（基于同一天同板块概念或同概念标签涨停）
        """
        if self.df is None:
            print("错误：数据未加载")
            return
        
        print("\n=== 股票关联关系分析 ===")
        
        # 按日期分组
        grouped_by_date = self.df.groupby('日期')
        
        print(f"\n日期范围：从 {grouped_by_date.groups.keys().__iter__().__next__()} 到 {list(grouped_by_date.groups.keys())[-1]}")
        print(f"总共有 {len(grouped_by_date)} 个交易日的数据")
        
        # 构建共现矩阵（记录每对股票在同一天同板块概念或同概念标签涨停的具体日期）
        self.co_occurrence_dates = defaultdict(set)
        self.stock_set = set()
        self.stock_to_concepts = defaultdict(set)  # 初始化股票到概念的映射
        self.stock_to_code = {}  # 初始化股票简称到代码的映射
        
        # 遍历每个日期
        for date, date_data in grouped_by_date:
            # 构建股票到所有概念的映射（包括板块概念和概念标签）
            stock_to_all_concepts = {}
            
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
                    all_concepts.append(plate_concept.strip())
                
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
                            # 确保股票对的顺序一致，避免重复计数
                            stock_pair = tuple(sorted([stocks[i], stocks[j]]))
                            self.co_occurrence_dates[stock_pair].add(date)
        
        print(f"\n共分析了 {len(self.stock_set)} 只股票")
        print(f"发现了 {len(self.co_occurrence_dates)} 对有共现关系的股票")
    
    def get_topk_related_stocks(self, target_stock, topk=10, match_300=False):
        """
        获取与目标股票关联性最高的topk股票
        
        参数：
        target_stock: 目标股票简称
        topk: 返回的相关股票数量
        match_300: 是否仅匹配股票代码以30开头的股票
        
        返回：
        list: 包含(top_stock, top_stock_code, 共现次数, 共现日期列表, 概念列表)的列表
        """
        if self.stock_set is None or self.co_occurrence_dates is None:
            print("错误：尚未进行关联关系分析")
            return []
        
        if target_stock not in self.stock_set:
            print(f"错误：未找到股票 '{target_stock}'")
            return []
        
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
        related_stocks.sort(key=lambda x: x[1], reverse=True)
        return related_stocks[:topk]
    
    def show_example(self, topk=10):
        """
        展示示例查询结果
        
        参数：
        topk: 返回的相关股票数量
        """
        if self.df is None:
            print("错误：数据未加载")
            return
        
        print("\n=== 示例：查询关联股票 ===")
        # 从数据中随机选择一个股票作为示例
        sample_stock = self.df['股票简称'].iloc[0]
        print(f"示例股票：{sample_stock}")
        
        top_related = self.get_topk_related_stocks(sample_stock, topk=topk)
        if top_related:
            print(f"\n与 '{sample_stock}' 关联性最高的{topk}只股票：")
            for i, (stock, stock_code, count, dates, concepts) in enumerate(top_related, 1):
                concepts_str = ', '.join(concepts) if concepts else '无'
                print(f"{i}. {stock}({stock_code}) - 共现次数: {count}, 共现日期: {', '.join(dates)}, 概念: {concepts_str}")
        else:
            print(f"\n未找到与 '{sample_stock}' 相关的股票数据")
    
    def interactive_query(self):
        """
        交互式查询股票关联关系
        """
        if self.stock_set is None or self.co_occurrence_dates is None:
            print("错误：尚未进行关联关系分析")
            return
        
        print("\n=== 交互式查询 ===")
        while True:
            user_stock = input("请输入要查询的股票简称（输入'q'退出）：").strip()
            if user_stock.lower() == 'q':
                break
            
            user_topk = input("请输入要返回的相关股票数量（默认10）：").strip()
            try:
                user_topk = int(user_topk) if user_topk else 10
            except ValueError:
                print("无效的数字，使用默认值10")
                user_topk = 10
            
            related_stocks = self.get_topk_related_stocks(user_stock, topk=user_topk)
            if related_stocks:
                print(f"\n与 '{user_stock}' 关联性最高的{user_topk}只股票：")
                for i, (stock, count, dates, concepts) in enumerate(related_stocks, 1):
                    concepts_str = ', '.join(concepts) if concepts else '无'
                    print(f"{i}. {stock} - 共现次数: {count}, 共现日期: {', '.join(dates)}, 概念: {concepts_str}")
            else:
                print(f"\n未找到与 '{user_stock}' 相关的股票数据")
            print("-" * 50)


if __name__ == "__main__":
    # 设置Excel文件路径
    file_path = '/Users/zhengshuocong/Documents/trae_projects/20251115-/板块涨停_关系型_全量.xlsx'
    
    try:
        # 创建分析器实例
        analyzer = StockCorrelationAnalyzer(file_path)
        
        # 显示数据信息
        analyzer.show_data_info()
        
        # 分析关联关系
        analyzer.analyze_correlation()
        
        # 显示示例
        analyzer.show_example()
        
        # 启动交互式查询
        analyzer.interactive_query()
        
    except Exception as e:
        print(f"程序执行出错: {e}")
        print("请检查文件路径和格式是否正确")