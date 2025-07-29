#!/usr/bin/env python3
"""
VLA智能综述生成器 - AI-Powered Survey Generator
结合大模型和分析结果，逐步生成高质量VLA综述

功能:
1. 基于分析结果的框架生成
2. 智能内容分类和聚类
3. 逐章节综述撰写
4. 技术演进分析
5. 研究趋势预测
6. 完整综述报告生成
"""

import pandas as pd
import numpy as np
import json
import os
import openai
from collections import defaultdict, Counter
import re
from datetime import datetime
import argparse
import configparser
from typing import Dict, List, Any, Optional
import time
import tiktoken

class VLAIntelligentSurveyGenerator:
    def __init__(self, csv_path: str, analysis_results_dir: str, config_path: str = "config/apikey.ini"):
        """初始化智能综述生成器"""
        self.csv_path = csv_path
        self.analysis_results_dir = analysis_results_dir
        self.config_path = config_path
        self.df = pd.DataFrame()
        self.analysis_data = {}
        self.classification_data = {}
        self.client = None
        self.model_name = "gpt-4"
        
        # 加载数据和配置
        self.load_data()
        self.load_analysis_results()
        self.setup_openai()
        
    def load_data(self):
        """加载原始CSV数据"""
        try:
            self.df = pd.read_csv(self.csv_path, encoding='utf-8')
            print(f"✅ 加载原始数据: {len(self.df)} 篇论文")
        except Exception as e:
            print(f"❌ 数据加载失败: {e}")
            
    def load_analysis_results(self):
        """加载分析结果"""
        try:
            # 加载分类总结JSON
            classification_path = os.path.join(self.analysis_results_dir, "vla_classification_summary.json")
            if os.path.exists(classification_path):
                with open(classification_path, 'r', encoding='utf-8') as f:
                    self.classification_data = json.load(f)
                print(f"✅ 加载分类数据: {self.classification_data['metadata']['total_papers']} 篇论文")
            
            # 读取综述报告作为参考
            report_path = os.path.join(self.analysis_results_dir, "vla_survey_report.md")
            if os.path.exists(report_path):
                with open(report_path, 'r', encoding='utf-8') as f:
                    self.analysis_report = f.read()
                print("✅ 加载分析报告")
                
        except Exception as e:
            print(f"⚠️ 分析结果加载失败: {e}")
            
    def setup_openai(self):
        """设置OpenAI客户端"""
        try:
            config = configparser.ConfigParser()
            config.read(self.config_path)
            
            api_base = config.get('OpenAI', 'OPENAI_API_BASE')
            api_keys = eval(config.get('OpenAI', 'OPENAI_API_KEYS'))
            self.model_name = config.get('OpenAI', 'CHATGPT_MODEL', fallback='gpt-4')
            
            # 设置openai配置
            openai.api_base = api_base
            openai.api_key = api_keys[0] if isinstance(api_keys, list) else api_keys
            
            print(f"✅ OpenAI客户端初始化完成，模型: {self.model_name}")
            
        except Exception as e:
            print(f"❌ OpenAI配置失败: {e}")
            
    def call_llm(self, messages: List[Dict], max_tokens: int = 4000, temperature: float = 0.3) -> str:
        """调用大模型"""
        try:
            # 使用与chat_paper_simple.py相同的调用方式
            if hasattr(openai, 'api_type') and openai.api_type == 'azure':
                response = openai.ChatCompletion.create(
                    engine=self.model_name,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
            else:
                response = openai.ChatCompletion.create(
                    model=self.model_name,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
            
            # 获取响应内容
            result = ''
            for choice in response.choices:
                result += choice.message.content
            
            # 显示token使用情况
            if hasattr(response, 'usage'):
                print(f"Token使用 - 输入: {response.usage.prompt_tokens}, 输出: {response.usage.completion_tokens}, 总计: {response.usage.total_tokens}")
            
            return result
                
        except Exception as e:
            print(f"❌ LLM调用失败: {e}")
            return f"[LLM调用失败] 错误: {str(e)}"
            
    def count_tokens(self, text: str) -> int:
        """计算token数量"""
        try:
            encoding = tiktoken.encoding_for_model(self.model_name)
            return len(encoding.encode(text))
        except:
            # 简单估算：中文约1.5字符/token，英文约4字符/token
            chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
            english_chars = len(text) - chinese_chars
            return int(chinese_chars / 1.5 + english_chars / 4)
    
    def generate_survey_framework(self) -> Dict[str, Any]:
        """生成综述框架"""
        print("\n🏗️ 生成综述框架...")
        
        # 准备数据摘要
        architecture_dist = self.classification_data.get('architecture_classification', {})
        bottleneck_dist = self.classification_data.get('bottleneck_classification', {})
        overall_trends = self.classification_data.get('overall_trends', {})
        
        prompt = f"""基于以下VLA模型研究数据，设计一个系统性的综述框架：

## 数据概览
- 总论文数: {self.classification_data.get('metadata', {}).get('total_papers', 0)}篇
- 主流架构: {overall_trends.get('most_common_architecture', '未知')}
- 数据瓶颈比例: {overall_trends.get('bottleneck_distribution', {}).get('data_bottleneck_ratio', 0):.1%}
- 算力瓶颈比例: {overall_trends.get('bottleneck_distribution', {}).get('compute_bottleneck_ratio', 0):.1%}

## 架构分布
{json.dumps(architecture_dist, ensure_ascii=False, indent=2)}

## 瓶颈分类
{json.dumps(bottleneck_dist, ensure_ascii=False, indent=2)}

请设计一个结构化的综述框架，包括：
1. 主要章节和子章节
2. 每个章节的核心内容和研究问题
3. 章节间的逻辑关系
4. 预期的页数分配

要求：
- 突出资源受限这一核心主题
- 体现VLA模型的技术演进
- 包含定量分析和定性总结
- 适合顶级期刊发表

请以JSON格式返回框架结构。"""

        messages = [
            {"role": "system", "content": "你是一位专业的AI研究员，擅长撰写高质量的综述论文。"},
            {"role": "user", "content": prompt}
        ]
        
        response = self.call_llm(messages, max_tokens=3000)
        
        try:
            # 提取JSON部分
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                framework = json.loads(json_match.group())
            else:
                # 如果没有找到JSON，使用默认框架
                framework = self._get_default_framework()
        except:
            framework = self._get_default_framework()
        
        print("✅ 综述框架生成完成")
        return framework
    
    def _get_default_framework(self) -> Dict[str, Any]:
        """默认综述框架"""
        return {
            "title": "Vision-Language-Action Models under Resource Constraints: A Comprehensive Survey",
            "sections": [
                {
                    "name": "Introduction",
                    "subsections": ["Background", "Motivation", "Contributions", "Organization"],
                    "pages": 3
                },
                {
                    "name": "Background and Related Work",
                    "subsections": ["VLA Model Evolution", "Resource Constraints in AI", "Efficiency Optimization Techniques"],
                    "pages": 4
                },
                {
                    "name": "VLA Architecture Taxonomy",
                    "subsections": ["End-to-End VLA", "Hierarchical VLA", "Hybrid Architectures", "Comparative Analysis"],
                    "pages": 6
                },
                {
                    "name": "Resource Bottleneck Analysis",
                    "subsections": ["Data Bottlenecks", "Compute Bottlenecks", "Combined Constraints", "Impact Assessment"],
                    "pages": 5
                },
                {
                    "name": "Solution Strategies and Innovations",
                    "subsections": ["Data Efficiency Techniques", "Compute Optimization Methods", "Architectural Innovations", "Case Studies"],
                    "pages": 8
                },
                {
                    "name": "Performance Analysis and Benchmarking",
                    "subsections": ["Evaluation Metrics", "Benchmark Datasets", "Performance Trends", "Resource-Performance Trade-offs"],
                    "pages": 4
                },
                {
                    "name": "Future Directions and Open Challenges",
                    "subsections": ["Emerging Trends", "Technical Challenges", "Research Opportunities", "Industry Applications"],
                    "pages": 3
                },
                {
                    "name": "Conclusion",
                    "subsections": ["Key Findings", "Implications", "Final Remarks"],
                    "pages": 2
                }
            ]
        }
    
    def classify_papers_by_themes(self, framework: Dict[str, Any]) -> Dict[str, List[Dict]]:
        """按主题分类论文"""
        print("\n📚 按主题分类论文...")
        
        themes = {}
        
        # 为每个主要章节创建分类
        for section in framework.get('sections', []):
            section_name = section['name']
            if section_name in ['Introduction', 'Conclusion', 'Background and Related Work']:
                continue  # 跳过非技术章节
                
            themes[section_name] = []
        
        # 基于架构类型分类
        for arch_type, arch_data in self.classification_data.get('architecture_classification', {}).items():
            if arch_data.get('paper_count', 0) > 0:
                papers_info = []
                arch_papers = self.df[self.df['VLA架构类型'] == arch_type]
                
                for _, paper in arch_papers.iterrows():
                    paper_info = {
                        'title': paper.get('论文标题', ''),
                        'authors': paper.get('作者', ''),
                        'year': paper.get('发表年份', ''),
                        'architecture': paper.get('VLA架构类型', ''),
                        'data_bottleneck': paper.get('数据瓶颈', ''),
                        'compute_bottleneck': paper.get('算力瓶颈', ''),
                        'innovation': paper.get('创新点', ''),
                        'contribution': paper.get('主要贡献/目标', ''),
                        'performance': paper.get('性能指标', ''),
                        'limitations': paper.get('缺点/局限', ''),
                        'future_work': paper.get('未来方向', '')
                    }
                    papers_info.append(paper_info)
                
                # 根据架构类型分配到相应主题
                if 'Architecture' in themes or 'VLA Architecture Taxonomy' in themes:
                    theme_key = 'VLA Architecture Taxonomy' if 'VLA Architecture Taxonomy' in themes else 'Architecture'
                    themes[theme_key].extend(papers_info)
        
        # 基于资源瓶颈分类
        bottleneck_classification = self.classification_data.get('bottleneck_classification', {})
        for bottleneck_type, bottleneck_data in bottleneck_classification.items():
            if bottleneck_data.get('paper_count', 0) > 0:
                # 这些论文应该归类到资源瓶颈分析章节
                if 'Resource Bottleneck Analysis' in themes:
                    # 获取具体论文信息需要从原始数据中筛选
                    pass  # 这里可以进一步细化分类逻辑
        
        print(f"✅ 论文主题分类完成，共{len(themes)}个主题")
        return themes
    
    def generate_section_content(self, section_name: str, subsections: List[str], 
                                related_papers: List[Dict], max_pages: int = 5) -> str:
        """生成章节内容"""
        print(f"\n✍️ 生成章节: {section_name}")
        
        # 准备相关论文摘要
        papers_summary = ""
        if related_papers:
            papers_summary = "\n## 相关论文摘要:\n"
            for i, paper in enumerate(related_papers[:20]):  # 限制论文数量以避免token超限
                # 安全获取论文信息，处理NaN和None值
                title = self._safe_get_value(paper, 'title', 'Unknown')
                year = self._safe_get_value(paper, 'year', 'Unknown')
                architecture = self._safe_get_value(paper, 'architecture', 'Unknown')
                contribution = self._safe_get_value(paper, 'contribution', 'Unknown')
                innovation = self._safe_get_value(paper, 'innovation', 'Unknown')
                
                papers_summary += f"**{i+1}. {title}** ({year})\n"
                papers_summary += f"- 架构: {architecture}\n"
                papers_summary += f"- 贡献: {contribution[:200]}...\n"
                papers_summary += f"- 创新点: {innovation[:150]}...\n\n"
        
        # 检查token数量
        base_prompt_tokens = self.count_tokens(papers_summary)
        if base_prompt_tokens > 15000:  # 如果太长，截断论文摘要
            papers_summary = papers_summary[:15000] + "\n...(更多论文信息已截断)"
        
        prompt = f"""请为VLA模型资源受限研究综述撰写"{section_name}"章节。

## 章节要求:
- 子章节: {', '.join(subsections)}
- 预期页数: {max_pages}页
- 学术水准: 顶级期刊标准
- 语言: 中文，专业术语保留英文

## 写作要求:
1. 结构清晰，逻辑严谨
2. 包含定量分析和定性总结
3. 突出资源受限这一核心主题
4. 引用具体论文和数据
5. 保持客观和批判性分析

{papers_summary}

## 统计数据参考:
- 端到端VLA: {self.classification_data.get('architecture_classification', {}).get('端到端VLA', {}).get('paper_count', 0)}篇
- 混合架构: {self.classification_data.get('architecture_classification', {}).get('混合架构', {}).get('paper_count', 0)}篇  
- 分层式VLA: {self.classification_data.get('architecture_classification', {}).get('分层式VLA', {}).get('paper_count', 0)}篇
- 双重瓶颈: {self.classification_data.get('bottleneck_classification', {}).get('both_bottlenecks', {}).get('paper_count', 0)}篇

请生成完整的章节内容，包括子章节划分和详细论述。"""

        messages = [
            {"role": "system", "content": "你是一位资深的AI研究员，专门研究Vision-Language-Action模型，擅长撰写高质量的学术综述。"},
            {"role": "user", "content": prompt}
        ]
        
        content = self.call_llm(messages, max_tokens=6000, temperature=0.2)
        
        print(f"✅ 章节生成完成: {len(content)} 字符")
        return content
    
    def generate_technical_analysis(self) -> str:
        """生成技术分析章节"""
        print("\n🔬 生成技术分析...")
        
        # 提取技术关键词和趋势
        innovations = []
        solutions = []
        
        for _, paper in self.df.iterrows():
            if paper.get('创新点') and paper.get('创新点') != '未提及':
                innovations.append(paper.get('创新点'))
            if paper.get('数据瓶颈解决策略') and paper.get('数据瓶颈解决策略') != '未提及':
                solutions.append(paper.get('数据瓶颈解决策略'))
            if paper.get('算力瓶颈解决策略') and paper.get('算力瓶颈解决策略') != '未提及':
                solutions.append(paper.get('算力瓶颈解决策略'))
        
        prompt = f"""基于163篇VLA模型研究论文，生成深度技术分析章节。

## 创新点统计 (前20个):
{str(innovations[:20])}

## 解决策略统计 (前20个):
{str(solutions[:20])}

## 架构分布:
- 端到端VLA: 87篇 (53.4%)
- 混合架构: 37篇 (22.7%) 
- 分层式VLA: 37篇 (22.7%)

## 资源瓶颈现状:
- 双重瓶颈: 66篇 (40.5%)
- 仅算力瓶颈: 55篇 (33.7%)
- 仅数据瓶颈: 16篇 (9.8%)

请生成一个深度技术分析章节，包括：

### 5.1 技术演进路径分析
- VLA架构的历史发展
- 从简单到复杂的演进趋势
- 关键技术突破点

### 5.2 资源约束下的架构设计原则
- 端到端vs分层式的权衡
- 混合架构的优势分析
- 设计原则和最佳实践

### 5.3 关键技术创新分析
- 数据效率提升技术
- 计算优化方法
- 多模态融合创新

### 5.4 性能-资源权衡策略
- 定量分析不同方法的权衡点
- 成本-效益分析框架
- 实际部署考虑因素

要求：
- 深度技术分析，避免浅层罗列
- 包含定量数据支撑
- 体现批判性思维
- 约3000-4000字"""

        messages = [
            {"role": "system", "content": "你是一位技术专家，专长于深度分析AI模型架构和优化技术。"},
            {"role": "user", "content": prompt}
        ]
        
        analysis = self.call_llm(messages, max_tokens=5000, temperature=0.2)
        print("✅ 技术分析生成完成")
        return analysis
    
    def generate_future_directions(self) -> str:
        """生成未来方向章节"""
        print("\n🔮 生成未来发展方向...")
        
        # 收集未来方向信息
        future_directions = []
        limitations = []
        
        for _, paper in self.df.iterrows():
            if paper.get('未来方向') and paper.get('未来方向') != '未提及':
                future_directions.append(paper.get('未来方向'))
            if paper.get('缺点/局限') and paper.get('缺点/局限') != '未提及':
                limitations.append(paper.get('缺点/局限'))
        
        prompt = f"""基于VLA模型研究现状，生成前瞻性的未来发展方向章节。

## 当前局限性 (样本):
{str(limitations[:15])}

## 研究者提出的未来方向 (样本):
{str(future_directions[:15])}

## 技术现状:
- 平均成功率: 62.9%
- 标准差: 28.3%
- 平均模型规模: 13.82B参数
- 主要挑战: 数据稀缺、计算密集、泛化能力、实时性

请生成未来发展方向章节，包括：

### 7.1 技术发展趋势预测
- 短期(1-2年)技术发展
- 中期(3-5年)技术突破
- 长期(5-10年)技术愿景

### 7.2 关键挑战与机遇
- 当前技术瓶颈分析
- 潜在突破点识别
- 跨学科合作机会

### 7.3 新兴研究方向
- 基于分析数据的新兴趋势
- 未被充分探索的领域
- 高影响力研究问题

### 7.4 产业应用前景
- 实际部署场景
- 商业化潜力分析
- 社会影响评估

要求：
- 基于数据的客观预测
- 避免过度乐观或悲观
- 结合当前技术限制
- 提供可行的研究建议
- 约2500-3000字"""

        messages = [
            {"role": "system", "content": "你是一位资深的AI研究战略专家，擅长技术趋势预测和研究方向规划。"},
            {"role": "user", "content": prompt}
        ]
        
        future_content = self.call_llm(messages, max_tokens=4000, temperature=0.3)
        print("✅ 未来方向生成完成")
        return future_content
    
    def generate_complete_survey(self, output_path: str = "complete_vla_survey.md") -> str:
        """生成完整综述"""
        print("\n📝 生成完整综述...")
        
        # 1. 生成框架
        framework = self.generate_survey_framework()
        
        # 2. 分类论文
        paper_themes = self.classify_papers_by_themes(framework)
        
        # 3. 生成各章节
        complete_survey = f"""# {framework.get('title', 'VLA Models under Resource Constraints: A Comprehensive Survey')}

**摘要**: 本综述系统分析了163篇关于Vision-Language-Action (VLA)模型在资源受限环境下的研究论文，涵盖了从2023年到2025年的最新进展。我们发现端到端VLA架构占主导地位(53.4%)，但40.5%的研究面临数据和算力双重瓶颈。通过定量分析和定性总结，本文为VLA模型的高效部署和优化提供了系统性指导。

**关键词**: Vision-Language-Action, 资源约束, 模型优化, 多模态学习, 具身智能

---

"""
        
        # 生成主要技术章节
        sections_to_generate = [
            'VLA Architecture Taxonomy',
            'Resource Bottleneck Analysis', 
            'Solution Strategies and Innovations',
            'Performance Analysis and Benchmarking'
        ]
        
        for section in framework.get('sections', []):
            section_name = section['name']
            
            if section_name == 'Introduction':
                complete_survey += self._generate_introduction()
            elif section_name in sections_to_generate:
                subsections = section.get('subsections', [])
                max_pages = section.get('pages', 5)
                related_papers = paper_themes.get(section_name, [])
                
                content = self.generate_section_content(
                    section_name, subsections, related_papers, max_pages
                )
                complete_survey += f"\n## {section_name}\n\n{content}\n\n"
                
            elif section_name == 'Future Directions and Open Challenges':
                complete_survey += f"\n## {section_name}\n\n"
                complete_survey += self.generate_future_directions()
                complete_survey += "\n\n"
                
            elif section_name == 'Conclusion':
                complete_survey += self._generate_conclusion()
        
        # 添加技术分析
        complete_survey += "\n## 深度技术分析\n\n"
        complete_survey += self.generate_technical_analysis()
        complete_survey += "\n\n"
        
        # 保存完整综述
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(complete_survey)
        
        print(f"✅ 完整综述已生成: {output_path}")
        print(f"📊 综述长度: {len(complete_survey)} 字符")
        return complete_survey
    
    def _generate_introduction(self) -> str:
        """生成引言章节"""
        return """## 1. Introduction

Vision-Language-Action (VLA) 模型作为具身智能领域的重要突破，通过整合视觉感知、语言理解和动作执行能力，为机器人在复杂环境中的自主决策提供了新的解决方案。然而，在实际应用中，VLA模型面临着严重的资源约束挑战，包括数据获取困难、计算资源有限、存储容量不足等问题。

### 1.1 研究背景

随着深度学习和大模型技术的快速发展，VLA模型在机器人操作、导航和交互任务中展现出了巨大潜力。从早期的端到端学习方法到现在的分层式架构和混合系统，VLA模型的设计理念经历了显著变化。然而，这些模型的实际部署仍然面临着资源受限的现实挑战。

### 1.2 研究动机

本综述的研究动机源于以下几个关键观察：
1. **数据瓶颈普遍存在**：83篇论文(50.9%)报告了数据瓶颈问题
2. **算力需求持续增长**：121篇论文(74.2%)面临算力瓶颈
3. **双重约束日益突出**：66篇论文(40.5%)同时面临数据和算力双重瓶颈
4. **解决方案亟需系统化**：现有解决策略缺乏统一的理论框架

### 1.3 主要贡献

本综述的主要贡献包括：
- 首次系统性分析了VLA模型在资源受限环境下的研究现状
- 提出了基于资源约束的VLA架构分类体系
- 总结了数据效率和计算优化的关键技术
- 预测了未来VLA模型发展的技术趋势

### 1.4 文章组织

本文其余部分组织如下：第2节介绍相关背景和工作；第3节提出VLA架构分类体系；第4节深入分析资源瓶颈问题；第5节总结解决策略和技术创新；第6节进行性能分析和基准测试；第7节讨论未来方向和开放挑战；第8节总结全文。

"""
    
    def _generate_conclusion(self) -> str:
        """生成结论章节"""
        return """## 8. Conclusion

### 8.1 主要发现

通过对163篇VLA模型研究论文的系统分析，我们得出以下主要发现：

1. **架构演进趋势明确**：端到端VLA架构占主导地位(53.4%)，但混合架构和分层式VLA正在快速发展，各占22.7%的份额。

2. **资源瓶颈问题严重**：超过74%的研究面临算力瓶颈，50.9%面临数据瓶颈，40.5%面临双重瓶颈，资源约束已成为VLA模型发展的主要障碍。

3. **解决方案逐渐成熟**：数据增强、模型压缩、知识蒸馏、分层设计等技术已形成相对完整的解决方案体系。

4. **性能改善显著**：平均成功率达到62.9%，但标准差较大(28.3%)，说明不同方法的性能差异明显。

### 8.2 理论贡献

本综述在理论层面的主要贡献包括：
- 建立了基于资源约束的VLA模型分类框架
- 提出了资源-性能权衡的定量分析方法
- 总结了VLA模型优化的设计原则和最佳实践

### 8.3 实践指导

对于VLA模型的实际部署，我们提供以下指导建议：
1. 根据资源约束选择合适的架构类型
2. 优先考虑数据效率优化技术
3. 采用渐进式部署策略
4. 建立性能-资源监控体系

### 8.4 研究影响

本综述有望推动VLA模型在资源受限环境下的进一步发展，为相关研究提供理论基础和实践指导，促进具身智能技术的产业化应用。

### 8.5 最终评述

VLA模型在资源受限环境下的研究仍处于快速发展阶段。随着硬件技术进步和算法创新，我们有理由相信资源约束问题将逐步得到缓解，VLA模型将在更广泛的应用场景中发挥重要作用。

---

*本综述基于163篇相关论文的系统分析，数据截止到2025年1月。*
"""

    def run_complete_analysis(self, output_dir: str = "intelligent_survey_results"):
        """运行完整的智能综述生成"""
        print("🚀 开始智能综述生成...")
        
        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)
        
        # 生成完整综述
        survey_path = os.path.join(output_dir, "complete_vla_survey.md")
        complete_survey = self.generate_complete_survey(survey_path)
        
        # 生成框架文件
        framework = self.generate_survey_framework()
        framework_path = os.path.join(output_dir, "survey_framework.json")
        with open(framework_path, 'w', encoding='utf-8') as f:
            json.dump(framework, f, ensure_ascii=False, indent=2)
        
        # 生成技术分析
        tech_analysis = self.generate_technical_analysis()
        tech_path = os.path.join(output_dir, "technical_analysis.md")
        with open(tech_path, 'w', encoding='utf-8') as f:
            f.write(tech_analysis)
        
        # 生成未来方向
        future_directions = self.generate_future_directions()
        future_path = os.path.join(output_dir, "future_directions.md")
        with open(future_path, 'w', encoding='utf-8') as f:
            f.write(future_directions)
        
        print(f"\n✅ 智能综述生成完成！")
        print(f"📝 完整综述: {survey_path}")
        print(f"🏗️ 综述框架: {framework_path}")
        print(f"🔬 技术分析: {tech_path}")
        print(f"🔮 未来方向: {future_path}")

    def _safe_get_value(self, data: Dict, key: str, default: str = "未提及") -> str:
        """安全获取字典值，处理NaN、None和各种异常情况"""
        try:
            value = data.get(key, default)
            # 处理pandas的NaN值
            if pd.isna(value) or value is None:
                return default
            # 处理空字符串
            if str(value).strip() == "":
                return default
            # 处理numpy.nan等特殊值
            if str(value).lower() in ['nan', 'none', 'null']:
                return default
            return str(value)
        except Exception:
            return default


def main():
    parser = argparse.ArgumentParser(description='VLA智能综述生成器')
    parser.add_argument('--csv_path', type=str, required=True, 
                       help='VLA论文CSV数据路径')
    parser.add_argument('--analysis_dir', type=str, required=True,
                       help='分析结果目录路径')
    parser.add_argument('--config_path', type=str, default='apikey.ini',
                       help='API配置文件路径')
    parser.add_argument('--output_dir', type=str, default='intelligent_survey_results',
                       help='输出目录')
    
    args = parser.parse_args()
    
    # 创建智能综述生成器
    generator = VLAIntelligentSurveyGenerator(
        csv_path=args.csv_path,
        analysis_results_dir=args.analysis_dir,
        config_path=args.config_path
    )
    
    # 运行完整分析
    generator.run_complete_analysis(args.output_dir)


if __name__ == "__main__":
    main()
