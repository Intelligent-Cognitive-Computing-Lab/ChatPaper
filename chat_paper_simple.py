import argparse
import configparser
import datetime
import os
import re
import openai
import tiktoken
import fitz  # PyMuPDF
import json
import hashlib


class Paper:
    def __init__(self, path, title=''):
        """初始化Paper对象，只处理本地PDF文件"""
        self.path = path
        self.section_names = []
        self.section_texts = {}
        self.title_page = 0
        
        # 解析PDF
        self.pdf = fitz.open(path)
        self.title = self.get_title() if title == '' else title
        self.parse_pdf()
        
    def parse_pdf(self):
        """解析PDF内容"""
        self.text_list = [page.get_text() for page in self.pdf]
        self.all_text = ' '.join(self.text_list)
        self.section_page_dict = self._get_all_page_index()
        print("section_page_dict", self.section_page_dict)
        self.section_text_dict = self._get_all_page()
        self.section_text_dict.update({"title": self.title})
        self.section_text_dict.update({"paper_info": self.get_paper_info()})
        self.pdf.close()
        
    def get_paper_info(self):
        """获取论文基本信息"""
        first_page_text = self.pdf[self.title_page].get_text()
        if "Abstract" in self.section_text_dict.keys():
            abstract_text = self.section_text_dict['Abstract']
        else:
            abstract_text = ""
        first_page_text = first_page_text.replace(abstract_text, "")
        return first_page_text
        
    def get_title(self):
        """从PDF中提取标题"""
        doc = self.pdf
        max_font_size = 0
        max_string = ""
        max_font_sizes = [0]
        
        for page_index, page in enumerate(doc):
            text = page.get_text("dict")
            blocks = text["blocks"]
            for block in blocks:
                if block["type"] == 0 and len(block['lines']):
                    if len(block["lines"][0]["spans"]):
                        font_size = block["lines"][0]["spans"][0]["size"]
                        max_font_sizes.append(font_size)
                        if font_size > max_font_size:
                            max_font_size = font_size
                            max_string = block["lines"][0]["spans"][0]["text"]
        
        max_font_sizes.sort()
        print("max_font_sizes", max_font_sizes[-10:])
        
        cur_title = ''
        for page_index, page in enumerate(doc):
            text = page.get_text("dict")
            blocks = text["blocks"]
            for block in blocks:
                if block["type"] == 0 and len(block['lines']):
                    if len(block["lines"][0]["spans"]):
                        cur_string = block["lines"][0]["spans"][0]["text"]
                        font_size = block["lines"][0]["spans"][0]["size"]
                        
                        if abs(font_size - max_font_sizes[-1]) < 0.3 or abs(font_size - max_font_sizes[-2]) < 0.3:
                            if len(cur_string) > 4 and "arXiv" not in cur_string:
                                if cur_title == '':
                                    cur_title += cur_string
                                else:
                                    cur_title += ' ' + cur_string
                            self.title_page = page_index
        
        title = cur_title.replace('\n', ' ')
        return title

    def _get_all_page_index(self):
        """获取各章节在PDF中的页码"""
        section_list = ["Abstract", 
                        'Introduction', 'Related Work', 'Background', 
                        "Preliminary", "Problem Formulation",
                        'Methods', 'Methodology', "Method", 'Approach', 'Approaches',
                        "Materials and Methods", "Experiment Settings",
                        'Experiment', "Experimental Results", "Evaluation", "Experiments",                        
                        "Results", 'Findings', 'Data Analysis',                                                                        
                        "Discussion", "Results and Discussion", "Conclusion",
                        'References']
        
        section_page_dict = {}
        for page_index, page in enumerate(self.pdf):
            cur_text = page.get_text()
            for section_name in section_list:
                section_name_upper = section_name.upper()
                if "Abstract" == section_name and section_name in cur_text:
                    section_page_dict[section_name] = page_index
                else:
                    if section_name + '\n' in cur_text:
                        section_page_dict[section_name] = page_index
                    elif section_name_upper + '\n' in cur_text:
                        section_page_dict[section_name] = page_index
        
        return section_page_dict

    def _get_all_page(self):
        """获取各章节的文本内容"""
        section_dict = {}
        text_list = [page.get_text() for page in self.pdf]
        
        for sec_index, sec_name in enumerate(self.section_page_dict):
            print(sec_index, sec_name, self.section_page_dict[sec_name])
            
            start_page = self.section_page_dict[sec_name]
            if sec_index < len(list(self.section_page_dict.keys()))-1:
                end_page = self.section_page_dict[list(self.section_page_dict.keys())[sec_index+1]]
            else:
                end_page = len(text_list)
            
            print("start_page, end_page:", start_page, end_page)
            cur_sec_text = ''
            
            if end_page - start_page == 0:
                if sec_index < len(list(self.section_page_dict.keys()))-1:
                    next_sec = list(self.section_page_dict.keys())[sec_index+1]
                    if text_list[start_page].find(sec_name) == -1:
                        start_i = text_list[start_page].find(sec_name.upper())
                    else:
                        start_i = text_list[start_page].find(sec_name)
                    if text_list[start_page].find(next_sec) == -1:
                        end_i = text_list[start_page].find(next_sec.upper())
                    else:
                        end_i = text_list[start_page].find(next_sec)                        
                    cur_sec_text += text_list[start_page][start_i:end_i]
            else:
                for page_i in range(start_page, end_page):                    
                    if page_i == start_page:
                        if text_list[start_page].find(sec_name) == -1:
                            start_i = text_list[start_page].find(sec_name.upper())
                        else:
                            start_i = text_list[start_page].find(sec_name)
                        cur_sec_text += text_list[page_i][start_i:]
                    elif page_i < end_page:
                        cur_sec_text += text_list[page_i]
                    elif page_i == end_page:
                        if sec_index < len(list(self.section_page_dict.keys()))-1:
                            next_sec = list(self.section_page_dict.keys())[sec_index+1]
                            if text_list[start_page].find(next_sec) == -1:
                                end_i = text_list[start_page].find(next_sec.upper())
                            else:
                                end_i = text_list[start_page].find(next_sec)  
                            cur_sec_text += text_list[page_i][:end_i]
            
            section_dict[sec_name] = cur_sec_text.replace('-\n', '').replace('\n', ' ')
        
        return section_dict


class Reader:
    def __init__(self, key_word, args=None):
        """初始化Reader，只用于本地PDF总结"""
        self.key_word = key_word
        self.language = 'Chinese' if args and args.language == 'zh' else 'English'
        
        # 读取配置文件
        self.config = configparser.ConfigParser()
        self.config.read('apikey.ini')
        
        # OpenAI配置
        OPENAI_KEY = os.environ.get("OPENAI_KEY", "")
        openai.api_base = self.config.get('OpenAI', 'OPENAI_API_BASE')
        self.chat_api_list = self.config.get('OpenAI', 'OPENAI_API_KEYS')[1:-1].replace('\'', '').split(',')
        self.chat_api_list.append(OPENAI_KEY)
        self.chat_api_list = [api.strip() for api in self.chat_api_list if len(api) > 20]
        self.chatgpt_model = self.config.get('OpenAI', 'CHATGPT_MODEL')

        # 如果没有OpenAI key，使用Azure
        if not self.chat_api_list:
            self.chat_api_list.append(self.config.get('AzureOPenAI', 'OPENAI_API_KEYS'))
            self.chatgpt_model = self.config.get('AzureOPenAI', 'CHATGPT_MODEL')
            openai.api_base = self.config.get('AzureOPenAI', 'OPENAI_API_BASE')
            openai.api_type = 'azure'
            openai.api_version = self.config.get('AzureOPenAI', 'OPENAI_API_VERSION')

        self.cur_api = 0
        self.file_format = args.file_format if args else 'md'
        self.max_token_num = args.max_tokens if args else 4096
        self.encoding = tiktoken.get_encoding("gpt2")
        self.token_manager = TokenManager(max_token_num=self.max_token_num, model=self.chatgpt_model)
        
        # 进度跟踪
        self.progress_file = 'processing_progress.json'
        self.export_path = os.path.join('./', 'export')
        if not os.path.exists(self.export_path):
            os.makedirs(self.export_path)
        
        # CSV合并相关
        self.merged_csv_file = None
        self.csv_header_written = False

    def get_paper_hash(self, paper_path):
        """生成论文文件的唯一标识"""
        with open(paper_path, 'rb') as f:
            file_hash = hashlib.md5(f.read()).hexdigest()
        return file_hash

    def load_progress(self):
        """加载处理进度"""
        if os.path.exists(self.progress_file):
            try:
                with open(self.progress_file, 'r', encoding='utf-8') as f:
                    progress = json.load(f)
                # 检查是否已有合并文件，如果有则标记表头已写入
                if os.path.exists(self.merged_csv_file if hasattr(self, 'merged_csv_file') else ''):
                    self.csv_header_written = True
                    print("📋 检测到现有合并文件，将继续追加数据")
                return progress
            except:
                return {}
        return {}

    def save_progress(self, progress):
        """保存处理进度"""
        with open(self.progress_file, 'w', encoding='utf-8') as f:
            json.dump(progress, f, ensure_ascii=False, indent=2)

    def is_paper_processed(self, paper_path, progress):
        """检查论文是否已经处理过"""
        paper_hash = self.get_paper_hash(paper_path)
        return paper_hash in progress and progress[paper_hash].get('status') == 'completed'

    def mark_paper_completed(self, paper_path, output_file, progress):
        """标记论文处理完成"""
        paper_hash = self.get_paper_hash(paper_path)
        progress[paper_hash] = {
            'status': 'completed',
            'paper_path': paper_path,
            'output_file': output_file,
            'completed_time': str(datetime.datetime.now())
        }
        self.save_progress(progress)

    def validateTitle(self, title):
        """修正文件名中的特殊字符"""
        rstr = r"[\/\\\:\*\?\"\<\>\|]"
        new_title = re.sub(rstr, "_", title)
        return new_title

    def summary_with_chat(self, pdf_paths, truncation_strategy="balanced"):
        """逐篇预处理+总结论文，支持断点续传"""
        print(f"\n=== 开始处理PDF文件，总共 {len(pdf_paths)} 个文件，策略: {truncation_strategy} ===")
        
        # 初始化合并的CSV文件
        date_str = str(datetime.datetime.now())[:13].replace(' ', '-')
        self.merged_csv_file = os.path.join(self.export_path, f"{date_str}-merged_papers.csv")
        
        # 加载进度（会检查现有文件）
        progress = self.load_progress()
        
        # 检查合并文件是否已存在且有内容
        if os.path.exists(self.merged_csv_file):
            with open(self.merged_csv_file, 'r', encoding='utf-8') as f:
                existing_content = f.read().strip()
                if existing_content:
                    self.csv_header_written = True
                    print(f"📄 检测到现有合并文件，将继续追加: {self.merged_csv_file}")
                else:
                    self.csv_header_written = False
                    print(f"📄 创建新的合并文件: {self.merged_csv_file}")
        else:
            self.csv_header_written = False
            print(f"📄 创建新的合并文件: {self.merged_csv_file}")
        
        processed_count = 0
        skipped_count = 0
        failed_count = 0
        
        for pdf_index, pdf_path in enumerate(pdf_paths):
            print(f"\n--- 处理第 {pdf_index + 1}/{len(pdf_paths)} 个PDF文件 ---")
            print(f"文件路径: {pdf_path}")
            
            # 检查是否已经处理过
            if self.is_paper_processed(pdf_path, progress):
                print(f"✅ PDF已处理过，跳过")
                skipped_count += 1
                continue
            
            try:
                # 逐篇预处理+总结
                success = self.process_single_pdf_complete(pdf_path, truncation_strategy, progress)
                if success:
                    processed_count += 1
                    print(f"✅ 第 {pdf_index + 1} 个PDF处理完成")
                else:
                    failed_count += 1
                    print(f"❌ 第 {pdf_index + 1} 个PDF处理失败")
                    
            except KeyboardInterrupt:
                print(f"\n⚠️  用户中断程序")
                print(f"已处理: {processed_count} 篇，跳过: {skipped_count} 篇，失败: {failed_count} 篇")
                print(f"进度已保存，下次运行将从中断处继续")
                print(f"📄 当前结果已保存到: {self.merged_csv_file}")
                return
            except Exception as e:
                failed_count += 1
                print(f"❌ 处理PDF时发生错误: {e}")
                continue
        
        print(f"\n=== 所有PDF处理完成 ===")
        print(f"新处理: {processed_count} 篇，跳过: {skipped_count} 篇，失败: {failed_count} 篇，总计: {len(pdf_paths)} 个文件")
        print(f"📄 合并结果已保存到: {self.merged_csv_file}")

    def process_single_pdf_complete(self, pdf_path, truncation_strategy, progress):
        """完整处理单个PDF：预处理+总结"""
        paper = None
        try:
            print(f"📖 开始解析PDF...")
            # 预处理：解析PDF
            paper = Paper(path=pdf_path)
            print(f"📄 PDF解析完成，标题: {paper.title[:80]}...")
            
            # 总结处理
            success = self.process_single_paper(paper, truncation_strategy, progress)
            
            # 清理内存
            if paper and hasattr(paper, 'pdf'):
                try:
                    paper.pdf.close()
                except:
                    pass
            del paper
            
            return success
            
        except Exception as e:
            print(f"❌ PDF预处理失败: {e}")
            # 确保清理资源
            if paper and hasattr(paper, 'pdf'):
                try:
                    paper.pdf.close()
                except:
                    pass
            return False

    def process_single_paper(self, paper, truncation_strategy, progress):
        """处理单篇已解析的论文"""
        try:
            # 准备所有文本内容
            all_text = ''
            all_text += 'Title: ' + paper.title + '\n'
            all_text += 'Paper_info: ' + paper.section_text_dict['paper_info'] + '\n'
            
            # 添加各个章节内容
            for section_name, section_content in paper.section_text_dict.items():
                if section_name not in ['title', 'paper_info']:
                    all_text += f'{section_name}: {section_content}\n'
            
            original_length = len(all_text)
            original_tokens = self.token_manager.count_tokens(all_text)
            print(f"📊 论文内容长度: {original_length} 字符, {original_tokens} tokens")
            
            # 生成结构化总结
            print("🤖 开始生成结构化总结...")
            chat_conclusion_text = ""
            retry_count = 0
            max_retries = 3
            
            while retry_count < max_retries:
                try:
                    print(f"🔄 调用API (尝试 {retry_count + 1}/{max_retries})")
                    chat_conclusion_text = self.chat_conclusion(
                        text=all_text, 
                        truncation_strategy=truncation_strategy
                    )
                    print("✅ 结构化总结生成成功")
                    break
                except Exception as e:
                    retry_count += 1
                    print(f"❌ API调用失败 (尝试 {retry_count}): {e}")
                    
                    if retry_count >= max_retries:
                        print("⚠️  达到最大重试次数，跳过此论文")
                        return False

            # 保存结果到合并的CSV文件
            print("💾 保存结果到合并CSV文件...")
            self.append_to_merged_csv(chat_conclusion_text)
            
            # 同时保存单独的文件作为备份
            date_str = str(datetime.datetime.now())[:13].replace(' ', '-')
            backup_file = os.path.join(self.export_path, 'individual_backups',
                                     date_str + '-' + self.validateTitle(paper.title[:80]) + ".csv")
            
            # 创建备份目录
            backup_dir = os.path.dirname(backup_file)
            if not os.path.exists(backup_dir):
                os.makedirs(backup_dir)
            
            self.export_to_markdown(chat_conclusion_text, file_name=backup_file)
            
            # 标记完成并保存进度
            self.mark_paper_completed(paper.path, self.merged_csv_file, progress)
            
            return True
            
        except Exception as e:
            print(f"❌ 处理论文时出错: {e}")
            return False

    def append_to_merged_csv(self, csv_content):
        """将CSV内容追加到合并文件中"""
        try:
            lines = csv_content.strip().split('\n')
            if len(lines) < 2:
                print("⚠️  CSV内容格式不正确，跳过")
                return
            
            header_line = lines[0]
            data_line = lines[1]
            
            # 如果是第一次写入，写入表头
            if not self.csv_header_written:
                with open(self.merged_csv_file, 'w', encoding='utf-8') as f:
                    f.write(header_line + '\n')
                self.csv_header_written = True
                print("📋 CSV表头已写入")
            
            # 追加数据行（跳过表头）
            with open(self.merged_csv_file, 'a', encoding='utf-8') as f:
                f.write(data_line + '\n')
            
            print(f"📝 数据已追加到合并文件")
            
        except Exception as e:
            print(f"❌ 追加CSV内容失败: {e}")

    def chat_conclusion(self, text, conclusion_prompt_token=800, truncation_strategy="balanced"):
        """结构化总结论文"""
        # 确保API配置正确
        openai.api_key = self.chat_api_list[self.cur_api]
        
        self.cur_api += 1
        self.cur_api = 0 if self.cur_api >= len(self.chat_api_list) - 1 else self.cur_api
        
        text_token = self.token_manager.count_tokens(text)
        print(f"原始文本token数: {text_token}")
        
        # 使用智能截断
        processed_text = self.token_manager.smart_truncate(
            text, 
            reserved_tokens=conclusion_prompt_token, 
            strategy=truncation_strategy
        )
        processed_token = self.token_manager.count_tokens(processed_text)
        print(f"处理后文本token数: {processed_token}, 策略: {truncation_strategy}")
        
        return self._single_call_conclusion(processed_text)
    
    def _single_call_conclusion(self, text):
        """单次LLM调用进行结构化总结"""
        messages = [
            {"role": "system",
             "content": f"You are a research expert specializing in Vision Language Action (VLA) models and resource-constrained AI systems. Your expertise focuses on analyzing data bottlenecks and computational bottlenecks in VLA models. You are conducting a comprehensive survey on 'Resource-Constrained Vision Language Action Models' in the field of [{self.key_word}]."},
            {"role": "assistant",
             "content": "I'll analyze this VLA-related paper with special attention to resource constraints, data bottlenecks, and computational bottlenecks. Here's the complete paper content: " + text},
            {"role": "user", "content": """
Please analyze this paper focusing on Vision Language Action (VLA) models and resource constraints. Output results in CSV format with exactly two lines: header line and data line.

Use these headers (do not modify):
论文标题,作者,发表年份,VLA架构类型,主要贡献/目标,数据瓶颈,算力瓶颈,资源约束类型,数据类型,数据规模,数据获取方法,数据瓶颈解决策略,模型规模,训练资源需求,推理效率,算力瓶颈解决策略,任务类型,实验环境,性能指标,资源-性能权衡,优点,缺点/局限,未来方向,创新点

Analysis Guidelines:
1. **VLA架构类型**: 分类为"端到端VLA"、"分层式VLA"、"混合架构"、"非VLA"之一
2. **数据瓶颈**: 严格使用"是"或"否"，判断是否存在数据稀缺/标注成本高/数据质量等问题
3. **算力瓶颈**: 严格使用"是"或"否"，判断是否存在训练/推理计算资源限制
4. **资源约束类型**: 从"数据稀缺/标注成本/计算资源/存储限制/实时性要求/内存限制"中选择，多个用"/"分隔
5. **数据规模**: 提供具体数量，如"10K样本"、"1M轨迹"、"100小时视频"等
6. **训练资源需求**: 具体描述如"8×V100 GPU，72小时"、"未提及"
7. **推理效率**: 包含FPS、延迟、内存占用等，如"30FPS，50ms延迟"
8. **性能指标**: 重点关注成功率、精度等与资源的权衡
9. **资源-性能权衡**: 描述在资源约束下的性能变化，如"数据减半时精度下降10%"

Special Focus Areas:
- 数据效率提升方法（数据增强、合成数据、少样本学习）
- 计算效率优化（模型压缩、知识蒸馏、高效架构）
- 多模态融合的资源开销
- 实时推理的资源约束
- 具身智能中的资源限制

Output Requirements:
1. Use Chinese for descriptions, English for technical terms/model names/proper nouns
2. Use "未提及" for missing information
3. Escape commas in fields with double quotes
4. Provide quantitative data when available
5. Focus on resource-related innovations and constraints
"""},
        ]

        try:
            if hasattr(openai, 'api_type') and openai.api_type == 'azure':
                response = openai.ChatCompletion.create(
                    engine=self.chatgpt_model,
                    messages=messages,
                    temperature=0.1,
                    max_tokens=2000
                )
            else:
                response = openai.ChatCompletion.create(
                    model=self.chatgpt_model,
                    messages=messages,
                    temperature=0.1,
                    max_tokens=2000
                )
                
            result = ''
            for choice in response.choices:
                result += choice.message.content
            
            print(f"Token使用情况 - 输入: {response.usage.prompt_tokens}, 输出: {response.usage.completion_tokens}, 总计: {response.usage.total_tokens}")
            return result
            
        except Exception as api_error:
            print(f"API调用错误详情: {api_error}")
            raise api_error

    def export_to_markdown(self, text, file_name, mode='w'):
        """导出到markdown文件"""
        with open(file_name, mode, encoding="utf-8") as f:
            f.write(text)


class TokenManager:
    """智能Token管理器"""
    
    def __init__(self, max_token_num=4096, model="gpt-3.5-turbo"):
        self.max_token_num = max_token_num
        self.encoding = tiktoken.get_encoding("gpt2")
        self.model = model
        
    def count_tokens(self, text):
        """计算文本的token数量"""
        return len(self.encoding.encode(text))
    
    def smart_truncate(self, text, reserved_tokens=1000, strategy="balanced"):
        """智能截断文本"""
        text_tokens = self.count_tokens(text)
        max_content_tokens = self.max_token_num - reserved_tokens
        
        if text_tokens <= max_content_tokens:
            return text
        
        if strategy == "front":
            return self._truncate_front(text, max_content_tokens)
        elif strategy == "balanced":
            return self._truncate_balanced(text, max_content_tokens)
        elif strategy == "sections":
            return self._truncate_sections_priority(text, max_content_tokens)
        else:
            return self._truncate_balanced(text, max_content_tokens)
    
    def _truncate_front(self, text, max_tokens):
        """只保留前半部分"""
        tokens = self.encoding.encode(text)
        if len(tokens) > max_tokens:
            truncated_tokens = tokens[:max_tokens]
            truncated_text = self.encoding.decode(truncated_tokens)
            return self._clean_truncation(truncated_text)
        return text
    
    def _truncate_balanced(self, text, max_tokens):
        """平衡截断：保留开头和结尾"""
        front_ratio = 0.4
        back_ratio = 0.4
        
        tokens = self.encoding.encode(text)
        if len(tokens) <= max_tokens:
            return text
            
        front_tokens = int(max_tokens * front_ratio)
        back_tokens = int(max_tokens * back_ratio)
        
        front_part = self.encoding.decode(tokens[:front_tokens])
        back_part = self.encoding.decode(tokens[-back_tokens:])
        
        separator = "\n\n[...内容因长度限制有所省略...]\n\n"
        combined = front_part + separator + back_part
        
        if self.count_tokens(combined) > max_tokens:
            separator_tokens = self.count_tokens(separator)
            available_tokens = max_tokens - separator_tokens
            front_tokens = int(available_tokens * 0.5)
            back_tokens = available_tokens - front_tokens
            
            front_part = self.encoding.decode(tokens[:front_tokens])
            back_part = self.encoding.decode(tokens[-back_tokens:])
            combined = front_part + separator + back_part
        
        return self._clean_truncation(combined)
    
    def _truncate_sections_priority(self, text, max_tokens):
        """章节优先截断：优先保留重要章节的完整内容"""
        # 定义章节重要性优先级（从高到低）
        priority_sections = [
            'Title:', 'Paper_info:', 'Abstract:', 
            'Introduction:', 'Method:', 'Methods:', 'Methodology:', 'Approach:', 'Approaches:',
            'Results:', 'Experimental Results:', 'Findings:', 
            'Conclusion:', 'Discussion:', 'Results and Discussion:',
            'Related Work:', 'Background:', 'Preliminary:', 'Problem Formulation:',
            'Experiments:', 'Experiment:', 'Evaluation:', 'Experiment Settings:',
            'References:'
        ]
        
        # 按章节分割文本
        sections = {}
        current_section = "Header"
        current_content = ""
        
        lines = text.split('\n')
        for line in lines:
            # 检查是否是新章节
            is_new_section = False
            for section_name in priority_sections:
                if line.strip().startswith(section_name):
                    # 保存当前章节
                    if current_content.strip():
                        sections[current_section] = current_content.strip()
                    # 开始新章节
                    current_section = section_name.rstrip(':')
                    current_content = line + '\n'
                    is_new_section = True
                    break
            
            if not is_new_section:
                current_content += line + '\n'
        
        # 保存最后一个章节
        if current_content.strip():
            sections[current_section] = current_content.strip()
        
        # 按优先级逐个添加章节
        result_text = ""
        used_tokens = 0
        
        for section_name in priority_sections:
            section_key = section_name.rstrip(':')
            if section_key in sections:
                section_content = sections[section_key]
                section_tokens = self.count_tokens(section_content)
                
                if used_tokens + section_tokens <= max_tokens:
                    result_text += section_content + '\n\n'
                    used_tokens += section_tokens
                else:
                    # 如果章节太长，尝试截断该章节
                    remaining_tokens = max_tokens - used_tokens
                    if remaining_tokens > 100:  # 至少保留100个token
                        truncated_section = self._truncate_front(section_content, remaining_tokens)
                        result_text += truncated_section + '\n\n[...该章节因长度限制被截断...]\n\n'
                    break
        
        # 如果还有空间，添加其他未处理的章节
        for section_key, section_content in sections.items():
            if section_key + ':' not in priority_sections:
                section_tokens = self.count_tokens(section_content)
                if used_tokens + section_tokens <= max_tokens:
                    result_text += section_content + '\n\n'
                    used_tokens += section_tokens
                else:
                    break
        
        return self._clean_truncation(result_text)
    
    def _clean_truncation(self, text):
        """清理截断后的文本"""
        sentences = text.split('.')
        if len(sentences) > 1 and sentences[-1].strip() and len(sentences[-1]) < 50:
            text = '.'.join(sentences[:-1]) + '.'
        return text.strip()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf_path", type=str, default=r'demo.pdf', help="PDF文件路径或包含PDF文件的文件夹路径")
    parser.add_argument("--key_word", type=str, default='reinforcement learning', help="研究领域关键词")
    parser.add_argument("--file_format", type=str, default='csv', help="导出的文件格式 (csv)")
    parser.add_argument("--language", type=str, default='zh', help="输出语言 (zh/en)")
    parser.add_argument("--truncation_strategy", type=str, default="sections", 
                        choices=['front', 'balanced', 'sections'],
                        help="长论文处理策略: front(前半部分) / balanced(平衡保留) / sections(章节优先)")
    parser.add_argument("--max_tokens", type=int, default=4096, 
                        help="最大token数限制")
    parser.add_argument("--resume", action="store_true", 
                        help="从上次中断处继续处理")

    args = parser.parse_args()
    
    print(f"=== ChatPaper 本地PDF总结工具 ===")
    print(f"PDF路径: {args.pdf_path}")
    print(f"研究领域: {args.key_word}")
    print(f"处理策略: {args.truncation_strategy}")
    print(f"最大tokens: {args.max_tokens}")
    print(f"断点续传: {'启用' if args.resume else '禁用'}")
    
    reader = Reader(key_word=args.key_word, args=args)
    reader.max_token_num = args.max_tokens
    reader.token_manager.max_token_num = args.max_tokens
    
    # 收集PDF文件路径，但不预处理
    pdf_paths = []
    if args.pdf_path.endswith(".pdf"):
        pdf_paths.append(args.pdf_path)
    else:
        for root, dirs, files in os.walk(args.pdf_path):
            print("root:", root, "dirs:", dirs, 'files:', files)
            for filename in files:
                if filename.endswith(".pdf"):
                    pdf_paths.append(os.path.join(root, filename))
    
    print(f"------------------找到PDF文件数: {len(pdf_paths)}------------------")
    
    # 显示进度信息
    if args.resume:
        progress = reader.load_progress()
        completed_count = sum(1 for p in progress.values() if p.get('status') == 'completed')
        print(f"已完成论文数: {completed_count}")
    
    [print(f"{pdf_index + 1}. {pdf_path.split('/')[-1]}") for pdf_index, pdf_path in enumerate(pdf_paths)]
    
    if pdf_paths:
        # 逐篇预处理+总结
        reader.summary_with_chat(pdf_paths, truncation_strategy=args.truncation_strategy)
        print("\n=== 处理完成 ===")
    else:
        print("未找到PDF文件！")
