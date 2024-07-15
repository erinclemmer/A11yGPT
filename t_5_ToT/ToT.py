# Based on Tree of thought paper: https://arxiv.org/abs/2305.10601

import re
import json
from time import sleep
from typing import Callable, List

from lib import GptChat, WCGAError

get_vote_prompt = lambda instruction: f'''
Given an instruction and several choices, decide which choice is most promising.
Analyze each choice in detail, then respond only with "The best choice is s", where s the integer id of the choice.

Consider the following instruction as a basis for your decision:
{instruction}

Choices:
'''

def get_ToT_sample(chat: GptChat, html: str, wcga_error: WCGAError):
    chat.reset_chat()
    chat.add_message("user", f"Here is the html for the page:\n{html}")
    chat.add_message("assistant", "Ok")
    chat.add_message("user", f"This is the type of problem: {wcga_error.success_criteria}")
    chat.add_message("assistant", "Ok")
    cot = chat.send('Think through finding the problem step by step')
    with open('t_5_ToT/result_prompt.txt', 'r', encoding='utf-8') as f:
        result_prompt = f.read()
    data = json.loads(chat.send(result_prompt))
    data['CoT'] = cot
    return data

class ToT:
    task: str
    get_sample: Callable[[], str]
    get_sample_string: Callable[[any], str]
    num_samples: int

    def __init__(
            self, 
            api_key: str, 
            get_sample: Callable[[], str], 
            get_sample_string: Callable[[any], str],
            num_samples: int, 
            num_votes: int, 
            vote_prompt: str
        ):
        self.num_samples = num_samples
        self.get_sample = get_sample
        self.get_sample_string = get_sample_string
        if self.get_sample_string is None:
            self.get_sample_string = lambda x: x
        self.num_votes = num_votes
        self.vote_prompt = vote_prompt
        self.chat = GptChat(None, api_key)

    def get_samples(self):
        samples = []
        for i in range(self.num_samples):
            print(f'Getting sample {i + 1} of {self.num_samples}')
            samples.append(self.get_sample())
        return samples

    def get_vote_prompt(self, samples: List[str]):
        prompt = self.vote_prompt
        for i, y in enumerate(samples, 1):
            prompt += f'Choice {i}: {y}\n\n'
        return prompt

    def get_vote(self, samples: List[str]):
        prompt = self.get_vote_prompt(samples)
        self.chat.reset_chat()
        vote_output = self.chat.send(prompt)
        pattern = r".*best choice is .*(\d+).*"
        match = re.match(pattern, vote_output, re.DOTALL)
        try:
            if match:
                vote = int(match.groups()[0]) - 1
                if vote in range(len(samples)):
                    return vote
                else:
                    print(f'vote out of range: {vote}')
                    return self.get_vote(samples)
            else:
                print(f'vote no match: {[vote_output]}')
                return self.get_vote(samples)
        except Exception as e:
            print(f'vote exception: {e}')
            sleep(1)
            return self.get_vote(samples)

    def get_votes(self, samples: List[str]):
        vote_result = [0] * len(samples)
        print(f'Vote Prompt:\n{self.get_vote_prompt(samples)}')
        for _ in range(self.num_votes):
            print(f'Getting vote {_ + 1} of {self.num_votes}')
            vote = self.get_vote(samples)
            vote_result[vote] += 1
        return vote_result

    def select_sample(self, samples: List[str], votes: List[int]):
        max_votes = (0, -1)
        for i, v in enumerate(votes):
            if v > max_votes[0]:
                max_votes = (v, samples[i])
        print(f'votes: {votes}')
        return max_votes[1]

    def run(self):
        samples = self.get_samples()
        sample_strings = [self.get_sample_string(s) for s in samples]
        votes = self.get_votes(sample_strings)
        return self.select_sample(samples, votes)

def get_ToT_fix(chat: GptChat, html: str, wcga_error: WCGAError):
    with open('t_5_ToT/sys_prompt.txt', 'r', encoding='utf-8') as f:
        instruction = f.read()
    vote_prompt = get_vote_prompt(instruction)
    def get_sample():
        return get_ToT_sample(chat, html, wcga_error)
    def get_sample_string(sample):
        offending_line = sample['offending_line']
        fixed_line = sample['fixed_line']
        return f'Offending line: {offending_line}\n\nFixed line: {fixed_line}'
    tot = ToT(chat.api_key, get_sample, get_sample_string, 4, 3, vote_prompt)
    return tot.run()