from typing import Optional
from model import Model
from translator.pdf_parser import PDFParser
from translator.writer import Writer
from utils import LOG

class PDFTranslator:
    def __init__(self, model: Model):
        self.model = model
        self.pdf_parser = PDFParser()
        self.writer = Writer()

    def translate_pdf(
        self, 
        pdf_file_path: str, 
        file_format: str = 'PDF', 
        source_language: str = '英文',
        target_language: str = '中文', 
        output_file_path: str = None, 
        pages: Optional[int] = None,
        translation_style: str = "default"
    ):
        """翻译PDF文件

        Args:
            pdf_file_path: PDF文件路径
            file_format: 输出文件格式
            source_language: 源语言
            target_language: 目标语言
            output_file_path: 输出文件路径
            pages: 翻译的页数
            translation_style: 翻译风格

        Returns:
            str: 翻译后的文件路径
        """
        self.book = self.pdf_parser.parse_pdf(pdf_file_path, pages)
        output_file = output_file_path or pdf_file_path.replace('.pdf', f'_translated.{file_format.lower()}')

        for page_idx, page in enumerate(self.book.pages):
            for content_idx, content in enumerate(page.contents):
                # 根据源语言和目标语言以及风格获取提示词
                style_prompt = self._get_style_prompt(source_language, target_language, translation_style)
                
                # 组合提示词和原文
                prompt = f"{style_prompt}\n\n原文：{content.original}"
                
                LOG.debug(prompt)
                translation, status = self.model.make_request(prompt)
                LOG.info(translation)
                
                # 更新内容
                self.book.pages[page_idx].contents[content_idx].set_translation(translation, status)

        # 保存翻译后的文件
        self.writer.save_translated_book(self.book, output_file, file_format)
        return output_file

    def _get_style_prompt(self, source_language: str, target_language: str, style: str) -> str:
        """
        获取特定语言和风格的提示词模板
        """
        # 针对源语言和目标语言组合的提示词
        combined_prompts = {
            ("英文", "中文"): {
                "default": f"请将以下英文文本翻译成中文，保持原文的意思和语气。",
                "novel": f"请将以下英文文本翻译成中文，采用小说写作风格，注重情节流畅性和人物刻画。",
                "news": f"请将以下英文文本翻译成中文，采用新闻写作风格，保持客观、准确、简洁。",
                "technical": f"请将以下英文文本翻译成中文，采用技术文档风格，保持专业性和准确性。",
                "literary": f"请将以下英文文本翻译成中文，采用文学写作风格，注重文采和意境。",
                "business": f"请将以下英文文本翻译成中文，采用商务写作风格，保持专业、正式、得体。",
                "academic": f"请将以下英文文本翻译成中文，采用学术写作风格，保持严谨性和专业性。",
                "casual": f"请将以下英文文本翻译成中文，采用口语化风格，保持自然、轻松、易懂。"
            },
            ("中文", "英文"): {
                "default": f"Please translate the following Chinese text into English, maintaining the original meaning and tone.",
                "novel": f"Please translate the following Chinese text into English, using a novel writing style that emphasizes plot flow and character development.",
                "news": f"Please translate the following Chinese text into English, using a journalistic style that maintains objectivity, accuracy, and conciseness.",
                "technical": f"Please translate the following Chinese text into English, using a technical documentation style that maintains professionalism and accuracy.",
                "literary": f"Please translate the following Chinese text into English, using a literary style that emphasizes artistic expression and imagery.",
                "business": f"Please translate the following Chinese text into English, using a business writing style that maintains professionalism and formality.",
                "academic": f"Please translate the following Chinese text into English, using an academic style that maintains rigor and scholarly tone.",
                "casual": f"Please translate the following Chinese text into English, using a casual style that is natural, relaxed, and easy to understand."
            }
        }

        # 获取特定语言组合的提示词
        lang_key = (source_language, target_language)
        if lang_key in combined_prompts:
            prompts = combined_prompts[lang_key]
            return prompts.get(style, prompts["default"])
        
        # 如果没有特定组合，返回通用提示词
        return f"请将以下{source_language}文本翻译成{target_language}，保持原文的意思和语气。"
