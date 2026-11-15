from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

root = Path(__file__).resolve().parent
extension = root / "extension"
target = root / "sketchup-ai-bridge.rbz"
with ZipFile(target, "w", ZIP_DEFLATED) as archive:
    for file in sorted(extension.rglob("*")):
        if file.is_file():
            archive.write(file, file.relative_to(extension))
print(target)
