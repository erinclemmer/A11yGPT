import os
import json
import time
import datetime
from typing import List

from openai import OpenAI
import tiktoken

class Message:
    role: str
    content: str

    def __init__(self, role: str, content: str):
        self.role = role
        self.content = content

class Conversation:
    messages: List[Message]

    def __init__(self, messages: List[Message]):
        self.messages = messages

    def to_object(self):
        messages = []
        for m in self.messages:
            messages.append({
                "role": m.role,
                "content": m.content
            })
        return messages
    
    def to_string(self):
        s = ''
        for msg in self.messages:
            s += f'########\nRole: {msg.role}\n{msg.content}\n\n'
        return s

class GptEmbeddings:
    def __init__(self, api_key: str):
        self.openai_client = OpenAI(api_key=api_key)

    def get_embedding(self, text: str):
        return self.openai_client.embeddings.create(
            input=text,
            model="text-embedding-3-large"
        ).data[0].embedding

class GptChat:
    messages: List[Message]
    conversations: List[Conversation]

    def __init__(self, system_prompt_file: str, api_key: str) -> None:
        if not os.path.exists(system_prompt_file):
            raise Exception(f"Could not find sys prompt file at {system_prompt_file}")
        with open(system_prompt_file, 'r', encoding='utf-8') as f:
            self.system_prompt = f.read()
        
        self.openai_client = OpenAI(api_key=api_key)
        self.encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
        self.system_prompt_tokens = len(self.encoding.encode(self.system_prompt))
        self.messages = []
        self.conversations = []
        self.reset_chat()
        self.total_tokens = 0

    def save_completions(self, file_name):
        if len(self.conversations) == 0:
            return
        text = ''
        for completion in self.conversations:
            text += json.dumps(completion.to_object()) + '\n'
        today = datetime.date.today().strftime("%Y-%m-%d")
        if not os.path.exists('completions'):
            os.mkdir('completions')
        with open(f'completions/{file_name}_{today}.jsonl', 'w', encoding='utf-8') as f:
            f.write(text)

    def add_message(self, role: str, message: str):
        self.messages.append(Message(role, message))

    def reset_chat(self):
        if len(self.messages) > 1:
            self.conversations.append(Conversation(self.messages))
        self.messages = [ ]
        self.add_message("system", self.system_prompt)

    def get_message_tokens(self) -> int:
        message_tokens = 0
        for m in self.messages:
            message_tokens += len(self.encoding.encode(m.content))
        return message_tokens

    def send(self, message: str, max_tokens=500) -> str:
        message_tokens = self.get_message_tokens()
        message_tokens += len(self.encoding.encode(message))
        print(f"Sending chat with {message_tokens} tokens")
        
        if message_tokens >= 4096 - 200:
            raise "Chat Error too many tokens"
        
        self.add_message("user", message)
        
        defaultConfig = {
            "model": 'gpt-3.5-turbo',
            "max_tokens": max_tokens,
            "messages": Conversation(self.messages).to_object(),
            "temperature": 1
        }

        try:
            res = self.openai_client.chat.completions.create(**defaultConfig)
        except:
            print('Error when sending chat, retrying in one minute')
            time.sleep(60)
            self.messages = self.messages[:-1]
            self.send(message, max_tokens)
        msg = res.choices[0].message.content.strip()
        print(f"GPT API responded with {res.usage.completion_tokens} tokens")
        self.add_message(msg, "assistant")
        self.total_tokens += res.usage.total_tokens
        return msg