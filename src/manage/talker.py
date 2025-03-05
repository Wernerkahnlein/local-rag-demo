import requests
import os
import logging
from jinja2 import Environment, select_autoescape, FileSystemLoader

logger = logging.getLogger(__name__)
logger.setLevel(os.environ.get("LOG_LEVEL", "INFO"))

class Talker:

    def __init__(self, chatter_url = "http://chatter:8081", jinja_fs_path = "/app/src/manage/templates"):
        self.llama_chatter_url = chatter_url
        self.template_loader = FileSystemLoader(searchpath=jinja_fs_path)
        self.jinja_env = Environment(
            loader=self.template_loader,
            autoescape=select_autoescape()
        )
        

    def call_llama_completion(self, payload: str):
            headers = {
                'Content-Type': 'application/json'
            }

            response = requests.post(f"{self.url}/completion", json=payload, headers=headers)
            logger.info(response.json())
            return response.status_code


    def call_chat_completions(self, system_prompt: str, prompt: str, model: str = "DeepSeek-R1-Distill-Qwen", template = "DeepSeek-R1-Distill-Qwen"):
            template = self.jinja_env.get_template(f"{template}.tpl")
            rendered_template = template.render(
                Messages=[
                    {
                        "Role": "user", "Content": prompt
                    }
                ]
            )
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": rendered_template}
                ]
            }
            headers = {
                'Content-Type': 'application/json'
            }

            logger.info(payload)

            response = requests.post(f"{self.llama_chatter_url}/v1/chat/completions", json=payload, headers=headers)
            return response.json()
