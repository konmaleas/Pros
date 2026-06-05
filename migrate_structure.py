'''
Project Structure Migration Script
Creates new organized structure and moves files from old layout
'''
from pathlib import Path
import shutil
from datetime import datetime
from typing import List, Tuple

# Configuration
PROJECT_ROOT = Path('/home/konstantinos/PycharmProjects/Pros')
BACKUP_SUFFIX = f'_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}'


class ProjectMigrator:
    '''Migrates project to new organized structure'''
    
    def __init__(self, project_root: Path):
        self.root = project_root
        self.log: List[str] = []
        self.errors: List[str] = []
        
    def log_action(self, message: str):
        '''Log an action'''
        timestamp = datetime.now().strftime('%H:%M:%S')
        log_msg = f'[{timestamp}] {message}'
        self.log.append(log_msg)
        print(log_msg)
        
    def log_error(self, message: str):
        '''Log an error'''
        self.errors.append(message)
        print(f'ERROR: {message}')
    
    def create_new_structure(self) -> None:
        '''Create the new directory structure'''
        self.log_action('Creating new directory structure...')
        
        directories = [
            # Source code
            'src/pdf_pipeline/core',
            'src/pdf_pipeline/models',
            'src/pdf_pipeline/utils',
            'src/pdf_pipeline/cli',
            
            # Tests
            'tests/fixtures',
            
            # Data
            'data/raw',
            'data/processed',
            
            # Output
            'output/filtered_texts',
            'output/batch_results',
            'output/reports',
            
            # Config
            'config',
            
            # Documentation
            'docs',
            
            # Archive
            'archive/legacy_code',
            
            # Notes
            'notes/chat_summaries',
            'notes/debug_sessions',
        ]
        
        for dir_path in directories:
            full_path = self.root / dir_path
            full_path.mkdir(parents=True, exist_ok=True)
            self.log_action(f'Created: {dir_path}')
            
            # Create __init__.py for Python packages
            if 'src/' in dir_path or dir_path == 'tests':
                init_file = full_path / '__init__.py'
                if not init_file.exists():
                    init_file.touch()
                    self.log_action(f'Created: {dir_path}/__init__.py')
    
    def copy_core_modules(self) -> None:
        '''Copy core pipeline modules from v16_workable'''
        self.log_action('Copying core modules from v16_workable...')
        
        source_dir = self.root / 'claude' / 'v16_workable'
        target_dir = self.root / 'src' / 'pdf_pipeline' / 'core'
        
        if not source_dir.exists():
            self.log_error(f'Source directory not found: {source_dir}')
            return
        
        core_files = [
            'text_extractor.py',
            'text_processor.py',
            'frequency_analyzer.py',
            'adaptive_filter.py',
            'pattern_analyzer.py',
        ]
        
        for filename in core_files:
            source = source_dir / filename
            target = target_dir / filename
            
            if source.exists():
                shutil.copy2(source, target)
                self.log_action(f'Copied: {filename} -> src/pdf_pipeline/core/')
            else:
                self.log_error(f'File not found: {source}')
    
    def copy_cli_scripts(self) -> None:
        '''Copy CLI scripts from v16_workable'''
        self.log_action('Copying CLI scripts...')
        
        source_dir = self.root / 'claude' / 'v16_workable'
        target_dir = self.root / 'src' / 'pdf_pipeline' / 'cli'
        
        cli_files = [
            ('main_title_search.py', 'single_file.py'),
            ('batch_processor.py', 'batch_processor.py'),
        ]
        
        for source_name, target_name in cli_files:
            source = source_dir / source_name
            target = target_dir / target_name
            
            if source.exists():
                shutil.copy2(source, target)
                self.log_action(f'Copied: {source_name} -> src/pdf_pipeline/cli/{target_name}')
            else:
                self.log_error(f'File not found: {source}')
    
    def copy_utility_modules(self) -> None:
        '''Copy utility modules from modules/ directory'''
        self.log_action('Copying utility modules...')
        
        source_dir = self.root / 'modules'
        target_dir = self.root / 'src' / 'pdf_pipeline' / 'utils'
        
        if not source_dir.exists():
            self.log_error(f'Modules directory not found: {source_dir}')
            return
        
        utility_files = {
            'file_opers.py': 'file_ops.py',
            'path_manipulation.py': 'path_ops.py',
            'string_manipulation.py': 'text_ops.py',
            'letter_conversion.py': 'letter_conversion.py',
            'dates.py': 'dates.py',
            'time_oper.py': 'time_ops.py',
        }
        
        for source_name, target_name in utility_files.items():
            source = source_dir / source_name
            target = target_dir / target_name
            
            if source.exists():
                shutil.copy2(source, target)
                self.log_action(f'Copied: {source_name} -> src/pdf_pipeline/utils/{target_name}')
            else:
                self.log_action(f'Skipped: {source_name} (not found)')
    
    def archive_old_versions(self) -> None:
        '''Move old version directories to archive'''
        self.log_action('Archiving old version directories...')
        
        claude_dir = self.root / 'claude'
        archive_dir = self.root / 'archive' / 'legacy_code'
        
        if not claude_dir.exists():
            self.log_error(f'Claude directory not found: {claude_dir}')
            return
        
        # Version directories to archive (exclude v16_workable)
        version_patterns = ['v0', 'v1', 'v2', 'v3', 'v4', 'v5', 'v6', 'v7', 'v8', 
                          'v9_workable', 'v10', 'v11_workable', 'v12', 'v13', 'v14', 
                          'v15', 'v17', 'v18', 'v19', 'compare_v16_19_batch_processor']
        
        for item in claude_dir.iterdir():
            if item.is_dir() and item.name in version_patterns:
                target = archive_dir / item.name
                try:
                    shutil.move(str(item), str(target))
                    self.log_action(f'Archived: {item.name}')
                except Exception as e:
                    self.log_error(f'Failed to archive {item.name}: {e}')
    
    def move_chat_files(self) -> None:
        '''Move chat summaries to notes/'''
        self.log_action('Moving chat files...')
        
        source_dir = self.root / 'claude' / 'chat'
        target_dir = self.root / 'notes' / 'chat_summaries'
        
        if not source_dir.exists():
            self.log_action('No chat directory found, skipping...')
            return
        
        try:
            for file in source_dir.glob('*.txt'):
                target = target_dir / file.name
                shutil.move(str(file), str(target))
                self.log_action(f'Moved: chat/{file.name} -> notes/chat_summaries/')
            
            # Remove empty chat directory
            if not any(source_dir.iterdir()):
                source_dir.rmdir()
        except Exception as e:
            self.log_error(f'Failed to move chat files: {e}')
    
    def move_output_files(self) -> None:
        '''Move output files to new output/ directory'''
        self.log_action('Moving output files...')
        
        # Move filtered texts from v16_workable
        source_filtered = self.root / 'claude' / 'v16_workable' / 'filtered_texts'
        target_filtered = self.root / 'output' / 'filtered_texts'
        
        if source_filtered.exists():
            for item in source_filtered.iterdir():
                if item.is_dir():
                    target = target_filtered / item.name
                    shutil.copytree(item, target, dirs_exist_ok=True)
                    self.log_action(f'Copied: filtered_texts/{item.name}')
        
        # Move batch results from v17
        source_batch = self.root / 'claude' / 'v17' / 'batch_results'
        target_batch = self.root / 'output' / 'batch_results'
        
        if source_batch.exists():
            for item in source_batch.iterdir():
                target = target_batch / item.name
                if item.is_file():
                    shutil.copy2(item, target)
                    self.log_action(f'Copied: batch_results/{item.name}')
        
        # Move reports
        source_reports = self.root / 'files' / 'reports'
        target_reports = self.root / 'output' / 'reports'
        
        if source_reports.exists():
            for item in source_reports.iterdir():
                if item.is_dir():
                    target = target_reports / item.name
                    shutil.copytree(item, target, dirs_exist_ok=True)
                    self.log_action(f'Copied: reports/{item.name}')
    
    def create_config_files(self) -> None:
        '''Create initial configuration files'''
        self.log_action('Creating configuration files...')
        
        # Constants
        constants_file = self.root / 'config' / 'constants.py'
        constants_content = """'''
Pipeline constants and configuration
'''

# Frequency threshold for noise detection
NOISE_THRESHOLD = 76

# Maximum distance for anchor viability
MAX_ANCHOR_DISTANCE = 15

# Template title pattern
TITLE_PATTERN = r'^[A-Z0-9]+-[A-Z0-9]+-[A-Z0-9]+-[A-Z]+-[A-Z]+-\\d+-[A-Z0-9]+$'

# Supported file extensions
SUPPORTED_EXTENSIONS = ['.pdf']
"""
        constants_file.write_text(constants_content)
        self.log_action('Created: config/constants.py')
        
        # Pipeline config
        pipeline_config = self.root / 'config' / 'pipeline_config.py'
        pipeline_content = """'''
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
"""
        pipeline_config.write_text(pipeline_content)
        self.log_action('Created: config/pipeline_config.py')
    
    def create_gitignore(self) -> None:
        '''Create .gitignore file'''
        self.log_action('Creating .gitignore...')
        
        gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
*.egg-info/
dist/
build/
.venv/
venv/
*.pkl

# IDE
.idea/
.vscode/
*.swp
*.swo

# Project specific
data/raw/*.pdf
data/processed/
output/
*.tar.gz

# OS
.DS_Store
Thumbs.db

# Logs
*.log
start_time.txt
"""
        gitignore = self.root / '.gitignore'
        gitignore.write_text(gitignore_content)
        self.log_action('Created: .gitignore')
    
    def create_readme(self) -> None:
        '''Create README.md'''
        self.log_action('Creating README.md...')
        
        readme_content = """# PDF Processing Pipeline

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
"""
        readme = self.root / 'README.md'
        readme.write_text(readme_content)
        self.log_action('Created: README.md')
    
    def save_migration_log(self) -> None:
        '''Save migration log to file'''
        log_file = self.root / 'notes' / 'migration_log.txt'
        
        content = f"""Project Migration Log
{'='*60}
Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

ACTIONS TAKEN:
{'='*60}
"""
        content += '\n'.join(self.log)
        
        if self.errors:
            content += f'\n\nERRORS:\n{"="*60}\n'
            content += '\n'.join(self.errors)
        
        log_file.write_text(content)
        print(f'\n✓ Migration log saved to: {log_file}')
    
    def run(self) -> None:
        '''Execute full migration'''
        print('='*60)
        print('PROJECT STRUCTURE MIGRATION')
        print('='*60)
        print(f'Project root: {self.root}')
        print()
        
        try:
            self.create_new_structure()
            self.copy_core_modules()
            self.copy_cli_scripts()
            self.copy_utility_modules()
            self.create_config_files()
            self.create_gitignore()
            self.create_readme()
            self.move_chat_files()
            self.move_output_files()
            self.archive_old_versions()
            self.save_migration_log()
            
            print()
            print('='*60)
            print('MIGRATION COMPLETED SUCCESSFULLY!')
            print('='*60)
            print(f'Total actions: {len(self.log)}')
            print(f'Total errors: {len(self.errors)}')
            print()
            print('Next steps:')
            print('1. Review the migration log in notes/migration_log.txt')
            print('2. Check that v16_workable is preserved in archive/')
            print('3. Test the new structure')
            print('4. Remove old claude/ directory when satisfied')
            
        except Exception as e:
            self.log_error(f'Migration failed: {e}')
            raise


if __name__ == '__main__':
    migrator = ProjectMigrator(PROJECT_ROOT)
    migrator.run()
