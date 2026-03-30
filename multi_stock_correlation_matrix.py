import akshare as ak
import pandas as pd
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt
import seaborn as sns
import argparse

# 设置中文字体和图表样式
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS']  # 用于显示中文
plt.rcParams['axes.unicode_minus'] = False  # 用于显示负号


def get_stock_data(symbol, start_date, end_date, period="5"):
    """
    获取股票的分钟级别数据
    """
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


def plot_correlation_heatmap(correlation_matrix, method='pearson', filename='correlation_heatmap.png'):
    """
    绘制相关性矩阵热力图
    """
    if correlation_matrix is None:
        return
    
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
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"相关性矩阵热力图已保存为: {filename}")


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


def plot_significance_heatmap(pvalue_matrix, filename='significance_heatmap.png'):
    """
    绘制显著性p值矩阵热力图
    """
    if pvalue_matrix is None:
        return
    
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
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"显著性矩阵热力图已保存为: {filename}")


def analyze_stock_group_correlation(stocks, start_date, end_date, period="5"):
    """
    分析一组股票的相关性
    """
    print(f"开始分析 {len(stocks)} 只股票的相关性...")
    print(f"时间范围: {start_date} 到 {end_date}")
    print(f"周期: {period} 分钟")
    print("=" * 60)
    
    # 1. 获取所有股票数据
    stock_datas = []
    stock_names = []
    valid_stocks = []
    
    for symbol, name in stocks:
        print(f"正在获取 {name} ({symbol}) 数据...")
        data = get_stock_data(symbol, start_date, end_date, period)
        if data is not None:
            stock_datas.append(data)
            stock_names.append(name)
            valid_stocks.append((symbol, name))
            print(f"✓ 成功获取 {name} ({symbol}) 数据，共 {len(data)} 条记录")
        else:
            print(f"✗ 无法获取 {name} ({symbol}) 数据")
    
    if not valid_stocks:
        print("错误：没有成功获取任何股票数据")
        return
    
    print(f"\n成功获取 {len(valid_stocks)} 只股票的数据")
    print("=" * 60)
    
    # 2. 创建收益率矩阵
    print("\n正在创建收益率矩阵...")
    returns_matrix = create_returns_matrix(stock_datas, stock_names)
    
    if returns_matrix is None:
        print("错误：无法创建收益率矩阵")
        return
    
    print(f"✓ 收益率矩阵创建成功，共 {len(returns_matrix)} 个时间点")
    print("=" * 60)
    
    # 3. 计算并绘制不同方法的相关性矩阵
    correlation_methods = ['pearson', 'spearman', 'kendall']
    
    for method in correlation_methods:
        print(f"\n正在计算 {method} 相关系数矩阵...")
        correlation_matrix = calculate_correlation_matrix(returns_matrix, method)
        
        if correlation_matrix is not None:
            print(f"✓ {method} 相关系数矩阵计算成功")
            print(f"\n{method} 相关系数矩阵:")
            print(correlation_matrix.round(4))
            
            # 保存相关性矩阵到CSV文件
            csv_filename = f'correlation_matrix_{method}.csv'
            correlation_matrix.to_csv(csv_filename)
            print(f"✓ 相关性矩阵已保存为: {csv_filename}")
            
            # 绘制热力图
            heatmap_filename = f'correlation_heatmap_{method}.png'
            plot_correlation_heatmap(correlation_matrix, method, heatmap_filename)
        else:
            print(f"✗ 无法计算 {method} 相关系数矩阵")
    
    # 4. 计算并绘制显著性矩阵
    print(f"\n正在计算相关性显著性p值矩阵...")
    significance_matrix = calculate_significance_matrix(returns_matrix)
    
    if significance_matrix is not None:
        print(f"✓ 显著性p值矩阵计算成功")
        print(f"\n显著性p值矩阵（部分显示）:")
        print(significance_matrix.round(4).head())
        
        # 保存显著性矩阵到CSV文件
        csv_filename = f'significance_pvalue_matrix.csv'
        significance_matrix.to_csv(csv_filename)
        print(f"✓ 显著性p值矩阵已保存为: {csv_filename}")
        
        # 绘制热力图
        heatmap_filename = f'significance_heatmap.png'
        plot_significance_heatmap(significance_matrix, heatmap_filename)
    
    print("\n" + "=" * 60)
    print("多股票相关性分析完成！")
    print(f"分析的股票: {', '.join([name for _, name in valid_stocks])}")
    print("所有结果文件已保存到当前目录")


def parse_arguments():
    """
    解析命令行参数
    """
    parser = argparse.ArgumentParser(description='多股票相关性矩阵分析工具')
    
    parser.add_argument('-s', '--stocks', nargs='+', required=True,
                      help='股票代码和名称，格式为"代码:名称"，例如：301308:江波龙 300475:香农芯创')
    
    parser.add_argument('-sd', '--start_date', default='2025-12-15 09:30:00',
                      help='开始时间，格式：YYYY-MM-DD HH:MM:SS，默认：2025-12-15 09:30:00')
    
    parser.add_argument('-ed', '--end_date', default='2025-12-15 15:00:00',
                      help='结束时间，格式：YYYY-MM-DD HH:MM:SS，默认：2025-12-15 15:00:00')
    
    parser.add_argument('-p', '--period', default='5',
                      help='周期（分钟），默认：5')
    
    return parser.parse_args()


def main():
    """
    主函数
    """
    # 解析命令行参数
    args = parse_arguments()
    
    # 解析股票参数
    try:
        stocks = []
        for stock_arg in args.stocks:
            symbol, name = stock_arg.split(':')
            stocks.append((symbol, name))
        
        if not stocks:
            print("错误：请至少提供一只股票")
            return
            
    except ValueError:
        print("错误：股票参数格式不正确，请使用\"代码:名称\"格式，例如：301308:江波龙")
        return
    
    # 执行分析
    analyze_stock_group_correlation(
        stocks=stocks,
        start_date=args.start_date,
        end_date=args.end_date,
        period=args.period
    )


if __name__ == "__main__":
    main()