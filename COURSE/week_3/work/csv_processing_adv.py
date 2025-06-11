"""
JSON Handling
-----------
Complete the following functions according to their docstrings.
This exercise focuses on working with JSON data in Python.
"""

import json
import os
import csv
from typing import Dict, List, Union, Tuple, Any, Optional

# Type aliases for clarity
JSONData = Union[Dict[str, Any], List[Any]]
SchemaType = Dict[str, Dict[str, Union[str, bool]]]
ValidationResult = Tuple[bool, List[str]]

def read_json_file(filepath: str) -> JSONData:
    """
    Read and parse a JSON file.
    
    Args:
        filepath (str): Path to the JSON file
        
    Returns:
        dict or list: Parsed JSON data
        
    Raises:
        FileNotFoundError: If the file doesn't exist
        json.JSONDecodeError: If the file contains invalid JSON
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def write_json_file(filepath: str, data: JSONData, indent: int = 2) -> bool:
    """
    Write data to a JSON file.
    
    Args:
        filepath (str): Path to the JSON file
        data (dict or list): Data to write
        indent (int, optional): Number of spaces for indentation. Defaults to 2.
        
    Returns:
        bool: True if write was successful
        
    Raises:
        TypeError: If data is not JSON serializable
    """
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=indent, ensure_ascii=False)
        return True
    except TypeError as e:
        raise TypeError(f"Data is not JSON serializable: {e}")

def update_json_file(filepath: str, update_dict: Dict[str, Any], 
                    create_if_not_exists: bool = False) -> Dict[str, Any]:
    """
    Update a JSON file with new key-value pairs.
    If the file contains a dictionary, update the dictionary.
    If the file doesn't exist and create_if_not_exists is True, create a new file.
    
    Args:
        filepath (str): Path to the JSON file
        update_dict (dict): Dictionary with updates
        create_if_not_exists (bool, optional): Whether to create the file if it doesn't exist. 
                                               Defaults to False.
        
    Returns:
        dict: Updated JSON data
        
    Raises:
        FileNotFoundError: If the file doesn't exist and create_if_not_exists is False
        TypeError: If the file doesn't contain a dictionary
    """
    if not os.path.exists(filepath):
        if create_if_not_exists:
            data: Dict[str, Any] = {}
        else:
            raise FileNotFoundError(f"File not found: {filepath}")
    else:
        data = read_json_file(filepath)
        
    if not isinstance(data, dict):
        raise TypeError("JSON file must contain a dictionary to be updated")
    
    data.update(update_dict)
    write_json_file(filepath, data)
    return data

def search_json(data: JSONData, key: str) -> List[Any]:
    """
    Search for all occurrences of a key in a JSON structure (recursive).
    
    Args:
        data (dict or list): JSON data to search
        key (str): Key to search for
        
    Returns:
        list: List of values corresponding to the key
    """
    results: List[Any] = []
    
    def search_recursive(obj: Any) -> None:
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k == key:
                    results.append(v)
                search_recursive(v)
        elif isinstance(obj, list):
            for item in obj:
                search_recursive(item)
    
    search_recursive(data)
    return results

def validate_json_schema(data: Dict[str, Any], schema: SchemaType) -> ValidationResult:
    """
    Validate a JSON object against a simple schema.
    
    A simple schema is a dictionary where:
    - Keys are the expected keys in the data
    - Values are dictionaries with:
        - 'type': The expected type ('str', 'int', 'float', 'bool', 'dict', 'list', etc.)
        - 'required': Boolean indicating if the key is required
    
    Example schema:
    {
        'name': {'type': 'str', 'required': True},
        'age': {'type': 'int', 'required': False}
    }
    
    Args:
        data (dict): JSON data to validate
        schema (dict): Schema to validate against
        
    Returns:
        tuple: (is_valid, errors) where is_valid is a boolean and
               errors is a list of error messages (empty if valid)
    """
    errors: List[str] = []
    
    # Map string type names to Python types
    type_map: Dict[str, type] = {
        'str': str,
        'int': int,
        'float': float,
        'bool': bool,
        'dict': dict,
        'list': list
    }
    
    # Check for required keys
    for key, rules in schema.items():
        if rules.get('required', False) and key not in data:
            errors.append(f"Required key '{key}' is missing")
    
    # Check data types
    for key, value in data.items():
        if key in schema:
            expected_type = schema[key].get('type')
            if expected_type:
                if expected_type in type_map:
                    expected_python_type = type_map[expected_type]
                    if not isinstance(value, expected_python_type):
                        errors.append(f"Key '{key}' should be of type '{expected_type}', but is '{type(value).__name__}'")
    
    is_valid = len(errors) == 0
    return is_valid, errors

def convert_csv_to_json(csv_filepath: str, json_filepath: str, has_header: bool = True) -> bool:
    """
    Convert a CSV file to a JSON file.
    
    Args:
        csv_filepath (str): Path to the CSV file
        json_filepath (str): Path to the output JSON file
        has_header (bool, optional): Whether the CSV has a header row. Defaults to True.
        
    Returns:
        bool: True if conversion was successful
        
    Raises:
        FileNotFoundError: If the CSV file doesn't exist
    """
    if not os.path.exists(csv_filepath):
        raise FileNotFoundError(f"CSV file not found: {csv_filepath}")
    
    data: List[Union[Dict[str, str], List[str]]] = []
    
    with open(csv_filepath, 'r', encoding='utf-8') as csvfile:
        if has_header:
            reader = csv.DictReader(csvfile)
            for row in reader:
                data.append(dict(row))
        else:
            reader = csv.reader(csvfile)
            for row in reader:
                data.append(row)
    
    write_json_file(json_filepath, data)
    return True

def merge_json_files(filepaths: List[str], output_filepath: str) -> JSONData:
    """
    Merge multiple JSON files into one. All files must contain either dictionaries or lists.
    
    If files contain dictionaries, merge them into a single dictionary.
    If files contain lists, concatenate them into a single list.
    
    Args:
        filepaths (list): List of paths to JSON files
        output_filepath (str): Path to the output JSON file
        
    Returns:
        dict or list: Merged JSON data
        
    Raises:
        FileNotFoundError: If any input file doesn't exist
        TypeError: If input files contain incompatible types
    """
    if not filepaths:
        raise ValueError("No filepaths provided")
    
    # Read the first file to determine the type
    first_data = read_json_file(filepaths[0])
    
    if isinstance(first_data, dict):
        merged_data: Dict[str, Any] = {}
        for filepath in filepaths:
            data = read_json_file(filepath)
            if not isinstance(data, dict):
                raise TypeError(f"File {filepath} contains {type(data).__name__}, but expected dict")
            merged_data.update(data)
    elif isinstance(first_data, list):
        merged_data: List[Any] = []
        for filepath in filepaths:
            data = read_json_file(filepath)
            if not isinstance(data, list):
                raise TypeError(f"File {filepath} contains {type(data).__name__}, but expected list")
            merged_data.extend(data)
    else:
        raise TypeError(f"Unsupported JSON type: {type(first_data).__name__}")
    
    write_json_file(output_filepath, merged_data)
    return merged_data

def pretty_print_json(data: JSONData) -> str:
    """
    Pretty print JSON data.
    
    Args:
        data (dict or list): JSON data to print
        
    Returns:
        str: Pretty-printed JSON string
    """
    return json.dumps(data, indent=2, ensure_ascii=False)

def main() -> None:
    """Run examples to test your functions."""
    # Create a sample JSON file
    sample_data: Dict[str, Any] = {
        "people": [
            {"id": 1, "name": "John", "age": 30, "city": "New York"},
            {"id": 2, "name": "Jane", "age": 25, "city": "Los Angeles"},
            {"id": 3, "name": "Bob", "age": 35, "city": "Chicago"}
        ],
        "organization": "Example Corp",
        "created_at": "2023-06-15"
    }
    sample_file: str = "sample.json"
    write_json_file(sample_file, sample_data)
    print(f"Created sample JSON file: {sample_file}")
    
    # Read JSON file
    print("\nReading JSON file:")
    data = read_json_file(sample_file)
    print(pretty_print_json(data))
    
    # Update JSON file
    print("\nUpdating JSON file:")
    update_dict: Dict[str, str] = {
        "organization": "New Corp",
        "updated_at": "2023-06-16"
    }
    updated_data = update_json_file(sample_file, update_dict)
    print(f"Updated data: {pretty_print_json(updated_data)}")
    
    # Search JSON
    print("\nSearching for 'name' in JSON:")
    names = search_json(data, "name")
    print(f"Found names: {names}")
    
    # Validate JSON
    print("\nValidating JSON against schema:")
    schema: SchemaType = {
        "people": {"type": "list", "required": True},
        "organization": {"type": "str", "required": True},
        "created_at": {"type": "str", "required": False}
    }
    is_valid, errors = validate_json_schema(data, schema)
    print(f"Is valid: {is_valid}")
    if errors:
        print(f"Validation errors: {errors}")
    
    # Clean up
    os.remove(sample_file)
    print(f"\nCleaned up sample file: {sample_file}")

if __name__ == "__main__":
    main()  