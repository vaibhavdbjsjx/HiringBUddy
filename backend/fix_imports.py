import os

def fix_file(filepath):
    with open(filepath, 'r') as f:
        content = f.read()
    content = content.replace("from config", "from config")
    with open(filepath, 'w') as f:
        f.write(content)

for root, _, files in os.walk('.'):
    for file in files:
        if file.endswith('.py'):
            fix_file(os.path.join(root, file))

