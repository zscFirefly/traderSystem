# 股票网页子项目

这个目录把原来根目录里的网页能力单独收拢成一个可独立运行的小项目。

## 目录结构

- `run.py`: 启动入口
- `Makefile`: 常用开发命令
- `stock_web_app/`: Flask 应用代码
- `stock_web_app/templates/index.html`: 页面模板
- `tests/`: 基础烟测
- `data/`: Excel 数据文件
- `.env.example`: 环境变量示例
- `requirements.txt`: 网页项目依赖

## 启动方式

1. 安装依赖：

   ```bash
   make install
   ```

2. 当前仓库中的 Excel 数据文件已移动到：

   - `data/板块涨停_关系型_全量_org.xlsx`

   如需替换数据，可继续使用该文件名，或通过环境变量 `STOCK_DATA_FILE` 指定其他路径。

3. 启动服务：

   ```bash
   make run
   ```

默认监听 `0.0.0.0:8080`。可通过 `FLASK_DEBUG`、`FLASK_RUN_HOST`、`FLASK_RUN_PORT` 覆盖默认配置。

## 数据源说明

- 股票关联查询使用本地 Excel 数据
- “股票相关性分析”接口使用 `baostock` 分钟线数据
- 首次运行前请确保已安装 `baostock`

## 测试与检查

```bash
make test
make compile
```

也可以直接运行 `python -m stock_web_app`。
