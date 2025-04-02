import os
from reportlab.lib import colors, pagesizes, units
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak,
    Flowable, Frame, PageTemplate, BaseDocTemplate
)
from reportlab.lib.units import inch, point
from reportlab.pdfgen import canvas
from reportlab.lib.colors import black, white

from book import Book, ContentType
from utils import LOG

class PositionedParagraph(Flowable):
    def __init__(self, text, style, x, y, width, height):
        Flowable.__init__(self)
        self.text = text
        self.style = style
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    def draw(self):
        self.canv.saveState()
        self.canv.translate(self.x, self.y)
        p = Paragraph(self.text, self.style)
        w, h = p.wrap(self.width, self.height)
        p.drawOn(self.canv, 0, 0)
        self.canv.restoreState()

class PositionedTable(Flowable):
    def __init__(self, data, style, x, y, width, height):
        Flowable.__init__(self)
        self.data = data
        self.style = style
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    def draw(self):
        self.canv.saveState()
        self.canv.translate(self.x, self.y)
        table = Table(self.data)
        table.setStyle(self.style)
        w, h = table.wrap(self.width, self.height)
        table.drawOn(self.canv, 0, 0)
        self.canv.restoreState()

class Writer:
    def __init__(self):
        pass

    def save_translated_book(self, book: Book, output_file_path: str = None, file_format: str = "PDF"):
        if file_format.lower() == "pdf":
            self._save_translated_book_pdf(book, output_file_path)
        elif file_format.lower() == "markdown":
            self._save_translated_book_markdown(book, output_file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_format}")

    def _save_translated_book_pdf(self, book: Book, output_file_path: str = None):
        if output_file_path is None:
            output_file_path = book.pdf_file_path.replace('.pdf', f'_translated.pdf')

        LOG.info(f"pdf_file_path: {book.pdf_file_path}")
        LOG.info(f"开始翻译: {output_file_path}")

        # Register Chinese font
        font_path = "../fonts/simsun.ttc"
        pdfmetrics.registerFont(TTFont("SimSun", font_path))

        # Create styles
        styles = getSampleStyleSheet()
        normal_style = styles['Normal']
        normal_style.fontName = 'SimSun'
        normal_style.fontSize = 12
        normal_style.leading = 14

        # Create document with original page size
        doc = BaseDocTemplate(
            output_file_path,
            pagesize=pagesizes.letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )

        # Process each page
        for page in book.pages:
            # Create page template
            frame = Frame(
                doc.leftMargin,
                doc.bottomMargin,
                doc.width - doc.leftMargin - doc.rightMargin,
                doc.height - doc.topMargin - doc.bottomMargin,
                id='normal'
            )
            template = PageTemplate(id='main', frames=[frame])
            doc.addPageTemplates([template])

            # Create story for this page
            story = []

            # Process contents in order of their vertical position
            sorted_contents = sorted(
                page.contents,
                key=lambda x: x.layout_info['bbox'][1] if hasattr(x, 'layout_info') else 0
            )

            for content in sorted_contents:
                if content.status:
                    if content.content_type == ContentType.TEXT:
                        # Create positioned paragraph
                        layout = content.layout_info
                        bbox = layout['bbox']
                        width = bbox[2] - bbox[0]
                        height = bbox[3] - bbox[1]
                        
                        # Convert coordinates to points
                        x = bbox[0] * point
                        y = doc.height - bbox[3] * point  # Convert from bottom-left to top-left
                        
                        p = PositionedParagraph(
                            content.translation,
                            normal_style,
                            x,
                            y,
                            width * point,
                            height * point
                        )
                        story.append(p)

                    elif content.content_type == ContentType.TABLE:
                        # Create positioned table
                        layout = content.layout_info
                        bbox = layout['bbox']
                        width = bbox[2] - bbox[0]
                        height = bbox[3] - bbox[1]
                        
                        # Convert coordinates to points
                        x = bbox[0] * point
                        y = doc.height - bbox[3] * point
                        
                        # Create table style
                        table_style = TableStyle([
                            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                            ('FONTNAME', (0, 0), (-1, -1), 'SimSun'),
                            ('FONTSIZE', (0, 0), (-1, -1), 12),
                            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                            ('GRID', (0, 0), (-1, -1), 1, colors.black)
                        ])
                        
                        t = PositionedTable(
                            content.translation.values.tolist(),
                            table_style,
                            x,
                            y,
                            width * point,
                            height * point
                        )
                        story.append(t)

            # Build the page
            doc.build(story)

        LOG.info(f"翻译完成: {output_file_path}")

    def _save_translated_book_markdown(self, book: Book, output_file_path: str = None):
        if output_file_path is None:
            output_file_path = book.pdf_file_path.replace('.pdf', f'_translated.md')

        LOG.info(f"pdf_file_path: {book.pdf_file_path}")
        LOG.info(f"开始翻译: {output_file_path}")
        with open(output_file_path, 'w', encoding='utf-8') as output_file:
            # Iterate over the pages and contents
            for page in book.pages:
                for content in page.contents:
                    if content.status:
                        if content.content_type == ContentType.TEXT:
                            # Add translated text to the Markdown file
                            text = content.translation
                            output_file.write(text + '\n\n')

                        elif content.content_type == ContentType.TABLE:
                            # Add table to the Markdown file
                            table = content.translation
                            header = '| ' + ' | '.join(str(column) for column in table.columns) + ' |' + '\n'
                            separator = '| ' + ' | '.join(['---'] * len(table.columns)) + ' |' + '\n'
                            body = '\n'.join(['| ' + ' | '.join(str(cell) for cell in row) + ' |' for row in table.values.tolist()]) + '\n\n'
                            output_file.write(header + separator + body)

                # Add a page break (horizontal rule) after each page except the last one
                if page != book.pages[-1]:
                    output_file.write('---\n\n')

        LOG.info(f"翻译完成: {output_file_path}")