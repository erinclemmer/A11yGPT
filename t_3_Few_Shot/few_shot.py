# Language Models are Few Shot Learners: https://proceedings.neurips.cc/paper_files/paper/2020/file/1457c0d6bfcb4967418bfb8ac142f64a-Paper.pdf
# ^ GPT-3 paper

import json

from gpt import GptChat
from lib import WCGAError

def fs_get_fix(chat: GptChat, html: str, wcga_error: WCGAError):
	chat.reset_chat()
	chat.add_message("user", f"Here is the html for the page:\n{html}")
	chat.add_message("assistant", "Ok")
	chat.add_message("user", f"This is the type of problem: {wcga_error.success_criteria}")
	chat.add_message("assistant", "Ok")
	for ex in wcga_error.examples:
		chat.add_message("user", f"This is an example of the problem: {ex.problem}" + f"\n\nThis is a possible solution: {ex.solution}")
		chat.add_message("assistant", "Ok")
	return json.loads(chat.send(f"Find the problem"))
