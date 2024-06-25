import os
import json
from time import sleep
from typing import List

from gpt import GptChat, GptEmbeddings
from lib import get_api_key, get_cosine_similarity

SIM_THRESHOLD = .8

html_file = 'project2.html'
with open(html_file, 'r', encoding='utf-8') as f:
	html = f.read()

if not os.path.exists('sys_prompt.txt'):
	raise Exception('Could not find sys_prompt.txt')

api_key = get_api_key()
chat = GptChat('sys_prompt.txt', api_key)
embed = GptEmbeddings(api_key)
fixes = []
retries = 0

class GptFix:
	problem_type: str
	offending_line: str
	fixed_line: str
	o: dict
	embedding: List[float]

	def __init__(self, o: dict, embedding: List[float]):
		keys = [
			'problem_type',
			'offending_line',
			'fixed_line'
		]
		for key in keys:
			if not key in o:
				raise Exception(f'Could not find key in object')
		self.problem_type = o['problem_type']
		self.offending_line = o['offending_line']
		self.fixed_line = o['fixed_line']
		self.embedding = embedding
		self.o = o

	def to_string(self):
		print(f"""
{self.problem_type}
Problem: {self.offending_line}
Fixed: {self.fixed_line}
""")

	def to_object(self):
		return {
			""
		}

def find_closest_embedding(fix: GptFix, existing_fixes: List[GptFix]):
	closest = 0
	for exisiting_fix in existing_fixes:
		fix_embedding = exisiting_fix.embedding
		sim = get_cosine_similarity(fix.embedding, fix_embedding)
		if sim > closest:
			closest = sim
	return closest

while retries < 5:
	try:
		chat.reset_chat()
		res = json.loads(chat.send(f'Here is the html for the website:\n{html}'))
	except BaseException as e:
		print(e)
		sleep(1)
		continue
	try:
		embedding = embed.get_embedding(json.dumps(res))
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

with open('output.json', 'w', encoding='utf-8') as f:
	json.dump([f.o for f in fixes], f, indent=4)