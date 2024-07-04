import json
from gpt import GptEmbeddings
from lib import get_api_key, get_cosine_similarity
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
        self.o = o

class Promblem:
    line: int
    problem: str

    def __init__(self, html: str, o: dict, wcga_errors: List[WCGAError]):
        self.line = o['line']
        self.problem = html.split('\n')[self.line - 1].strip()
        self.wcga_error = None
        guideline = o['guideline']
        o['problem'] = self.problem
        self.o = o
        for err in wcga_errors:
            if err.guideline == guideline:
                self.wcga_error = err
        if self.wcga_error is None:
            raise Exception(f"Could not find guidline {guideline} for line {self.line}")

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
        problems.append(Promblem(html, item, wcga_errors))
    return problems

api_key = get_api_key()
embed = GptEmbeddings(api_key)

def get_fixes_from_objects(fixes_objects: List[dict]):
    fixes = []
    for item in fixes_objects:
        fixes.append(GptFix(item, embed.get_embedding(item['offending_line'])))
    return fixes

def get_fixes_for_guideline(fixes_file: str, guideline: str):
    with open(fixes_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    for item in data:
        if item['guideline'] != guideline:
            continue
        return get_fixes_from_objects(item['error_fixes'])

def get_fixes(file_name: str):
    with open(file_name, 'r', encoding='utf-8') as f:
        return get_fixes_from_objects(json.load(f))

def get_closest_fix_for_problem(problem: Promblem, fixes: List[GptFix]):
    closest = (0, None)
    for fix in fixes:
        problem_embedding = embed.get_embedding(problem.problem)
        sim = get_cosine_similarity(problem_embedding, fix.embedding)
        if sim > closest[0]:
            closest = (sim, fix)
    return closest[1]

WCGA_ERROR_FILE = 'wcga_errors.json'
def get_no_context_fixes_for_problems(html_file: str, violations_file: str, fixes_file: str):
    with open(html_file, 'r', encoding='utf-8') as f:
        html = f.read()

    wcga_errors = get_wcga_errors(WCGA_ERROR_FILE)
    problems = get_violations(html, violations_file, wcga_errors)
    output = []
    for problem in problems:
        fixes = get_fixes(fixes_file)
        closest_fix = get_closest_fix_for_problem(problem, fixes)
        output.append({
            "html_file": html_file,
            "guideline": problem.wcga_error.o,
            "problem": problem.o,
            "closest_fix": closest_fix.o
        })

    return output

def get_specific_fixes_for_problems(html_file: str, violations_file: str, fixes_file: str):
    with open(html_file, 'r', encoding='utf-8') as f:
        html = f.read()

    wcga_errors = get_wcga_errors(WCGA_ERROR_FILE)
    problems = get_violations(html, violations_file, wcga_errors)
    output = []
    for problem in problems:
        fixes = get_fixes_for_guideline(fixes_file, problem.wcga_error.guideline)
        closest_fix = get_closest_fix_for_problem(problem, fixes)
        output.append({
            "html_file": html_file,
            "guideline": problem.wcga_error.o,
            "problem": problem.o,
            "closest_fix": closest_fix.o
        })

    return output

OUTPUT_FILE = 'specific/output.json'
VIOLATIONS_FILE = 'specific/violations.json'
FIXES_FILE = 'specific/output_one.json'
HTML_FILE = 'specific/project1.html'

# output = get_no_context_fixes_for_problems(HTML_FILE, VIOLATIONS_FILE, FIXES_FILE)
# with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
#     json.dump(output, f, indent=4)

output = get_specific_fixes_for_problems(HTML_FILE, VIOLATIONS_FILE, FIXES_FILE)
with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
    json.dump(output, f, indent=4)