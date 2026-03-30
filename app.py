from flask import Flask, render_template, request, jsonify
import pandas as pd
from collections import defaultdict
import os
import networkx as nx
import akshare as ak
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt
import seaborn as sns
import io
import base64

app = Flask(__name__)

# 设置中文字体和图表样式
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS']  # 用于显示中文
plt.rcParams['axes.unicode_minus'] = False  # 用于显示负号

def get_stock_data(symbol, start_date, end_date, period="5"):
    """
    获取股票的分钟级别数据
    """
    print(f"获取股票 {symbol} 数据，时间范围 {start_date} 至 {end_date}，周期 {period}")
    try:
        data = ak.stock_zh_a_hist_min_em(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            period=period,
            adjust=""
        )
        return data
    except Exception as e:
        print(f"获取股票 {symbol} 数据失败: {e}")
        return None


def calculate_returns(stock_data, price_col='收盘'):
    """
    计算股票的收益率序列
    """
    if stock_data is None:
        return None
    
    # 确保数据按时间排序
    stock_data = stock_data.sort_values('时间')
    
    # 计算收益率
    stock_data['收益率'] = stock_data[price_col].pct_change()
    
    return stock_data[['时间', '收益率']]


def create_returns_matrix(stock_datas, stock_names):
    """
    创建多股票收益率矩阵
    """
    if not stock_datas or not stock_names:
        return None
    
    # 获取第一个股票的收益率数据作为基础
    returns_list = []
    for i, (stock_data, stock_name) in enumerate(zip(stock_datas, stock_names)):
        if stock_data is not None:
            returns = calculate_returns(stock_data)
            if returns is not None:
                returns = returns.rename(columns={'收益率': f'收益率_{stock_name}'})
                returns_list.append(returns)
        else:
            print(f"股票 {stock_name} 数据不可用，将被排除")
    
    if not returns_list:
        return None
    
    # 合并所有股票的收益率数据，按时间对齐
    merged_returns = returns_list[0]
    for returns in returns_list[1:]:
        merged_returns = pd.merge(merged_returns, returns, on='时间', how='inner')
    
    # 去除包含NaN值的行
    merged_returns = merged_returns.dropna()
    
    return merged_returns


def calculate_correlation_matrix(returns_matrix, method='pearson'):
    """
    计算相关性矩阵
    """
    if returns_matrix is None:
        return None
    
    # 提取收益率列
    return_cols = [col for col in returns_matrix.columns if col.startswith('收益率_')]
    
    if not return_cols:
        return None
    
    # 计算相关性矩阵
    correlation_matrix = returns_matrix[return_cols].corr(method=method)
    
    # 重命名列和索引，去除'收益率_'前缀
    correlation_matrix.columns = [col.replace('收益率_', '') for col in correlation_matrix.columns]
    correlation_matrix.index = [idx.replace('收益率_', '') for idx in correlation_matrix.index]
    
    return correlation_matrix


def calculate_significance_matrix(returns_matrix):
    """
    计算相关性显著性p值矩阵
    """
    if returns_matrix is None:
        return None
    
    # 提取收益率列
    return_cols = [col for col in returns_matrix.columns if col.startswith('收益率_')]
    
    if not return_cols:
        return None
    
    # 创建空的p值矩阵
    n = len(return_cols)
    pvalue_matrix = pd.DataFrame(np.ones((n, n)), columns=return_cols, index=return_cols)
    
    # 计算每对股票的显著性p值
    for i in range(n):
        for j in range(i+1, n):
            col1 = return_cols[i]
            col2 = return_cols[j]
            
            # 使用scipy计算pearson相关系数和p值
            corr, pvalue = stats.pearsonr(returns_matrix[col1], returns_matrix[col2])
            
            # 填充p值矩阵（对称矩阵）
            pvalue_matrix.loc[col1, col2] = pvalue
            pvalue_matrix.loc[col2, col1] = pvalue
    
    # 重命名列和索引，去除'收益率_'前缀
    pvalue_matrix.columns = [col.replace('收益率_', '') for col in pvalue_matrix.columns]
    pvalue_matrix.index = [idx.replace('收益率_', '') for idx in pvalue_matrix.index]
    
    return pvalue_matrix


def plot_correlation_heatmap_base64(correlation_matrix, method='pearson'):
    """
    绘制相关性矩阵热力图并返回base64编码
    """
    if correlation_matrix is None:
        return None
    
    plt.figure(figsize=(12, 10))
    
    # 使用热力图可视化相关性矩阵
    sns.heatmap(
        correlation_matrix,
        annot=True,          # 显示数值
        cmap='coolwarm',     # 颜色映射
        center=0,            # 颜色中心值
        fmt='.4f',           # 数值格式
        square=True,         # 正方形单元格
        linewidths=0.5,      # 单元格边框宽度
        cbar_kws={'shrink': 0.8}  # 颜色条大小
    )
    
    plt.title(f'股票相关性矩阵（{method} 相关系数）', fontsize=16, pad=20)
    plt.xticks(rotation=45, ha='right', fontsize=12)
    plt.yticks(rotation=0, fontsize=12)
    plt.tight_layout()
    
    # 将图像保存到内存中
    img = io.BytesIO()
    plt.savefig(img, format='png', dpi=300, bbox_inches='tight')
    img.seek(0)
    
    # 编码为base64
    base64_img = base64.b64encode(img.getvalue()).decode('utf-8')
    plt.close()
    
    return f'data:image/png;base64,{base64_img}'


def plot_significance_heatmap_base64(pvalue_matrix):
    """
    绘制显著性p值矩阵热力图并返回base64编码
    """
    if pvalue_matrix is None:
        return None
    
    plt.figure(figsize=(12, 10))
    
    # 创建显著性标记（p < 0.05 为显著）
    significance_matrix = pvalue_matrix < 0.05
    
    # 使用热力图可视化显著性
    sns.heatmap(
        pvalue_matrix,
        annot=significance_matrix,  # 显示显著性标记
        cmap='Reds',               # 红色系表示p值大小
        center=0.05,               # 以0.05为中心
        fmt='.4f',                 # 数值格式
        square=True,               # 正方形单元格
        linewidths=0.5,            # 单元格边框宽度
        cbar_kws={'shrink': 0.8},  # 颜色条大小
        mask=np.eye(len(pvalue_matrix)),  # 隐藏对角线
        annot_kws={'ha': 'center', 'va': 'center', 'color': 'black'}  # 显著性标记样式
    )
    
    plt.title('相关性显著性矩阵（p值，True表示p<0.05）', fontsize=16, pad=20)
    plt.xticks(rotation=45, ha='right', fontsize=12)
    plt.yticks(rotation=0, fontsize=12)
    plt.tight_layout()
    
    # 将图像保存到内存中
    img = io.BytesIO()
    plt.savefig(img, format='png', dpi=300, bbox_inches='tight')
    img.seek(0)
    
    # 编码为base64
    base64_img = base64.b64encode(img.getvalue()).decode('utf-8')
    plt.close()
    
    return f'data:image/png;base64,{base64_img}'

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

# 初始化分析器
try:
    file_path = os.path.join(os.path.dirname(__file__), '板块涨停_关系型_全量.xlsx')
    analyzer = StockCorrelationAnalyzer(file_path)
    print("股票关联分析器初始化成功")
except Exception as e:
    analyzer = None
    print(f"初始化失败: {e}")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/search_stocks', methods=['GET'])
def search_stocks():
    query = request.args.get('query', '').strip()
    if not query or not analyzer or analyzer.df.empty:
        return jsonify([])
    
    # 模糊搜索股票名称
    stocks = analyzer.df['股票简称'].unique()
    results = [stock for stock in stocks if query in stock]
    return jsonify(results[:10])  # 返回前10个匹配结果

@app.route('/api/related_stocks', methods=['GET'])
def related_stocks():
    stock = request.args.get('stock', '').strip()
    topk = request.args.get('topk', '10')
    match_300 = request.args.get('match_300', 'false').lower() == 'true'
    
    try:
        topk = int(topk) if topk else 10
        if not stock or not analyzer:
            return jsonify({'error': '参数错误'}), 400
        
        results = analyzer.get_topk_related_stocks(stock, topk, match_300)
        # 转换日期格式
        formatted_results = []
        for stock_name, stock_code, count, dates, concepts in results:
            formatted_dates = [date.strftime('%Y-%m-%d') if hasattr(date, 'strftime') else str(date) for date in dates]
            formatted_results.append({
                'stock_name': stock_name,
                'stock_code': stock_code,
                'count': count,
                'dates': formatted_dates,
                'concepts': concepts
            })
        
        return jsonify({
            'success': True,
            'target_stock': stock,
            'results': formatted_results
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/concept_stocks', methods=['GET'])
def concept_stocks():
    """
    根据概念查询相关股票
    整合stock_knowledge_graph.py的逻辑，构建知识图谱并分析股票关联
    """
    concept = request.args.get('concept', '').strip()
    topk = request.args.get('topk', '20')
    min_weight = request.args.get('min_weight', '1')
    
    try:
        topk = int(topk) if topk else 20
        min_weight = int(min_weight) if min_weight else 1
        if not concept or not analyzer:
            return jsonify({'error': '参数错误'}), 400
        
        # 构建概念到股票的映射
        concept_to_stocks = defaultdict(list)
        for stock_name, concepts_list in analyzer.stock_to_concepts.items():
            for stock_concept in concepts_list:
                concept_to_stocks[stock_concept].append(stock_name)
        
        # 检查概念是否存在
        if concept not in concept_to_stocks:
            return jsonify({
                'success': True,
                'concept': concept,
                'results': [],
                'message': f'未找到与概念 "{concept}" 相关的股票'
            })
        
        # 获取与概念相关的股票
        concept_stocks_list = concept_to_stocks[concept]
        
        # 构建该概念下股票的知识图谱，使用stock_knowledge_graph.py的方法
        # 创建股票关联数据
        linkage_data = []
        for stock_pair, dates in analyzer.co_occurrence_dates.items():
            stock1, stock2 = stock_pair
            # 只考虑该概念下的股票对
            if (stock1 in concept_stocks_list or stock2 in concept_stocks_list) and len(dates) >= min_weight:
                linkage_data.append({
                    '股票简称_A': stock1,
                    '股票简称_B': stock2,
                    '共现频次': len(dates),
                    '共现日期': sorted(list(dates))
                })
        
        # 构建子图谱
        G = nx.Graph()
        for item in linkage_data:
            G.add_edge(item['股票简称_A'], item['股票简称_B'], weight=item['共现频次'])
        
        # 计算中心性（使用stock_knowledge_graph.py的中心性分析方法）
        centrality = nx.degree_centrality(G) if G.number_of_nodes() > 0 else {}
        
        # 为每个股票准备详细信息，并按中心性排序
        results = []
        for stock_name in concept_stocks_list:
            stock_code = analyzer.stock_to_code.get(stock_name, '')
            all_concepts = list(analyzer.stock_to_concepts.get(stock_name, []))
            
            # 获取该股票在图谱中的中心性
            centrality_score = centrality.get(stock_name, 0)
            
            # 获取与该股票在同一概念下关联度最高的股票
            related_stocks = []
            if stock_name in G:
                neighbors = sorted(G.neighbors(stock_name), 
                                  key=lambda x: G[stock_name][x]['weight'], 
                                  reverse=True)
                related_stocks = neighbors[:5]  # 只取前5个最相关的
            
            results.append({
                'stock_name': stock_name,
                'stock_code': stock_code,
                'concepts': all_concepts,
                'centrality': round(centrality_score, 4),
                'related_stocks': related_stocks
            })
        
        # 按中心性降序排序，取前topk
        results.sort(key=lambda x: x['centrality'], reverse=True)
        
        # 转换日期格式
        for result in results:
            for related_stock in result['related_stocks']:
                # 查找共现日期
                stock_pair = tuple(sorted([result['stock_name'], related_stock]))
                if stock_pair in analyzer.co_occurrence_dates:
                    dates = analyzer.co_occurrence_dates[stock_pair]
                    # 这里不直接转换日期，因为results中不直接保存日期
                    pass
        
        return jsonify({
            'success': True,
            'concept': concept,
            'total_count': len(concept_stocks_list),
            'graph_stats': {
                'nodes': G.number_of_nodes(),
                'edges': G.number_of_edges()
            },
            'results': results[:topk]
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/debug_data', methods=['GET'])
def debug_data():
    """
    调试接口：查看当前加载的数据状态
    """
    if not analyzer:
        return jsonify({'error': '分析器未初始化'}), 400
    
    try:
        # 获取一些基本统计信息
        result = {
            'stock_count': len(analyzer.stock_set) if analyzer.stock_set else 0,
            'concept_count': len(set(c for concepts in analyzer.stock_to_concepts.values() for c in concepts)),
            'sample_stocks': list(analyzer.stock_set)[:10] if analyzer.stock_set else [],
            'sample_concepts': []
        }
        
        # 获取一些样本概念
        all_concepts = set()
        for concepts in analyzer.stock_to_concepts.values():
            all_concepts.update(concepts)
            if len(result['sample_concepts']) >= 10:
                break
        result['sample_concepts'] = list(all_concepts)[:10]
        
        return jsonify({
            'success': True,
            'data': result
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/multi_stock_correlation', methods=['POST'])
def multi_stock_correlation():
    """
    多股票相关性分析API接口
    
    请求参数：
    {"stocks": [{"symbol": "600519", "name": "贵州茅台"}, {"symbol": "000858", "name": "五粮液"}],
     "start_date": "2025-12-15 09:30:00",
     "end_date": "2025-12-15 15:00:00",
     "period": "5",
     "include_heatmap": true}
    """
    try:
        # 获取请求参数
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': '请求参数为空'}), 400
        
        stocks = data.get('stocks', [])
        start_date = data.get('start_date', '2025-12-15 09:30:00')
        end_date = data.get('end_date', '2025-12-15 15:00:00')
        period = data.get('period', '5')
        include_heatmap = data.get('include_heatmap', False)
        
        if not stocks:
            return jsonify({'success': False, 'error': '请至少提供一只股票'}), 400
        
        # 验证股票参数格式
        valid_stocks = []
        for stock in stocks:
            if 'stock_code' in stock and 'stock_name' in stock:
                valid_stocks.append((stock['stock_code'], stock['stock_name']))
            else:
                return jsonify({'success': False, 'error': '股票参数格式错误，需要包含symbol和name字段'}), 400
        
        if not valid_stocks:
            return jsonify({'success': False, 'error': '没有有效的股票参数'}), 400
        
        # 1. 获取所有股票数据
        stock_datas = []
        stock_names = []
        valid_stocks_list = []
        
        for symbol, name in valid_stocks:
            print(f"正在获取 {name} ({symbol}) 数据...")
            data = get_stock_data(symbol, start_date, end_date, period)
            if data is not None:
                stock_datas.append(data)
                stock_names.append(name)
                valid_stocks_list.append((symbol, name))
                print(f"✓ 成功获取 {name} ({symbol}) 数据，共 {len(data)} 条记录")
            else:
                print(f"✗ 无法获取 {name} ({symbol}) 数据")
        
        if not valid_stocks_list:
            return jsonify({'success': False, 'error': '没有成功获取任何股票数据'}), 400
        
        # 2. 创建收益率矩阵
        print("\n正在创建收益率矩阵...")
        returns_matrix = create_returns_matrix(stock_datas, stock_names)
        
        if returns_matrix is None:
            return jsonify({'success': False, 'error': '无法创建收益率矩阵'}), 400
        
        print(f"✓ 收益率矩阵创建成功，共 {len(returns_matrix)} 个时间点")
        
        # 3. 计算不同方法的相关性矩阵
        correlation_methods = ['pearson', 'spearman', 'kendall']
        correlation_results = {}
        
        for method in correlation_methods:
            print(f"\n正在计算 {method} 相关系数矩阵...")
            correlation_matrix = calculate_correlation_matrix(returns_matrix, method)
            
            if correlation_matrix is not None:
                print(f"✓ {method} 相关系数矩阵计算成功")
                
                # 转换为字典格式
                corr_dict = correlation_matrix.round(4).to_dict()
                
                # 计算热力图
                heatmap_base64 = None
                if include_heatmap:
                    heatmap_base64 = plot_correlation_heatmap_base64(correlation_matrix, method)
                
                correlation_results[method] = {
                    'matrix': corr_dict,
                    'heatmap_base64': heatmap_base64
                }
            else:
                print(f"✗ 无法计算 {method} 相关系数矩阵")
        
        # 4. 计算显著性矩阵
        print(f"\n正在计算相关性显著性p值矩阵...")
        significance_matrix = calculate_significance_matrix(returns_matrix)
        
        significance_result = None
        if significance_matrix is not None:
            print(f"✓ 显著性p值矩阵计算成功")
            
            # 转换为字典格式
            sig_dict = significance_matrix.round(4).to_dict()
            
            # 计算热力图
            sig_heatmap_base64 = None
            if include_heatmap:
                sig_heatmap_base64 = plot_significance_heatmap_base64(significance_matrix)
            
            significance_result = {
                'matrix': sig_dict,
                'heatmap_base64': sig_heatmap_base64
            }
        
        # 5. 构建返回结果
        result = {
            'success': True,
            'target_stocks': [{'symbol': symbol, 'name': name} for symbol, name in valid_stocks_list],
            'time_range': {'start_date': start_date, 'end_date': end_date},
            'period': period,
            'returns_count': len(returns_matrix),
            'correlation_results': correlation_results,
            'significance_result': significance_result
        }
        
        return jsonify(result)
    except Exception as e:
        print(f"API错误: {e}")
        return jsonify({'success': False, 'error': str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)