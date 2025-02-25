import pymupdf
import fitz
import requests
import json
import re
from pathlib import Path

summaries = Path("/summaries")
url = "http://llama:8080/completion"
headers = {
    'Content-Type': 'application/json'
}

for summary in summaries.iterdir():
    doc = pymupdf.open(summary.absolute())

    page = doc[0]

    content = page.get_text(option="text")

    # payload = {
    #     "model": "PDFai-Llama-3.1",
    #     "messages": [
    #         {
    #             "role": "user",
    #             "content": content
    #         }
    #     ]
    # }

    payload = {
        "prompt": "<|begin_of_text|><|start_header_id|>system<|end_header_id|>Answer the user's question in as much detail as possible. Be witty and precise but don't answer incorrectly!" +
        "<|eot_id|><|start_header_id|>user<|end_header_id|>How do you split an atom?<|eot_id|><|start_header_id|>assistant<|end_header_id|>"
    }

    response = requests.post(url, json=payload, headers=headers)
    print(response.json())
    break


