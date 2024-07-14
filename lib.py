import os
import json
import torch
from time import sleep
from typing import List, Callable

from gpt import GptEmbeddings, GptChat

def get_api_key():
	if not os.path.exists('config.json'):
		raise Exception("Could not find config.json")
	with open('config.json', 'r', encoding='utf-8') as f:
		config = json.load(f)

	if not 'openai_api_key' in config:
		raise Exception('Could not find key: openai_api_key in config')
	return config['openai_api_key']

def get_cosine_similarity(embedding1: List[float], embedding2: List[float]):
    # Move the embeddings to the GPU
    embedding1 = torch.tensor(embedding1)
    embedding2 = torch.tensor(embedding2)

    # Normalize the embeddings
    embedding1_norm = embedding1 / torch.norm(embedding1)
    embedding2_norm = embedding2 / torch.norm(embedding2)

    # Compute the cosine similarity
    similarity = torch.matmul(embedding1_norm, embedding2_norm.T)

    return similarity

class WCGAExample:
	problem: str
	solution: str

	def __init__(self, problem: str, solution: str):
		self.problem = problem
		self.solution = solution

class WCGAError:
	guideline: str
	success_criteria: str
	examples: List[WCGAExample]
	o: dict

	def __init__(self, o: dict):
		keys = [
			'guideline',
			'success_criteria',
			'examples'
		]
		for key in keys:
			if not key in o:
				raise Exception(f'Could not find key {key} in object')
		self.guideline = o[keys[0]]
		self.success_criteria = o[keys[1]]
		self.examples = [WCGAExample(item['problem'], item['solution']) for item in o[keys[2]]]
		self.o = o
		
def get_wcga_errors() -> List[WCGAError]:
    wcga_errors = []
    with open('wcga_errors.json', 'r', encoding='utf-8') as f:
        for item in json.load(f):
            wcga_errors.append(WCGAError(item))
    return wcga_errors

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

def find_closest_embedding(fix: GptFix, existing_fixes: List[GptFix]):
	closest = 0
	for exisiting_fix in existing_fixes:
		fix_embedding = exisiting_fix.embedding
		sim = get_cosine_similarity(fix.embedding, fix_embedding)
		if sim > closest:
			closest = sim
	return closest

def get_fixes_for_error(
		get_fix: Callable[[GptChat, str, WCGAError], dict], 
		chat: GptChat, 
		embed: GptEmbeddings, 
		html: str, 
		wcga_error: WCGAError, 
		sim_threshold: float
	) -> List[GptFix]:
	fixes = []
	retries = 0
	while retries < 5:
		try:
			res = get_fix(chat, html, wcga_error)
			if res['problem_type'] == 'NONE':
				retries += 1
				continue
		except BaseException as e:
			print(e)
			sleep(1)
			continue
		try:
			embedding = embed.get_embedding(res['offending_line'] + '\n\n' + res['fixed_line'])
			fix = GptFix(res, embedding)
			print(fix.to_string())
		except BaseException as e:
			print(e)
			sleep(1)
			continue

		closest = find_closest_embedding(fix, fixes)
		print(f'Closest sim {closest}')
		if closest > sim_threshold:
			retries += 1
			continue
		retries = 0
		fixes.append(fix)
		print(f'Added new fix, total {len(fixes)} fixes found\n\n')
	return fixes

def find_fixes_for_file(
		get_fix: Callable[[GptChat, str, WCGAError], dict],
		chat: GptChat, 
		embed: GptEmbeddings, 
		html_file: str, 
		fix_folder: str,
		sim_threshold: float,
		no_ctx: bool = False
	):
	fix_file = f'fixes/{fix_folder}/{html_file}.json'
	if os.path.exists(fix_file):
		print(f'Fixes already found for {fix_file}')
		return

	with open('html/' + html_file, 'r', encoding='utf-8') as f:
		html = f.read()
	
	fixes = []
	if no_ctx:
		for fix in get_fixes_for_error(get_fix, chat, embed, html, None, sim_threshold):
			fixes.append(fix.o)
	else:
		for wcga_error in get_wcga_errors():
			error_fixes = []
			for fix in get_fixes_for_error(get_fix, chat, embed, html, wcga_error, sim_threshold):
				o = fix.o
				del o['problem_type']
				error_fixes.append(o)
			o = wcga_error.o
			del o['examples']
			o['error_fixes'] = error_fixes
			fixes.append(o)

	if not os.path.exists(fix_folder):
		os.makedirs(fix_folder)
	
	with open(fix_file, 'w', encoding='utf-8') as f:
		json.dump(fixes, f, indent=4)

def run_test(
		get_fix: Callable[[GptChat, str, WCGAError], dict], 
		test_folder: str,
		api_key: str, 
		embed: GptEmbeddings,
		sim_threshold: float,
		no_ctx: bool = False
    ):
	chat = GptChat(f'{test_folder}/sys_prompt.txt', api_key)
	for html_file in os.listdir('html'):
		find_fixes_for_file(get_fix, chat, embed, html_file, test_folder, sim_threshold, no_ctx)
