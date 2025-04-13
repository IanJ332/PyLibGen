# Content of test_direct.py
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath('.'))

try:
    from libgen_explorer.api import LibGenAPI
    print("Import successful!")
    api = LibGenAPI()
    print("API instance created successfully!")
except Exception as e:
    print(f"Error: {type(e).__name__}: {e}")
    
    # Let's see what's actually in the module
    import importlib.util
    import inspect
    
    spec = importlib.util.spec_from_file_location(
        "api_module", 
        os.path.join("libgen_explorer", "api.py")
    )
    api_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(api_module)
    
    print("\nContents of api.py:")
    for name, obj in inspect.getmembers(api_module):
        if not name.startswith('__'):
            print(f"- {name}: {type(obj)}")