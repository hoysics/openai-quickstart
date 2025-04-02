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
    model_name: str = "gpt-3.5-turbo"
    file_format: str = "markdown"

@app.post("/translate")
async def translate_pdf_api(
    file: UploadFile = File(...),
    api_key: str = None,
    model_name: str = "gpt-3.5-turbo",
    file_format: str = "markdown"
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
        model = OpenAIModel(model=model_name, api_key=api_key)
        translator = PDFTranslator(model)
        
        # Perform translation
        translator.translate_pdf(temp_path, file_format)
        
        # Clean up temporary file
        os.remove(temp_path)
        
        return {"status": "success", "message": "Translation completed successfully"}
    except Exception as e:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise HTTPException(status_code=500, detail=str(e))

def translate_pdf_gui(pdf_file, api_key, model_name="gpt-3.5-turbo", file_format="markdown"):
    """
    GUI wrapper function for PDF translation
    """
    try:
        model = OpenAIModel(model=model_name, api_key=api_key)
        translator = PDFTranslator(model)
        translator.translate_pdf(pdf_file.name, file_format)
        return "Translation completed successfully!"
    except Exception as e:
        return f"Error during translation: {str(e)}"

def create_gui():
    """
    Create and launch the Gradio interface
    """
    with gr.Blocks(title="PDF Translator") as interface:
        gr.Markdown("# PDF Translator")
        gr.Markdown("Translate PDF documents using OpenAI's models")
        
        with gr.Row():
            with gr.Column():
                pdf_file = gr.File(label="Upload PDF File")
                api_key = gr.Textbox(
                    label="OpenAI API Key",
                    type="password",
                    placeholder="Enter your OpenAI API key"
                )
                model_name = gr.Dropdown(
                    choices=["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo-preview"],
                    value="gpt-3.5-turbo",
                    label="Select Model"
                )
                file_format = gr.Dropdown(
                    choices=["markdown", "txt"],
                    value="markdown",
                    label="Output Format"
                )
                translate_btn = gr.Button("Translate PDF")
            
            with gr.Column():
                output = gr.Textbox(label="Status", lines=3)
        
        translate_btn.click(
            fn=translate_pdf_gui,
            inputs=[pdf_file, api_key, model_name, file_format],
            outputs=output
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

            model_name = args.openai_model if args.openai_model else config['OpenAIModel']['model']
            api_key = args.openai_api_key if args.openai_api_key else config['OpenAIModel']['api_key']
            model = OpenAIModel(model=model_name, api_key=api_key)

            pdf_file_path = args.book if args.book else config['common']['book']
            file_format = args.file_format if args.file_format else config['common']['file_format']

            translator = PDFTranslator(model)
            translator.translate_pdf(pdf_file_path, file_format)
    else:
        # GUI mode
        interface = create_gui()
        interface.launch()
