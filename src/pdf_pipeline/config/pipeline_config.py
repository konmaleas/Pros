'''
Pipeline configuration
'''
from dataclasses import dataclass


@dataclass
class PipelineConfig:
    '''Configuration for PDF processing pipeline'''
    
    noise_threshold: int = 76
    max_anchor_distance: int = 15
    enable_spacy_filtering: bool = True
    output_debug_files: bool = False
    
    # Paths
    raw_data_dir: str = 'data/raw'
    processed_data_dir: str = 'data/processed'
    output_dir: str = 'output'
