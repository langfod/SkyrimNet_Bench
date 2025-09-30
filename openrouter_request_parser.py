#!/usr/bin/env python3
"""
OpenRouter Benchmarking Script - Request Parser (Enhanced with Variants)
Extracts sample data from OpenRouter input log file and organizes by prompt type.
Supports variant mappings for handling signature changes over time.
"""

import os
import re
import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from difflib import SequenceMatcher


BASE_LOG_DIR = "D:\SteamLibrary\steamapps\common\Skyrim Special Edition\Data\skse\Plugins\SkyrimNet\logs"
#BASE_LOG_DIR = "D:\temp\skyrimnet_logarchive"

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class OpenRouterRequestParser:
    def __init__(self, prompt_types_file: str = "prompt_types.json", 
                 variants_file: str = "prompt_type_variants.json",
                 input_log_file: str = Path(BASE_LOG_DIR).joinpath("openrouter_input.log.1"),
                 output_base_dir: str = "data/request"):
        self.prompt_types_file = prompt_types_file
        self.variants_file = variants_file
        self.input_log_file = input_log_file
        self.output_base_dir = Path(output_base_dir)
        self.prompt_types = {}
        self.variants = {}
        self.unique_identifiers = []
        
        # Regex pattern to match request lines
        self.request_pattern = re.compile(r'\[([^\]]+)\] Generate.*?\[([^\]]+)\]:')
        
    def load_prompt_types(self) -> Dict:
        """Load prompt types from JSON file."""
        try:
            with open(self.prompt_types_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.prompt_types = data.get('prompt_types', {})
            logger.info(f"Loaded {len(self.prompt_types)} prompt types")
            return self.prompt_types
        except Exception as e:
            logger.error(f"Error loading prompt types: {e}")
            return {}
    
    def load_variants(self) -> Dict:
        """Load prompt type variants from JSON file."""
        if not os.path.exists(self.variants_file):
            logger.warning(f"Variants file not found: {self.variants_file} - using default matching only")
            return {}
        
        try:
            with open(self.variants_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.variants = data.get('prompt_type_variants', {})
            logger.info(f"Loaded variants for {len(self.variants)} prompt types")
            return self.variants
        except Exception as e:
            logger.error(f"Error loading variants: {e}")
            return {}
    
    def create_folder_structure(self):
        """Create folder structure based on prompt types."""
        self.output_base_dir.mkdir(parents=True, exist_ok=True)
        
        for prompt_type in self.prompt_types.keys():
            folder_path = self.output_base_dir / prompt_type
            folder_path.mkdir(exist_ok=True)
            logger.info(f"Created/verified folder: {folder_path}")
    
    def similarity_score(self, a: str, b: str) -> float:
        """Calculate similarity between two strings."""
        return SequenceMatcher(None, a.lower(), b.lower()).ratio()
    
    def find_matching_prompt_type(self, content: str) -> Optional[str]:
        """
        Enhanced version that uses both original patterns and variants.
        Find which prompt type matches the content based on signature.
        """
        content_lower = content.lower()
        content_prefix = content_lower[:800]  # Check more characters
        
        # First, try exact pattern matching with variants
        if self.variants:
            for prompt_type, variant_data in self.variants.items():
                patterns = variant_data.get('patterns', [])
                for pattern in patterns:
                    pattern_lower = pattern.lower()
                    if pattern_lower in content_prefix:
                        logger.debug(f"Variant matched prompt type '{prompt_type}' with pattern: {pattern[:50]}...")
                        return prompt_type
        
        # Define key patterns for each prompt type (fallback)
        pattern_matches = {
            'dialogue_response': [
                'you are roleplaying as',
                'remain completely in character and speak as they would'
            ],
            'player_dialogue': [
                'you are roleplaying as',
                'you are reacting verbally to a'
            ],
            'player_thoughts': [
                'you are roleplaying as', 
                'you are thinking to yourself about the current situation'
            ],
            'gamemaster_action_selector': [
                'you are the gamemaster ai for skyrim',
                'acting like a tabletop dungeon master'
            ],
            'evaluate_mood': [
                'you are an ai mood analyzer for skyrim',
                'determining the emotional state of npcs'
            ],
            'generate_search_query': [
                'you are a memory search query generator',
                'generate a search query optimized for semantic similarity'
            ],
            'dialogue_speaker_selector': [
                'you are deciding which single skyrim npc should speak next',
                'identify the npc who would naturally speak next'
            ],
            'native_action_selector': [
                'you are an expert at determining what action should accompany',
                'you are an expect at determining what action should accompany'  # Handle typo
            ],
            'memory_builder': [
                'you are an ai assistant that summarizes game events into memories',
                'create personalized, first-person memories',
                'you are an expert on the elder scrolls universe'
            ],
            'evaluate_memory_relevance': [
                'you are an ai assistant that analyzes events in the game skyrim',
                'determine which ones are relevant to form memories'
            ],
            'mood_evaluator': [
                'you are an ai assistant that analyzes an npc\'s recent experiences',
                'determine their current mood'
            ],
            'character_profile_update': [
                'you are an expert at updating character profiles for npcs',
                'update the existing character bio'
            ],
            'dynamic_bio_update': [
                'you are an expert at updating character biographies',
                'based on recent events and character development'
            ],
            'player_dialogue_target_selector': [
                'you are an ai decision-maker for skyrim',
                'determining which npcs the player is addressing'
            ],
            'native_dialogue_transformer': [
                'your task is to transform dialogue to make it more immersive',
                'natural, and fitting for'
            ]
        }
        
        # Try pattern matching
        for prompt_type, patterns in pattern_matches.items():
            matches = 0
            for pattern in patterns:
                if pattern in content_prefix:
                    matches += 1
            
            # Require at least one pattern match
            if matches > 0:
                logger.debug(f"Pattern matched prompt type '{prompt_type}' with {matches} patterns")
                return prompt_type
        
        # Try fuzzy matching if enabled in variants
        if self.variants.get('fuzzy_matching', {}).get('enabled', False):
            min_threshold = self.variants['fuzzy_matching'].get('min_similarity_threshold', 0.7)
            
            best_match = None
            best_score = 0
            
            for prompt_type, data in self.prompt_types.items():
                signatures = [data.get('original_signature', ''), data.get('simplified_signature', '')]
                
                for signature in signatures:
                    if signature:
                        score = self.similarity_score(content_prefix[:200], signature[:200])
                        if score > best_score and score >= min_threshold:
                            best_score = score
                            best_match = prompt_type
            
            if best_match:
                logger.debug(f"Fuzzy matched prompt type '{best_match}' with score {best_score:.3f}")
                return best_match
        
        # Fall back to original signature matching
        for prompt_type, data in self.prompt_types.items():
            original_sig = data.get('original_signature', '').lower()
            simplified_sig = data.get('simplified_signature', '').lower()
            
            # Try to find a substantial match (at least 30 characters)
            if len(original_sig) > 30:
                sig_start = original_sig[:min(100, len(original_sig))]
                if sig_start in content_prefix:
                    logger.debug(f"Signature matched prompt type '{prompt_type}' via original signature")
                    return prompt_type
            
            if len(simplified_sig) > 30:
                sig_start = simplified_sig[:min(100, len(simplified_sig))]
                if sig_start in content_prefix:
                    logger.debug(f"Signature matched prompt type '{prompt_type}' via simplified signature")
                    return prompt_type
        
        logger.warning(f"No matching prompt type found for content starting with: {content[:150]}...")
        return None

    def parse_json_entry(self, json_text: str) -> Optional[Dict]:
        """Parse JSON entry from log file."""
        try:
            # Clean up the JSON text - handle control characters
            cleaned_json = json_text.encode('utf-8', errors='ignore').decode('utf-8')
            return json.loads(cleaned_json)
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            # Try with strict=False for more lenient parsing
            try:
                import ast
                # As a fallback, try to extract just the messages part if available
                if '"messages"' in cleaned_json:
                    logger.debug("Attempting manual JSON extraction")
                    # This is a more robust approach - we'll parse line by line
                    return self._manual_json_parse(cleaned_json)
            except Exception as e2:
                logger.error(f"Manual parse also failed: {e2}")
            return None
    
    def _manual_json_parse(self, json_text: str) -> Optional[Dict]:
        """Manual JSON parsing for problematic entries."""
        try:
            # Find the messages array manually
            lines = json_text.split('\n')
            result = {"messages": []}
            current_message = {}
            in_messages = False
            in_content = False
            content_lines = []
            brace_count = 0
            
            for line in lines:
                stripped = line.strip()
                
                if '"messages"' in stripped:
                    in_messages = True
                    continue
                
                if in_messages:
                    if stripped.startswith('{') and not in_content:
                        current_message = {}
                        brace_count = 1
                    elif '"content":' in stripped:
                        in_content = True
                        # Extract content value start
                        content_start = stripped.split('"content":', 1)[1].strip()
                        if content_start.startswith('"'):
                            content_lines = [content_start[1:]]  # Remove opening quote
                        continue
                    elif in_content:
                        if stripped.endswith('",') or stripped.endswith('"'):
                            # End of content
                            if stripped.endswith('",'):
                                content_lines.append(stripped[:-2])  # Remove closing quote and comma
                            else:
                                content_lines.append(stripped[:-1])  # Remove closing quote
                            current_message['content'] = '\n'.join(content_lines)
                            content_lines = []
                            in_content = False
                        else:
                            content_lines.append(stripped)
                        continue
                    elif '"role":' in stripped:
                        role_value = stripped.split('"role":', 1)[1].strip()
                        if role_value.startswith('"') and role_value.endswith('"'):
                            current_message['role'] = role_value[1:-1]
                        elif role_value.startswith('"') and role_value.endswith('",'):
                            current_message['role'] = role_value[1:-2]
                    elif stripped == '}' or stripped == '},':
                        if current_message:
                            result["messages"].append(current_message)
                            current_message = {}
                    elif stripped == ']':
                        in_messages = False
                        break
            
            if result["messages"]:
                return result
            return None
        except Exception as e:
            logger.error(f"Manual parsing failed: {e}")
            return None

    def extract_messages_content(self, messages: List[Dict]) -> str:
        """Extract and combine content from messages array."""
        content_parts = []
        for message in messages:
            if 'content' in message:
                content_parts.append(message['content'])
        return '\n\n'.join(content_parts)
    
    def save_request_data(self, unique_id: str, prompt_type: str, content: str):
        """Save request data to appropriate folder."""
        folder_path = self.output_base_dir / prompt_type
        file_path = folder_path / f"{unique_id}.txt"
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            logger.info(f"Saved request {unique_id} to {file_path}")
        except Exception as e:
            logger.error(f"Error saving request {unique_id}: {e}")
    
    def save_unique_identifiers(self, filename: str = "unique_identifiers.json"):
        """Save all unique identifiers to a file for later use."""
        output_file = Path(filename)
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'identifiers': self.unique_identifiers,
                    'total_count': len(self.unique_identifiers)
                }, f, indent=2)
            logger.info(f"Saved {len(self.unique_identifiers)} unique identifiers to {output_file}")
        except Exception as e:
            logger.error(f"Error saving unique identifiers: {e}")
    
    def process_log_file(self):
        """Process the OpenRouter input log file."""
        if not os.path.exists(self.input_log_file):
            logger.error(f"Input log file not found: {self.input_log_file}")
            return
        
        logger.info(f"Processing log file: {self.input_log_file}")
        
        # Read file line by line to handle large files better
        with open(self.input_log_file, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Look for request start pattern
            match = self.request_pattern.match(line)
            if match:
                timestamp = match.group(1)
                unique_id = match.group(2)
                
                logger.debug(f"Processing request {unique_id}")
                
                # Collect JSON content until next request or end of file
                json_lines = []
                i += 1
                
                while i < len(lines):
                    next_line = lines[i]
                    # Check if we've hit the next request
                    if self.request_pattern.match(next_line.strip()):
                        break
                    json_lines.append(next_line)
                    i += 1
                
                # Join and clean JSON content
                json_content = ''.join(json_lines).strip()
                
                # Parse JSON
                request_data = self.parse_json_entry(json_content)
                if not request_data:
                    logger.warning(f"Failed to parse JSON for request {unique_id}")
                    continue
                
                # Extract messages
                messages = request_data.get('messages', [])
                if not messages:
                    logger.warning(f"No messages found for request {unique_id}")
                    continue
                
                # Get combined content
                combined_content = self.extract_messages_content(messages)
                
                # Find matching prompt type
                prompt_type = self.find_matching_prompt_type(combined_content)
                if not prompt_type:
                    # Save to 'unknown' folder
                    prompt_type = 'unknown'
                    unknown_folder = self.output_base_dir / 'unknown'
                    unknown_folder.mkdir(exist_ok=True)
                
                # Save the request data
                self.save_request_data(unique_id, prompt_type, combined_content)
                
                # Track unique identifier
                self.unique_identifiers.append({
                    'id': unique_id,
                    'timestamp': timestamp,
                    'prompt_type': prompt_type
                })
            else:
                i += 1
    
    def run(self):
        """Main execution method."""
        logger.info("Starting OpenRouter Request Parser (Enhanced with Variants)")
        
        # Load prompt types
        if not self.load_prompt_types():
            logger.error("Failed to load prompt types. Exiting.")
            return
        
        # Load variants
        self.load_variants()
        
        # Create folder structure
        self.create_folder_structure()
        
        # Process log file
        self.process_log_file()
        
        # Save unique identifiers for later use
        self.save_unique_identifiers()
        
        # Summary
        logger.info(f"Processing complete!")
        logger.info(f"Total requests processed: {len(self.unique_identifiers)}")
        
        # Count by prompt type
        type_counts = {}
        for entry in self.unique_identifiers:
            prompt_type = entry['prompt_type']
            type_counts[prompt_type] = type_counts.get(prompt_type, 0) + 1
        
        logger.info("Requests by prompt type:")
        for prompt_type, count in sorted(type_counts.items()):
            logger.info(f"  {prompt_type}: {count}")
        
        # Show variants usage
        if self.variants:
            logger.info(f"Variant mappings loaded for {len(self.variants)} prompt types")

def main():
    parser = OpenRouterRequestParser()
    parser.run()

if __name__ == "__main__":
    main()