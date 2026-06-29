import os, glob

dash_dir = r"c:\Users\Sahan\Documents\Agents development\MicroFinance-AgenticAi\microfinance-ai-system\frontend\app\(dashboard)"
files = glob.glob(os.path.join(dash_dir, "**", "page.tsx"), recursive=True)

count=0
for file in files:
    with open(file, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    new_lines = []
    modified = False
    for line in lines:
        if '<h1 className="text-2xl font-bold text-[var(--text-primary)]"' in line:
            modified = True
            continue
        new_lines.append(line)
        
    if modified:
        with open(file, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
        count += 1
print(f"Modified {count} files")
