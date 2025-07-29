#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
本地PDF论文总结快速启动脚本
"""
import os
import sys
import argparse
from chat_paper_simple import Paper, Reader

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='VLA模型资源受限研究专用PDF分析工具')
    parser.add_argument('pdf_path', type=str, help='PDF文件路径或文件夹路径')
    parser.add_argument('--key_word', '-k', type=str, 
                        default='vision language action model resource constraint', 
                        help='研究领域关键词，默认为VLA资源受限研究')
    parser.add_argument('--language', '-l', type=str, choices=['zh', 'en'], default='zh',
                        help='输出语言，默认为中文(zh)')
    parser.add_argument('--max_tokens', '-m', type=int, default=8192,
                        help='模型最大token限制，默认为8192（VLA论文通常较长）')
    parser.add_argument('--strategy', '-s', type=str, choices=['front', 'balanced', 'sections'], 
                        default='sections', help='长文本处理策略，默认为sections(章节优先，VLA研究推荐)')
    parser.add_argument('--format', '-f', type=str, default='csv',
                        help='输出格式，默认为CSV格式')
    
    args = parser.parse_args()
    
    print(f"\n=== VLA模型资源受限研究专用分析工具 ===")
    print(f"🎯 研究目标: 资源受限下的Vision Language Action Model")
    print(f"🔍 核心问题: 数据瓶颈 + 算力瓶颈")
    print(f"PDF路径: {args.pdf_path}")
    print(f"研究领域: {args.key_word}")
    print(f"输出语言: {'中文' if args.language=='zh' else '英文'}")
    print(f"处理策略: {args.strategy} {'(VLA专用优化)' if args.strategy=='sections' else ''}")
    print(f"最大tokens: {args.max_tokens}")
    
    reader = Reader(key_word=args.key_word, args=args)
    reader.max_token_num = args.max_tokens
    reader.token_manager.max_token_num = args.max_tokens
    reader.file_format = args.format if hasattr(args, 'format') else 'csv'
    
    # 收集PDF文件路径，但不预处理
    pdf_paths = []
    
    # 处理单个PDF文件
    if args.pdf_path.lower().endswith(".pdf"):
        if not os.path.exists(args.pdf_path):
            print(f"错误: 找不到PDF文件 '{args.pdf_path}'")
            sys.exit(1)
        print(f"正在处理单个PDF文件: {os.path.basename(args.pdf_path)}")
        pdf_paths.append(args.pdf_path)
    
    # 处理文件夹中的所有PDF
    else:
        if not os.path.isdir(args.pdf_path):
            print(f"错误: '{args.pdf_path}' 不是有效的文件夹路径")
            sys.exit(1)
        
        print(f"正在扫描文件夹: {args.pdf_path}")
        pdf_count = 0
        
        for root, dirs, files in os.walk(args.pdf_path):
            for filename in files:
                if filename.lower().endswith(".pdf"):
                    pdf_path = os.path.join(root, filename)
                    print(f"发现PDF: {filename}")
                    pdf_paths.append(pdf_path)
                    pdf_count += 1
        
        print(f"总共找到 {pdf_count} 个PDF文件")
    
    if not pdf_paths:
        print("未找到任何PDF文件，退出程序")
        sys.exit(0)
    
    # 逐篇预处理+总结，结果合并到单个CSV文件
    print("\n开始逐篇处理论文并合并结果...")
    reader.summary_with_chat(pdf_paths, truncation_strategy=args.strategy)
    
    print("\n✅ 所有论文处理完成!")
    print("📄 合并结果保存在 ./export 目录下的merged_papers.csv文件中")
    print("💾 各论文的单独备份保存在 ./export/individual_backups 目录下")
