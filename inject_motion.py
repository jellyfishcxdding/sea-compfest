"""
Inject motion.css and motion.js into every HTML file.
Purely additive — does not change any existing tags.
"""
import os

HTML_DIR = r"C:\Users\Gracia\OneDrive - Bina Nusantara\activity\COMPFEST\seapedia"

CSS_TAG  = '<link rel="stylesheet" href="css/motion.css">'
JS_TAG   = '<script src="js/motion.js"></script>'

for fname in os.listdir(HTML_DIR):
    if not fname.endswith('.html'):
        continue
    path = os.path.join(HTML_DIR, fname)
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    changed = False

    # Inject CSS right before </head>
    if CSS_TAG not in content and '</head>' in content:
        content = content.replace('</head>', f'    {CSS_TAG}\n</head>', 1)
        changed = True

    # Inject JS right before </body> (after all existing scripts)
    if JS_TAG not in content and '</body>' in content:
        content = content.replace('</body>', f'    {JS_TAG}\n</body>', 1)
        changed = True

    if changed:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f'  Injected into: {fname}')
    else:
        print(f'  Already done:  {fname}')

print("\nAll done!")
