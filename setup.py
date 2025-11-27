import sys
import re

# Map PyPI package names to their import names
MAPPINGS = {
    "pillow": "PIL",
    "scikit-image": "skimage",
    "python-docx": "docx",
    "python-dotenv": "dotenv",
    "PyMuPDF": "pymupdf",
    "streamlit-extras": "streamlit_extras",
    "opencv-python": "cv2",
    "pytz": "pytz",
    "python-multipart": "multipart",
    # Example of same name
    # Add more mappings as needed
}

def parse_requirements_line(line):
    line = line.split('#', 1)[0].strip()
    if not line:
        return None
    package_name = re.split(r'[<>=~!@#]', line, maxsplit=1)[0].strip()
    package_name = package_name.split('[', 1)[0].strip()
    return package_name

def read_requirements(file_path):
    packages = []
    try:
        with open(file_path, 'r') as f:
            for line in f:
                pkg = parse_requirements_line(line)
                if pkg:
                    packages.append(pkg)
    except FileNotFoundError:
        print(f"❌ Error: {file_path} not found.", file=sys.stderr)
        sys.exit(1)
    return packages

def test_import(pkg_name):
    import_name = MAPPINGS.get(pkg_name, pkg_name)
    try:
        __import__(import_name)
        print(f"✅ {pkg_name} imported successfully (as {import_name})")
    except ImportError:
        print(f"❌ {pkg_name} (imported as {import_name}) NOT installed", file=sys.stderr)

print("Testing package installations...\n")
packages = read_requirements("requirements.txt")
for pkg in packages:
    test_import(pkg)