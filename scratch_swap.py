import re

def swap():
    with open('frontend/app/(dashboard)/loans/[id]/page.tsx', 'r', encoding='utf-8') as f:
        content = f.read()

    # Find cashflow block
    cashflow_regex = re.compile(r'(          \{cashflow && \(\n            <Card title="Cashflow Summary">.*?<\/Card>\n          \)\}\n)', re.DOTALL)
    cashflow_match = cashflow_regex.search(content)
    if not cashflow_match:
        print("Cashflow not found")
        return
    cashflow_str = cashflow_match.group(1)

    # Find documents and notes block
    docs_notes_regex = re.compile(r'(          \{\/\* Documents \*\/.*?<\/Card>\n          \)\}\n)', re.DOTALL)
    docs_notes_match = docs_notes_regex.search(content)
    if not docs_notes_match:
        print("Docs/Notes not found")
        return
    docs_notes_str = docs_notes_match.group(1)

    # First, remove them both
    content = content.replace(cashflow_str, "%%CASHFLOW_PLACEHOLDER%%\n")
    content = content.replace(docs_notes_str, "%%DOCS_NOTES_PLACEHOLDER%%\n")
    
    # Then insert them in each other's places
    content = content.replace("%%CASHFLOW_PLACEHOLDER%%\n", docs_notes_str)
    content = content.replace("%%DOCS_NOTES_PLACEHOLDER%%\n", cashflow_str)
    
    content = content.replace('{/* Right Column — Actions */}', '{/* Right Column — Actions & Cashflow */}')

    with open('frontend/app/(dashboard)/loans/[id]/page.tsx', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Swapped successfully")

if __name__ == "__main__":
    swap()
