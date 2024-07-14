# Self instruct paper: https://arxiv.org/pdf/2212.10560

import json

from gpt import GptChat
from lib import WCGAError

def guidance_get_fix(chat: GptChat, html: str, wcga_error: WCGAError):
	chat.reset_chat()
	chat.add_message("user", f"Here is the html for the page:\n{html}")
	chat.add_message("assistant", "Ok")
	chat.add_message("user", f"This is the type of problem: {wcga_error.success_criteria}")
	chat.add_message("assistant", "Ok")
	return json.loads(chat.send(f"Find the problem"))