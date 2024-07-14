import os
import json
import torch
from typing import List

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
