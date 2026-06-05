# PDF Processing Pipeline

Scalable, maintainable text processing pipeline for architectural/engineering PDF documents.

## Architecture

4-Stage Pipeline:
- **Stage 1A**: TextExtractor - PDF → Raw text
- **Stage 1B**: TextProcessor - Raw text → Clean lines
- **Stage 2**: FrequencyAnalyzer - Frequency counting & analysis
- **Stage 3**: AdaptiveFilter - Intelligent filtering
- **Stage 4**: PatternAnalyzer - Multi-file pattern detection

## Project Structure

```
src/pdf_pipeline/     # Main package
├── core/             # Pipeline stage implementations
├── models/           # Dataclasses for data structures
├── utils/            # Utility functions
└── cli/              # Command-line interfaces

tests/                # Unit tests
data/                 # Input files
output/               # Results
config/               # Configuration
docs/                 # Documentation
archive/              # Legacy code (v16_workable preserved)
notes/                # Development notes
```

## Usage

### Single File Processing
```python
from src.pdf_pipeline.cli.single_file import process_single_file

result = process_single_file('path/to/file.pdf')
```

### Batch Processing
```python
from src.pdf_pipeline.cli.batch_processor import BatchProcessor

processor = BatchProcessor(input_dir='data/raw')
results = processor.process_all()
```

## Requirements

- Python 3.11.7+
- PyMuPDF
- spaCy
- pandas

Install: `pip install -r requirements.txt`

## Development

Working version preserved in: `archive/legacy_code/v16_workable/`

All string quotes use single quotes: `'text'`
All classes are dataclasses
Use icecream for debugging: `ic(f'{var}')`
