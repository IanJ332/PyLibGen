# test_quick.py
import os
import sys

print(f"Python version: {sys.version}")
print(f"Current directory: {os.getcwd()}")

try:
    # Try to import pandas
    import pandas as pd
    print("✅ pandas imported successfully")
except ImportError as e:
    print(f"❌ pandas import error: {e}")

try:
    # Try to import requests
    import requests
    print("✅ requests imported successfully")
except ImportError as e:
    print(f"❌ requests import error: {e}")

# Try our api module
print("\nTesting api module:")
api_path = os.path.join(os.getcwd(), "libgen_explorer", "api.py")
print(f"API path: {api_path}")
print(f"File exists: {os.path.exists(api_path)}")

if os.path.exists(api_path):
    # Print first 10 lines of the file to check content
    print("\nFirst 10 lines of api.py:")
    with open(api_path, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            if i < 10:
                print(f"{i+1}: {line.strip()}")
            else:
                break

try:
    # Import directly from the file
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "api", 
        os.path.join(os.getcwd(), "libgen_explorer", "api.py")
    )
    api = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(api)
    
    # Check if the class exists
    if hasattr(api, 'LibGenAPI'):
        print("✅ LibGenAPI class found in api.py")
        # Try to create an instance
        try:
            api_instance = api.LibGenAPI()
            print("✅ LibGenAPI instance created successfully")
        except Exception as e:
            print(f"❌ Error creating LibGenAPI instance: {e}")
    else:
        print("❌ LibGenAPI class not found in api.py")
        print("Available objects in api.py:", [name for name in dir(api) if not name.startswith('__')])
except Exception as e:
    print(f"❌ Error importing api.py: {e}")

print("\nTrying to import from package:")
try:
    import libgen_explorer
    print("✅ libgen_explorer package imported")
    print("Contents of libgen_explorer package:", [name for name in dir(libgen_explorer) if not name.startswith('__')])
except ImportError as e:
    print(f"❌ Import error: {e}")