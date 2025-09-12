"""
Simple configuration for semantic search evaluation.
"""

from dataclasses import dataclass

import yaml


@dataclass
class Config:
    consultation_code: str
    output_file: str
    output_dir_timestamp: str
    k: int = 20
    use_question_prefix: bool = False
    import_data: bool = True
    
    @classmethod
    def from_yaml(cls, path: str) -> 'Config':
        with open(path, 'r') as f:
            data = yaml.safe_load(f)
        
        # Ensure output_file is saved in eval_semantic_search/results/
        from pathlib import Path
        output_file = Path(data['output_file'])
        if not output_file.is_absolute():
            # Make it relative to eval_semantic_search/results/
            eval_dir = Path(__file__).parent
            results_dir = eval_dir / 'results'
            results_dir.mkdir(exist_ok=True)
            data['output_file'] = str(results_dir / output_file)
        
        return cls(**data)