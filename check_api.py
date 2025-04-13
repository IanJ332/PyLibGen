# check_api.py
import os

api_path = os.path.join(os.getcwd(), "libgen_explorer", "api.py")
print(f"API path: {api_path}")
print(f"File exists: {os.path.exists(api_path)}")

if os.path.exists(api_path):
    # Print the entire file content
    print("\nContent of api.py:")
    with open(api_path, 'r', encoding='utf-8') as f:
        content = f.read()
        print(content)
        # Check if LibGenAPI class is in the content
        print("\nContains 'class LibGenAPI':", "class LibGenAPI" in content)