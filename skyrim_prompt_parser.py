#!/usr/bin/env python3
"""
Skyrim Prompt Parser
Extracts unique signatures from Skyrim AI mod prompt files for log parsing.

This script scans .prompt files in the SkyrimNet prompts directory and extracts
the first sentence from [system]...[end system] blocks to create unique signatures
for each prompt type.
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, List, Tuple, Set

# Configuration
PROMPTS_DIR = "D:\SteamLibrary\steamapps\common\Skyrim Special Edition\Data\skse\Plugins\SkyrimNet\prompts"
OUTPUT_FILE = "prompt_types.json"
EXCEPTIONS_FILE = "prompt_parser_exceptions.json"
IGNORED_FOLDERS = {"web", "submodules", "documentation"}

def load_exceptions_config() -> Tuple[Set[str], Dict]:
    """
    Load exception files configuration.
    
    Returns:
        Tuple of (exception_files_set, config_dict)
    """
    try:
        with open(EXCEPTIONS_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        exception_files = set(config.get('exception_files', {}).get('files', []))
        print(f"Loaded {len(exception_files)} exception files from {EXCEPTIONS_FILE}")
        
        return exception_files, config
    
    except FileNotFoundError:
        print(f"Warning: Exception config file not found: {EXCEPTIONS_FILE}")
        return set(), {}
    except Exception as e:
        print(f"Error loading exception config: {e}")
        return set(), {}

def extract_system_block(content: str) -> str:
    """
    Extract content between [ system ] and [ end system ] tags.
    
    Args:
        content: The full file content
        
    Returns:
        The content within the system block, or empty string if not found
    """
    # Pattern to match [ system ] ... [ end system ] (case insensitive, flexible whitespace)
    pattern = r'\[\s*system\s*\](.*?)\[\s*end\s+system\s*\]'
    match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
    
    if match:
        return match.group(1).strip()
    return ""

def extract_raw_content(content: str, max_length: int = 200) -> str:
    """
    Extract signature from raw file content (for exception files without [ system ] blocks).
    
    Args:
        content: The full file content
        max_length: Maximum length for the signature
        
    Returns:
        Extracted signature from raw content
    """
    if not content:
        return ""
    
    # Clean up the content
    cleaned_content = re.sub(r'\s+', ' ', content).strip()
    
    # Remove any template-specific markers that might be at the start
    # Look for common patterns and remove them
    patterns_to_remove = [
        r'^```[a-zA-Z]*\s*',  # Remove code block markers
        r'^---\s*',           # Remove yaml front matter markers
        r'^#.*?\n',           # Remove markdown headers at the start
    ]
    
    for pattern in patterns_to_remove:
        cleaned_content = re.sub(pattern, '', cleaned_content, flags=re.MULTILINE)
    
    cleaned_content = cleaned_content.strip()
    
    # If the content is already short enough, return it
    if len(cleaned_content) <= max_length:
        return cleaned_content
    
    # Otherwise, find a good breaking point (sentence boundary preferred)
    truncated = cleaned_content[:max_length]
    
    # Try to break at sentence boundary
    last_sentence_end = max(
        truncated.rfind('.'),
        truncated.rfind('!'),
        truncated.rfind('?')
    )
    
    if last_sentence_end > max_length * 0.5:  # If we found a good break point
        return truncated[:last_sentence_end + 1].strip()
    else:
        # Break at word boundary
        last_space = truncated.rfind(' ')
        if last_space > max_length * 0.7:
            return truncated[:last_space].strip() + "..."
        else:
            return truncated + "..."

def extract_unique_signature(text: str) -> str:
    """
    Extract a unique signature from the given text.
    Takes more than just the first sentence to ensure uniqueness.
    
    Args:
        text: The text to extract signature from
        
    Returns:
        A unique signature that can distinguish between prompt types
    """
    if not text:
        return ""
    
    # Clean up the text first - remove extra whitespace and newlines
    cleaned_text = re.sub(r'\s+', ' ', text).strip()
    
    # Look for key distinguishing phrases that make prompts unique
    distinguishing_phrases = [
        'thinking to yourself',
        'reacting verbally',
        'speak as they would',
        'reacting internally', 
        'speaking to',
        'in character and speak',
        'thoughts about',
        'verbal response',
        'internal thoughts',
        'remain completely in character',
        'verbally to a',
        'just occurred',
        'about the current situation'
    ]
    
    # First, find real sentence boundaries while ignoring periods inside template variables
    # We'll use a more sophisticated approach to find sentence endings
    real_sentences = []
    
    # Split into potential sentences but be smarter about template variables
    temp_text = cleaned_text
    # Temporarily replace template variables to avoid false sentence breaks
    template_replacements = {}
    template_counter = 0
    
    # Find and replace template variables like {{ ... }}
    template_pattern = r'\{\{[^}]*\}\}'
    for match in re.finditer(template_pattern, temp_text):
        placeholder = f"TEMPLATE_{template_counter}"
        template_replacements[placeholder] = match.group()
        temp_text = temp_text.replace(match.group(), placeholder)
        template_counter += 1
    
    # Now split by real sentence endings
    sentence_pattern = r'[.!?]+\s+'
    potential_sentences = re.split(sentence_pattern, temp_text)
    
    # Restore template variables
    for i, sentence in enumerate(potential_sentences):
        for placeholder, original in template_replacements.items():
            sentence = sentence.replace(placeholder, original)
        potential_sentences[i] = sentence.strip()
    
    # Remove empty sentences
    real_sentences = [s for s in potential_sentences if s.strip()]
    
    # Now find the signature by looking for distinguishing phrases
    signature_parts = []
    
    for sentence in real_sentences[:4]:  # Look at up to 4 real sentences
        if sentence:
            signature_parts.append(sentence)
            
            # Check if this sentence contains a distinguishing phrase
            if any(phrase in sentence.lower() for phrase in distinguishing_phrases):
                break  # We found uniqueness, stop here
                
            # Stop if we have enough length
            full_signature = '. '.join(signature_parts)
            if len(full_signature) >= 150:
                break
    
    # Join with proper sentence endings
    if signature_parts:
        signature = '. '.join(signature_parts)
        # Ensure it ends with proper punctuation
        if not signature.endswith(('.', '!', '?')):
            signature += '.'
    else:
        # Fallback to first 100 characters
        signature = cleaned_text[:100] + "..." if len(cleaned_text) > 100 else cleaned_text
    
    return signature.strip()

def get_prompt_type(filename: str) -> str:
    """
    Extract prompt type from filename.
    Example: "dialogue_response.prompt" -> "dialogue_response"
    
    Args:
        filename: The filename with extension
        
    Returns:
        The prompt type (filename without .prompt extension)
    """
    return Path(filename).stem

def should_ignore_directory(dir_path: Path) -> bool:
    """
    Check if a directory should be ignored based on IGNORED_FOLDERS.
    
    Args:
        dir_path: Path to the directory
        
    Returns:
        True if directory should be ignored
    """
    return any(ignored in dir_path.parts for ignored in IGNORED_FOLDERS)

def scan_prompt_files(base_dir: str) -> List[Tuple[str, str]]:
    """
    Recursively scan for .prompt files and extract their signatures.
    
    Args:
        base_dir: Base directory to scan
        
    Returns:
        List of tuples (prompt_type, signature)
    """
    results = []
    base_path = Path(base_dir)
    
    if not base_path.exists():
        print(f"Warning: Directory does not exist: {base_dir}")
        return results
    
    print(f"Scanning directory: {base_dir}")
    
    # Load exception files configuration
    exception_files, config = load_exceptions_config()
    max_length = config.get('configuration', {}).get('max_signature_length', 200)
    
    # Walk through all subdirectories
    for root, dirs, files in os.walk(base_path):
        root_path = Path(root)
        
        # Skip ignored directories
        if should_ignore_directory(root_path):
            print(f"Skipping ignored directory: {root_path}")
            continue
        
        # Process .prompt files
        for file in files:
            if file.endswith('.prompt'):
                file_path = root_path / file
                prompt_type = get_prompt_type(file)
                is_exception_file = file in exception_files
                
                print(f"Processing: {file_path}{' (EXCEPTION FILE)' if is_exception_file else ''}")
                
                try:
                    # Read file content
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    if is_exception_file:
                        # Handle exception files - extract from raw content
                        print(f"  Using raw content extraction for exception file")
                        signature = extract_raw_content(content, max_length)
                        if not signature:
                            print(f"  Warning: No content extracted from exception file {file}")
                            continue
                        print(f"  Extracted (raw): {signature[:50]}...")
                    else:
                        # Handle normal files - extract from system block
                        system_content = extract_system_block(content)
                        if not system_content:
                            print(f"  Warning: No [system] block found in {file}")
                            continue
                        
                        # Extract unique signature
                        signature = extract_unique_signature(system_content)
                        if not signature:
                            print(f"  Warning: No signature extracted from {file}")
                            continue
                        print(f"  Extracted (system): {signature[:50]}...")
                    
                    results.append((prompt_type, signature))
                    
                except Exception as e:
                    print(f"  Error processing {file_path}: {e}")
    
    return results

def simplify_signature(signature: str) -> str:
    """
    Simplify signature to its base but unique form.
    Removes template variables but preserves enough context for uniqueness.
    
    Args:
        signature: Original signature
        
    Returns:
        Simplified signature that maintains uniqueness
    """
    # First, clean up template variables but preserve some context
    # Replace {{ variable.name }} with [VAR] but keep surrounding text
    simplified = re.sub(r'\{\{[^}]*\}\}', '[VAR]', signature)
    
    # Remove conditional blocks like {% if ... %} but keep the content
    simplified = re.sub(r'\{%[^%]*%\}', '', simplified)
    
    # Clean up multiple [VAR] tokens that are adjacent
    simplified = re.sub(r'\[VAR\]\s*,\s*\[VAR\]', '[VAR]', simplified)
    simplified = re.sub(r'\[VAR\]\s+\[VAR\]', '[VAR]', simplified)
    
    # Clean up extra whitespace
    simplified = re.sub(r'\s+', ' ', simplified).strip()
    
    # Remove trailing periods for consistency, but keep other punctuation
    simplified = simplified.rstrip('.')
    
    # If the simplified version is too short, keep more of the original
    if len(simplified) < 20:
        # Keep original but just clean up whitespace
        simplified = re.sub(r'\s+', ' ', signature).strip().rstrip('.')
    
    return simplified

def create_prompt_types_json(prompt_data: List[Tuple[str, str]]) -> Dict:
    """
    Create the final JSON structure with original and simplified signatures.
    Each prompt type gets its own usage field.
    
    Args:
        prompt_data: List of (prompt_type, signature) tuples
        
    Returns:
        Dictionary ready for JSON serialization
    """
    result = {
        "prompt_types": {}
    }
    
    for prompt_type, original_signature in prompt_data:
        simplified_signature = simplify_signature(original_signature)
        
        result["prompt_types"][prompt_type] = {
            "usage": "default",  # Each prompt type has its own usage field
            "original_signature": original_signature,
            "simplified_signature": simplified_signature
        }
    
    return result

def main():
    """Main execution function."""
    print("SkyrimNet Prompt Parser (Enhanced with Exception File Support)")
    print("=" * 70)
    
    # Load and display exception configuration
    exception_files, config = load_exceptions_config()
    if exception_files:
        print(f"\nException files configured: {', '.join(sorted(exception_files))}")
    
    # First Pass: Scan and extract signatures
    print("\n** FIRST PASS: Extracting signatures **")
    prompt_data = scan_prompt_files(PROMPTS_DIR)
    
    if not prompt_data:
        print("No prompt files found or processed successfully.")
        return
    
    print(f"\nFound {len(prompt_data)} prompt files")
    
    # Count exception vs normal files
    processed_exceptions = []
    processed_normal = []
    
    for prompt_type, _ in prompt_data:
        filename = f"{prompt_type}.prompt"
        if filename in exception_files:
            processed_exceptions.append(prompt_type)
        else:
            processed_normal.append(prompt_type)
    
    print(f"Normal files processed: {len(processed_normal)}")
    print(f"Exception files processed: {len(processed_exceptions)}")
    if processed_exceptions:
        print(f"Exception files: {', '.join(sorted(processed_exceptions))}")
    
    # Second Pass: Simplify signatures
    print("\n** SECOND PASS: Simplifying signatures **")
    json_data = create_prompt_types_json(prompt_data)
    
    # Display results
    print("\nResults:")
    for prompt_type, data in json_data["prompt_types"].items():
        filename = f"{prompt_type}.prompt"
        file_type = "(EXCEPTION)" if filename in exception_files else "(NORMAL)"
        print(f"\n{prompt_type} {file_type}:")
        print(f"  Original: {data['original_signature']}")
        print(f"  Simplified: {data['simplified_signature']}")
    
    # Save to JSON file
    try:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)
        print(f"\n✓ Results saved to: {OUTPUT_FILE}")
        print(f"✓ Exception files processed: {len(processed_exceptions)}")
        print(f"✓ Normal files processed: {len(processed_normal)}")
    except Exception as e:
        print(f"\n✗ Error saving to {OUTPUT_FILE}: {e}")

if __name__ == "__main__":
    main()