with open(r'c:\Users\jhoan\Documents\gicateca_tesis\tests\test_engine_normalizer.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines, 1):
    if 'class TestNormalizeCuerpo' in line:
        print(f"Line {i}: {line.strip()}")
