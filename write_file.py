import sys
from pathlib import Path

if len(sys.argv) < 2:
    print("Usage: python write_file.py <relative_path>")
    sys.exit(1)

rel = sys.argv[1]
print(f"Paste content for {rel}")
print("Then press Ctrl+Z and Enter to finish:")
print("-" * 60)

content = sys.stdin.read()

p = Path(rel)
p.parent.mkdir(parents=True, exist_ok=True)
p.write_text(content, encoding="utf-8")
print("-" * 60)
print(f"WROTE: {rel} ({len(content)} bytes)")