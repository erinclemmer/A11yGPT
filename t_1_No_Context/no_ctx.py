import json

from gpt import GptChat

def no_ctx_get_fix(chat: GptChat, html: str, _: None):
	chat.reset_chat()
	chat.add_message("user", f"Here is the html for the page:\n{html}")
	chat.add_message("assistant", "Ok")
	return json.loads(chat.send(f"Find the problem"))