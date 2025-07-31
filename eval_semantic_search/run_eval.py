#!/usr/bin/env python3
"""
Semantic search evaluation script - handles single config files or directories.
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'consultation_analyser.settings.local')
django.setup()

from eval_semantic_search.config import Config  # noqa: E402
from eval_semantic_search.embeddings import EmbeddingGenerator  # noqa: E402
from eval_semantic_search.evaluation import evaluate_consultation  # noqa: E402
from eval_semantic_search.ingestion import import_consultation_data  # noqa: E402

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def process_config(config_file: Path, no_import_data: bool) -> dict:
    """Process a single config file and return results"""
    # Load config
    config = Config.from_yaml(str(config_file))
    
    # Initialize embedding generator (hardcoded to text-embedding-3-small)
    embedding_generator = EmbeddingGenerator()
    
    # Import data unless explicitly disabled
    should_import = config.import_data and not no_import_data
    
    if should_import:
        logger.info("Importing consultation data...")
        import_consultation_data(
            config.consultation_code,
            embedding_generator,
            config.output_dir_timestamp,
            config.use_question_prefix
        )
    
    # Run evaluation
    logger.info("Running evaluation...")
    results = evaluate_consultation(
        config.consultation_code,
        embedding_generator,
        config.k
    )
    
    # Add config metadata to results
    results['config_file'] = config_file.name
    results['config'] = {
        'k': config.k,
        'use_question_prefix': config.use_question_prefix,
        'output_file': str(config.output_file)
    }
    
    # Save results
    with open(config.output_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    return results


def main():
    parser = argparse.ArgumentParser(description='Evaluate semantic search precision')
    parser.add_argument('--config', required=True, help='Config file or directory containing config files')
    parser.add_argument('--no-import-data', action='store_true', help='Skip data import (override config)')
    parser.add_argument('--pattern', default='*.yaml', help='Config file pattern for directories (default: *.yaml)')
    
    args = parser.parse_args()
    
    config_path = Path(args.config)
    
    # Determine if it's a file or directory
    if config_path.is_file():
        # Single file mode
        print(f"Processing single config: {config_path.name}")
        
        try:
            results = process_config(config_path, args.no_import_data)
            
            print(f"\nEvaluation complete for: {results['consultation']}")
            print(f"Overall precision: {results['overall_precision']:.3f}")
            print(f"Results saved to: {results['config']['output_file']}")
            
        except Exception as e:
            logger.error(f"Evaluation failed: {str(e)}", exc_info=True)
            sys.exit(1)
    
    elif config_path.is_dir():
        # Directory mode - batch processing
        config_files = list(config_path.glob(args.pattern))
        if not config_files:
            print(f"No config files found matching pattern {args.pattern} in {config_path}")
            sys.exit(1)
        
        config_files.sort()
        print(f"Found {len(config_files)} config files to process")
        
        results_summary = []
        
        for config_file in config_files:
            print(f"\n{'='*60}")
            print(f"Processing: {config_file.name}")
            print(f"{'='*60}")
            
            try:
                results = process_config(config_file, args.no_import_data)
                
                # Add to summary
                results_summary.append({
                    'config_file': config_file.name,
                    'consultation': results['consultation'],
                    'overall_precision': results['overall_precision'],
                    'total_themes': results['total_themes'],
                    'use_question_prefix': results['config']['use_question_prefix'],
                    'output_file': results['config']['output_file']
                })
                
                print(f"✓ Completed: {config_file.name}")
                print(f"  Overall precision: {results['overall_precision']:.3f}")
                print(f"  Output: {results['config']['output_file']}")
                
            except Exception as e:
                print(f"✗ Failed: {config_file.name}")
                print(f"  Error: {str(e)}")
                logger.exception(f"Error processing {config_file}")
        
        # Print summary
        if len(config_files) > 1 and results_summary:
            print(f"\n{'='*60}")
            print("BATCH EVALUATION SUMMARY")
            print(f"{'='*60}")
            
            # Sort by precision descending
            results_summary.sort(key=lambda x: x['overall_precision'], reverse=True)
            
            print(f"{'Config':<25} {'Prefix':<8} {'Precision':<10} {'Themes':<8}")
            print("-" * 70)
            
            for result in results_summary:
                prefix_str = "Yes" if result['use_question_prefix'] else "No"
                
                print(f"{result['config_file']:<25} {prefix_str:<8} "
                      f"{result['overall_precision']:<10.3f} {result['total_themes']:<8}")
            
            # Save summary
            summary_file = config_path / 'batch_summary.json'
            with open(summary_file, 'w') as f:
                json.dump(results_summary, f, indent=2, default=str)
            
            print(f"\nSummary saved to: {summary_file}")
            print(f"Best performing config: {results_summary[0]['config_file']} "
                  f"(precision: {results_summary[0]['overall_precision']:.3f})")
    
    else:
        print(f"Error: {config_path} is neither a file nor a directory")
        sys.exit(1)


if __name__ == '__main__':
    main()