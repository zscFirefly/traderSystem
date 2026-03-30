import pandas as pd
import networkx as nx

def build_knowledge_graph(linkage_df, min_weight=1):
    """
    构建股票关联知识图谱
    
    参数：
    linkage_df: 包含股票关联数据的DataFrame，需要包含'股票代码_A'、'股票简称_A'、'股票代码_B'、'股票简称_B'和'共现频次'列
    min_weight: 最小权重阈值，低于此值的关联将被忽略
    
    返回：
    networkx.Graph: 构建好的无向图
    """
    print(f"[日志] 开始构建股票关联知识图谱...")
    print(f"[日志] 关联数据记录数: {len(linkage_df)}")
    print(f"[日志] 最小权重阈值: {min_weight}")
    
    # 1. 初始化图
    G = nx.Graph()
    print(f"[日志] 图初始化完成")
    
    # 2. 添加边
    print(f"[日志] 开始添加边...")
    # 只需要单向边即可 (因为图是无向的，A-B关联等于B-A关联)
    # 我们需要先对 linkage_df 去重，只保留 A < B 的行，以免权重翻倍
    edges_data = linkage_df[linkage_df['股票代码_A'] < linkage_df['股票代码_B']]
    print(f"[日志] 去重后需要处理的边数: {len(edges_data)}")
    
    total_edges = len(edges_data)
    added_edges = 0
    
    for idx, row in edges_data.iterrows():
        # 每处理5000条边显示一次进度
        if idx % 5000 == 0:
            print(f"[日志] 正在添加边 {idx}/{total_edges} ({idx/total_edges*100:.1f}%)")
            
        if row['共现频次'] >= min_weight: # 过滤掉偶然关联
            G.add_edge(row['股票简称_A'], row['股票简称_B'], weight=row['共现频次'])
            added_edges += 1
    
    print(f"[日志] 边添加完成")
    print(f"[日志] 最终知识图谱统计:")
    print(f"[日志] - 节点数量: {len(G.nodes())}")
    print(f"[日志] - 边数量: {len(G.edges())}")
    print(f"[日志] - 权重过滤后添加的边数: {added_edges}")
    
    return G

def analyze_communities(G):
    """
    分析图中的社区结构和中心性
    
    参数：
    G: networkx.Graph对象
    
    返回：
    tuple: (communities, centrality)
        communities: 连通子图列表
        centrality: 度中心性字典
    """
    print(f"[日志] 开始分析社区结构...")
    print(f"[日志] 图节点数: {len(G.nodes())}, 边数: {len(G.edges())}")
    
    # 1. 寻找连通子图 (即一个个独立的圈子)
    print(f"[日志] 正在计算连通子图...")
    # 实际产品中可以使用 Louvain 算法进行更复杂的社区划分
    communities = list(nx.connected_components(G))
    print(f"[日志] 连通子图计算完成，共找到 {len(communities)} 个社区")
    
    # 统计社区大小分布
    community_sizes = sorted([len(c) for c in communities], reverse=True)
    print(f"[日志] 社区大小分布（前10个）: {community_sizes[:10]}")
    
    # 2. 计算节点的度中心性 (Degree Centrality) - 谁的连接最多
    print(f"[日志] 正在计算节点度中心性...")
    centrality = nx.degree_centrality(G)
    print(f"[日志] 度中心性计算完成")
    
    # 显示中心性最高的5个节点
    top_nodes = sorted(centrality.items(), key=lambda x: x[1], reverse=True)[:5]
    print(f"[日志] 中心性最高的5个节点:")
    for node, score in top_nodes:
        print(f"[日志]   {node}: {score:.4f}")
    
    return communities, centrality

def read_excel_data(excel_file, sheet_name='股票维度'):
    """
    读取Excel文件中的股票数据
    
    参数：
    excel_file: Excel文件路径
    sheet_name: 工作表名称
    
    返回：
    DataFrame: 股票数据
    """
    print(f"[日志] 开始读取Excel文件: {excel_file}, 工作表: {sheet_name}")
    try:
        print(f"[日志] 正在加载Excel数据...")
        df = pd.read_excel(excel_file, sheet_name=sheet_name)
        print(f"[日志] Excel数据加载成功，共{len(df)}行数据")
        print(f"[日志] 数据列名: {list(df.columns)}")
        
        # 确保股票代码格式为字符串，添加前导零
        if '股票代码' in df.columns:
            print(f"[日志] 正在格式化股票代码...")
            df['股票代码'] = df['股票代码'].apply(lambda x: f"{int(x):06d}" if pd.notna(x) else "")
            print(f"[日志] 股票代码格式化完成")
        else:
            print(f"[日志] 警告: 数据中不存在'股票代码'列")
        
        # 显示数据样例
        print(f"[日志] 数据前3行样例:")
        print(df.head(3))
        
        return df
    except Exception as e:
        print(f"[日志] 错误: 读取Excel文件时出错: {e}")
        raise

def generate_linkage_data_from_csv(csv_file):
    """
    从CSV文件生成股票关联数据
    
    参数：
    csv_file: 股票到概念映射的CSV文件路径
    
    返回：
    DataFrame: 包含股票关联数据的DataFrame
    """
    print(f"[日志] 开始生成股票关联数据...")
    
    # 读取CSV文件
    print(f"[日志] 正在读取CSV文件: {csv_file}")
    stock_concept_df = pd.read_csv(csv_file)
    print(f"[日志] CSV数据加载成功，共{len(stock_concept_df)}行数据")
    print(f"[日志] 数据列名: {list(stock_concept_df.columns)}")
    
    # 显示数据样例
    print(f"[日志] 数据前3行样例:")
    print(stock_concept_df.head(3))
    
    # 为了保持与原函数兼容，我们需要获取股票代码信息
    # 由于CSV文件可能不包含股票代码，我们可以生成假的代码
    print(f"[日志] 生成股票代码映射...")
    all_stocks = sorted(stock_concept_df['股票简称'].unique())
    stock_to_code = {stock: f"{i:06d}" for i, stock in enumerate(all_stocks, 1)}
    print(f"[日志] 共生成 {len(stock_to_code)} 个股票代码映射")
    
    # 计算股票之间的共现关系
    co_occurrence = {}
    print(f"[日志] 开始计算股票共现关系...")
    
    # 按日期和概念分组，统计每对股票的共现频次
    grouped = stock_concept_df.groupby(['日期', '概念'])
    total_groups = len(grouped)
    print(f"[日志] 总共需要处理 {total_groups} 个日期和概念组合...")
    
    for idx, (key, group) in enumerate(grouped, 1):
        # 每处理50个组显示一次进度
        if idx % 50 == 0 or idx == total_groups:
            print(f"[日志] 已处理 {idx}/{total_groups} 个组合 ({idx/total_groups*100:.1f}%)")
            
        date, concept = key
        stocks = group['股票简称'].unique()
        
        # 每处理500个组，显示详细信息
        if idx % 500 == 0:
            print(f"[日志] 处理详情 - 日期: {date}, 概念: {concept}, 股票数量: {len(stocks)}")
        
        # 计算每对股票的共现
        for i in range(len(stocks)):
            for j in range(i + 1, len(stocks)):
                stock1, stock2 = stocks[i], stocks[j]
                code1, code2 = stock_to_code[stock1], stock_to_code[stock2]
                
                # 确保顺序一致
                if code1 > code2:
                    stock1, stock2 = stock2, stock1
                    code1, code2 = code2, code1
                
                key = (stock1, stock2)
                co_occurrence[key] = co_occurrence.get(key, 0) + 1
    
    print(f"[日志] 共现关系计算完成，共生成 {len(co_occurrence)} 对股票关联")
    
    # 转换为DataFrame
    print(f"[日志] 开始转换为DataFrame格式...")
    linkage_data = []
    total_pairs = len(co_occurrence)
    
    for idx, ((stock1, stock2), count) in enumerate(co_occurrence.items(), 1):
        # 每处理5000对显示一次进度
        if idx % 5000 == 0 or idx == total_pairs:
            print(f"[日志] 正在构建DataFrame {idx}/{total_pairs} ({idx/total_pairs*100:.1f}%)")
        
        # 获取股票代码
        stock1_code = stock_to_code[stock1]
        stock2_code = stock_to_code[stock2]
        
        linkage_data.append({
            '股票代码_A': stock1_code,
            '股票简称_A': stock1,
            '股票代码_B': stock2_code,
            '股票简称_B': stock2,
            '共现频次': count
        })
    
    result_df = pd.DataFrame(linkage_data)
    print(f"[日志] DataFrame转换完成，共 {len(result_df)} 条记录")
    print(f"[日志] 关联数据生成完成")
    
    return result_df

def main():
    """
    主函数
    """
    print("[日志] ======== 开始股票关联族谱分析 ========")
    
    # 设置CSV文件路径
    csv_file = 'stock_to_concepts.csv'
    print(f"[日志] 设置数据文件路径: {csv_file}")
    
    # 步骤1: 生成股票关联数据
    print("\n[日志] ======== 步骤1: 生成股票关联数据 ========")
    linkage_df = generate_linkage_data_from_csv(csv_file)
    print(f"[日志] 股票关联数据生成完成，共 {len(linkage_df)} 条记录")
    
    # 步骤2: 构建知识图谱
    print("\n[日志] ======== 步骤2: 构建知识图谱 ========")
    min_weight = 1
    print(f"[日志] 设置最小权重阈值: {min_weight}")
    G = build_knowledge_graph(linkage_df, min_weight=min_weight)
    print(f"[日志] 知识图谱构建完成")
    
    # 步骤3: 分析社区结构
    print("\n[日志] ======== 步骤3: 分析社区结构 ========")
    communities, centrality = analyze_communities(G)
    print(f"[日志] 社区结构分析完成")
    
    # 步骤4: 输出分析结果
    print("\n[日志] ======== 步骤4: 输出分析结果 ========")
    print(f"\n[日志] 【产品形式二】全市场涨停关联族谱分析：")
    print(f"[日志] 识别出 {len(communities)} 个强关联股票团伙。")
    
    # 找出最大的一个团伙
    largest_clique = max(communities, key=len)
    print(f"[日志] 最大关联团伙成员数量: {len(largest_clique)}只")
    print(f"[日志] 最大关联团伙前10名成员: {list(largest_clique)[:10]}")
    
    # 在这个团伙中，谁是中心节点？
    print(f"[日志] 正在计算最大团伙的核心中枢...")
    sub_graph = G.subgraph(largest_clique)
    degrees = nx.degree(sub_graph, weight='weight') # 使用权重(共现次数)计算度
    leader = max(dict(degrees), key=dict(degrees).get)
    leader_score = dict(degrees)[leader]
    print(f"[日志] 该团伙的核心中枢(带头大哥)是: {leader}")
    print(f"[日志] 核心中枢加权连接强度: {leader_score}")
    
    # 找出前10个中心节点
    sorted_centrality = sorted(centrality.items(), key=lambda x: x[1], reverse=True)
    print("\n[日志] 全市场股票中心性排名前10：")
    for i, (stock, centrality_score) in enumerate(sorted_centrality[:10], 1):
        print(f"[日志] {i}. {stock}: {centrality_score:.4f}")
    
    # 保存结果
    output_file = 'stock_community_analysis.txt'
    print(f"\n[日志] ======== 步骤5: 保存分析结果 ========")
    print(f"[日志] 正在保存分析结果到文件: {output_file}")
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("【全市场涨停关联族谱分析结果】\n\n")
            f.write(f"识别出 {len(communities)} 个强关联股票团伙\n\n")
            
            f.write("最大关联团伙详情：\n")
            f.write(f"成员数量: {len(largest_clique)}只\n")
            f.write(f"成员列表: {', '.join(largest_clique)}\n")
            f.write(f"核心中枢: {leader} (加权连接强度: {leader_score})\n\n")
            
            f.write("全市场股票中心性排名前20：\n")
            for i, (stock, score) in enumerate(sorted_centrality[:20], 1):
                f.write(f"{i}. {stock}: {score:.4f}\n")
        print(f"[日志] 分析结果保存成功！")
    except Exception as e:
        print(f"[日志] 错误: 保存分析结果失败: {e}")
    
    print("\n[日志] ======== 股票关联族谱分析全部完成！ ========")

if __name__ == "__main__":
    main()