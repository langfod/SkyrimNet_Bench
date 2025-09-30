#!/usr/bin/env python3
"""
OpenRouter Benchmarking Analysis
Analyzes timing data and creates benchmarking reports.
"""

import json
import statistics
from pathlib import Path
from typing import Dict, List
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BenchmarkAnalyzer:
    def __init__(self, timing_data_file: str = "response_timing_data.json"):
        self.timing_data_file = timing_data_file
        self.timing_data = {}
        
    def load_timing_data(self):
        """Load timing data from JSON file."""
        try:
            with open(self.timing_data_file, 'r', encoding='utf-8') as f:
                self.timing_data = json.load(f)
            logger.info(f"Loaded timing data for {self.timing_data.get('total_responses', 0)} responses")
            return True
        except Exception as e:
            logger.error(f"Error loading timing data: {e}")
            return False
    
    def analyze_by_prompt_type(self):
        """Analyze response times by prompt type."""
        if not self.timing_data.get('responses'):
            logger.error("No response data available")
            return {}
        
        # Group responses by prompt type
        by_type = {}
        for response in self.timing_data['responses']:
            prompt_type = response.get('prompt_type', 'unknown')
            response_time = response.get('response_time')
            
            if response_time is not None:
                if prompt_type not in by_type:
                    by_type[prompt_type] = []
                by_type[prompt_type].append(response_time)
        
        # Calculate statistics for each type
        analysis = {}
        for prompt_type, times in by_type.items():
            if times:
                analysis[prompt_type] = {
                    'count': len(times),
                    'average': statistics.mean(times),
                    'median': statistics.median(times),
                    'min': min(times),
                    'max': max(times),
                    'std_dev': statistics.stdev(times) if len(times) > 1 else 0,
                    'times': times
                }
        
        return analysis
    
    def generate_report(self):
        """Generate a comprehensive benchmarking report."""
        if not self.load_timing_data():
            return
        
        print("=" * 60)
        print("OPENROUTER API BENCHMARKING REPORT")
        print("=" * 60)
        
        # Overall statistics
        total_responses = self.timing_data.get('total_responses', 0)
        avg_time = self.timing_data.get('average_response_time', 0)
        min_time = self.timing_data.get('min_response_time', 0)
        max_time = self.timing_data.get('max_response_time', 0)
        
        print(f"\nOVERALL STATISTICS:")
        print(f"  Total Responses: {total_responses}")
        print(f"  Average Response Time: {avg_time:.3f}s")
        print(f"  Fastest Response: {min_time:.3f}s")
        print(f"  Slowest Response: {max_time:.3f}s")
        print(f"  Response Time Range: {max_time - min_time:.3f}s")
        
        # Analysis by prompt type
        type_analysis = self.analyze_by_prompt_type()
        
        print(f"\nRESPONSE TIME BY PROMPT TYPE:")
        print("-" * 60)
        
        # Sort by average response time
        sorted_types = sorted(type_analysis.items(), key=lambda x: x[1]['average'])
        
        for prompt_type, stats in sorted_types:
            print(f"\n{prompt_type.upper()}:")
            print(f"  Count: {stats['count']}")
            print(f"  Average: {stats['average']:.3f}s")
            print(f"  Median: {stats['median']:.3f}s")
            print(f"  Range: {stats['min']:.3f}s - {stats['max']:.3f}s")
            print(f"  Std Dev: {stats['std_dev']:.3f}s")
            
            # Performance classification
            if stats['average'] < 2.0:
                performance = "FAST"
            elif stats['average'] < 4.0:
                performance = "MODERATE"
            elif stats['average'] < 8.0:
                performance = "SLOW"
            else:
                performance = "VERY SLOW"
            print(f"  Performance: {performance}")
        
        # Find outliers
        print(f"\nPERFORMANCE OUTLIERS:")
        print("-" * 60)
        
        all_times = []
        for response in self.timing_data['responses']:
            if response.get('response_time') is not None:
                all_times.append(response)
        
        # Sort by response time
        all_times.sort(key=lambda x: x['response_time'])
        
        print("\nFASTEST RESPONSES:")
        for response in all_times[:5]:
            print(f"  {response['id']} ({response['prompt_type']}): {response['response_time']:.3f}s")
        
        print("\nSLOWEST RESPONSES:")
        for response in all_times[-5:]:
            print(f"  {response['id']} ({response['prompt_type']}): {response['response_time']:.3f}s")
        
        # Recommendations
        print(f"\nRECOMMENDations:")
        print("-" * 60)
        
        fastest_type = min(sorted_types, key=lambda x: x[1]['average'])
        slowest_type = max(sorted_types, key=lambda x: x[1]['average'])
        
        print(f"• Fastest prompt type: {fastest_type[0]} ({fastest_type[1]['average']:.3f}s avg)")
        print(f"• Slowest prompt type: {slowest_type[0]} ({slowest_type[1]['average']:.3f}s avg)")
        
        if avg_time > 5.0:
            print(f"• Overall response time is HIGH ({avg_time:.3f}s) - consider optimizing prompts")
        elif avg_time > 3.0:
            print(f"• Overall response time is MODERATE ({avg_time:.3f}s) - good performance")
        else:
            print(f"• Overall response time is EXCELLENT ({avg_time:.3f}s)")
        
        # Consistency analysis
        high_variance_types = [name for name, stats in type_analysis.items() 
                             if stats['std_dev'] > 2.0 and stats['count'] > 3]
        
        if high_variance_types:
            print(f"• High variance prompt types (inconsistent timing): {', '.join(high_variance_types)}")
            print("  Consider investigating these for optimization opportunities")
        
        print("\n" + "=" * 60)
    
    def save_analysis_json(self, filename: str = "benchmark_analysis.json"):
        """Save detailed analysis to JSON file."""
        if not self.load_timing_data():
            return
            
        type_analysis = self.analyze_by_prompt_type()
        
        analysis_data = {
            'overall_stats': {
                'total_responses': self.timing_data.get('total_responses', 0),
                'average_response_time': self.timing_data.get('average_response_time', 0),
                'min_response_time': self.timing_data.get('min_response_time', 0),
                'max_response_time': self.timing_data.get('max_response_time', 0)
            },
            'by_prompt_type': type_analysis,
            'fastest_responses': [],
            'slowest_responses': []
        }
        
        # Add fastest/slowest
        all_times = []
        for response in self.timing_data['responses']:
            if response.get('response_time') is not None:
                all_times.append(response)
        
        all_times.sort(key=lambda x: x['response_time'])
        analysis_data['fastest_responses'] = all_times[:5]
        analysis_data['slowest_responses'] = all_times[-5:]
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(analysis_data, f, indent=2)
            logger.info(f"Saved detailed analysis to {filename}")
        except Exception as e:
            logger.error(f"Error saving analysis: {e}")

def main():
    analyzer = BenchmarkAnalyzer()
    analyzer.generate_report()
    analyzer.save_analysis_json()

if __name__ == "__main__":
    main()