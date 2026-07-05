import json
import sys
import os

def extract_architecture(file_path):
    print(f"Reading {file_path}...")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading file: {e}")
        return

    # Split into main sections by '@'
    sections = [sec.strip() for sec in content.split('@')]
    architecture = {}

    for i, section in enumerate(sections):
        if not section:
            continue
            
        # Split section into individual JSON strings by '|'
        items = [item.strip() for item in section.split('|') if item.strip()]
        
        section_summary = {
            "total_items_in_section": len(items),
            "unique_structures": []
        }
        
        schema_tracker = {}
        parse_errors = 0
        
        for item in items:
            try:
                parsed = json.loads(item)
                # Create a unique signature based on the keys present in the JSON
                keys_tuple = tuple(sorted(parsed.keys()))
                
                if keys_tuple not in schema_tracker:
                    schema_tracker[keys_tuple] = {
                        "count": 0,
                        "data_types": {k: type(v).__name__ for k, v in parsed.items()},
                        "example_data": parsed
                    }
                schema_tracker[keys_tuple]["count"] += 1
            except json.JSONDecodeError:
                parse_errors += 1

        for keys, data in schema_tracker.items():
            section_summary["unique_structures"].append(data)
            
        if parse_errors > 0:
            section_summary["json_parse_errors"] = parse_errors
            
        architecture[f"Section_{i}"] = section_summary

    output_file = 'save_architecture.json'
    with open(output_file, 'w', encoding='utf-8') as out:
        json.dump(architecture, out, indent=4)
    
    print(f"Success! Extracted architecture saved to: {os.path.abspath(output_file)}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python extract_schema.py <path_to_save_file>")
    else:
        extract_architecture(sys.argv[1])