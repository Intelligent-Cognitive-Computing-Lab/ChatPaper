#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VLA研究结果分析工具
"""
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter
import numpy as np
import re

class VLAAnalyzer:
    def __init__(self, csv_file_path: str):
        self.df = pd.read_csv(csv_file_path)
        plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS']
        plt.rcParams['axes.unicode_minus'] = False
        
    def analyze_resource_bottlenecks(self):
        """分析资源瓶颈分布"""
        print("=== 资源瓶颈分析 ===")
        
        # 数据瓶颈vs算力瓶颈分布
        bottleneck_combo = self.df.groupby(['数据瓶颈', '算力瓶颈']).size()
        print("数据瓶颈 vs 算力瓶颈分布:")
        print(bottleneck_combo)
        
        # VLA架构类型与资源瓶颈关系
        vla_bottleneck = pd.crosstab(self.df['VLA架构类型'], 
                                   [self.df['数据瓶颈'], self.df['算力瓶颈']])
        print("\nVLA架构类型与资源瓶颈关系:")
        print(vla_bottleneck)
    
    def analyze_solutions(self):
        """分析解决方案分布"""
        print("\n=== 解决方案分析 ===")
        
        # 数据瓶颈解决策略
        data_solutions = []
        for solution in self.df['数据瓶颈解决策略'].dropna():
            if solution != '未提及':
                data_solutions.extend([s.strip() for s in solution.split('/')])
        
        print("数据瓶颈解决策略TOP10:")
        data_counter = Counter(data_solutions)
        for solution, count in data_counter.most_common(10):
            print(f"  {solution}: {count}")
        
        # 算力瓶颈解决策略
        compute_solutions = []
        for solution in self.df['算力瓶颈解决策略'].dropna():
            if solution != '未提及':
                compute_solutions.extend([s.strip() for s in solution.split('/')])
        
        print("\n算力瓶颈解决策略TOP10:")
        compute_counter = Counter(compute_solutions)
        for solution, count in compute_counter.most_common(10):
            print(f"  {solution}: {count}")
    
    def analyze_model_scales(self):
        """分析模型规模分布"""
        print("\n=== 模型规模分析 ===")
        
        # 提取参数量
        param_counts = []
        for scale in self.df['模型规模']:
            if isinstance(scale, str) and '参数' in scale:
                # 提取数字部分
                match = re.search(r'(\d+[\.\d]*)\s*([KMB])?\s*参数', scale)
                if match:
                    num = float(match.group(1))
                    unit = match.group(2) if match.group(2) else ''
                    
                    if unit == 'K':
                        param_counts.append(num / 1000)  # 转换为B
                    elif unit == 'M':
                        param_counts.append(num / 1000)  # 转换为B
                    elif unit == 'B':
                        param_counts.append(num)
                    else:
                        param_counts.append(num / 1e9)  # 假设为原始参数数
        
        if param_counts:
            print(f"模型参数量统计(B参数):")
            print(f"  平均: {np.mean(param_counts):.2f}B")
            print(f"  中位数: {np.median(param_counts):.2f}B")
            print(f"  最小: {np.min(param_counts):.2f}B")
            print(f"  最大: {np.max(param_counts):.2f}B")
    
    def analyze_temporal_trends(self):
        """分析时间趋势"""
        print("\n=== 时间趋势分析 ===")
        
        # 按年份统计
        year_counts = self.df['发表年份'].value_counts().sort_index()
        print("论文发表年份分布:")
        for year, count in year_counts.items():
            print(f"  {year}: {count}篇")
        
        # 按年份和VLA类型统计
        year_vla = pd.crosstab(self.df['发表年份'], self.df['VLA架构类型'])
        print("\n年份-VLA架构类型分布:")
        print(year_vla)
    
    def analyze_data_quality(self):
        """分析数据质量"""
        print("\n=== 数据质量分析 ===")
        
        total_papers = len(self.df)
        
        # 基础信息完整性
        basic_info_completeness = {
            '标题': (self.df['论文标题'].notna() & (self.df['论文标题'] != '')).sum() / total_papers,
            '作者': (self.df['作者'] != '未提及').sum() / total_papers,
            '年份': (self.df['发表年份'] != '未提及').sum() / total_papers,
        }
        
        print("基础信息完整性:")
        for field, rate in basic_info_completeness.items():
            print(f"  {field}: {rate:.1%}")
        
        # 技术信息完整性
        tech_info_completeness = {
            '模型规模': (self.df['模型规模'] != '未提及').sum() / total_papers,
            '训练资源': (self.df['训练资源需求'] != '未提及').sum() / total_papers,
            '推理效率': (self.df['推理效率'] != '未提及').sum() / total_papers,
            '性能指标': (self.df['性能指标'] != '未提及').sum() / total_papers,
        }
        
        print("\n技术信息完整性:")
        for field, rate in tech_info_completeness.items():
            status = "✅" if rate > 0.7 else "⚠️" if rate > 0.4 else "❌"
            print(f"  {field}: {rate:.1%} {status}")

    def analyze_author_distribution(self):
        """分析作者分布"""
        print("\n=== 作者分布分析 ===")
        
        # 提取第一作者
        first_authors = []
        for author in self.df['作者']:
            if author != '未提及':
                # 提取第一作者姓名
                first_author = author.split(' et al.')[0].split(',')[0].strip()
                if first_author and len(first_author) > 1:
                    first_authors.append(first_author)
        
        if first_authors:
            author_counts = Counter(first_authors)
            print(f"总作者数: {len(author_counts)}")
            print(f"多篇论文作者数: {sum(1 for count in author_counts.values() if count > 1)}")
            
            # 显示高产作者
            top_authors = author_counts.most_common(5)
            print("\n高产作者TOP5:")
            for author, count in top_authors:
                if count > 1:
                    print(f"  {author}: {count}篇")

    def analyze_venue_distribution(self):
        """分析发表期刊/会议分布"""
        print("\n=== 发表venue分析 ===")
        
        # 从文件名推断venue信息
        venues = []
        for idx, row in self.df.iterrows():
            filename = row['文件名'] if '文件名' in self.df.columns else ''
            
            # 从文件名推断venue
            venue = self._infer_venue_from_filename(filename)
            venues.append(venue)
        
        venue_counts = Counter(venues)
        print("推断的venue分布:")
        for venue, count in venue_counts.most_common(10):
            if venue != '未知':
                print(f"  {venue}: {count}篇")

    def _infer_venue_from_filename(self, filename: str) -> str:
        """从文件名推断venue"""
        filename_lower = filename.lower()
        
        venue_patterns = {
            'arxiv': r'arxiv',
            'ICLR': r'iclr',
            'ICML': r'icml', 
            'NeurIPS': r'neurips|nips',
            'CVPR': r'cvpr',
            'ICCV': r'iccv',
            'ECCV': r'eccv',
            'AAAI': r'aaai',
            'IJCAI': r'ijcai',
            'RSS': r'rss',
            'ICRA': r'icra',
            'IROS': r'iros',
            'CoRL': r'corl',
        }
        
        for venue, pattern in venue_patterns.items():
            if re.search(pattern, filename_lower):
                return venue
        
        return '未知'

    def generate_insights(self):
        """生成研究洞察"""
        print("\n=== 研究洞察 ===")
        
        total_papers = len(self.df)
        data_bottleneck_rate = (self.df['数据瓶颈'] == '是').sum() / total_papers
        compute_bottleneck_rate = (self.df['算力瓶颈'] == '是').sum() / total_papers
        both_bottleneck_rate = ((self.df['数据瓶颈'] == '是') & 
                              (self.df['算力瓶颈'] == '是')).sum() / total_papers
        
        print(f"1. 资源瓶颈普遍性:")
        print(f"   - {data_bottleneck_rate:.1%}的研究面临数据瓶颈")
        print(f"   - {compute_bottleneck_rate:.1%}的研究面临算力瓶颈")
        print(f"   - {both_bottleneck_rate:.1%}的研究同时面临两种瓶颈")
        
        # VLA架构偏好
        vla_dist = self.df['VLA架构类型'].value_counts(normalize=True)
        dominant_type = vla_dist.index[0]
        print(f"\n2. VLA架构偏好:")
        print(f"   - {dominant_type}是最主流的架构({vla_dist.iloc[0]:.1%})")
        
        # 缺失数据分析
        missing_rates = {
            '训练资源需求': (self.df['训练资源需求'] == '未提及').sum() / total_papers,
            '推理效率': (self.df['推理效率'] == '未提及').sum() / total_papers,
            '作者': (self.df['作者'] == '未提及').sum() / total_papers
        }
        
        print(f"\n3. 数据完整性问题:")
        for field, rate in missing_rates.items():
            if rate > 0.3:  # 超过30%缺失
                print(f"   - {field}缺失率过高({rate:.1%})")

def main():
    csv_file = "/Users/sunyukun/Projects/ChatPaper/export/2025-07-29-10-merged_papers.csv"
    
    analyzer = VLAAnalyzer(csv_file)
    
    analyzer.analyze_resource_bottlenecks()
    analyzer.analyze_solutions()
    analyzer.analyze_model_scales()
    analyzer.analyze_temporal_trends()
    analyzer.analyze_data_quality()
    analyzer.analyze_author_distribution()
    analyzer.analyze_venue_distribution()
    analyzer.generate_insights()

if __name__ == "__main__":
    main()
