with open(r'c:\Users\jhoan\Documents\gicateca_tesis\app\modules\generation\preprocessor.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines, 1):
    if 'EXCLUDED_KEYS' in line:
        print(f"Line {i}: {line.strip()}")
