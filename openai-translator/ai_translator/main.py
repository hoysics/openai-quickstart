import sys
import os
import gradio as gr
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import uvicorn

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils import ArgumentParser, ConfigLoader, LOG
from model import GLMModel, OpenAIModel
from translator import PDFTranslator

# 自定义CSS样式
CUSTOM_CSS = """
:root {
    --background-fill-primary: #1e2029;
    --background-fill-secondary: #1b1c25;
    --input-background-fill: #272831;
    --block-background-fill: #272831;
    --block-border-color: #3f4047;
    --block-title-text-color: #ffffff;
    --body-text-color: #ffffff;
    --color-accent-soft: #343541;
    --button-primary-background-fill: #ee6c4d;
    --button-primary-background-fill-hover: #f27d61;
    --button-secondary-background-fill: #2e303b;
    --button-secondary-background-fill-hover: #3c3e4c;
}

.gradio-container {
    max-width: 1200px !important;
    margin: 0 auto;
}

#pdf-upload {
    border: 2px dashed #3f4047;
    border-radius: 8px;
    background-color: #272831;
    padding: 20px;
    text-align: center;
}

.upload-button {
    background-color: #ee6c4d !important;
    color: white !important;
}

.title {
    text-align: center;
    font-size: 24px;
    font-weight: bold;
    margin-bottom: 30px;
}
"""

# FastAPI app
app = FastAPI(
    title="PDF Translator API",
    description="API for translating PDF documents using OpenAI models",
    version="1.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TranslationRequest(BaseModel):
    api_key: str
    model_name: str = "chatglm2-6b"
    file_format: str = "markdown"
    translation_style: str = "default"
    target_language: str = "中文"
    source_language: str = "英文"

# 支持的源语言
SOURCE_LANGUAGES = {
    "英文": "English",
    "中文": "Chinese",
    "日文": "Japanese",
    "韩文": "Korean",
    "法文": "French",
    "德文": "German",
    "西班牙文": "Spanish",
    "俄文": "Russian"
}

# 支持的目标语言
TARGET_LANGUAGES = {
    "中文": "Chinese",
    "英文": "English",
    "日文": "Japanese",
    "韩文": "Korean",
    "法文": "French",
    "德文": "German",
    "西班牙文": "Spanish",
    "俄文": "Russian"
}

# 预定义的翻译风格
TRANSLATION_STYLES = {
    "default": "标准翻译",
    "novel": "小说风格",
    "news": "新闻稿风格",
    "technical": "技术文档风格",
    "literary": "文学风格",
    "business": "商务风格",
    "academic": "学术风格",
    "casual": "口语风格"
}

# 风格提示词模板（按语言分类）
STYLE_PROMPTS = {
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
    "英文": {
        "default": "Please translate the following text into English, maintaining the original meaning and tone.",
        "novel": "Please translate the following text into English, using a novel writing style that emphasizes plot flow and character development.",
        "news": "Please translate the following text into English, using a journalistic style that maintains objectivity, accuracy, and conciseness.",
        "technical": "Please translate the following text into English, using a technical documentation style that maintains professionalism and accuracy.",
        "literary": "Please translate the following text into English, using a literary style that emphasizes artistic expression and imagery.",
        "business": "Please translate the following text into English, using a business writing style that maintains professionalism and formality.",
        "academic": "Please translate the following text into English, using an academic style that maintains rigor and scholarly tone.",
        "casual": "Please translate the following text into English, using a casual style that is natural, relaxed, and easy to understand."
    },
    "日文": {
        "default": "以下のテキストを日本語に翻訳してください。原文の意味と語調を保ってください。",
        "novel": "以下のテキストを日本語に翻訳してください。小説の文体を使用し、ストーリーの流れとキャラクター描写に重点を置いてください。",
        "news": "以下のテキストを日本語に翻訳してください。ニュース記事の文体を使用し、客観性、正確性、簡潔さを保ってください。",
        "technical": "以下のテキストを日本語に翻訳してください。技術文書の文体を使用し、専門性と正確性を保ってください。",
        "literary": "以下のテキストを日本語に翻訳してください。文学的な文体を使用し、文章の美しさとイメージを重視してください。",
        "business": "以下のテキストを日本語に翻訳してください。ビジネス文書の文体を使用し、専門性とフォーマルさを保ってください。",
        "academic": "以下のテキストを日本語に翻訳してください。学術的な文体を使用し、厳密性と学術的な語調を保ってください。",
        "casual": "以下のテキストを日本語に翻訳してください。カジュアルな文体を使用し、自然で親しみやすい表現にしてください。"
    },
    "韩文": {
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

@app.post("/translate")
async def translate_pdf_api(
    file: UploadFile = File(...),
    source_language: str = "英文",
    target_language: str = "中文",
    translation_style: str = "default",
    file_format: str = "pdf"
):
    """
    API endpoint for PDF translation
    """
    try:
        # Save uploaded file temporarily
        temp_path = f"temp_{file.filename}"
        with open(temp_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Initialize model and translator
        model = GLMModel()
        translator = PDFTranslator(model)
        
        # Perform translation with style
        result_path = translator.translate_pdf(
            temp_path, 
            file_format,
            source_language=source_language,
            target_language=target_language,
            translation_style=translation_style
        )
        
        # Clean up temporary file
        os.remove(temp_path)
        
        return {"status": "success", "message": "Translation completed successfully", "result_path": result_path}
    except Exception as e:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise HTTPException(status_code=500, detail=str(e))

def translate_pdf_gui(
    pdf_file, 
    source_language="英文",
    target_language="中文",
    translation_style="default"
):
    """
    GUI wrapper function for PDF translation
    """
    try:
        if pdf_file is None:
            return None, "请上传PDF文件"
            
        # Initialize model and translator
        model = GLMModel()
        translator = PDFTranslator(model)
        
        # Perform translation
        output_path = translator.translate_pdf(
            pdf_file.name, 
            "pdf",
            source_language=source_language,
            target_language=target_language,
            translation_style=translation_style
        )
        
        return output_path, "翻译完成！"
    except Exception as e:
        return None, f"翻译错误: {str(e)}"

def create_gui():
    """
    Create and launch the Gradio interface based on the image
    """
    with gr.Blocks(
        css=CUSTOM_CSS,
        theme=gr.themes.Base(),
        title="OpenAI-Translator v2.0"
    ) as interface:
        gr.HTML('<div class="title">OpenAI-Translator v2.0 （PDF 电子书翻译工具）</div>')
        
        with gr.Row():
            with gr.Column():
                pdf_file = gr.File(
                    label="上传PDF文件",
                    file_types=[".pdf"],
                    elem_id="pdf-upload"
                )
                
                upload_text = gr.HTML(
                    """
                    <div style="text-align: center; margin-top: -20px; color: #aaa;">
                        <p>Drop File Here</p>
                        <p>- or -</p>
                        <p>Click to Upload</p>
                    </div>
                    """
                )
            
            with gr.Column():
                output_file = gr.File(
                    label="下载翻译文件",
                    interactive=False,
                    elem_id="output-file"
                )
        
        with gr.Row():
            with gr.Column():
                source_language = gr.Textbox(
                    label="源语言（默认：英文）",
                    value="English",
                    elem_id="source-lang"
                )
            
        with gr.Row():
            with gr.Column():
                target_language = gr.Textbox(
                    label="目标语言（默认：中文）",
                    value="Chinese",
                    elem_id="target-lang"
                )
        
        with gr.Row():
            with gr.Column():
                clear_btn = gr.Button("Clear", variant="secondary")
            
            with gr.Column():
                submit_btn = gr.Button("Submit", variant="primary")
        
        # Status message
        status_msg = gr.Textbox(
            label="状态",
            visible=False
        )
        
        # Event handlers
        submit_btn.click(
            fn=translate_pdf_gui,
            inputs=[pdf_file, source_language, target_language, "default"],
            outputs=[output_file, status_msg]
        )
        
        clear_btn.click(
            fn=lambda: (None, ""),
            inputs=[],
            outputs=[pdf_file, status_msg]
        )
    
    return interface

def run_api_server(host="0.0.0.0", port=8000):
    """
    Run the FastAPI server
    """
    uvicorn.run(app, host=host, port=port)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "--api":
            # API server mode
            run_api_server()
        else:
            # Command line mode
            argument_parser = ArgumentParser()
            args = argument_parser.parse_arguments()
            config_loader = ConfigLoader(args.config)
            config = config_loader.load_config()

            model = GLMModel()  # 使用ChatGLM2-6B模型
            pdf_file_path = args.book if args.book else config['common']['book']
            file_format = args.file_format if args.file_format else config['common']['file_format']

            translator = PDFTranslator(model)
            translator.translate_pdf(pdf_file_path, file_format)
    else:
        # GUI mode
        interface = create_gui()
        interface.launch()
