# 股票关联关系分析系统

本项目是一个股票数据分析工具集，包含数据处理、概念股票映射、关联关系分析和Web可视化应用，帮助用户理解股票之间的关联关系和概念分类。

## 系统架构

- **后端框架**: Flask
- **数据处理**: pandas, networkx (用于知识图谱构建)
- **数据存储**: Excel文件, CSV文件
- **前端**: HTML (位于templates/index.html)
- **核心工具**: 数据预处理、概念分析、知识图谱构建、Web应用

## 核心检索逻辑

### 1. 数据初始化与关联分析

系统通过`StockCorrelationAnalyzer`类实现核心的关联分析功能：

```python
# 初始化分析器
analyzer = StockCorrelationAnalyzer(file_path, sheet_name='股票维度')
```

初始化过程包含两个关键步骤：

1. **数据加载** (`read_data()`): 从Excel文件读取股票数据
2. **关联关系分析** (`analyze_correlation()`): 分析股票之间的共现关系

### 2. 关联关系计算原理

关联分析基于以下核心逻辑：

1. **按日期分组**：将数据按交易日期进行分组
2. **构建概念映射**：
   - 为每个股票构建概念集合（包括板块概念和概念标签）
   - 构建双向映射：股票→概念 和 概念→股票
3. **共现关系计算**：
   - 在同一概念组内，计算每对股票的共现次数（同一天涨停的次数）
   - 记录每对股票的具体共现日期
4. **结果存储**：使用`co_occurrence_dates`字典存储共现关系

### 3. 股票搜索功能

通过`/api/search_stocks`端点提供模糊搜索功能：

```python
@app.route('/api/search_stocks', methods=['GET'])
def search_stocks():
    # 模糊匹配股票简称中包含查询字符串的结果
    stocks = analyzer.df['股票简称'].unique()
    results = [stock for stock in stocks if query in stock]
```

**特点**：
- 支持模糊匹配（股票名称中包含查询字符串）
- 限制返回前10个匹配结果
- 无查询条件时返回空列表

### 3. 相关股票检索功能

通过`/api/related_stocks`端点提供股票相关性分析：

```python
@app.route('/api/related_stocks', methods=['GET'])
def related_stocks():
    # 获取参数
    stock = request.args.get('stock', '').strip()  # 目标股票
    topk = request.args.get('topk', '10')         # 返回数量
    match_300 = request.args.get('match_300', 'false') == 'true'  # 是否仅匹配创业板
```

**检索参数**：
- `stock`: 目标股票简称（必填）
- `topk`: 返回的相关股票数量（默认10）
- `match_300`: 是否仅匹配股票代码以30开头的创业板股票（布尔值）

**检索流程**：
1. 参数验证和转换
2. 调用`get_topk_related_stocks()`获取相关股票
3. 格式化返回数据（包括日期格式转换）
4. 错误处理和状态返回

### 4. 概念相关股票查询功能

通过`/api/concept_stocks`端点提供概念相关股票的知识图谱分析：

**功能概述**：
- 根据指定概念查询相关股票
- 计算并返回知识图谱统计信息
- 按节点度中心性排序返回相关股票

**检索参数**：
- `concept`: 目标概念名称（必填）
- `topk`: 返回的相关股票数量（默认10）
- `min_weight`: 最小关联权重（默认1）

**返回数据格式**：
```json
{
  "success": true,
  "concept": "目标概念",
  "graph_stats": {
    "nodes": 1334,
    "edges": 2261
  },
  "results": [
    {
      "stock_name": "股票名称",
      "stock_code": "股票代码",
      "centrality": 0.85,
      "concepts": ["概念1", "概念2"],
      "related_stocks": ["相关股票1", "相关股票2"]
    }
  ]
}
```

**检索流程**：
1. 接收概念参数并验证
2. 调用知识图谱分析功能
3. 计算股票节点的度中心性
4. 生成并返回结构化数据

### 5. 相关度排序算法

相关股票排序基于以下规则：

```python
# 按共现次数降序排序，取前topk
related_stocks.sort(key=lambda x: x[2], reverse=True)
return related_stocks[:topk]
```

- **主要排序依据**：股票共现次数（同一天涨停的次数）
- **次要信息**：共现日期列表、共同概念标签、股票代码

## 数据结构

### 输入数据格式

Excel文件（`板块涨停_关系型_全量.xlsx`）需要包含以下关键字段：
- `日期`: 交易日期
- `股票简称`: 股票名称
- `股票代码`: 股票代码（数字）
- `板块概念`: 主要板块概念
- `概念标签`: 逗号分隔的概念标签列表

### 输出数据格式

相关股票API返回JSON格式：

```json
{
  "success": true,
  "target_stock": "目标股票名称",
  "results": [
    {
      "stock_name": "相关股票名称",
      "stock_code": "股票代码(6位)",
      "count": 共现次数,
      "dates": ["2023-01-01", "2023-01-05"],
      "concepts": ["概念1", "概念2"]
    }
  ]
}
```

## 运行指南

### 安装依赖

```bash
pip install flask pandas openpyxl
```

### 启动应用

```bash
python app.py
```

应用将运行在 `http://0.0.0.0:8080`

## 错误处理机制

系统包含多层错误处理：

1. **文件读取错误**：处理文件不存在、工作表不存在等情况
2. **数据验证错误**：检查必要参数是否存在
3. **业务逻辑错误**：如未找到指定股票时返回友好错误信息
4. **通用异常捕获**：确保系统稳定性

## 扩展功能

- **创业板过滤**：通过`match_300`参数支持仅显示创业板股票
- **股票代码格式化**：确保股票代码显示为标准6位数字格式
- **概念聚合**：同时考虑板块概念和概念标签进行关联分析

## 性能优化

- 使用字典和集合优化关联关系查找效率
- 限制搜索结果数量，避免返回过多数据
- 应用初始化时预计算所有关联关系，提高查询响应速度

## 工具集详解

### 1. 数据预处理工具 (process_stock_concepts.py)

#### 功能概述
该脚本用于处理原始Excel数据，构建股票到概念的映射和概念到股票的反向映射，并将处理后的数据保存到CSV文件中以供后续分析使用。

#### 核心类和方法

##### StockConceptProcessor类

```python
class StockConceptProcessor:
    def __init__(self, file_path, sheet_name='股票维度', output_dir=None):
        # 初始化处理器，设置文件路径、工作表名称和输出目录
```

**主要方法：**

- `read_data()`: 读取Excel文件中的股票数据
- `process()`: 处理股票概念映射，构建双向映射关系
- `save_to_csv()`: 将处理后的数据保存到CSV文件

#### 处理流程
1. **数据读取**: 从Excel文件读取股票数据，包含股票简称、板块概念、概念标签和日期等信息
2. **数据分组**: 按日期对数据进行分组处理
3. **映射构建**:
   - 构建股票→概念映射（收集每个股票的所有概念标签）
   - 构建概念→股票映射（反向索引，用于概念查询）
4. **数据保存**: 生成两个CSV文件：
   - `stock_to_concepts.csv`: 股票到概念的映射关系
   - `concept_to_stocks.csv`: 概念到股票的映射关系
5. **统计分析**: 输出处理结果统计，包括总股票数、总概念数和总关联关系数

#### 数据统计
- 总概念数: 644个
- 总股票数: 6148只
- 支持中英文概念标签处理

#### 使用方法

```bash
python process_stock_concepts.py -i 输入Excel文件路径 -o 输出目录 -s 工作表名称
```

**参数说明：**
- `-i, --input`: 输入Excel文件路径（必填）
- `-o, --output_dir`: 输出CSV文件目录（可选，默认为当前目录）
- `-s, --sheet`: Excel工作表名称（可选，默认为'股票维度'）

### 2. 概念股票权重分析工具 (concept_stock_analyzer.py)

#### 功能概述
该脚本用于分析概念股票权重，计算每个概念下各股票出现的频率，并支持按概念查询股票列表、列出可用概念等功能。

#### 核心函数

##### analyze_concept_stocks(csv_file='concept_to_stocks.csv')

```python
def analyze_concept_stocks(csv_file='concept_to_stocks.csv'):
    # 分析概念股票权重，计算每个概念下各股票出现的频率
```

**功能：**
- 读取概念-股票CSV文件
- 计算每个概念下各股票的权重（基于出现频率）
- 按权重排序股票列表
- 执行数据质量检查和异常处理

##### query_concept_stocks(concept_stock_sorted, concept_name, top_n=None)

```python
def query_concept_stocks(concept_stock_sorted, concept_name, top_n=None):
    # 查询指定概念下的股票，按权重排序
```

**功能：**
- 查询指定概念的股票列表
- 支持模糊匹配和自动提示
- 可限制返回数量

##### list_available_concepts(concept_stock_sorted, top_n=50)

```python
def list_available_concepts(concept_stock_sorted, top_n=50):
    # 列出所有可用的概念及其包含的股票数量
```

**功能：**
- 按股票数量排序并显示概念列表
- 支持限制显示数量
- 提供使用示例提示

#### 使用方法

##### 查看可用概念列表
```bash
python concept_stock_analyzer.py -l
```

##### 查询特定概念的股票
```bash
python concept_stock_analyzer.py -c 概念名称 -n 显示数量
```

**参数说明：**
- `-i, --input`: 输入的概念股票CSV文件路径（可选，默认为'concept_to_stocks.csv'）
- `-c, --concept`: 要查询的概念名称（必填，除非使用-l参数）
- `-n, --top`: 返回前N个权重最高的股票（可选，默认为20）
- `-l, --list`: 列出所有可用的概念（可选）
- `--list-top`: 列出概念时显示前N个概念（可选，默认为50）

#### 输出格式

**概念查询输出：**
```
=== 概念名称 概念下的股票（按权重排序）===
共找到 123 只股票，显示前 20 只
排名       股票简称    权重（出现次数）  占比
------------------------------------------------------------
1         股票A       15             12.34%
2         股票B       12             9.87%
...
------------------------------------------------------------
前20只股票权重覆盖率: 65.43%
```

### 5. 知识图谱构建工具 (stock_knowledge_graph.py)

#### 功能概述
该脚本用于构建股票知识图谱，分析股票之间的关联关系，并执行社区发现分析，识别股票网络中的核心节点和社区结构。

#### 输入输出
- **输入**: `stock_to_concepts.csv` 或 `stock_to_concepts.xlsx`
- **输出**: `stock_community_analysis.txt` 分析报告

#### 主要功能
- 构建股票知识图谱
- 计算股票-股票关联权重
- 执行社区发现算法
- 识别核心中枢股票
- 支持概念相关股票查询的核心数据处理

### 4. Web应用 (app.py)

#### 功能概述
基于Flask的Web应用，提供股票搜索、相关股票推荐和概念相关股票查询功能，可视化展示股票关联关系和概念知识图谱。

#### 主要API端点
- `/api/search_stocks`: 股票模糊搜索
- `/api/related_stocks`: 相关股票推荐
- `/api/concept_stocks`: 概念相关股票查询（新增）

## 整体工作流程

1. **数据预处理**
   ```bash
   python process_stock_concepts.py -i 原始Excel文件.xlsx
   ```
   - 生成 `stock_to_concepts.csv` 和 `concept_to_stocks.csv`

2. **概念股票分析**
   ```bash
   python concept_stock_analyzer.py -l  # 查看概念列表
   python concept_stock_analyzer.py -c 锂电池  # 查询特定概念
   ```
   - 获取各概念下的股票权重分析

3. **知识图谱构建**（可选）
   ```bash
   python stock_knowledge_graph.py
   ```
   - 生成社区分析报告

4. **启动Web应用**
   ```bash
   python app.py
   ```
   - 访问 http://localhost:8080 使用Web界面

## 数据文件说明

### 1. 输入文件
- **原始Excel文件**: 包含股票基本信息、概念标签等数据
  - 关键字段: 日期、股票简称、股票代码、板块概念、概念标签

### 2. 中间文件
- **stock_to_concepts.csv**: 股票到概念的映射关系
  - 字段: 日期、股票简称、概念

- **concept_to_stocks.csv**: 概念到股票的映射关系
  - 字段: 日期、概念、股票简称

### 3. 输出文件
- **stock_community_analysis.txt**: 股票社区分析报告
  - 包含社区发现结果、核心中枢节点分析

## 技术特点

1. **模块化设计**: 各功能模块独立，便于维护和扩展
2. **完善的错误处理**: 包含文件检查、数据验证、异常捕获等机制
3. **数据质量控制**: 支持缺失值检测、数据清洗和有效性验证
4. **灵活的参数配置**: 所有工具支持命令行参数，便于自动化和批量处理
5. **丰富的统计信息**: 提供详细的处理过程日志和结果统计

## Web功能详解

### 股票搜索
- 支持模糊匹配股票名称
- 实时搜索建议和自动补全
- 限制返回数量优化性能

### 相关股票展示
- 按关联度排序展示
- 显示关联次数和日期
- 支持创业板过滤功能

### 概念相关股票查询（新增）
- 点击概念标签弹出模态框显示相关股票
- 展示知识图谱统计信息（节点数、边数）
- 按中心性排序展示股票列表
- 支持动态调整显示股票数量
- 提供完善的加载状态和错误处理

### 用户体验优化
- 响应式模态框设计
- 平滑过渡动画效果
- 悬停交互反馈
- 无障碍访问支持
- 模态框关闭后焦点正确管理
- 蒙层自动清理机制

## 扩展建议

1. **数据更新机制**: 添加定时更新数据的功能
2. **可视化增强**: 引入更丰富的图表展示关联关系和概念分布
3. **多维度分析**: 支持按板块、行业、地域等多维度分析
4. **历史趋势分析**: 分析概念热度和股票关联的时间变化趋势
5. **高级搜索功能**: 支持组合条件搜索（多概念、时间范围等）
6. **知识图谱可视化**: 直接在前端展示股票关系网络图谱
7. **概念聚类分析**: 自动发现相关概念群组