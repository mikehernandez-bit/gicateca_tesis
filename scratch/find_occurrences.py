import re

with open(r'c:\Users\jhoan\Documents\gicateca_tesis\app\engine\normalizer.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines, 1):
    if 'paragraph_centered' in line:
        print(f"Line {i}: {line.strip()}")
