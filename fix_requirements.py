with open('requirements.txt', 'r') as f:
    lines = f.readlines()

with open('requirements.txt', 'w') as f:
    for line in lines:
        if 'PyQt6-Multimedia' not in line:
            f.write(line)
