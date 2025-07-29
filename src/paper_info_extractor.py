#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
论文基础信息本地提取器
"""
import re
import fitz
from typing import Dict, List, Optional, Tuple
import datetime
from dataclasses import dataclass

@dataclass
class PaperInfo:
    title: str
    authors: str
    year: str
    abstract: str
    keywords: List[str]
    venue: str
    doi: str
    arxiv_id: Optional[str] = None # Added arxiv_id

class PaperInfoExtractor:
    def __init__(self):
        self.author_separators = [',', '，', 'and', '&', ';', '；']
        self.year_patterns = [r'(\d{4})', r'20[12]\d']
        self.institution_keywords = [
            'university', 'institute', 'laboratory', 'lab', 'research',
            'center', 'centre', 'college', 'school', 'academy',
            '大学', '学院', '研究所', '实验室', '中心',
            'dept', 'department', 'faculty', 'division', 'group', 'team',
            'ai2robotics', 'nvidia', 'google', 'microsoft', 'meta', 'amazon',
            'tsinghua university', 'peking university', 'georgia institute of technology',
            'chinese university of hong kong', 'state key laboratory', 'beijing academy of artificial intelligence'
        ]
        self.venue_patterns = [
            # arXiv预印本
            r'arXiv preprint',
            # 会议论文集
            r'Proceedings of\s+[\w\s]+',
            r'In Proceedings of\s+[\w\s]+',
            # IEEE会议
            r'IEEE.*?Conference',
            r'IEEE.*?Workshop',
            r'IEEE.*?Symposium',
            # ACM会议
            r'ACM.*?Conference',
            r'ACM.*?Workshop',
            # 顶级AI/ML会议 - 严格匹配
            r'\b(ICLR|ICML|NeurIPS|NIPS|CVPR|ICCV|ECCV|AAAI|IJCAI)\s+20\d{2}\b',
            r'\b(ICRA|IROS|RSS|CoRL)\s+20\d{2}\b',  # 机器人会议
            # 期刊
            r'\b(Nature|Science|Cell)\b',
            r'Nature\s+\w+',  # Nature子刊
            r'Science\s+\w+',  # Science子刊
            # 其他常见会议/期刊缩写
            r'\b(SIGRAPH|SIGGRAPH|CHI|UIST|CSCW)\b',
            # 期刊全名模式
            r'Journal of\s+[\w\s]+',
            r'IEEE Transactions on\s+[\w\s]+',
            r'ACM Transactions on\s+[\w\s]+',
        ]
    
    def extract_paper_info(self, pdf_path: str) -> PaperInfo:
        print(f"[DEBUG] Entering extract_paper_info for {pdf_path}")
        try:
            pdf = fitz.open(pdf_path)
            first_page_text = pdf[0].get_text()
            
            title = self._extract_title(pdf)
            authors = self._extract_authors(first_page_text, title)
            year = self._extract_year(first_page_text, pdf_path)
            abstract = self._extract_abstract(first_page_text)
            keywords = self._extract_keywords(first_page_text)
            venue = self._extract_venue(first_page_text)
            doi = self._extract_doi(first_page_text)
            arxiv_id = self._extract_arxiv_id(first_page_text) # Extract arXiv ID
            
            pdf.close()
            print(f"[DEBUG] Exiting extract_paper_info for {pdf_path}")
            return PaperInfo(title, authors, year, abstract, keywords, venue, doi, arxiv_id)
            
        except Exception as e:
            print(f"信息提取失败 {pdf_path}: {e}")
            return PaperInfo("", "", "", "", [], "", "", None)

    def _extract_title(self, doc) -> str:
        print("[DEBUG] Entering _extract_title")
        try:
            first_page = doc[0]
            text_dict = first_page.get_text("dict")
            
            font_data = []
            for block in text_dict["blocks"]:
                if block["type"] == 0:
                    for line in block["lines"]:
                        line_text = "".join(span["text"] for span in line["spans"]).strip()
                        if line_text and "arxiv:" not in line_text.lower() and len(line_text) > 5:
                            max_font_size = max(span["size"] for span in line["spans"])
                            font_data.append({
                                'text': line_text,
                                'font_size': max_font_size,
                                'y_pos': line["bbox"][1]
                            })
            
            if not font_data:
                print("[DEBUG] _extract_title: No font data found.")
                return ""

            font_data.sort(key=lambda x: (-x['font_size'], x['y_pos']))
            
            if not font_data:
                print("[DEBUG] _extract_title: No sorted font data.")
                return ""
            
            title_font_size = font_data[0]['font_size']
            # 标题候选者是字体大小与最大字体大小相近的文本
            title_candidates = [item for item in font_data if abs(item['font_size'] - title_font_size) < 1.0]
            
            # 过滤掉明显不是标题的候选
            title_candidates = [cand for cand in title_candidates if not any(kw in cand['text'].lower() for kw in ['abstract', 'introduction'])]

            if not title_candidates: 
                print("[DEBUG] _extract_title: No title candidates after filtering.")
                return ""

            # 按Y坐标排序，确保标题行按正确顺序连接
            title_candidates.sort(key=lambda x: x['y_pos'])
            
            # 合并多行标题
            title = " ".join(item['text'] for item in title_candidates)
            cleaned_title = self._clean_title(title)
            print(f"[DEBUG] Exiting _extract_title with: {cleaned_title}")
            return cleaned_title

        except Exception as e:
            print(f"[DEBUG] Error in _extract_title: {e}")
            return ""

    def _extract_authors(self, first_page_text: str, title: str) -> str:
        print("[DEBUG] Entering _extract_authors")
        lines = [line.strip() for line in first_page_text.split('\n') if line.strip()]
        
        if not title:
            print("[DEBUG] _extract_authors: No title provided.")
            return "未提及"

        try:
            title_end_index = -1
            title_words = set(self._clean_title(title).lower().split())

            for i, line in enumerate(lines):
                line_words = set(line.lower().split())
                # 标题可能跨越多行，找到最后一行
                if len(title_words & line_words) / len(title_words) > 0.5:
                    title_end_index = i

            if title_end_index == -1:
                print("[DEBUG] _extract_authors: Title end index not found.")
                return "未提及"

            author_lines = []
            # 在标题结束后的几行内寻找作者
            for i in range(title_end_index + 1, min(title_end_index + 8, len(lines))):
                line = lines[i]
                if "abstract" in line.lower() or "introduction" in line.lower():
                    print(f"[DEBUG] _extract_authors: Found abstract/introduction, stopping at line {i}")
                    break
                if self._is_likely_author_line(line):
                    author_lines.append(line)
            
            if author_lines:
                extracted_names = self._extract_author_names(" ".join(author_lines))
                print(f"[DEBUG] Exiting _extract_authors with: {extracted_names}")
                return extracted_names

        except Exception as e:
            print(f"[DEBUG] Error in _extract_authors: {e}")
            pass

        print("[DEBUG] Exiting _extract_authors with: 未提及")
        return "未提及"

    def _is_likely_author_line(self, line: str) -> bool:
        # print(f"[DEBUG] Entering _is_likely_author_line for line: {line[:50]}...")
        if not line or len(line) < 5 or len(line) > 400: return False
        
        line_lower = line.lower()
        # 排除明显的非作者行
        exclude_keywords = [
            'abstract', 'introduction', 'email:', 'code:', 'http',
            'figure', 'table', 'acknowledgments', 'references',
            'appendix', 'supplementary material', 'contact',
            'copyright', 'license', 'disclaimer'
        ]
        if any(kw in line_lower for kw in exclude_keywords): 
            # print(f"[DEBUG] _is_likely_author_line: Excluded by keyword: {line_lower[:50]}...")
            return False
        
        # 排除机构信息行
        if self._is_affiliation_line(line): 
            # print(f"[DEBUG] _is_likely_author_line: Excluded by affiliation: {line_lower[:50]}...")
            return False

        # 包含多个由逗号或'and'分隔的姓名模式
        name_pattern = r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?\b' # 匹配 Firstname Lastname
        names_found = re.findall(name_pattern, line)
        if len(names_found) >= 1 and ((';' in line or ',' in line or 'and' in line_lower) and len(re.split(r',|and', line)) > 1):
            # print(f"[DEBUG] _is_likely_author_line: Matched by name pattern and separators: {line_lower[:50]}...")
            return True

        # 包含多个大写单词（可能是名字缩写或姓氏）
        capital_words = re.findall(r'\b[A-Z][a-z]*\b', line)
        if len(capital_words) >= 2:
            # print(f"[DEBUG] _is_likely_author_line: Matched by multiple capital words: {line_lower[:50]}...")
            return True

        # 包含上标
        if re.search(r'[\d\*\u2020\u2021]', line):
            # print(f"[DEBUG] _is_likely_author_line: Matched by superscript: {line_lower[:50]}...")
            return True

        # print(f"[DEBUG] _is_likely_author_line: No match for line: {line_lower[:50]}...")
        return False

    def _extract_author_names(self, author_text: str) -> str:
        print(f"[DEBUG] Entering _extract_author_names for text: {author_text[:100]}...")
        
        # 先移除明显的标题部分
        title_indicators = ['survey', 'analysis', 'model', 'system', 'architecture', 'framework', 'robotic', 'manipulation', 'vision', 'language', 'action']
        
        # 查找标题结束和作者开始的位置
        author_start_idx = 0
        for indicator in title_indicators:
            pattern = rf'\b{re.escape(indicator)}\b'
            match = re.search(pattern, author_text, re.IGNORECASE)
            if match:
                # 从标题关键词后开始寻找作者
                potential_start = match.end()
                # 找到后面的第一个大写字母开头的可能作者名
                post_match = author_text[potential_start:]
                author_match = re.search(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]*\.?)*\s+[A-Z][a-z]+', post_match)
                if author_match:
                    author_start_idx = potential_start + author_match.start()
                    break
        
        if author_start_idx > 0:
            author_text = author_text[author_start_idx:]
            print(f"[DEBUG] Trimmed title part, new text: {author_text[:100]}...")
        
        # 移除括号内容（通常是机构缩写或邮箱）
        author_text = re.sub(r'\([^)]*\)', '', author_text)
        
        # 保留带星号等符号的作者名，但在后续处理中清理符号
        original_text = author_text
        
        # 移除邮箱地址
        author_text = re.sub(r'\S*@\S*\s?', '', author_text)

        # 移除明显的机构关键词
        for kw in self.institution_keywords:
            author_text = re.sub(r'\b' + re.escape(kw) + r'\b', '', author_text, flags=re.IGNORECASE)

        # 清理多余的空格
        author_text = re.sub(r'\s+', ' ', author_text).strip()
        
        print(f"[DEBUG] Cleaned author text: {author_text[:100]}...")

        # 智能分割作者姓名
        authors_raw = []
        
        # 首先尝试用分号分割（最可靠）
        if ';' in author_text:
            authors_raw = re.split(r'\s*;\s*', author_text)
        # 其次尝试用逗号分割，但要小心处理
        elif ',' in author_text:
            # 使用更智能的逗号分割，考虑名字中的逗号
            parts = re.split(r',\s*', author_text)
            authors_raw = []
            i = 0
            while i < len(parts):
                part = parts[i].strip()
                # 检查这部分是否看起来像完整的名字
                if re.match(r'^[A-Z][a-z]*(?:\s+[A-Z][a-z]*)*\s*[*†‡\d]*$', part):
                    authors_raw.append(part)
                elif i + 1 < len(parts):
                    # 可能是 "Last, First" 格式，尝试合并下一部分
                    next_part = parts[i + 1].strip()
                    if re.match(r'^[A-Z][a-z]*(?:\s+[A-Z]\.?)*$', next_part):
                        authors_raw.append(f"{next_part} {part}")
                        i += 1  # 跳过下一部分
                    else:
                        authors_raw.append(part)
                else:
                    authors_raw.append(part)
                i += 1
        # 最后尝试用"and"分割
        else:
            authors_raw = re.split(r'\s+and\s+', author_text)
        
        # 如果分割结果不理想，尝试按空格模式识别
        if len(authors_raw) == 1 and len(authors_raw[0]) > 50:
            # 可能是多个作者连在一起，尝试用模式匹配分离
            text = authors_raw[0]
            # 查找所有可能的作者名模式
            name_pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]*\.?)*\s+[A-Z][a-z]+)(?:\d+[*†‡]*)?'
            potential_names = re.findall(name_pattern, text)
            if len(potential_names) > 1:
                authors_raw = potential_names
        
        # 处理被错误连接的多个作者（如 "Shangke Lyu2 Ying Peng2 Donglin Wang2"）
        expanded_authors = []
        for author in authors_raw:
            author = author.strip()
            if not author:
                continue
            
            # 检查是否包含多个连续的姓名模式
            multiple_names_pattern = r'\b([A-Z][a-z]+\s+[A-Z][a-z]+)(?:\d+[*†‡]*\s*)+([A-Z][a-z]+\s+[A-Z][a-z]+)'
            if re.search(multiple_names_pattern, author):
                # 使用更精确的模式分离多个姓名
                names = re.findall(r'\b([A-Z][a-z]+\s+[A-Z][a-z]+)(?:\d+[*†‡]*\s*)*', author)
                if len(names) > 1:
                    expanded_authors.extend(names)
                    continue
            
            expanded_authors.append(author)
        
        authors_raw = expanded_authors
        
        cleaned_authors = []
        for author in authors_raw:
            author = author.strip()
            if not author:
                continue
                
            print(f"[DEBUG] Processing author candidate: '{author}'")
            
            # 移除数字上标和特殊符号，但保持名字结构
            clean_author = re.sub(r'[\d*†‡∗]+', '', author).strip()
            
            # 检查长度和基本格式
            if len(clean_author) < 3 or len(clean_author) > 40:
                print(f"[DEBUG] Rejected author (length): {author}")
                continue
            
            # 特殊处理：如果包含明显的标题词汇，尝试从中提取人名
            if any(word in clean_author.lower() for word in title_indicators):
                print(f"[DEBUG] Found title keywords in: '{clean_author}'")
                # 在包含标题的文本中查找人名
                name_matches = re.findall(r'\b([A-Z][a-z]+\s+[A-Z][a-z]+)\b', clean_author)
                valid_names = []
                for name in name_matches:
                    if not any(word in name.lower() for word in title_indicators):
                        valid_names.append(name)
                
                if valid_names:
                    clean_author = valid_names[0]
                    print(f"[DEBUG] Extracted name from title-mixed text: {clean_author}")
                else:
                    print(f"[DEBUG] No valid names found in title-mixed text")
                    continue
            
            # 验证是否是有效的人名格式
            name_patterns = [
                r'^[A-Z][a-z]+\s+[A-Z][a-z]+$',  # Firstname Lastname
                r'^[A-Z][a-z]+\s+[A-Z]\.\s*[A-Z][a-z]+$',  # Firstname M. Lastname
                r'^[A-Z]\.\s*[A-Z][a-z]+$',  # F. Lastname
                r'^[A-Z][a-z]+\s+[A-Z]\.$',  # Firstname L.
                r'^[A-Z][a-z]+\s+[A-Z][a-z]+\s+[A-Z][a-z]+$',  # Three names
                r'^[A-Z][a-z]+\s+[A-Z]+\s+[A-Z][a-z]+$',  # 包含中间名缩写
                r'^[A-Z][a-z]+-[A-Z][a-z]+\s+[A-Z][a-z]+$',  # 连字符姓名：Jia-Feng Cai
                r'^[A-Z][a-z]+\s+[A-Z][a-z]+-[A-Z][a-z]+$',  # 连字符姓：John Smith-Jones
                r'^[A-Z][a-z]+$',  # 单个名字（在某些情况下）
            ]
            
            is_valid_name = any(re.match(pattern, clean_author) for pattern in name_patterns)
            
            # 额外检查：确保不包含明显的非人名词汇
            invalid_words = [
                # 机构相关
                'university', 'institute', 'department', 'laboratory', 'center', 'school', 'college', 'corp', 'inc', 'ltd', 'group', 'team', 'intelligence', 'berkeley', 'stanford', 'mit', 'research', 'technologies', 'lab',
                # 地名
                'moscow', 'russia', 'china', 'beijing', 'shanghai', 'california', 'texas', 'london', 'paris', 'tokyo', 'seoul', 'singapore',
                # 技术词汇
                'dataset', 'chat', 'model', 'system', 'framework', 'algorithm', 'science', 'engineering', 'computer', 'artificial', 'machine', 'learning', 'vision', 'language', 'action', 'robot', 'robotics',
                # 期刊/会议
                'proceedings', 'conference', 'workshop', 'journal', 'nature', 'science', 'ieee', 'acm', 'cvpr', 'iccv', 'nips', 'icml', 'iclr',
                # 其他
                'applications', 'abstract', 'paper', 'study', 'analysis', 'method', 'approach'
            ]
            contains_invalid = any(word in clean_author.lower() for word in invalid_words)
            
            if is_valid_name and not contains_invalid:
                # 再次检查是否包含机构关键词
                if not any(kw in clean_author.lower() for kw in self.institution_keywords):
                    cleaned_authors.append(clean_author)
                    print(f"[DEBUG] Added valid author: {clean_author}")
                else:
                    print(f"[DEBUG] Rejected author (institution keyword): {clean_author}")
            else:
                print(f"[DEBUG] Rejected author (invalid pattern): {clean_author}")

        # 过滤掉重复的姓名
        cleaned_authors = list(dict.fromkeys(cleaned_authors)) # 保持顺序的去重

        if not cleaned_authors:
            print("[DEBUG] _extract_author_names: No cleaned authors found.")
            return "未提及"

        # 格式化输出
        if len(cleaned_authors) == 1:
            result = cleaned_authors[0]
        elif len(cleaned_authors) > 5:
            result = ", ".join(cleaned_authors[:5]) + " et al."
        else:
            result = ", ".join(cleaned_authors)
        
        print(f"[DEBUG] Exiting _extract_author_names with: {result}")
        return result

    def _extract_year(self, first_page_text: str, pdf_path: str) -> str:
        print("[DEBUG] Entering _extract_year")
        current_year = datetime.datetime.now().year
        
        # 先从文件路径中提取年份
        path_years = []
        for match in re.findall(r'(20\d{2})', pdf_path):
            try:
                year = int(match)
                if 1990 <= year <= current_year + 1:
                    path_years.append(year)
            except ValueError:
                continue
        
        # 从文本中提取年份
        text_years = []
        for pattern in self.year_patterns:
            for match in re.findall(pattern, first_page_text):
                try:
                    year = int(match)
                    if 1990 <= year <= current_year + 1:
                        text_years.append(year)
                except ValueError:
                    continue
        
        # 优先选择路径中最新的年份（通常更准确）
        if path_years:
            selected_year = max(path_years)
            print(f"[DEBUG] Exiting _extract_year with: {selected_year} (from path)")
            return str(selected_year)
        
        # 如果路径中没有，选择文本中最新的年份
        if text_years:
            selected_year = max(text_years)
            print(f"[DEBUG] Exiting _extract_year with: {selected_year} (from text)")
            return str(selected_year)
        
        print("[DEBUG] Exiting _extract_year with: 未提及")
        return "未提及"

    def _extract_abstract(self, first_page_text: str) -> str:
        print("[DEBUG] Entering _extract_abstract")
        # 使用更安全的正则表达式，避免灾难性回溯
        abstract_pattern = r'\b(Abstract|ABSTRACT|\u6458\u8981)\b[\s.:]*(.*?)(?=\n\s*\n|\b(?:Introduction|Keywords|1\.?\s+Introduction)|\Z)'
        match = re.search(abstract_pattern, first_page_text, re.DOTALL | re.IGNORECASE)
        if match:
            abstract = match.group(2).strip()
            cleaned_abstract = re.sub(r'\s+', ' ', abstract.replace('\n', ' ')).strip()
            print(f"[DEBUG] Exiting _extract_abstract with: {cleaned_abstract[:50]}...")
            return cleaned_abstract
        print("[DEBUG] Exiting _extract_abstract with: \"\"")
        return ""

    def _extract_keywords(self, first_page_text: str) -> List[str]:
        print("[DEBUG] Entering _extract_keywords")
        match = re.search(r'\b(Keywords|KEYWORDS|\u5173\u952e\u8bcd)[\s:.]*(.*)', first_page_text, re.IGNORECASE)
        if match:
            line = match.group(2)
            end_match = re.search(r'(\n|\b(Introduction|1\\.))', line, re.IGNORECASE)
            if end_match: line = line[:end_match.start()]
            kws = re.split(r'[,;\uFF0C\uFF1B]', line)
            cleaned_kws = [kw.strip() for kw in kws if 2 < len(kw.strip()) < 50][:10]
            print(f"[DEBUG] Exiting _extract_keywords with: {cleaned_kws}")
            return cleaned_kws
        print("[DEBUG] Exiting _extract_keywords with: []")
        return []

    def _extract_venue(self, first_page_text: str) -> str:
        print("[DEBUG] Entering _extract_venue")
        
        # 首先在前几行查找，因为期刊/会议信息通常在论文开头
        lines = first_page_text.split('\n')
        search_text = '\n'.join(lines[:20])  # 只搜索前20行
        
        # 按优先级搜索不同类型的venue
        for pattern in self.venue_patterns:
            match = re.search(pattern, search_text, re.IGNORECASE)
            if match: 
                venue = match.group(0).strip()
                # 清理venue字符串
                venue = self._clean_venue(venue)
                
                # 验证venue是否合理（不是作者名或其他误识别）
                if venue and len(venue) > 2 and self._is_valid_venue(venue):
                    print(f"[DEBUG] Exiting _extract_venue with: {venue}")
                    return venue
        
        # 如果前面没找到，在全文中搜索关键模式
        key_patterns = [
            r'\b(ICLR|ICML|NeurIPS|NIPS|CVPR|ICCV|ECCV|AAAI|IJCAI)\s+20\d{2}\b',
            r'\b(ICRA|IROS|RSS|CoRL)\s+20\d{2}\b',
            r'\bNature\s+(?:Communications|Machine Intelligence|Robotics)\b',
            r'\bScience\s+(?:Robotics|Advances)\b',
        ]
        
        for pattern in key_patterns:
            match = re.search(pattern, first_page_text, re.IGNORECASE)
            if match:
                venue = match.group(0).strip()
                print(f"[DEBUG] Exiting _extract_venue with: {venue}")
                return venue
                
        print("[DEBUG] Exiting _extract_venue with: \"\"")
        return ""
    
    def _clean_venue(self, venue: str) -> str:
        """清理venue字符串"""
        # 移除多余的空格
        venue = re.sub(r'\s+', ' ', venue).strip()
        # 移除末尾的标点符号
        venue = re.sub(r'[.,;:]+$', '', venue)
        return venue
    
    def _is_valid_venue(self, venue: str) -> bool:
        """验证venue是否是有效的期刊/会议名"""
        venue_lower = venue.lower()
        
        # 检查是否是明显的作者名格式 (如 "Ding12", "Smith1" 等)
        if re.match(r'^[A-Z][a-z]+\d+[*†‡]*$', venue):
            return False
        
        # 检查是否是纯数字或太短
        if venue.isdigit() or len(venue) < 3:
            return False
        
        # 检查是否包含明显的作者名模式
        author_patterns = [
            r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b',  # Firstname Lastname
            r'\b[A-Z][a-z]+\d+\b',  # Name with number
        ]
        for pattern in author_patterns:
            if re.search(pattern, venue):
                return False
        
        # 检查是否包含期刊/会议的常见词汇
        valid_keywords = [
            'conference', 'workshop', 'symposium', 'journal', 'transactions',
            'proceedings', 'arxiv', 'preprint', 
            'ieee', 'acm', 'iclr', 'icml', 'neurips', 'nips', 'cvpr', 'iccv',
            'eccv', 'aaai', 'ijcai', 'icra', 'iros', 'rss', 'corl'
        ]
        
        # 特殊处理一些期刊名：只有在特定上下文中才认为有效
        context_dependent = ['nature', 'science', 'cell']
        
        # 首先检查是否包含明确的期刊/会议词汇
        if any(keyword in venue_lower for keyword in valid_keywords):
            return True
        
        # 对于上下文相关的词汇，需要更严格的验证
        if any(keyword in venue_lower for keyword in context_dependent):
            # 检查是否在期刊/会议的上下文中
            if len(venue) > 10 or any(word in venue_lower for word in ['communications', 'robotics', 'advances', 'machine']):
                return True
            else:
                return False
        
        # 如果不包含明显的期刊/会议词汇，但也不是明显的错误，可能是简短的会议名
        if len(venue) >= 4 and not venue.isdigit() and venue.isupper():
            return True
        
        return False

    def _extract_doi(self, text: str) -> str:
        print("[DEBUG] Entering _extract_doi")
        
        # DOI的多种格式模式
        doi_patterns = [
            # 标准DOI格式：10.xxxx/xxxxx
            r'\b(10\.\d{4,9}/[-._;()\w\[\]/:]+)\b',
            # 在URL中的DOI
            r'doi\.org/(10\.\d{4,9}/[-._;()\w\[\]/:]+)',
            r'dx\.doi\.org/(10\.\d{4,9}/[-._;()\w\[\]/:]+)',
            # DOI标签后的格式
            r'DOI\s*:?\s*(10\.\d{4,9}/[-._;()\w\[\]/:]+)',
            r'doi\s*:?\s*(10\.\d{4,9}/[-._;()\w\[\]/:]+)',
        ]
        
        for pattern in doi_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                doi = match.group(1)
                # 清理DOI末尾可能的标点符号
                doi = re.sub(r'[.,;)\]}]+$', '', doi)
                if self._is_valid_doi(doi):
                    print(f"[DEBUG] Exiting _extract_doi with: {doi}")
                    return doi
        
        print("[DEBUG] Exiting _extract_doi with: \"\"")
        return ""
    
    def _is_valid_doi(self, doi: str) -> bool:
        """验证DOI是否有效"""
        # 基本格式检查
        if not doi.startswith('10.'):
            return False
        
        # 长度检查
        if len(doi) < 7 or len(doi) > 200:
            return False
        
        # 必须包含斜杠
        if '/' not in doi:
            return False
        
        return True

    def _extract_arxiv_id(self, text: str) -> Optional[str]:
        print("[DEBUG] Entering _extract_arxiv_id")
        
        # arXiv ID的多种格式模式
        arxiv_patterns = [
            # 新格式：arXiv:YYMM.NNNNN[vN] (从2007年4月开始)
            r'arXiv:(\d{4}\.\d{4,5}(?:v\d+)?)\b',
            # 旧格式：arXiv:subject-class/YYMMnnn[vN] (2007年4月之前)
            r'arXiv:([a-z-]+/\d{7}(?:v\d+)?)\b',
            # 仅ID格式：YYMM.NNNNN[vN]
            r'\b(\d{4}\.\d{4,5}(?:v\d+)?)\b',
            # 在URL中的格式
            r'arxiv\.org/abs/(\d{4}\.\d{4,5}(?:v\d+)?)',
            r'arxiv\.org/abs/([a-z-]+/\d{7}(?:v\d+)?)',
            # 其他可能的变体
            r'arXiv\s*:\s*(\d{4}\.\d{4,5}(?:v\d+)?)',
            r'arxiv\s*:\s*(\d{4}\.\d{4,5}(?:v\d+)?)',
        ]
        
        for pattern in arxiv_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                arxiv_id = match.group(1)
                # 验证提取的ID是否合理
                if self._is_valid_arxiv_id(arxiv_id):
                    print(f"[DEBUG] Exiting _extract_arxiv_id with: {arxiv_id}")
                    return arxiv_id
        
        print("[DEBUG] Exiting _extract_arxiv_id with: None")
        return None
    
    def _is_valid_arxiv_id(self, arxiv_id: str) -> bool:
        """验证arXiv ID是否有效"""
        # 新格式验证：YYMM.NNNNN[vN]
        if re.match(r'^\d{4}\.\d{4,5}(?:v\d+)?$', arxiv_id):
            year_month = arxiv_id[:4]
            year = int(year_month[:2])
            month = int(year_month[2:])
            # 检查年月是否合理（假设从07年4月开始到当前）
            if 7 <= year <= 99 or 0 <= year <= 50:  # 2007-2099, 处理两位年份
                if 1 <= month <= 12:
                    return True
        
        # 旧格式验证：subject-class/YYMMnnn[vN]
        if re.match(r'^[a-z-]+/\d{7}(?:v\d+)?$', arxiv_id):
            return True
        
        # 对于其他格式，进行基本验证
        if len(arxiv_id) >= 6 and any(c.isdigit() for c in arxiv_id):
            return True
        
        return False

    def _clean_title(self, title: str) -> str:
        # print("[DEBUG] Entering _clean_title")
        title = re.sub(r'\s+', ' ', title.replace('\n', ' ')).strip()
        cleaned_title = re.sub(r'[\*\u2020\u2021]$', '', title).strip()
        # print(f"[DEBUG] Exiting _clean_title with: {cleaned_title}")
        return cleaned_title

    def _is_affiliation_line(self, line: str) -> bool:
        """判断是否为机构信息行"""
        line_lower = line.lower()
        # 检查是否包含机构关键词
        for keyword in self.institution_keywords:
            if keyword in line_lower:
                return True
        
        # 检查是否包含邮箱地址
        if re.search(r'\S+@\S+\.\S+', line):
            return True
        
        # 检查是否包含地址信息
        address_patterns = [
            r'\b\d+\s+[A-Za-z\s]+(?:street|st|avenue|ave|road|rd|drive|dr|blvd|boulevard)\b',
            r'\b[A-Z]{2}\s+\d{5}\b',  # 美国邮编
            r'\b\d{5}\s+[A-Z][a-z]+\b',  # 国际邮编格式
        ]
        for pattern in address_patterns:
            if re.search(pattern, line, re.IGNORECASE):
                return True
        
        return False

def enhance_paper_with_local_info(paper, extractor: PaperInfoExtractor) -> Dict[str, Optional[str]]:
    print(f"[DEBUG] Entering enhance_paper_with_local_info for {paper.path}")
    try:
        paper_info = extractor.extract_paper_info(paper.path)
        if not paper.title or len(paper.title) < 10:
            paper.title = paper_info.title
        
        result = {
            'extracted_title': paper_info.title,
            'extracted_authors': paper_info.authors,
            'extracted_year': paper_info.year,
            'extracted_abstract': paper_info.abstract,
            'extracted_venue': paper_info.venue,
            'extracted_doi': paper_info.doi,
            'extracted_arxiv_id': paper_info.arxiv_id, # Added arxiv_id
            'file_name': paper.path.split('/')[-1]
        }
        print(f"[DEBUG] Exiting enhance_paper_with_local_info for {paper.path}")
        return result
    except Exception as e:
        print(f"本地信息提取失败: {e}")
        return {
            'extracted_title': paper.title,
            'extracted_authors': '未提及',
            'extracted_year': '未提及',
            'extracted_abstract': '',
            'extracted_venue': '',
            'extracted_doi': '',
            'extracted_arxiv_id': None, # Added arxiv_id
            'file_name': paper.path.split('/')[-1]
        }