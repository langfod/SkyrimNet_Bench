#!/usr/bin/env python3
"""
OpenRouter Benchmarking Script - Response Parser
Extracts response data from OpenRouter output log file and organizes by prompt type.
"""

import os
import re
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

BASE_LOG_DIR = "D:\SteamLibrary\steamapps\common\Skyrim Special Edition\Data\skse\Plugins\SkyrimNet\logs"

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class OpenRouterResponseParser:
    def __init__(self, unique_identifiers_file: str = "unique_identifiers.json",
                 output_log_file: str = Path(BASE_LOG_DIR).joinpath("openrouter_output.log.1"),
                 output_base_dir: str = "data/response"):
        self.unique_identifiers_file = unique_identifiers_file
        self.output_log_file = output_log_file
        self.output_base_dir = Path(output_base_dir)
        self.unique_identifiers = {}
        self.processed_responses = []
        self.timing_data = []
        
        # Regex pattern to match response lines
        self.response_pattern = re.compile(r'\[([^\]]+)\] Generate.*?response \[([^\]]+)\]:')
        
    def load_unique_identifiers(self) -> Dict:
        """Load unique identifiers from JSON file."""
        try:
            with open(self.unique_identifiers_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                identifiers = data.get('identifiers', [])
                
                # Create lookup dictionary for faster access
                self.unique_identifiers = {
                    item['id']: {
                        'timestamp': item['timestamp'],
                        'prompt_type': item['prompt_type']
                    }
                    for item in identifiers
                }
                
            logger.info(f"Loaded {len(self.unique_identifiers)} unique identifiers")
            return self.unique_identifiers
        except Exception as e:
            logger.error(f"Error loading unique identifiers: {e}")
            return {}
    
    def create_folder_structure(self):
        """Create folder structure based on prompt types from unique identifiers."""
        self.output_base_dir.mkdir(parents=True, exist_ok=True)
        
        # Get unique prompt types from loaded identifiers
        prompt_types = set(data['prompt_type'] for data in self.unique_identifiers.values())
        
        for prompt_type in prompt_types:
            folder_path = self.output_base_dir / prompt_type
            folder_path.mkdir(exist_ok=True)
            logger.info(f"Created/verified folder: {folder_path}")
    
    def calculate_response_time(self, request_timestamp: str, response_timestamp: str) -> Optional[float]:
        """Calculate response time in seconds between request and response."""
        try:
            # Parse timestamps
            req_dt = datetime.strptime(request_timestamp, "%Y-%m-%d %H:%M:%S.%f")
            resp_dt = datetime.strptime(response_timestamp, "%Y-%m-%d %H:%M:%S.%f")
            
            # Calculate difference in seconds
            time_diff = (resp_dt - req_dt).total_seconds()
            return time_diff
        except Exception as e:
            logger.warning(f"Error calculating response time: {e}")
            return None
    
    def save_response_data(self, unique_id: str, prompt_type: str, content: str, 
                          response_time: Optional[float] = None):
        """Save response data to appropriate folder."""
        folder_path = self.output_base_dir / prompt_type
        file_path = folder_path / f"{unique_id}.txt"
        
        try:
            # Add timing metadata to the content
            metadata = f"# Response ID: {unique_id}\n"
            metadata += f"# Prompt Type: {prompt_type}\n"
            if response_time is not None:
                metadata += f"# Response Time: {response_time:.3f} seconds\n"
            metadata += f"# Content:\n\n"
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(metadata + content)
            logger.info(f"Saved response {unique_id} to {file_path}")
            
            if response_time is not None:
                logger.info(f"Response time for {unique_id}: {response_time:.3f}s")
                
        except Exception as e:
            logger.error(f"Error saving response {unique_id}: {e}")
    
    def save_timing_data(self, filename: str = "response_timing_data.json"):
        """Save all timing data to a file for benchmarking analysis."""
        output_file = Path(filename)
        try:
            timing_summary = {
                'total_responses': len(self.timing_data),
                'responses_with_timing': len([t for t in self.timing_data if t['response_time'] is not None]),
                'average_response_time': None,
                'min_response_time': None,
                'max_response_time': None,
                'responses': self.timing_data
            }
            
            # Calculate statistics
            valid_times = [t['response_time'] for t in self.timing_data if t['response_time'] is not None]
            if valid_times:
                timing_summary['average_response_time'] = sum(valid_times) / len(valid_times)
                timing_summary['min_response_time'] = min(valid_times)
                timing_summary['max_response_time'] = max(valid_times)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(timing_summary, f, indent=2)
            
            logger.info(f"Saved timing data for {len(self.timing_data)} responses to {output_file}")
            if valid_times:
                logger.info(f"Average response time: {timing_summary['average_response_time']:.3f}s")
                logger.info(f"Response time range: {timing_summary['min_response_time']:.3f}s - {timing_summary['max_response_time']:.3f}s")
                
        except Exception as e:
            logger.error(f"Error saving timing data: {e}")
    
    def process_log_file(self):
        """Process the OpenRouter output log file."""
        if not os.path.exists(self.output_log_file):
            logger.error(f"Output log file not found: {self.output_log_file}")
            return
        
        logger.info(f"Processing log file: {self.output_log_file}")
        
        # Read file line by line to handle large files better
        with open(self.output_log_file, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        
        i = 0
        matched_responses = 0
        unmatched_responses = 0
        
        while i < len(lines):
            line = lines[i].strip()
            
            # Look for response start pattern
            match = self.response_pattern.match(line)
            if match:
                response_timestamp = match.group(1)
                unique_id = match.group(2)
                
                logger.debug(f"Processing response {unique_id}")
                
                # Check if this ID exists in our request data
                if unique_id not in self.unique_identifiers:
                    logger.warning(f"Response ID {unique_id} not found in request data - skipping")
                    unmatched_responses += 1
                    i += 1
                    continue
                
                # Get prompt type from our lookup
                request_data = self.unique_identifiers[unique_id]
                prompt_type = request_data['prompt_type']
                request_timestamp = request_data['timestamp']
                
                # Calculate response time
                response_time = self.calculate_response_time(request_timestamp, response_timestamp)
                
                # Collect response content until next response or end of file
                content_lines = []
                i += 1
                
                while i < len(lines):
                    next_line = lines[i]
                    # Check if we've hit the next response
                    if self.response_pattern.match(next_line.strip()):
                        break
                    content_lines.append(next_line)
                    i += 1
                
                # Join and clean content
                content = ''.join(content_lines).strip()
                
                # Save the response data
                self.save_response_data(unique_id, prompt_type, content, response_time)
                
                # Track processed response
                self.processed_responses.append({
                    'id': unique_id,
                    'prompt_type': prompt_type,
                    'request_timestamp': request_timestamp,
                    'response_timestamp': response_timestamp,
                    'response_time': response_time,
                    'content_length': len(content)
                })
                
                # Track timing data
                self.timing_data.append({
                    'id': unique_id,
                    'prompt_type': prompt_type,
                    'request_timestamp': request_timestamp,  
                    'response_timestamp': response_timestamp,
                    'response_time': response_time
                })
                
                matched_responses += 1
            else:
                i += 1
        
        logger.info(f"Matched responses: {matched_responses}")
        logger.info(f"Unmatched responses: {unmatched_responses}")
    
    def run(self):
        """Main execution method."""
        logger.info("Starting OpenRouter Response Parser")
        
        # Load unique identifiers
        if not self.load_unique_identifiers():
            logger.error("Failed to load unique identifiers. Exiting.")
            return
        
        # Create folder structure
        self.create_folder_structure()
        
        # Process log file
        self.process_log_file()
        
        # Save timing data for benchmarking
        self.save_timing_data()
        
        # Summary
        logger.info(f"Processing complete!")
        logger.info(f"Total responses processed: {len(self.processed_responses)}")
        
        # Count by prompt type
        type_counts = {}
        for response in self.processed_responses:
            prompt_type = response['prompt_type']
            type_counts[prompt_type] = type_counts.get(prompt_type, 0) + 1
        
        logger.info("Responses by prompt type:")
        for prompt_type, count in sorted(type_counts.items()):
            logger.info(f"  {prompt_type}: {count}")

def main():
    parser = OpenRouterResponseParser()
    parser.run()

if __name__ == "__main__":
    main()