#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CSV数据验证和清理工具
"""
import pandas as pd
import re
import os
from typing import Dict, List, Tuple

class VLADataValidator:
    def __init__(self, csv_file_path: str):
        self.csv_file = csv_file_path
        self.df = pd.read_csv(csv_file_path)
        self.issues = []
        
    def validate_all(self) -> Dict[str, List[str]]:
        """执行所有验证检查"""
        self.validate_year_format()
        self.validate_vla_types()
        self.validate_bottleneck_values()
        self.validate_data_scale_format()
        self.validate_model_scale_format()
        self.validate_missing_key_fields()
        
        return self.get_validation_report()
    
    def validate_year_format(self):
        """验证年份格式"""
        invalid_years = []
        for idx, year in enumerate(self.df['发表年份']):
            if year != '未提及' and not re.match(r'^\d{4}$', str(year)):
                invalid_years.append(f"Row {idx+1}: '{year}'")
        
        if invalid_years:
            self.issues.append({
                'type': '年份格式错误',
                'count': len(invalid_years),
                'examples': invalid_years[:5]
            })
    
    def validate_vla_types(self):
        """验证VLA架构类型"""
        valid_types = {'端到端VLA', '分层式VLA', '混合架构', '非VLA'}
        invalid_types = []
        
        for idx, vla_type in enumerate(self.df['VLA架构类型']):
            if vla_type not in valid_types:
                invalid_types.append(f"Row {idx+1}: '{vla_type}'")
        
        if invalid_types:
            self.issues.append({
                'type': 'VLA架构类型不规范',
                'count': len(invalid_types),
                'examples': invalid_types[:5]
            })
    
    def validate_bottleneck_values(self):
        """验证瓶颈字段值"""
        valid_values = {'是', '否'}
        
        for field in ['数据瓶颈', '算力瓶颈']:
            invalid_values = []
            for idx, value in enumerate(self.df[field]):
                if value not in valid_values:
                    invalid_values.append(f"Row {idx+1}: '{value}'")
            
            if invalid_values:
                self.issues.append({
                    'type': f'{field}值不规范',
                    'count': len(invalid_values),
                    'examples': invalid_values[:5]
                })
    
    def validate_data_scale_format(self):
        """验证数据规模格式"""
        invalid_scales = []
        scale_pattern = r'(\d+[\.\d]*[KMB]?\s*(轨迹|小时|样本|帧|图像|视频|任务|演示))|未提及'
        
        for idx, scale in enumerate(self.df['数据规模']):
            if not re.search(scale_pattern, str(scale)):
                invalid_scales.append(f"Row {idx+1}: '{scale}'")
        
        if invalid_scales:
            self.issues.append({
                'type': '数据规模格式不规范',
                'count': len(invalid_scales),
                'examples': invalid_scales[:5]
            })
    
    def validate_model_scale_format(self):
        """验证模型规模格式"""
        invalid_scales = []
        scale_pattern = r'(\d+[\.\d]*[KMB]?\s*参数)|(\w+架构)|未提及'
        
        for idx, scale in enumerate(self.df['模型规模']):
            if not re.search(scale_pattern, str(scale)):
                invalid_scales.append(f"Row {idx+1}: '{scale}'")
        
        if invalid_scales:
            self.issues.append({
                'type': '模型规模格式不规范',
                'count': len(invalid_scales),
                'examples': invalid_scales[:5]
            })
    
    def validate_missing_key_fields(self):
        """检查关键字段缺失情况"""
        key_fields = ['训练资源需求', '推理效率', '性能指标', '资源-性能权衡']
        
        for field in key_fields:
            missing_count = (self.df[field] == '未提及').sum()
            missing_rate = missing_count / len(self.df) * 100
            
            if missing_rate > 50:  # 超过50%缺失
                self.issues.append({
                    'type': f'{field}缺失率过高',
                    'count': missing_count,
                    'rate': f'{missing_rate:.1f}%'
                })
    
    def get_validation_report(self) -> Dict:
        """获取验证报告"""
        return {
            'total_papers': len(self.df),
            'issues_found': len(self.issues),
            'issues': self.issues,
            'summary': self._generate_summary()
        }
    
    def _generate_summary(self) -> Dict:
        """生成数据质量摘要"""
        return {
            'vla_type_distribution': self.df['VLA架构类型'].value_counts().to_dict(),
            'data_bottleneck_rate': (self.df['数据瓶颈'] == '是').sum() / len(self.df) * 100,
            'compute_bottleneck_rate': (self.df['算力瓶颈'] == '是').sum() / len(self.df) * 100,
            'missing_author_rate': (self.df['作者'] == '未提及').sum() / len(self.df) * 100,
            'missing_training_resource_rate': (self.df['训练资源需求'] == '未提及').sum() / len(self.df) * 100
        }
    
    def export_cleaned_csv(self, output_path: str):
        """导出清理后的CSV"""
        # 这里可以添加自动清理逻辑
        cleaned_df = self.df.copy()
        
        # 标准化年份格式
        cleaned_df['发表年份'] = cleaned_df['发表年份'].apply(self._standardize_year)
        
        # 标准化作者格式
        cleaned_df['作者'] = cleaned_df['作者'].apply(self._standardize_author)
        
        cleaned_df.to_csv(output_path, index=False, encoding='utf-8')
        print(f"清理后的CSV已保存到: {output_path}")
    
    def _standardize_year(self, year):
        """标准化年份"""
        if pd.isna(year) or year == '未提及':
            return '未提及'
        year_str = str(year)
        if re.match(r'^\d{4}$', year_str):
            return year_str
        return '未提及'
    
    def _standardize_author(self, author):
        """标准化作者"""
        if pd.isna(author) or author == '未提及':
            return '未提及'
        
        # 提取第一作者
        author_str = str(author)
        if ',' in author_str:
            first_author = author_str.split(',')[0].strip()
            return f"{first_author} et al."
        elif len(author_str) > 50:
            # 太长的作者列表截断
            return f"{author_str[:30]}... et al."
        
        return author_str

def main():
    csv_file = "/Users/sunyukun/Projects/ChatPaper/export/2025-07-29-10-merged_papers.csv"
    
    if not os.path.exists(csv_file):
        print(f"CSV文件不存在: {csv_file}")
        return
    
    validator = VLADataValidator(csv_file)
    report = validator.validate_all()
    
    print("=== VLA数据验证报告 ===")
    print(f"总论文数: {report['total_papers']}")
    print(f"发现问题数: {report['issues_found']}")
    
    print("\n=== 数据质量摘要 ===")
    summary = report['summary']
    print(f"VLA架构分布: {summary['vla_type_distribution']}")
    print(f"数据瓶颈率: {summary['data_bottleneck_rate']:.1f}%")
    print(f"算力瓶颈率: {summary['compute_bottleneck_rate']:.1f}%")
    print(f"作者缺失率: {summary['missing_author_rate']:.1f}%")
    print(f"训练资源缺失率: {summary['missing_training_resource_rate']:.1f}%")
    
    if report['issues']:
        print("\n=== 发现的问题 ===")
        for issue in report['issues']:
            print(f"- {issue['type']}: {issue['count']}个")
            if 'examples' in issue:
                print(f"  示例: {issue['examples']}")
    
    # 导出清理后的数据
    output_file = csv_file.replace('.csv', '_cleaned.csv')
    validator.export_cleaned_csv(output_file)

if __name__ == "__main__":
    main()
