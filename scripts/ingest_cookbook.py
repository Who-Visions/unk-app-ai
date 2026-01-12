import os
import json
import fnmatch

REPO_PATH = "temp_cookbook_repo"
OUTPUT_FILE = "gemini_cookbook_code.md"

def ingest_cookbook():
    with open(OUTPUT_FILE, "w", encoding="utf-8") as out:
        out.write("# Google Gemini Cookbook Code Examples\n\n")
        
        for root, dirs, files in os.walk(REPO_PATH):
            # Skip .git and irrelevant folders
            if ".git" in dirs:
                dirs.remove(".git")
            
            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, REPO_PATH)
                
                if file.endswith(".ipynb"):
                    process_notebook(file_path, rel_path, out)
                elif file.endswith(".py"):
                    process_python_file(file_path, rel_path, out)

def process_notebook(file_path, rel_path, out):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            notebook = json.load(f)
            
        out.write(f"\n## {rel_path}\n\n")
        
        for cell in notebook.get("cells", []):
            if cell.get("cell_type") == "code":
                source = "".join(cell.get("source", []))
                if source.strip():
                    out.write("```python\n")
                    out.write(source)
                    out.write("\n```\n")
    except Exception as e:
        print(f"Error processing {rel_path}: {e}")

def process_python_file(file_path, rel_path, out):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        out.write(f"\n## {rel_path}\n\n")
        out.write("```python\n")
        out.write(content)
        out.write("\n```\n")
    except Exception as e:
        print(f"Error processing {rel_path}: {e}")

if __name__ == "__main__":
    ingest_cookbook()
    print(f"Generated {OUTPUT_FILE}")
