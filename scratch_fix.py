import sys

file_path = r'c:\Users\Sahan\Documents\Agents development\MicroFinance-AgenticAi\microfinance-ai-system\frontend\app\(dashboard)\audit\page.tsx'
with open(file_path, 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('{String(r.username || r.user || "System")}', '{String(r.user_name || r.username || r.user || "System")}')

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(text)
print('Replaced string in frontend/app/(dashboard)/audit/page.tsx')
