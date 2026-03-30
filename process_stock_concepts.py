#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票概念映射数据处理脚本

该脚本用于处理股票数据，构建股票到概念的映射和概念到股票的反向映射，
并将处理后的数据保存到CSV文件中以供后续使用。
"""

import pandas as pd
from collections import defaultdict
import argparse
import os


class StockConceptProcessor:
    """
    股票概念映射处理器
    用于处理股票数据，构建股票到概念的映射和概念到股票的反向映射
    """
    
    def __init__(self, file_path, sheet_name='股票维度', output_dir=None):
        """
        初始化股票概念映射处理器
        
        参数：
        file_path: Excel文件路径
        sheet_name: 工作表名称，默认为'股票维度'
        output_dir: 输出目录路径，默认为None（使用当前目录）
        """
        self.file_path = file_path
        self.sheet_name = sheet_name
        self.output_dir = output_dir
        self.df = None
        # 存储所有日期的股票-概念映射
        self.all_dates_stock_to_concepts = {}
        # 存储所有日期的概念-股票映射
        self.all_dates_concept_to_stocks = {}
        
        # 初始化时读取数据
        self.read_data()
    
    def read_data(self):
        """
        读取Excel文件中的股票数据
        """
        try:
            print(f"开始处理数据文件: {self.file_path}")
            self.df = pd.read_excel(self.file_path, sheet_name=self.sheet_name)
            print(f"成功读取数据，共 {len(self.df)} 条记录")
            print(f"数据形状: {self.df.shape}")
            print(f"列名: {self.df.columns.tolist()}")
        except FileNotFoundError:
            raise Exception(f"文件未找到 - {self.file_path}")
        except ValueError as e:
            if "No sheet named" in str(e):
                raise Exception(f"未找到名为【{self.sheet_name}】的工作表")
            else:
                raise Exception(f"读取Excel文件时发生值错误 - {e}")
        except Exception as e:
            raise Exception(f"读取文件时发生未知错误 - {e}")
    
    def process(self):
        """
        处理股票概念映射数据
        """
        # 验证必要的列是否存在
        required_columns = ['股票简称', '板块概念', '概念标签', '日期']
        missing_columns = [col for col in required_columns if col not in self.df.columns]
        if missing_columns:
            print(f"错误：缺少必要的列: {missing_columns}")
            # 为了测试，我们可以继续处理，即使列名不匹配
            print("警告：列名不匹配，尝试使用实际列名进行处理...")
            print(f"实际列名: {self.df.columns.tolist()}")
            return
        
        # 1. 构建股票到概念的映射（按日期分组处理）
        print("开始构建股票到概念的映射...")
        
        # 按日期分组处理数据
        date_groups = self.df.groupby('日期')
        print(f"数据按日期分为 {len(date_groups)} 组")
        
        for date, date_data in date_groups:
            print(f"处理日期: {date}")
            
            # 构建股票到所有概念的映射
            stock_to_all_concepts = {}
            
            for _, row in date_data.iterrows():
                # 收集所有概念（板块概念 + 概念标签）
                all_concepts = []
                
                # 处理板块概念（单个概念）
                if pd.notna(row['板块概念']) and row['板块概念'].strip():
                    all_concepts.append(row['板块概念'].strip())
                
                # 处理概念标签（多个概念，顿号分隔）
                if pd.notna(row['概念标签']) and row['概念标签'].strip():
                    concept_tags = [c.strip() for c in row['概念标签'].split('、') if c.strip()]
                    all_concepts.extend(concept_tags)
                
                # 去重并存储
                stock_to_all_concepts[row['股票简称']] = list(set(all_concepts))
            
            # 保存当前日期的股票-概念映射
            self.all_dates_stock_to_concepts[date] = stock_to_all_concepts
            
            # 构建概念到股票的映射
            concept_to_stocks = defaultdict(list)
            for stock, concepts in stock_to_all_concepts.items():
                for concept in concepts:
                    concept_to_stocks[concept].append(stock)
            
            # 保存当前日期的概念-股票映射
            self.all_dates_concept_to_stocks[date] = concept_to_stocks
            
            print(f"  日期 {date} 共处理 {len(stock_to_all_concepts)} 只股票, {len(concept_to_stocks)} 个概念")
        
        print("股票到概念的映射和概念到股票的反向映射构建完成")
        
        # 2. 保存处理后的数据到CSV文件
        self.save_to_csv()
        
    def save_to_csv(self):
        """
        将处理后的数据保存到CSV文件
        """
        if not self.output_dir:
            self.output_dir = os.getcwd()
        
        print("开始保存处理后的数据到CSV文件...")
        
        # 保存股票到概念的映射
        stock_concept_data = []
        for date, stock_to_concepts in self.all_dates_stock_to_concepts.items():
            for stock, concepts in stock_to_concepts.items():
                for concept in concepts:
                    stock_concept_data.append({
                        '日期': date,
                        '股票简称': stock,
                        '概念': concept
                    })
        
        # 创建股票-概念数据框并保存
        stock_concept_df = pd.DataFrame(stock_concept_data)
        stock_concept_file = os.path.join(self.output_dir, 'stock_to_concepts.csv')
        stock_concept_df.to_csv(stock_concept_file, index=False, encoding='utf-8-sig')
        print(f"股票到概念的映射已保存到: {stock_concept_file}")
        
        # 保存概念到股票的映射
        concept_stock_data = []
        for date, concept_to_stocks in self.all_dates_concept_to_stocks.items():
            for concept, stocks in concept_to_stocks.items():
                for stock in stocks:
                    concept_stock_data.append({
                        '日期': date,
                        '概念': concept,
                        '股票简称': stock
                    })
        
        # 创建概念-股票数据框并保存
        concept_stock_df = pd.DataFrame(concept_stock_data)
        concept_stock_file = os.path.join(self.output_dir, 'concept_to_stocks.csv')
        concept_stock_df.to_csv(concept_stock_file, index=False, encoding='utf-8-sig')
        print(f"概念到股票的映射已保存到: {concept_stock_file}")
        
        # 统计信息
        total_stocks = len(set(stock_concept_df['股票简称']))
        total_concepts = len(set(stock_concept_df['概念']))
        total_relations = len(stock_concept_df)
        
        print(f"数据处理完成！")
        print(f"统计信息:")
        print(f"- 总股票数: {total_stocks}")
        print(f"- 总概念数: {total_concepts}")
        print(f"- 总关联关系数: {total_relations}")
        print(f"- 涉及日期数: {len(self.all_dates_stock_to_concepts)}")


def main():
    """
    主函数，处理命令行参数
    """
    parser = argparse.ArgumentParser(description='股票概念映射数据处理工具')
    parser.add_argument('-i', '--input', required=True, help='输入Excel文件路径')
    parser.add_argument('-o', '--output_dir', default=None, help='输出CSV文件目录')
    parser.add_argument('-s', '--sheet', default='股票维度', help='Excel工作表名称')
    args = parser.parse_args()
    
    try:
        # 创建处理器实例
        processor = StockConceptProcessor(
            file_path=args.input,
            sheet_name=args.sheet,
            output_dir=args.output_dir
        )
        
        # 处理数据
        processor.process()
        
    except Exception as e:
        print(f"错误: {e}")
        import sys
        sys.exit(1)

if __name__ == "__main__":
    main()