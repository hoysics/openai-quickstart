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
        target_language: str = '中文', 
        output_file_path: str = None, 
        pages: Optional[int] = None,
        translation_style: str = "default"
    ):
        self.book = self.pdf_parser.parse_pdf(pdf_file_path, pages)

        for page_idx, page in enumerate(self.book.pages):
            for content_idx, content in enumerate(page.contents):
                # Get style-specific prompt for the target language
                style_prompt = self._get_style_prompt(target_language, translation_style)
                
                # Combine style prompt with translation prompt
                prompt = f"{style_prompt}\n\n原文：{content.original}"
                
                LOG.debug(prompt)
                translation, status = self.model.make_request(prompt)
                LOG.info(translation)
                
                # Update the content in self.book.pages directly
                self.book.pages[page_idx].contents[content_idx].set_translation(translation, status)

        self.writer.save_translated_book(self.book, output_file_path, file_format)

    def _get_style_prompt(self, target_language: str, style: str) -> str:
        """
        Get the style-specific prompt template for the target language
        """
        style_prompts = {
            "中文": {
                "default": "请将以下文本翻译成中文，保持原文的意思和语气。",
                "novel": "请将以下文本翻译成中文，采用小说写作风格，注重情节流畅性和人物刻画。",
                "news": "请将以下文本翻译成中文，采用新闻写作风格，保持客观、准确、简洁。",
                "technical": "请将以下文本翻译成中文，采用技术文档风格，保持专业性和准确性。",
                "literary": "请将以下文本翻译成中文，采用文学写作风格，注重文采和意境。",
                "business": "请将以下文本翻译成中文，采用商务写作风格，保持专业、正式、得体。",
                "academic": "请将以下文本翻译成中文，采用学术写作风格，保持严谨性和专业性。",
                "casual": "请将以下文本翻译成中文，采用口语化风格，保持自然、轻松、易懂。"
            },
            "英语": {
                "default": "Please translate the following text into English, maintaining the original meaning and tone.",
                "novel": "Please translate the following text into English, using a novel writing style that emphasizes plot flow and character development.",
                "news": "Please translate the following text into English, using a journalistic style that maintains objectivity, accuracy, and conciseness.",
                "technical": "Please translate the following text into English, using a technical documentation style that maintains professionalism and accuracy.",
                "literary": "Please translate the following text into English, using a literary style that emphasizes artistic expression and imagery.",
                "business": "Please translate the following text into English, using a business writing style that maintains professionalism and formality.",
                "academic": "Please translate the following text into English, using an academic style that maintains rigor and scholarly tone.",
                "casual": "Please translate the following text into English, using a casual style that is natural, relaxed, and easy to understand."
            },
            "日语": {
                "default": "以下のテキストを日本語に翻訳してください。原文の意味と語調を保ってください。",
                "novel": "以下のテキストを日本語に翻訳してください。小説の文体を使用し、ストーリーの流れとキャラクター描写に重点を置いてください。",
                "news": "以下のテキストを日本語に翻訳してください。ニュース記事の文体を使用し、客観性、正確性、簡潔さを保ってください。",
                "technical": "以下のテキストを日本語に翻訳してください。技術文書の文体を使用し、専門性と正確性を保ってください。",
                "literary": "以下のテキストを日本語に翻訳してください。文学的な文体を使用し、文章の美しさとイメージを重視してください。",
                "business": "以下のテキストを日本語に翻訳してください。ビジネス文書の文体を使用し、専門性とフォーマルさを保ってください。",
                "academic": "以下のテキストを日本語に翻訳してください。学術的な文体を使用し、厳密性と学術的な語調を保ってください。",
                "casual": "以下のテキストを日本語に翻訳してください。カジュアルな文体を使用し、自然で親しみやすい表現にしてください。"
            },
            "韩语": {
                "default": "다음 텍스트를 한국어로 번역해 주세요. 원문의 의미와 어조를 유지해 주세요.",
                "novel": "다음 텍스트를 한국어로 번역해 주세요. 소설 스타일을 사용하여 줄거리의 흐름과 인물 묘사에 중점을 두어 주세요.",
                "news": "다음 텍스트를 한국어로 번역해 주세요. 뉴스 스타일을 사용하여 객관성, 정확성, 간결성을 유지해 주세요.",
                "technical": "다음 텍스트를 한국어로 번역해 주세요. 기술 문서 스타일을 사용하여 전문성과 정확성을 유지해 주세요.",
                "literary": "다음 텍스트를 한국어로 번역해 주세요. 문학적 스타일을 사용하여 문장의 아름다움과 이미지를 중시해 주세요.",
                "business": "다음 텍스트를 한국어로 번역해 주세요. 비즈니스 스타일을 사용하여 전문성과 격식을 유지해 주세요.",
                "academic": "다음 텍스트를 한국어로 번역해 주세요. 학술적 스타일을 사용하여 엄격성과 학술적 어조를 유지해 주세요.",
                "casual": "다음 텍스트를 한국어로 번역해 주세요. 일상적인 스타일을 사용하여 자연스럽고 친근한 표현으로 해 주세요."
            }
        }
        
        # Get the language-specific prompts
        language_prompts = style_prompts.get(target_language, style_prompts["中文"])
        # Get the style-specific prompt
        return language_prompts.get(style, language_prompts["default"])
