from lib import get_api_key, run_test
from gpt import GptEmbeddings

from t_1_No_Context.no_ctx import no_ctx_get_fix
from t_2_Guidance.guidance import guidance_get_fix
from t_3_Few_Shot.few_shot import fs_get_fix
from t_4_CoT.cot import cot_get_fix
from Compile.compile import compile

SIM_THRESHOLD = .6

def run():
    api_key = get_api_key()
    embed = GptEmbeddings(api_key)
    folders = [
        't_2_Guidance',
        't_3_Few_Shot',
        't_4_CoT'
    ]
    run_test(no_ctx_get_fix, 't_1_No_Context', api_key, embed, SIM_THRESHOLD, no_ctx=True)
    run_test(guidance_get_fix, folders[1], api_key, embed, SIM_THRESHOLD)
    run_test(fs_get_fix, folders[2], api_key, embed, SIM_THRESHOLD)
    run_test(cot_get_fix, folders[3], api_key, embed, SIM_THRESHOLD)
    compile(api_key, folders)

run()