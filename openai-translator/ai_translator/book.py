from enum import Enum
from typing import List, Dict, Any
import pandas as pd

class ContentType(Enum):
    TEXT = "text"
    TABLE = "table"

class Content:
    def __init__(self, content_type: ContentType, original: str, layout_info: Dict[str, Any] = None):
        self.content_type = content_type
        self.original = original
        self.translation = None
        self.status = False
        self.layout_info = layout_info or {}

    def set_translation(self, translation: str, status: bool):
        self.translation = translation
        self.status = status

class TextContent(Content):
    def __init__(self, original: str, layout_info: Dict[str, Any] = None):
        super().__init__(ContentType.TEXT, original, layout_info)

class TableContent(Content):
    def __init__(self, table_data: List[List[str]], layout_info: Dict[str, Any] = None):
        super().__init__(ContentType.TABLE, table_data, layout_info)
        self.translation = pd.DataFrame(table_data[1:], columns=table_data[0])

class Page:
    def __init__(self):
        self.contents: List[Content] = []

    def add_content(self, content: Content):
        self.contents.append(content)

class Book:
    def __init__(self, pdf_file_path: str):
        self.pdf_file_path = pdf_file_path
        self.pages: List[Page] = []

    def add_page(self, page: Page):
        self.pages.append(page) 