import json
from typing import List

class WCGAError:
	guideline: str
	success_criteria: str
	error_example: str
	fixed_example: str

	def __init__(self, o: dict):
		keys = [
			'guideline',
			'success_criteria',
			'error_example',
			'fixed_example'
		]
		for key in keys:
			if not key in o:
				raise Exception(f'Could not find key {key} in object')
		self.guideline = o[keys[0]]
		self.success_criteria = o[keys[1]]
		self.error_example = o[keys[2]]
		self.fixed_example = o[keys[3]]

class Promblem:
	line: int
	problem: str

	def __init__(self, html: str, line: int, guideline: str, wcga_errors: List[WCGAError]):
		self.line = line
		self.problem = html.split('\n')[line - 1].strip()
		self.wcga_error = None
		for err in wcga_errors:
			if err.guideline == guideline:
				self.wcga_error = err
		if self.wcga_error is None:
			raise Exception(f"Could not find guidline {guideline} for line {line}")

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

def get_wcga_errors(file_name: str):
    wcga_errors = []
    with open(file_name, 'r', encoding='utf-8') as f:
        for item in json.load(f):
            wcga_errors.append(WCGAError(item))
    return wcga_errors

def get_violations(html: str, file_name: str, wcga_errors: List[WCGAError]) -> List[Promblem]:
    with open(file_name, 'r', encoding='utf-8') as f:
        data = json.load(f)
    problems = []
    for item in data:
        problems.append(Promblem(html, item['line'], item['guideline'], wcga_errors))
    return problems

def get_fixes_from_objects(fixes_objects: List[dict]):
    fixes = []
    for item in fixes_objects:
        fixes.append(GptFix())
		

def get_fixes_for_guideline(guideline: str):
	1

WCGA_ERROR_FILE = 'wcga_errors.json'
VIOLATIONS_FILE = 'violations.json'
FIXES_FILE = 'output1.json'
HTML_FILE = 'project1.html'

with open(HTML_FILE, 'r', encoding='utf-8') as f:
	html = f.read()

wcga_errors = get_wcga_errors(WCGA_ERROR_FILE)
problems = get_violations(html, VIOLATIONS_FILE, wcga_errors)
for problem in problems:
	get_fixes_for_guideline(problem.wcga_error.guideline)