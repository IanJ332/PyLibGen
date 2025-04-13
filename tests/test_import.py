# test_import.py
try:
    from libgen_explorer.api import LibGenAPI
    print("Import successful!")
    api = LibGenAPI()
    print("API instance created successfully!")
except Exception as e:
    print(f"Error: {e}")