# WCGA 2.2: https://www.w3.org/TR/WCAG22/

import os
import json
from gpt import GptChat

from typing import List, Tuple
from lib import get_api_key

api_key = get_api_key()

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

wcga_errors = []
with open('wcga_errors.json', 'r', encoding='utf-8') as f:
	for item in json.load(f):
		wcga_errors.append(WCGAError(item))

def fix_page(html: str, found_error_lines: List[Tuple[int, str]]):
	found_problems = [Promblem(html, line, rule, wcga_errors) for line, rule in found_error_lines]

	def fix_problem(problem: Promblem):
		chat = GptChat("sys_prompt.txt", api_key)
		chat.add_message("user", f"Here is the html for the page:\n{html}")
		chat.add_message("assistant", "Ok")
		chat.add_message("user", f"This is the type of problem: {problem.wcga_error.success_criteria}\n\nHere is the offending line: {problem.problem}")
		chat.add_message("assistant", "Ok")
		chat.add_message("user", f"Here is an example of the error: {problem.wcga_error.error_example}\n\nAnd here is an example of that error fixed: {problem.wcga_error.fixed_example}")
		chat.add_message("assistant", "Ok")
		return chat.send("Fix the problem")

	fixes = []
	for problem in found_problems:
		fixes.append({
			"line": problem.line,
			"problem": problem.problem,
			"fix": fix_problem(problem)
		})
	return fixes

def fix_page_one():
	html_file = "project1.html"
	with open(html_file, 'r', encoding='utf-8') as f:
		html = f.read()

	fixes = fix_page(html, [
		(98, "1.1.1"),
		(122, "4.1.1"),
		(6, "2.4.2"),
		(140, "1.3.1.1"),
		(134, "1.3.1.2")
	])

	output_file = "output1.json"
	with open(output_file, 'w', encoding='utf-8') as f:
		json.dump(fixes, f, indent=4)

def fix_page_two():
	html_file = "project2.html"
	with open(html_file, 'r', encoding='utf-8') as f:
		html = f.read()

	fixes = fix_page(html, [
		(49, "1.1.1"),
		(63, "1.4.2"),
		(36, "1.3.1.3"),
		(61, "1.4.4.2"),
		(52, "1.4.4.1")
	])

	output_file = "output2.json"
	with open(output_file, 'w', encoding='utf-8') as f:
		json.dump(fixes, f, indent=4)

fix_page_two()