"""
File Operations Exercise
----------------------
Complete the following functions according to their docstrings.
This exercise focuses on reading, writing, and manipulating files in Python.
"""

import os
import shutil
import time

def read_text_file(filepath):
    """
    Read and return the contents of a text file.
    
    Args:
        filepath (str): Path to the text file
        
    Returns:
        str: Contents of the file
        
    Raises:
        FileNotFoundError: If the file doesn't exist
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")
    
    with open(filepath, 'r', encoding='utf-8') as file:
        return file.read()

def write_text_file(filepath, content, mode='w'):
    """
    Write content to a text file.
    
    Args:
        filepath (str): Path to the text file
        content (str): Content to write to the file
        mode (str, optional): File open mode ('w' for write, 'a' for append). Defaults to 'w'.
        
    Returns:
        bool: True if write was successful
        
    Raises:
        IOError: If writing to the file fails
    """
    try:
        with open(filepath, mode, encoding='utf-8') as file:
            file.write(content)
        return True
    except IOError as e:
        raise IOError(f"Failed to write to file: {e}")

def count_lines_words_chars(filepath):
    """
    Count the number of lines, words, and characters in a text file.
    
    Args:
        filepath (str): Path to the text file
        
    Returns:
        tuple: (line_count, word_count, char_count)
        
    Raises:
        FileNotFoundError: If the file doesn't exist
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")
    
    line_count = 0
    word_count = 0
    char_count = 0
    
    with open(filepath, 'r', encoding='utf-8') as file:
        for line in file:
            line_count += 1
            word_count += len(line.split())
            char_count += len(line)
    
    return (line_count, word_count, char_count)

def find_and_replace(filepath, old_text, new_text):
    """
    Find all occurrences of old_text in the file and replace with new_text.
    
    Args:
        filepath (str): Path to the text file
        old_text (str): Text to find
        new_text (str): Text to replace with
        
    Returns:
        int: Number of replacements made
        
    Raises:
        FileNotFoundError: If the file doesn't exist
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")
    
    # Read the file content
    with open(filepath, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Count replacements
    replacement_count = content.count(old_text)
    
    # Replace text
    new_content = content.replace(old_text, new_text)
    
    # Write back to file
    with open(filepath, 'w', encoding='utf-8') as file:
        file.write(new_content)
    
    return replacement_count

def copy_file(source, destination, overwrite=False):
    """
    Copy a file from source to destination.
    
    Args:
        source (str): Path to the source file
        destination (str): Path to the destination file
        overwrite (bool, optional): Whether to overwrite if destination exists. Defaults to False.
        
    Returns:
        bool: True if copy was successful
        
    Raises:
        FileNotFoundError: If the source file doesn't exist
        FileExistsError: If destination exists and overwrite is False
    """
    if not os.path.exists(source):
        raise FileNotFoundError(f"Source file not found: {source}")
    
    if os.path.exists(destination) and not overwrite:
        raise FileExistsError(f"Destination file already exists: {destination}")
    
    shutil.copy2(source, destination)
    return True

def create_directory_structure(base_path, structure):
    """
    Create a directory structure based on the provided dictionary.
    
    Args:
        base_path (str): Base path where to create the structure
        structure (dict): Directory structure represented as a dictionary
            Example: {'dir1': {'subdir1': {}, 'subdir2': {}}, 'dir2': {}}
        
    Returns:
        bool: True if structure was created successfully
        
    Raises:
        IOError: If directory creation fails
    """
    try:
        def create_dirs(current_path, struct):
            for dir_name, substructure in struct.items():
                dir_path = os.path.join(current_path, dir_name)
                os.makedirs(dir_path, exist_ok=True)
                if substructure:
                    create_dirs(dir_path, substructure)
        
        create_dirs(base_path, structure)
        return True
    except Exception as e:
        raise IOError(f"Failed to create directory structure: {e}")

def get_file_info(filepath):
    """
    Get information about a file.
    
    Args:
        filepath (str): Path to the file
        
    Returns:
        dict: Dictionary containing:
            - size: File size in bytes
            - last_modified: Last modification timestamp
            - created: Creation timestamp
            - is_directory: Boolean indicating if it's a directory
            - extension: File extension (empty if directory)
        
    Raises:
        FileNotFoundError: If the file doesn't exist
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")
    
    stat_info = os.stat(filepath)
    is_dir = os.path.isdir(filepath)
    
    info = {
        'size': stat_info.st_size,
        'last_modified': stat_info.st_mtime,
        'created': stat_info.st_ctime,
        'is_directory': is_dir,
        'extension': '' if is_dir else os.path.splitext(filepath)[1]
    }
    
    return info

def binary_file_copy(source, destination, chunk_size=1024):
    """
    Copy a binary file from source to destination in chunks.
    
    Args:
        source (str): Path to the source file
        destination (str): Path to the destination file
        chunk_size (int, optional): Size of chunks to read/write in bytes. Defaults to 1024.
        
    Returns:
        int: Number of bytes copied
        
    Raises:
        FileNotFoundError: If the source file doesn't exist
    """
    if not os.path.exists(source):
        raise FileNotFoundError(f"Source file not found: {source}")
    
    bytes_copied = 0
    
    with open(source, 'rb') as src_file:
        with open(destination, 'wb') as dst_file:
            while True:
                chunk = src_file.read(chunk_size)
                if not chunk:
                    break
                dst_file.write(chunk)
                bytes_copied += len(chunk)
    
    return bytes_copied

def main():
    """Run examples to test your functions."""
    # Create a test file
    test_file = "test_file.txt"
    test_content = "This is line 1.\nThis is line 2.\nThis is line 3.\n"
    print(f"Writing to {test_file}...")
    write_text_file(test_file, test_content)
    
    # Read the file
    print(f"Reading from {test_file}...")
    content = read_text_file(test_file)
    print(f"Content:\n{content}")
    
    # Count lines, words, chars
    lines, words, chars = count_lines_words_chars(test_file)
    print(f"Lines: {lines}, Words: {words}, Characters: {chars}")
    
    # Find and replace
    replacements = find_and_replace(test_file, "line", "row")
    print(f"Replaced 'line' with 'row' {replacements} times")
    new_content = read_text_file(test_file)
    print(f"New content:\n{new_content}")
    
    # Copy file
    copy_destination = "test_file_copy.txt"
    copied = copy_file(test_file, copy_destination, True)
    print(f"Copied file: {copied}")
    
    # Get file info
    info = get_file_info(test_file)
    print(f"File info: {info}")
    
    # Clean up
    os.remove(test_file)
    os.remove(copy_destination)
    print("Cleaned up test files")

if __name__ == "__main__":
    main()