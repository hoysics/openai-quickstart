import pdfplumber
from typing import Optional, List, Dict
from book import Book, Page, Content, ContentType, TableContent, TextContent
from translator.exceptions import PageOutOfRangeException
from utils import LOG


class PDFParser:
    def __init__(self):
        pass

    def parse_pdf(self, pdf_file_path: str, pages: Optional[int] = None) -> Book:
        book = Book(pdf_file_path)

        with pdfplumber.open(pdf_file_path) as pdf:
            if pages is not None and pages > len(pdf.pages):
                raise PageOutOfRangeException(len(pdf.pages), pages)

            if pages is None:
                pages_to_parse = pdf.pages
            else:
                pages_to_parse = pdf.pages[:pages]

            for pdf_page in pages_to_parse:
                page = Page()
                
                # Extract text with layout information
                words = pdf_page.extract_words(
                    keep_blank_chars=True,
                    use_text_flow=True,
                    horizontal_ltr=True,
                    vertical_ttb=True,
                    extra_attrs=['fontname', 'size', 'top', 'bottom', 'x0', 'x1', 'y0', 'y1']
                )
                
                # Extract tables
                tables = pdf_page.extract_tables()
                
                # Group words by their vertical position to identify text blocks
                text_blocks = self._group_words_into_blocks(words)
                
                # Process text blocks
                for block in text_blocks:
                    text_content = TextContent(
                        content_type=ContentType.TEXT,
                        original=block['text'],
                        layout_info={
                            'font': block['font'],
                            'size': block['size'],
                            'bbox': block['bbox'],
                            'line_spacing': block['line_spacing']
                        }
                    )
                    page.add_content(text_content)
                    LOG.debug(f"[text_block]\n{block['text']}")

                # Process tables
                if tables:
                    for table_data in tables:
                        # Get table position
                        table_bbox = self._get_table_bbox(pdf_page, table_data)
                        table = TableContent(
                            table_data,
                            layout_info={'bbox': table_bbox}
                        )
                        page.add_content(table)
                        LOG.debug(f"[table]\n{table}")

                book.add_page(page)

        return book

    def _group_words_into_blocks(self, words: List[Dict]) -> List[Dict]:
        """
        Group words into text blocks based on their vertical position and font properties
        """
        if not words:
            return []

        blocks = []
        current_block = {
            'text': '',
            'font': words[0]['fontname'],
            'size': words[0]['size'],
            'bbox': [words[0]['x0'], words[0]['y0'], words[0]['x1'], words[0]['y1']],
            'line_spacing': 0,
            'words': [words[0]]
        }

        for word in words[1:]:
            # Check if word belongs to current block
            if (abs(word['y0'] - current_block['bbox'][1]) < 5 and  # Same line
                word['fontname'] == current_block['font'] and
                word['size'] == current_block['size']):
                current_block['words'].append(word)
                current_block['bbox'][2] = max(current_block['bbox'][2], word['x1'])
                current_block['bbox'][3] = max(current_block['bbox'][3], word['y1'])
            else:
                # Process current block
                current_block['text'] = self._merge_words(current_block['words'])
                current_block['line_spacing'] = self._calculate_line_spacing(current_block['words'])
                blocks.append(current_block)
                
                # Start new block
                current_block = {
                    'text': '',
                    'font': word['fontname'],
                    'size': word['size'],
                    'bbox': [word['x0'], word['y0'], word['x1'], word['y1']],
                    'line_spacing': 0,
                    'words': [word]
                }

        # Process last block
        current_block['text'] = self._merge_words(current_block['words'])
        current_block['line_spacing'] = self._calculate_line_spacing(current_block['words'])
        blocks.append(current_block)

        return blocks

    def _merge_words(self, words: List[Dict]) -> str:
        """
        Merge words into text while preserving spacing
        """
        text = ''
        for i, word in enumerate(words):
            if i > 0:
                # Add space if words are not too close
                if word['x0'] - words[i-1]['x1'] > 2:
                    text += ' '
            text += word['text']
        return text

    def _calculate_line_spacing(self, words: List[Dict]) -> float:
        """
        Calculate average line spacing in the text block
        """
        if len(words) < 2:
            return 0
        spacings = []
        for i in range(1, len(words)):
            if words[i]['y0'] != words[i-1]['y0']:  # Different lines
                spacing = words[i]['y0'] - words[i-1]['y1']
                spacings.append(spacing)
        return sum(spacings) / len(spacings) if spacings else 0

    def _get_table_bbox(self, page, table_data) -> List[float]:
        """
        Get the bounding box of a table
        """
        # This is a simplified version - you might want to implement more accurate table detection
        words = page.extract_words()
        table_words = [w for w in words if any(cell in w['text'] for row in table_data for cell in row)]
        if not table_words:
            return [0, 0, 0, 0]
        
        x0 = min(w['x0'] for w in table_words)
        y0 = min(w['y0'] for w in table_words)
        x1 = max(w['x1'] for w in table_words)
        y1 = max(w['y1'] for w in table_words)
        
        return [x0, y0, x1, y1]
