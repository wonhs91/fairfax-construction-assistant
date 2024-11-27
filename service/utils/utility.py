
import re
import json

def extract_json_from_string(string):
    # Find patterns that look like JSON objects
    pattern = r'{[^{}]*}'
    matches = re.finditer(pattern, string)
    
    results = []
    for match in matches:
        try:
            json_obj = json.loads(match.group())
            results.append(json_obj)
        except json.JSONDecodeError:
            continue
    
    return results
