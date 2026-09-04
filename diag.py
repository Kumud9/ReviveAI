import os
from dotenv import load_dotenv

env_path = os.path.abspath('.env')
print('.env path:', env_path)
print('.env exists:', os.path.exists(env_path))

has_key = False
has_model = False

if os.path.exists(env_path):
    with open(env_path, 'r', encoding='utf-8') as f:
        content = f.read()
        for line in content.splitlines():
            line = line.strip()
            if line.startswith('LLM_API_KEY=') and len(line) > len('LLM_API_KEY='):
                has_key = True
            if line.startswith('LLM_MODEL=') and len(line) > len('LLM_MODEL='):
                has_model = True

print('LLM_API_KEY in file:', 'YES' if has_key else 'NO')
print('LLM_MODEL in file:', 'YES' if has_model else 'NO')

load_dotenv()
print('LLM_API_KEY detected:', 'YES' if bool(os.getenv('LLM_API_KEY')) else 'NO')
print('LLM_MODEL detected:', 'YES' if bool(os.getenv('LLM_MODEL')) else 'NO')
print('Working directory:', os.getcwd())
