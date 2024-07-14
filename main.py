import os
from typing import Callable
from lib import get_api_key, find_fixes_for_file, WCGAError
from gpt import GptEmbeddings, GptChat

from t_1_No_Context.no_ctx import no_ctx_get_fix
from t_2_Guidance.guidance import guidance_get_fix
from t_3_Few_Shot.few_shot import fs_get_fix
from t_4_CoT.cot import cot_get_fix
from t_5_Compile.compile import compile

SIM_THRESHOLD = .6

def run_test(
		get_fix: Callable[[GptChat, str, WCGAError], dict], 
		folder: str,
		api_key: str, 
		embed: GptEmbeddings
    ):
	chat = GptChat(f'{folder}/sys_prompt.txt', api_key)
	for file in os.listdir('html'):
		find_fixes_for_file(get_fix, chat, embed, file, folder, SIM_THRESHOLD, True)

def run():
    api_key = get_api_key()
    embed = GptEmbeddings(api_key)
    run_test(no_ctx_get_fix, 't_1_no_ctx', api_key, embed)
    run_test(guidance_get_fix, 't_2_guidance', api_key, embed)
    run_test(fs_get_fix, 't_3_few_shot', api_key, embed)
    run_test(cot_get_fix, 't_4_cot', api_key, embed)
    compile()

run()