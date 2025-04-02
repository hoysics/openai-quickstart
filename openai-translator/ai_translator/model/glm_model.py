import requests
import simplejson
import os

from .model import Model
from utils import LOG

class GLMModel(Model):
    def __init__(self, model_url: str = "http://localhost:8000/chat", timeout: int = 60):
        """初始化ChatGLM2-6B模型

        Args:
            model_url: ChatGLM2-6B API地址，默认为本地部署的地址
            timeout: 请求超时时间，默认60秒
        """
        self.model_url = model_url
        self.timeout = timeout
        LOG.info(f"使用ChatGLM2-6B模型，API地址: {model_url}")

    def make_request(self, prompt):
        """向ChatGLM2-6B模型发送请求

        Args:
            prompt: 提示词

        Returns:
            tuple: (翻译结果, 是否成功)
        """
        try:
            payload = {
                "prompt": prompt,
                "history": [],
                "max_length": 2048,
                "temperature": 0.7
            }
            LOG.debug(f"发送请求到 ChatGLM2-6B: {self.model_url}")
            LOG.debug(f"请求内容: {prompt[:100]}...")
            
            response = requests.post(self.model_url, json=payload, timeout=self.timeout)
            response.raise_for_status()
            
            response_dict = response.json()
            if "response" in response_dict:
                translation = response_dict["response"]
                LOG.debug(f"ChatGLM2-6B 响应: {translation[:100]}...")
                return translation, True
            else:
                LOG.error(f"无效的ChatGLM2-6B响应: {response_dict}")
                return "", False
                
        except requests.exceptions.RequestException as e:
            LOG.error(f"请求异常：{e}")
            raise Exception(f"请求异常：{e}")
        except requests.exceptions.Timeout as e:
            LOG.error(f"请求超时：{e}")
            raise Exception(f"请求超时：{e}")
        except simplejson.errors.JSONDecodeError as e:
            LOG.error(f"JSON解析错误：{e}")
            raise Exception("Error: response is not valid JSON format.")
        except Exception as e:
            LOG.error(f"发生了未知错误：{e}")
            raise Exception(f"发生了未知错误：{e}")
        
        return "", False
