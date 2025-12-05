file_path = r'c:\Users\Soham\OneDrive\Desktop\DataQualityWatchTowers\templates\dashboard\home_enhanced.html'
with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Indices are 0-based, so line N is index N-1.

# Block 3: Style injection (1205-1212) -> Indices 1204-1211 (inclusive)
print("Block 3:")
for i in range(1204, 1212):
    if i < len(lines):
        print(f"{i+1}: {lines[i].rstrip()}")

# Block 2: Theme logic (507-537) -> Indices 506-536 (inclusive)
print("\nBlock 2:")
for i in range(506, 537):
    if i < len(lines):
        print(f"{i+1}: {lines[i].rstrip()}")

# Block 1: Button (282-284) -> Indices 281-283 (inclusive)
print("\nBlock 1:")
for i in range(281, 284):
    if i < len(lines):
        print(f"{i+1}: {lines[i].rstrip()}")
