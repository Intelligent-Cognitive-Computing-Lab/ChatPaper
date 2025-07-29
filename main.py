#!/usr/bin/env python3
"""
ChatPaper - VLA模型资源受限研究综述工具
主入口程序，集成论文分析、报告生成和LLM智能综述功能
"""

import os
import sys
import argparse
from datetime import datetime

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='ChatPaper - VLA模型资源受限研究综述工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  
  1. 批量分析PDF论文:
     python main.py analyze --pdf_path papers/ --parallel --max_workers 3
  
  2. 生成统计分析报告:
     python main.py report --csv_path results/export/vla_all_250729.csv
  
  3. 使用LLM生成智能综述:
     python main.py survey --csv_path results/export/vla_all_250729.csv --generate_chapters
  
  4. 完整流程（分析+报告+综述）:
     python main.py full --pdf_path papers/ --parallel
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # 1. 论文分析命令
    analyze_parser = subparsers.add_parser('analyze', help='批量分析PDF论文')
    analyze_parser.add_argument('--pdf_path', required=True, help='PDF文件或文件夹路径')
    analyze_parser.add_argument('--key_word', default='vision language action', help='研究领域关键词')
    analyze_parser.add_argument('--parallel', action='store_true', help='启用多线程并行处理')
    analyze_parser.add_argument('--max_workers', type=int, default=3, help='并发线程数')
    analyze_parser.add_argument('--max_tokens', type=int, default=60000, help='最大token数')
    analyze_parser.add_argument('--language', default='zh', help='输出语言')
    analyze_parser.add_argument('--resume', action='store_true', help='断点续传')
    
    # 2. 报告生成命令
    report_parser = subparsers.add_parser('report', help='生成统计分析报告')
    report_parser.add_argument('--csv_path', required=True, help='CSV数据文件路径')
    report_parser.add_argument('--output_dir', default='results/analysis_results', help='输出目录')
    
    # 3. 智能综述命令
    survey_parser = subparsers.add_parser('survey', help='使用LLM生成智能综述')
    survey_parser.add_argument('--csv_path', required=True, help='CSV数据文件路径')
    survey_parser.add_argument('--analysis_dir', default='results/analysis_results', help='分析结果目录')
    survey_parser.add_argument('--generate_chapters', action='store_true', help='生成详细章节内容')
    survey_parser.add_argument('--output_dir', default='results/intelligent_survey_results', help='输出目录')
    
    # 4. 完整流程命令
    full_parser = subparsers.add_parser('full', help='完整流程（分析+报告+综述）')
    full_parser.add_argument('--pdf_path', required=True, help='PDF文件或文件夹路径')
    full_parser.add_argument('--parallel', action='store_true', help='启用多线程并行处理')
    full_parser.add_argument('--max_workers', type=int, default=3, help='并发线程数')
    full_parser.add_argument('--generate_chapters', action='store_true', help='生成详细章节内容')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    print("🚀 ChatPaper - VLA模型资源受限研究综述工具")
    print("=" * 60)
    print(f"⏰ 启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🔧 执行命令: {args.command}")
    print()
    
    try:
        if args.command == 'analyze':
            run_analyze(args)
        elif args.command == 'report':
            run_report(args)
        elif args.command == 'survey':
            run_survey(args)
        elif args.command == 'full':
            run_full_pipeline(args)
            
    except KeyboardInterrupt:
        print("\n⚠️  用户中断执行")
    except Exception as e:
        print(f"\n❌ 执行失败: {str(e)}")
        return 1
    
    print(f"\n✅ 任务完成! 结果保存在 results/ 目录下")
    return 0

def run_analyze(args):
    """执行论文分析"""
    from chat_paper_simple import main as analyze_main
    
    print("📚 开始批量分析PDF论文...")
    
    # 构建分析参数
    analyze_args = [
        '--pdf_path', args.pdf_path,
        '--key_word', args.key_word,
        '--language', args.language,
        '--max_tokens', str(args.max_tokens)
    ]
    
    if args.parallel:
        analyze_args.extend(['--parallel', '--max_workers', str(args.max_workers)])
    
    if args.resume:
        analyze_args.append('--resume')
    
    # 临时修改sys.argv来传递参数
    original_argv = sys.argv
    sys.argv = ['chat_paper_simple.py'] + analyze_args
    
    try:
        analyze_main()
    finally:
        sys.argv = original_argv
    
    print("✅ 论文分析完成")

def run_report(args):
    """执行报告生成"""
    from vla_survey_analyzer import VLASurveyAnalyzer
    
    print("📊 开始生成统计分析报告...")
    
    if not os.path.exists(args.csv_path):
        raise FileNotFoundError(f"CSV文件不存在: {args.csv_path}")
    
    # 创建输出目录
    os.makedirs(args.output_dir, exist_ok=True)
    
    # 生成报告
    analyzer = VLASurveyAnalyzer(args.csv_path)
    analyzer.generate_comprehensive_report(args.output_dir)
    
    print("✅ 统计分析报告生成完成")

def run_survey(args):
    """执行智能综述生成"""
    from vla_intelligent_survey_generator import VLAIntelligentSurveyGenerator
    
    print("🤖 开始使用LLM生成智能综述...")
    
    if not os.path.exists(args.csv_path):
        raise FileNotFoundError(f"CSV文件不存在: {args.csv_path}")
    
    if not os.path.exists(args.analysis_dir):
        raise FileNotFoundError(f"分析结果目录不存在: {args.analysis_dir}")
    
    # 创建输出目录
    os.makedirs(args.output_dir, exist_ok=True)
    
    # 初始化综述生成器
    generator = VLAIntelligentSurveyGenerator(
        args.csv_path, 
        args.analysis_dir,
        config_path='config/apikey.ini'
    )
    
    # 生成综述框架
    print("📋 生成综述框架...")
    framework = generator.generate_survey_framework()
    
    # 分类论文
    print("📚 分类论文...")
    classification = generator.classify_papers_by_themes(framework)
    
    # 保存基础结果
    import json
    framework_path = os.path.join(args.output_dir, 'survey_framework.json')
    with open(framework_path, 'w', encoding='utf-8') as f:
        json.dump(framework, f, ensure_ascii=False, indent=2)
    
    classification_path = os.path.join(args.output_dir, 'paper_classification.json')
    with open(classification_path, 'w', encoding='utf-8') as f:
        json.dump(classification, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 框架和分类已保存")
    
    # 如果需要生成详细章节
    if args.generate_chapters:
        print("📝 生成详细章节内容...")
        generate_detailed_chapters(generator, framework, classification, args.output_dir)
    
    print("✅ 智能综述生成完成")

def generate_detailed_chapters(generator, framework, classification, output_dir):
    """生成详细章节内容"""
    
    chapters_dir = os.path.join(output_dir, 'chapters')
    os.makedirs(chapters_dir, exist_ok=True)
    
    # 选择要生成的核心章节
    target_sections = [
        "Introduction",
        "VLA Architecture Taxonomy", 
        "Resource Bottleneck Analysis",
        "Solution Strategies and Innovations"
    ]
    
    generated_chapters = []
    
    for section in framework.get('sections', []):
        section_name = section['name']
        
        if section_name not in target_sections:
            continue
            
        subsections = section.get('subsections', [])
        max_pages = section.get('pages', 3)
        
        print(f"  📝 生成章节: {section_name}")
        
        # 获取相关论文
        related_papers = []
        for category, papers in classification.items():
            if isinstance(papers, list):
                related_papers.extend(papers[:5])
                if len(related_papers) >= 15:
                    break
        
        # 生成章节内容
        content = generator.generate_section_content(
            section_name, subsections, related_papers, max_pages
        )
        
        # 保存章节
        safe_name = section_name.replace(' ', '_').replace('/', '_').lower()
        chapter_file = os.path.join(chapters_dir, f"{safe_name}.md")
        
        with open(chapter_file, 'w', encoding='utf-8') as f:
            f.write(f"# {section_name}\n\n")
            f.write(content)
        
        generated_chapters.append({
            'name': section_name,
            'file': chapter_file,
            'length': len(content)
        })
        
        print(f"     ✅ 完成 ({len(content)} 字符)")
    
    # 生成目录
    generate_chapters_index(framework, generated_chapters, chapters_dir)
    
    print(f"  📑 已生成 {len(generated_chapters)} 个章节")

def generate_chapters_index(framework, generated_chapters, chapters_dir):
    """生成章节目录"""
    
    index_content = f"""# VLA模型资源受限研究综述

*生成时间: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}*

## 目录

"""
    
    chapter_files = {ch['name']: os.path.basename(ch['file']) for ch in generated_chapters}
    
    for i, section in enumerate(framework.get('sections', [])):
        section_name = section['name']
        pages = section.get('pages', 3)
        
        if section_name in chapter_files:
            filename = chapter_files[section_name]
            index_content += f"{i+1}. [{section_name}](./{filename}) *({pages}页)* ✅\n"
        else:
            index_content += f"{i+1}. {section_name} *({pages}页)* ⏳\n"
        
        for j, subsection in enumerate(section.get('subsections', [])):
            index_content += f"   {i+1}.{j+1} {subsection}\n"
        
        index_content += "\n"
    
    index_content += f"""
## 生成统计

- **已生成章节**: {len(generated_chapters)}/{len(framework.get('sections', []))}
- **总字符数**: {sum(ch['length'] for ch in generated_chapters):,}

---
*本综述由ChatPaper智能生成*
"""
    
    index_file = os.path.join(chapters_dir, "README.md")
    with open(index_file, 'w', encoding='utf-8') as f:
        f.write(index_content)

def run_full_pipeline(args):
    """运行完整流程"""
    print("🔄 开始执行完整流程...")
    
    # 1. 分析论文
    print("\n" + "="*50)
    print("第1步: 批量分析PDF论文")
    print("="*50)
    
    analyze_args_obj = argparse.Namespace(
        pdf_path=args.pdf_path,
        key_word='vision language action',
        parallel=args.parallel,
        max_workers=args.max_workers,
        max_tokens=60000,
        language='zh',
        resume=False
    )
    run_analyze(analyze_args_obj)
    
    # 查找生成的CSV文件
    export_dir = 'results/export'
    if os.path.exists(export_dir):
        csv_files = [f for f in os.listdir(export_dir) if f.endswith('.csv') and 'merged' in f]
        if csv_files:
            # 使用最新的CSV文件
            csv_files.sort(reverse=True)
            csv_path = os.path.join(export_dir, csv_files[0])
        else:
            raise FileNotFoundError("未找到生成的CSV文件")
    else:
        raise FileNotFoundError("export目录不存在")
    
    # 2. 生成报告
    print("\n" + "="*50)
    print("第2步: 生成统计分析报告")
    print("="*50)
    
    report_args_obj = argparse.Namespace(
        csv_path=csv_path,
        output_dir='results/analysis_results'
    )
    run_report(report_args_obj)
    
    # 3. 生成智能综述
    print("\n" + "="*50)
    print("第3步: 生成智能综述")
    print("="*50)
    
    survey_args_obj = argparse.Namespace(
        csv_path=csv_path,
        analysis_dir='results/analysis_results',
        generate_chapters=args.generate_chapters,
        output_dir='results/intelligent_survey_results'
    )
    run_survey(survey_args_obj)
    
    print("\n🎉 完整流程执行完成!")
    print(f"📁 所有结果已保存在 results/ 目录下")

if __name__ == "__main__":
    sys.exit(main())
