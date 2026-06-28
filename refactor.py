import os
import re

html_files = [f for f in os.listdir('.') if f.endswith('.html')]

for filepath in html_files:
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Replace onclick="window.location.href='...'" with data-href="..."
    new_content = re.sub(r'onclick="window\.location\.href=\'([^\']+)\'"', r'data-href="\1"', content)
    
    if new_content != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Updated {filepath}")
