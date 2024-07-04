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
