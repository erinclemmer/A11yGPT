def get_api_key():
	if not os.path.exists('config.json'):
		raise Exception("Could not find config.json")
	with open('config.json', 'r', encoding='utf-8') as f:
		config = json.load(f)

	if not 'openai_api_key' in config:
		raise Exception('Could not find key: openai_api_key in config')
	return config['openai_api_key']
