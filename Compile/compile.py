import os
import json
from typing import List

from gpt import GptEmbeddings
from lib import get_cosine_similarity, WCGAError, GptFix, get_wcga_errors

WCGA_ERROR_FILE = 'wcga_errors.json'
VIOLATIONS_FILE = 'violations.json'

NO_CTX_FOLDER = '1_no_ctx'
GUIDANCE_FOLDER = '2_guidance'
FS_FOLDER = '3_fs'
COT_FOLDER = '4_cot'

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

def get_violations(html: str, html_file: str, violations_file: str, wcga_errors: List[WCGAError]) -> List[Promblem]:
    with open(violations_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    problems = []
    if not html_file in data:
        raise Exception(f'Could not find {html_file} key in violations file')
    for item in data[html_file]:
        problems.append(Promblem(html, item, wcga_errors))
    return problems

def get_fixes_from_objects(embed: GptEmbeddings, fixes_objects: List[dict]):
    fixes = []
    for item in fixes_objects:
        fixes.append(GptFix(item, embed.get_embedding(item['offending_line'])))
    return fixes

def get_fixes_for_guideline(embed: GptEmbeddings, fixes_file: str, guideline: str):
    with open(fixes_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    for item in data:
        if item['guideline'] != guideline:
            continue
        return get_fixes_from_objects(embed, item['error_fixes'])

def get_fixes(embed: GptEmbeddings, file_name: str):
    with open(file_name, 'r', encoding='utf-8') as f:
        return get_fixes_from_objects(embed, json.load(f))

def get_closest_fix_for_problem(embed: GptEmbeddings, problem: Promblem, fixes: List[GptFix]):
    closest = (0, None)
    for fix in fixes:
        problem_embedding = embed.get_embedding(problem.problem)
        sim = get_cosine_similarity(problem_embedding, fix.embedding)
        if sim > closest[0]:
            closest = (sim, fix)
    return closest[1]

def get_no_context_fixes_for_problems(embed: GptEmbeddings, html: str, html_file: str, violations_file: str, fixes_file: str):
    wcga_errors = get_wcga_errors(WCGA_ERROR_FILE)
    problems = get_violations(html, html_file, violations_file, wcga_errors)
    if problems is None:
        return []
    output = []
    for problem in problems:
        fixes = get_fixes(fixes_file)
        closest_fix = get_closest_fix_for_problem(embed, problem, fixes)
        output.append({
            "guideline": problem.wcga_error.o,
            "problem": problem.o,
            "closest_fix": closest_fix.o
        })

    return output

def get_guidance_fixes_for_problems(embed: GptEmbeddings, html: str, html_file: str, violations_file: str, fixes_file: str):
    wcga_errors = get_wcga_errors(WCGA_ERROR_FILE)
    problems = get_violations(html, html_file, violations_file, wcga_errors)
    if problems is None:
        return []
    output = []
    for problem in problems:
        fixes = get_fixes_for_guideline(embed, fixes_file, problem.wcga_error.guideline)
        closest_fix = get_closest_fix_for_problem(embed, problem, fixes)
        output.append({
            "guideline": problem.wcga_error.o,
            "problem": problem.o,
            "closest_fix": closest_fix.o if closest_fix is not None else None
        })

    return output

def compile(api_key: str, folders: List[str]):
    embed = GptEmbeddings(api_key)
    for folder in folders:
        if not os.path.exists(folder):
            os.mkdir(folder)

    if not os.path.exists('output'):
        os.mkdir('output')

    for html_file in os.listdir('html'):
        with open(f'html/{html_file}', 'r', encoding='utf-8') as f:
            html = f.read()

        no_ctx_fixes_file = f'fixes/1_No_Context/{html_file}.json'
        no_ctx_output_file = f'output/{NO_CTX_FOLDER}/{html_file}.json'
        if os.path.exists(no_ctx_fixes_file) and not os.path.exists(no_ctx_output_file):
            output_no_ctx = get_no_context_fixes_for_problems(embed, html, html_file, VIOLATIONS_FILE, no_ctx_fixes_file)
            with open(no_ctx_output_file, 'w', encoding='utf-8') as f:
                json.dump(output_no_ctx, f, indent=4)
        
        for folder in folders:
            fixes_file = f'fixes/{folder}/{html_file}.json'
            output_file = f'output/{folder}/{html_file}.json'
            if not os.path.exists(f'output/{folder}'):
                os.mkdir(f'output/{folder}')
            
            if os.path.exists(fixes_file) and not os.path.exists(output_file):
                output = get_guidance_fixes_for_problems(embed, html, html_file, VIOLATIONS_FILE, fixes_file)
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(output, f, indent=4)