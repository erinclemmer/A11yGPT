# Chain of Thought paper: https://proceedings.neurips.cc/paper_files/paper/2022/file/9d5609613524ecf4f15af0f7b31abca4-Paper-Conference.pdf

import os
import json

from gpt import GptChat
from lib import WCGAError

def cot_get_fix(chat: GptChat, html: str, wcga_error: WCGAError):
	chat.reset_chat()
	chat.add_message("user", f"Here is the html for the page:\n{html}")
	chat.add_message("assistant", "Ok")
	chat.add_message("user", f"This is the type of problem: {wcga_error.success_criteria}")
	chat.add_message("assistant", "Ok")
	cot = chat.send('Think through finding the problem step by step')
	with open('t_4_CoT/result_prompt.txt', 'r', encoding='utf-8') as f:
		result_prompt = f.read()
	data = json.loads(chat.send(result_prompt))
	data['CoT'] = cot
	return data