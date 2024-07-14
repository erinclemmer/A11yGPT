# Chain of Thought paper: https://proceedings.neurips.cc/paper_files/paper/2022/file/9d5609613524ecf4f15af0f7b31abca4-Paper-Conference.pdf

import os
import json
from time import sleep
from typing import List

from gpt import GptChat, GptEmbeddings
from lib import get_api_key, get_cosine_similarity, get_wcga_errors, WCGAError, GptFix

SIM_THRESHOLD = .86

if not os.path.exists('sys_prompt.txt'):
	raise Exception('Could not find sys_prompt.txt')

api_key = get_api_key()
chat = GptChat('sys_prompt.txt', api_key)
embed = GptEmbeddings(api_key)

with open('./result_prompt.txt', 'r', encoding='utf-8') as f:
	result_prompt = f.read()

def find_closest_embedding(fix: GptFix, existing_fixes: List[GptFix]):
	closest = 0
	for exisiting_fix in existing_fixes:
		fix_embedding = exisiting_fix.embedding
		sim = get_cosine_similarity(fix.embedding, fix_embedding)
		if sim > closest:
			closest = sim
	return closest

def get_fix(html: str, wcga_error: WCGAError):
	chat.reset_chat()
	chat.add_message("user", f"Here is the html for the page:\n{html}")
	chat.add_message("assistant", "Ok")
	chat.add_message("user", f"This is the type of problem: {wcga_error.success_criteria}")
	chat.add_message("assistant", "Ok")
	cot = chat.send('Think through finding the issues step by step')
	data = json.loads(chat.send(result_prompt))
	data['CoT'] = cot
	return data

def get_fixes_for_error(html: str, wcga_error: WCGAError) -> List[GptFix]:
	fixes = []
	retries = 0
	while retries < 5:
		try:
			res = get_fix(html, wcga_error)
			if res['problem_type'] == 'NONE':
				retries += 1
				continue
		except BaseException as e:
			print(e)
			sleep(1)
			continue
		try:
			embedding = embed.get_embedding(res['offending_line'])
			fix = GptFix(res, embedding)
			print(fix.to_string())
		except BaseException as e:
			print(e)
			sleep(1)
			continue

		closest = find_closest_embedding(fix, fixes)
		print(f'Closest sim {closest}')
		if closest > SIM_THRESHOLD:
			retries += 1
			continue
		retries = 0
		fixes.append(fix)
		print(f'Added new fix, total {len(fixes)} fixes found\n\n')
		break
	return fixes

def find_fixes_for_file(file_name: str):
	with open('../other_projects/html/' + file_name, 'r', encoding='utf-8') as f:
		html = f.read()
	fixes = []
	for wcga_error in get_wcga_errors():
		error_fixes = []
		for fix in get_fixes_for_error(html, wcga_error):
			error_fixes.append(fix.o)
		o = wcga_error.o
		o['error_fixes'] = error_fixes
		fixes.append(o)
	if not os.path.exists('fixes'):
		os.mkdir('fixes')

	with open(f'fixes/{file_name}.json', 'w', encoding='utf-8') as f:
		json.dump(fixes, f, indent=4)

for file in os.listdir('../other_projects/html'):
	find_fixes_for_file(file)