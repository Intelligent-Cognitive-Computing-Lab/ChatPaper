#!/usr/bin/env python3
"""
VLA综述分析工具 - Survey Analysis Tool
针对VLA论文数据进行系统性分类分析和综述总结

功能:
1. 数据统计分析 - 论文分布、趋势分析
2. 架构类型分析 - VLA架构分类统计
3. 资源瓶颈分析 - 数据瓶颈和算力瓶颈分布
4. 技术创新总结 - 创新点和解决方案归纳
5. 性能对比分析 - 不同方法的性能权衡
6. 综述报告生成 - 自动生成分析报告
"""

import pandas as pd
import numpy as np
from collections import Counter, defaultdict
import re
from datetime import datetime
import json
import argparse
import os

class VLASurveyAnalyzer:
    def __init__(self, csv_path):
        """初始化分析器"""
        self.csv_path = csv_path
        self.df = pd.DataFrame()  # 初始化为空DataFrame
        self.load_data()
        
    def load_data(self):
        """加载CSV数据"""
        try:
            self.df = pd.read_csv(self.csv_path, encoding='utf-8')
            print(f"✅ 成功加载 {len(self.df)} 篇论文数据")
            print(f"📊 数据字段: {list(self.df.columns)}")
        except Exception as e:
            print(f"❌ 数据加载失败: {e}")
            return False
        return True
    
    def basic_statistics(self):
        """基础统计分析"""
        print("\n" + "="*60)
        print("📊 VLA论文基础统计分析")
        print("="*60)
        
        # 总体统计
        total_papers = len(self.df)
        print(f"📚 论文总数: {total_papers}")
        
        # 年份分布
        years = self.df['发表年份'].value_counts().sort_index()
        print(f"\n📅 年份分布:")
        for year, count in years.items():
            print(f"  {year}: {count}篇")
        
        # 期刊会议分布(排除空值)
        venues = self.df['期刊会议'].dropna()
        venue_counts = venues.value_counts().head(10)
        print(f"\n🏛️ 主要发表平台 (Top 10):")
        for venue, count in venue_counts.items():
            if venue and venue != "未提及":
                print(f"  {venue}: {count}篇")
        
        # VLA架构类型分布
        arch_types = self.df['VLA架构类型'].value_counts()
        print(f"\n🏗️ VLA架构类型分布:")
        for arch, count in arch_types.items():
            percentage = (count/total_papers)*100
            print(f"  {arch}: {count}篇 ({percentage:.1f}%)")
        
        return {
            'total_papers': total_papers,
            'year_distribution': years.to_dict(),
            'venue_distribution': venue_counts.to_dict(),
            'architecture_distribution': arch_types.to_dict()
        }
    
    def resource_bottleneck_analysis(self):
        """资源瓶颈分析"""
        print("\n" + "="*60)
        print("🔍 资源瓶颈深度分析")
        print("="*60)
        
        # 数据瓶颈vs算力瓶颈分布
        data_bottleneck = self.df['数据瓶颈'].value_counts()
        compute_bottleneck = self.df['算力瓶颈'].value_counts()
        
        print("📊 资源瓶颈分布:")
        print(f"  数据瓶颈: {data_bottleneck.to_dict()}")
        print(f"  算力瓶颈: {compute_bottleneck.to_dict()}")
        
        # 双重瓶颈分析
        both_bottlenecks = self.df[
            (self.df['数据瓶颈'] == '是') & (self.df['算力瓶颈'] == '是')
        ]
        data_only = self.df[
            (self.df['数据瓶颈'] == '是') & (self.df['算力瓶颈'] == '否')
        ]
        compute_only = self.df[
            (self.df['数据瓶颈'] == '否') & (self.df['算力瓶颈'] == '是')
        ]
        no_bottleneck = self.df[
            (self.df['数据瓶颈'] == '否') & (self.df['算力瓶颈'] == '否')
        ]
        
        print(f"\n🔗 瓶颈组合分析:")
        print(f"  双重瓶颈 (数据+算力): {len(both_bottlenecks)}篇 ({len(both_bottlenecks)/len(self.df)*100:.1f}%)")
        print(f"  仅数据瓶颈: {len(data_only)}篇 ({len(data_only)/len(self.df)*100:.1f}%)")
        print(f"  仅算力瓶颈: {len(compute_only)}篇 ({len(compute_only)/len(self.df)*100:.1f}%)")
        print(f"  无明显瓶颈: {len(no_bottleneck)}篇 ({len(no_bottleneck)/len(self.df)*100:.1f}%)")
        
        # 资源约束类型分析
        constraint_types = self.df['资源约束类型'].value_counts()
        print(f"\n⚡ 资源约束类型分布:")
        for constraint, count in constraint_types.items():
            if constraint and constraint != "未提及":
                print(f"  {constraint}: {count}篇")
        
        # 架构类型与资源瓶颈的关联分析
        print(f"\n🏗️ 架构类型与资源瓶颈关联:")
        arch_bottleneck = pd.crosstab(
            self.df['VLA架构类型'], 
            [self.df['数据瓶颈'], self.df['算力瓶颈']], 
            margins=True
        )
        print(arch_bottleneck)
        
        return {
            'data_bottleneck_dist': data_bottleneck.to_dict(),
            'compute_bottleneck_dist': compute_bottleneck.to_dict(),
            'bottleneck_combinations': {
                'both': len(both_bottlenecks),
                'data_only': len(data_only),
                'compute_only': len(compute_only),
                'none': len(no_bottleneck)
            },
            'constraint_types': constraint_types.to_dict()
        }
    
    def solution_strategy_analysis(self):
        """解决策略分析"""
        print("\n" + "="*60)
        print("💡 解决策略与创新点分析")
        print("="*60)
        
        # 数据瓶颈解决策略
        data_strategies = self.df['数据瓶颈解决策略'].dropna()
        data_strategy_keywords = []
        for strategy in data_strategies:
            if strategy and strategy != "未提及":
                # 提取关键词
                keywords = re.findall(r'[\u4e00-\u9fff]+', str(strategy))
                data_strategy_keywords.extend(keywords)
        
        data_strategy_counter = Counter(data_strategy_keywords)
        common_data_strategies = data_strategy_counter.most_common(15)
        
        print("📈 数据瓶颈解决策略关键词 (Top 15):")
        for keyword, count in common_data_strategies:
            if len(keyword) > 1:  # 过滤单字
                print(f"  {keyword}: {count}次")
        
        # 算力瓶颈解决策略
        compute_strategies = self.df['算力瓶颈解决策略'].dropna()
        compute_strategy_keywords = []
        for strategy in compute_strategies:
            if strategy and strategy != "未提及":
                keywords = re.findall(r'[\u4e00-\u9fff]+', str(strategy))
                compute_strategy_keywords.extend(keywords)
        
        compute_strategy_counter = Counter(compute_strategy_keywords)
        common_compute_strategies = compute_strategy_counter.most_common(15)
        
        print(f"\n⚡ 算力瓶颈解决策略关键词 (Top 15):")
        for keyword, count in common_compute_strategies:
            if len(keyword) > 1:
                print(f"  {keyword}: {count}次")
        
        # 创新点分析
        innovations = self.df['创新点'].dropna()
        innovation_keywords = []
        for innovation in innovations:
            if innovation and innovation != "未提及":
                keywords = re.findall(r'[\u4e00-\u9fff]+', str(innovation))
                innovation_keywords.extend(keywords)
        
        innovation_counter = Counter(innovation_keywords)
        common_innovations = innovation_counter.most_common(20)
        
        print(f"\n🚀 技术创新关键词 (Top 20):")
        for keyword, count in common_innovations:
            if len(keyword) > 1:
                print(f"  {keyword}: {count}次")
        
        return {
            'data_strategies': common_data_strategies,
            'compute_strategies': common_compute_strategies,
            'innovations': common_innovations
        }
    
    def performance_analysis(self):
        """性能分析"""
        print("\n" + "="*60)
        print("📈 性能指标与权衡分析")
        print("="*60)
        
        # 提取成功率数据
        success_rates = []
        performance_data = self.df['性能指标'].dropna()
        
        for perf in performance_data:
            if perf and perf != "未提及":
                # 使用正则表达式提取成功率
                rates = re.findall(r'(\d+(?:\.\d+)?)%', str(perf))
                for rate in rates:
                    try:
                        success_rates.append(float(rate))
                    except:
                        continue
        
        if success_rates:
            print(f"🎯 成功率统计 (基于{len(success_rates)}个数据点):")
            print(f"  平均成功率: {np.mean(success_rates):.1f}%")
            print(f"  中位数: {np.median(success_rates):.1f}%")
            print(f"  最高成功率: {np.max(success_rates):.1f}%")
            print(f"  最低成功率: {np.min(success_rates):.1f}%")
            print(f"  标准差: {np.std(success_rates):.1f}%")
        
        # 模型规模分析
        model_sizes = []
        size_data = self.df['模型规模'].dropna()
        
        for size in size_data:
            if size and size != "未提及":
                # 提取参数量
                params = re.findall(r'(\d+(?:\.\d+)?)([BMK])', str(size))
                for param, unit in params:
                    try:
                        value = float(param)
                        if unit == 'B':
                            model_sizes.append(value)
                        elif unit == 'M':
                            model_sizes.append(value / 1000)
                        elif unit == 'K':
                            model_sizes.append(value / 1000000)
                    except:
                        continue
        
        if model_sizes:
            print(f"\n🧠 模型规模统计 (基于{len(model_sizes)}个数据点, 单位:B参数):")
            print(f"  平均规模: {np.mean(model_sizes):.2f}B")
            print(f"  中位数: {np.median(model_sizes):.2f}B")
            print(f"  最大规模: {np.max(model_sizes):.1f}B")
            print(f"  最小规模: {np.min(model_sizes):.3f}B")
        
        # 资源-性能权衡分析
        tradeoffs = self.df['资源-性能权衡'].dropna()
        tradeoff_keywords = []
        for tradeoff in tradeoffs:
            if tradeoff and tradeoff != "未提及":
                keywords = re.findall(r'[\u4e00-\u9fff]+', str(tradeoff))
                tradeoff_keywords.extend(keywords)
        
        tradeoff_counter = Counter(tradeoff_keywords)
        common_tradeoffs = tradeoff_counter.most_common(10)
        
        print(f"\n⚖️ 资源-性能权衡关键词 (Top 10):")
        for keyword, count in common_tradeoffs:
            if len(keyword) > 1:
                print(f"  {keyword}: {count}次")
        
        return {
            'success_rates': {
                'mean': np.mean(success_rates) if success_rates else 0,
                'median': np.median(success_rates) if success_rates else 0,
                'max': np.max(success_rates) if success_rates else 0,
                'min': np.min(success_rates) if success_rates else 0,
                'std': np.std(success_rates) if success_rates else 0
            },
            'model_sizes': {
                'mean': np.mean(model_sizes) if model_sizes else 0,
                'median': np.median(model_sizes) if model_sizes else 0,
                'max': np.max(model_sizes) if model_sizes else 0,
                'min': np.min(model_sizes) if model_sizes else 0
            },
            'tradeoffs': common_tradeoffs
        }
    
    def task_application_analysis(self):
        """任务应用分析"""
        print("\n" + "="*60)
        print("🎯 任务类型与应用场景分析")
        print("="*60)
        
        # 任务类型统计
        task_types = self.df['任务类型'].dropna()
        task_keywords = []
        for task in task_types:
            if task and task != "未提及":
                keywords = re.findall(r'[\u4e00-\u9fff]+', str(task))
                task_keywords.extend(keywords)
        
        task_counter = Counter(task_keywords)
        common_tasks = task_counter.most_common(15)
        
        print("🎯 任务类型关键词 (Top 15):")
        for keyword, count in common_tasks:
            if len(keyword) > 1:
                print(f"  {keyword}: {count}次")
        
        # 实验环境分析
        environments = self.df['实验环境'].dropna()
        env_keywords = []
        for env in environments:
            if env and env != "未提及":
                keywords = re.findall(r'[\u4e00-\u9fff]+', str(env))
                env_keywords.extend(keywords)
        
        env_counter = Counter(env_keywords)
        common_envs = env_counter.most_common(10)
        
        print(f"\n🌍 实验环境关键词 (Top 10):")
        for keyword, count in common_envs:
            if len(keyword) > 1:
                print(f"  {keyword}: {count}次")
        
        # 数据类型分析
        data_types = self.df['数据类型'].dropna()
        datatype_keywords = []
        for dtype in data_types:
            if dtype and dtype != "未提及":
                keywords = re.findall(r'[\u4e00-\u9fff]+', str(dtype))
                datatype_keywords.extend(keywords)
        
        datatype_counter = Counter(datatype_keywords)
        common_datatypes = datatype_counter.most_common(12)
        
        print(f"\n📊 数据类型关键词 (Top 12):")
        for keyword, count in common_datatypes:
            if len(keyword) > 1:
                print(f"  {keyword}: {count}次")
        
        return {
            'tasks': common_tasks,
            'environments': common_envs,
            'data_types': common_datatypes
        }
    
    def generate_survey_report(self, output_path="vla_survey_report.md"):
        """生成综述报告"""
        print(f"\n📝 正在生成综述报告...")
        
        # 收集所有分析结果
        basic_stats = self.basic_statistics()
        resource_analysis = self.resource_bottleneck_analysis()
        solution_analysis = self.solution_strategy_analysis()
        performance_analysis_result = self.performance_analysis()
        task_analysis = self.task_application_analysis()
        
        # 生成报告
        report = f"""# Vision-Language-Action (VLA) 模型资源受限研究综述报告

**生成时间**: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}  
**数据源**: {self.csv_path}  
**分析论文数量**: {basic_stats['total_papers']}篇

## 📊 1. 研究现状概览

### 1.1 时间趋势
- **主要发表年份**: {max(basic_stats['year_distribution'], key=basic_stats['year_distribution'].get)}年 ({basic_stats['year_distribution'][max(basic_stats['year_distribution'], key=basic_stats['year_distribution'].get)]}篇)
- **年度分布**: {dict(sorted(basic_stats['year_distribution'].items()))}

### 1.2 架构分布
"""
        
        # 架构分布
        for arch, count in basic_stats['architecture_distribution'].items():
            percentage = (count/basic_stats['total_papers'])*100
            report += f"- **{arch}**: {count}篇 ({percentage:.1f}%)\n"
        
        report += f"""
## 🔍 2. 资源瓶颈深度分析

### 2.1 瓶颈分布概况
- **存在数据瓶颈**: {resource_analysis['data_bottleneck_dist'].get('是', 0)}篇
- **存在算力瓶颈**: {resource_analysis['compute_bottleneck_dist'].get('是', 0)}篇

### 2.2 瓶颈组合分析
- **双重瓶颈(数据+算力)**: {resource_analysis['bottleneck_combinations']['both']}篇 ({resource_analysis['bottleneck_combinations']['both']/basic_stats['total_papers']*100:.1f}%)
- **仅数据瓶颈**: {resource_analysis['bottleneck_combinations']['data_only']}篇 ({resource_analysis['bottleneck_combinations']['data_only']/basic_stats['total_papers']*100:.1f}%)
- **仅算力瓶颈**: {resource_analysis['bottleneck_combinations']['compute_only']}篇 ({resource_analysis['bottleneck_combinations']['compute_only']/basic_stats['total_papers']*100:.1f}%)
- **无明显瓶颈**: {resource_analysis['bottleneck_combinations']['none']}篇 ({resource_analysis['bottleneck_combinations']['none']/basic_stats['total_papers']*100:.1f}%)

### 2.3 主要约束类型
"""
        
        # 约束类型
        for constraint, count in list(resource_analysis['constraint_types'].items())[:10]:
            if constraint and constraint != "未提及":
                report += f"- **{constraint}**: {count}篇\n"
        
        report += f"""
## 💡 3. 解决策略与技术创新

### 3.1 数据瓶颈解决策略 (Top 10)
"""
        
        # 数据策略
        for keyword, count in solution_analysis['data_strategies'][:10]:
            if len(keyword) > 1:
                report += f"- **{keyword}**: {count}次提及\n"
        
        report += f"""
### 3.2 算力瓶颈解决策略 (Top 10)
"""
        
        # 算力策略
        for keyword, count in solution_analysis['compute_strategies'][:10]:
            if len(keyword) > 1:
                report += f"- **{keyword}**: {count}次提及\n"
        
        report += f"""
### 3.3 主要技术创新 (Top 15)
"""
        
        # 创新点
        for keyword, count in solution_analysis['innovations'][:15]:
            if len(keyword) > 1:
                report += f"- **{keyword}**: {count}次提及\n"
        
        report += f"""
## 📈 4. 性能分析

### 4.1 成功率统计
- **平均成功率**: {performance_analysis_result['success_rates']['mean']:.1f}%
- **中位数成功率**: {performance_analysis_result['success_rates']['median']:.1f}%
- **最高成功率**: {performance_analysis_result['success_rates']['max']:.1f}%
- **成功率标准差**: {performance_analysis_result['success_rates']['std']:.1f}%

### 4.2 模型规模分析
- **平均模型规模**: {performance_analysis_result['model_sizes']['mean']:.2f}B参数
- **中位数模型规模**: {performance_analysis_result['model_sizes']['median']:.2f}B参数
- **最大模型规模**: {performance_analysis_result['model_sizes']['max']:.1f}B参数

### 4.3 资源-性能权衡策略 (Top 8)
"""
        
        # 权衡策略
        for keyword, count in performance_analysis_result['tradeoffs'][:8]:
            if len(keyword) > 1:
                report += f"- **{keyword}**: {count}次提及\n"
        
        report += f"""
## 🎯 5. 应用场景分析

### 5.1 主要任务类型 (Top 12)
"""
        
        # 任务类型
        for keyword, count in task_analysis['tasks'][:12]:
            if len(keyword) > 1:
                report += f"- **{keyword}**: {count}次\n"
        
        report += f"""
### 5.2 实验环境分布 (Top 8)
"""
        
        # 实验环境
        for keyword, count in task_analysis['environments'][:8]:
            if len(keyword) > 1:
                report += f"- **{keyword}**: {count}次\n"
        
        report += f"""
### 5.3 数据模态类型 (Top 10)
"""
        
        # 数据类型
        for keyword, count in task_analysis['data_types'][:10]:
            if len(keyword) > 1:
                report += f"- **{keyword}**: {count}次\n"
        
        report += f"""
## 🔮 6. 研究趋势与发展方向

### 6.1 主要发现
1. **架构演进**: {max(basic_stats['architecture_distribution'], key=basic_stats['architecture_distribution'].get)}是当前主流架构({basic_stats['architecture_distribution'][max(basic_stats['architecture_distribution'], key=basic_stats['architecture_distribution'].get)]}篇)
2. **瓶颈现状**: {resource_analysis['bottleneck_combinations']['both']}篇论文面临数据和算力双重瓶颈
3. **解决趋势**: 多模态融合、模型压缩、数据增强成为主要解决方向
4. **性能水平**: 平均成功率达到{performance_analysis_result['success_rates']['mean']:.1f}%，但方差较大({performance_analysis_result['success_rates']['std']:.1f}%)

### 6.2 技术挑战
1. **数据稀缺**: 高质量机器人演示数据获取困难
2. **计算密集**: 大模型训练和推理需要大量计算资源  
3. **泛化能力**: 从仿真到现实的迁移仍存在gap
4. **实时性**: 复杂任务的推理延迟问题

### 6.3 未来方向
1. **数据效率**: 少样本学习、数据合成、迁移学习
2. **计算效率**: 模型压缩、知识蒸馏、轻量化架构
3. **多模态融合**: 视觉-语言-触觉-本体感知整合
4. **长时程推理**: 分层规划、记忆机制、持续学习

## 📋 7. 数据说明

- **数据源**: {os.path.basename(self.csv_path)}
- **统计维度**: 25个专业字段
- **分析方法**: 关键词提取、统计分析、趋势归纳
- **更新时间**: {datetime.now().strftime('%Y-%m-%d')}

---
*本报告由VLA综述分析工具自动生成，基于{basic_stats['total_papers']}篇相关论文的系统分析*
"""
        
        # 保存报告
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"✅ 综述报告已生成: {output_path}")
        return report
    
    def generate_classification_summary(self, output_path="vla_classification_summary.json"):
        """生成分类总结JSON"""
        print(f"\n📊 正在生成分类总结...")
        
        # 按架构分类统计
        arch_classification = {}
        for arch in self.df['VLA架构类型'].unique():
            if pd.isna(arch):
                continue
            arch_papers = self.df[self.df['VLA架构类型'] == arch]
            
            arch_classification[arch] = {
                'paper_count': len(arch_papers),
                'data_bottleneck_ratio': len(arch_papers[arch_papers['数据瓶颈'] == '是']) / len(arch_papers),
                'compute_bottleneck_ratio': len(arch_papers[arch_papers['算力瓶颈'] == '是']) / len(arch_papers),
                'avg_success_rate': self._extract_avg_metric(arch_papers['性能指标'], r'(\d+(?:\.\d+)?)%'),
                'common_tasks': self._get_top_keywords(arch_papers['任务类型'], 5),
                'common_innovations': self._get_top_keywords(arch_papers['创新点'], 5),
                'representative_papers': arch_papers['论文标题'].head(3).tolist()
            }
        
        # 按瓶颈类型分类
        bottleneck_classification = {
            'data_bottleneck_only': self._analyze_bottleneck_group(
                self.df[(self.df['数据瓶颈'] == '是') & (self.df['算力瓶颈'] == '否')]
            ),
            'compute_bottleneck_only': self._analyze_bottleneck_group(
                self.df[(self.df['数据瓶颈'] == '否') & (self.df['算力瓶颈'] == '是')]
            ),
            'both_bottlenecks': self._analyze_bottleneck_group(
                self.df[(self.df['数据瓶颈'] == '是') & (self.df['算力瓶颈'] == '是')]
            ),
            'no_bottleneck': self._analyze_bottleneck_group(
                self.df[(self.df['数据瓶颈'] == '否') & (self.df['算力瓶颈'] == '否')]
            )
        }
        
        # 综合分类总结
        classification_summary = {
            'metadata': {
                'total_papers': len(self.df),
                'analysis_date': datetime.now().isoformat(),
                'data_source': self.csv_path
            },
            'architecture_classification': arch_classification,
            'bottleneck_classification': bottleneck_classification,
            'overall_trends': {
                'most_common_architecture': self.df['VLA架构类型'].value_counts().index[0] if len(self.df['VLA架构类型'].value_counts()) > 0 else "未知",
                'bottleneck_distribution': {
                    'data_bottleneck_ratio': len(self.df[self.df['数据瓶颈'] == '是']) / len(self.df),
                    'compute_bottleneck_ratio': len(self.df[self.df['算力瓶颈'] == '是']) / len(self.df)
                },
                'emerging_keywords': self._get_top_keywords(self.df['创新点'], 10)
            }
        }
        
        # 保存JSON
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(classification_summary, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 分类总结已生成: {output_path}")
        return classification_summary
    
    def _analyze_bottleneck_group(self, group_df):
        """分析特定瓶颈组的特征"""
        if len(group_df) == 0:
            return {'paper_count': 0}
            
        return {
            'paper_count': len(group_df),
            'architecture_distribution': group_df['VLA架构类型'].value_counts().to_dict(),
            'common_solutions': self._get_top_keywords(
                pd.concat([group_df['数据瓶颈解决策略'], group_df['算力瓶颈解决策略']]), 5
            ),
            'avg_model_size': self._extract_avg_metric(group_df['模型规模'], r'(\d+(?:\.\d+)?)[BMK]'),
            'representative_papers': group_df['论文标题'].head(3).tolist()
        }
    
    def _get_top_keywords(self, series, top_n=5):
        """从pandas Series中提取热门关键词"""
        keywords = []
        for item in series.dropna():
            if item and item != "未提及":
                extracted = re.findall(r'[\u4e00-\u9fff]+', str(item))
                keywords.extend([kw for kw in extracted if len(kw) > 1])
        
        counter = Counter(keywords)
        return [{'keyword': kw, 'count': count} for kw, count in counter.most_common(top_n)]
    
    def _extract_avg_metric(self, series, pattern):
        """从系列数据中提取数值指标的平均值"""
        values = []
        for item in series.dropna():
            if item and item != "未提及":
                matches = re.findall(pattern, str(item))
                for match in matches:
                    try:
                        values.append(float(match))
                    except:
                        continue
        return np.mean(values) if values else 0
    
    def run_full_analysis(self, report_path="vla_survey_report.md", 
                         classification_path="vla_classification_summary.json"):
        """运行完整分析"""
        print("🚀 开始VLA综述分析...")
        
        # 运行所有分析
        self.basic_statistics()
        self.resource_bottleneck_analysis()
        self.solution_strategy_analysis()
        self.performance_analysis()
        self.task_application_analysis()
        
        # 生成报告
        self.generate_survey_report(report_path)
        self.generate_classification_summary(classification_path)
        
        print(f"\n✅ 分析完成！")
        print(f"📝 综述报告: {report_path}")
        print(f"📊 分类总结: {classification_path}")
    
    def generate_comprehensive_report(self, output_dir="analysis_results"):
        """生成综合分析报告 - 统一接口方法
        
        Args:
            output_dir: 输出目录路径
        
        Returns:
            bool: 是否成功生成报告
        """
        try:
            print(f"\n📊 开始生成综合分析报告...")
            
            # 确保输出目录存在
            os.makedirs(output_dir, exist_ok=True)
            
            # 生成文件路径
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            report_path = os.path.join(output_dir, f"vla_comprehensive_report_{timestamp}.md")
            classification_path = os.path.join(output_dir, f"vla_classification_summary_{timestamp}.json")
            
            print(f"📁 输出目录: {output_dir}")
            print(f"📝 报告文件: {os.path.basename(report_path)}")
            print(f"📋 分类文件: {os.path.basename(classification_path)}")
            
            # 生成主报告
            report_content = self.generate_survey_report(report_path)
            
            # 生成分类摘要
            classification_content = self.generate_classification_summary(classification_path)
            
            print(f"\n✅ 综合分析report生成完成!")
            print(f"   - 主报告: {report_path}")
            print(f"   - 分类摘要: {classification_path}")
            print(f"   - 分析论文数: {len(self.df)}篇")
            
            return True
            
        except Exception as e:
            print(f"❌ 报告生成失败: {e}")
            return False
def main():
    parser = argparse.ArgumentParser(description='VLA综述分析工具')
    parser.add_argument('--csv_path', type=str, required=True, 
                       help='VLA论文CSV数据路径')
    parser.add_argument('--output_dir', type=str, default='./analysis_results',
                       help='输出目录')
    parser.add_argument('--report_name', type=str, default='vla_survey_report.md',
                       help='综述报告文件名')
    parser.add_argument('--classification_name', type=str, default='vla_classification_summary.json',
                       help='分类总结文件名')
    
    args = parser.parse_args()
    
    # 创建输出目录
    os.makedirs(args.output_dir, exist_ok=True)
    
    # 完整路径
    report_path = os.path.join(args.output_dir, args.report_name)
    classification_path = os.path.join(args.output_dir, args.classification_name)
    
    # 运行分析
    analyzer = VLASurveyAnalyzer(args.csv_path)
    analyzer.run_full_analysis(report_path, classification_path)


if __name__ == "__main__":
    main()
