"""
Redesigned PDF Text Processing System
=====================================

This redesign addresses the architectural issues identified in the original code:
- Separation of concerns
- Dependency injection
- Configuration management
- Error handling
- Testability
- Modular design
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union, Any
from enum import Enum
import logging
from collections import Counter


# ============================================================================
# CONFIGURATION MANAGEMENT
# ============================================================================

@dataclass
class ProcessingConfig:
    """Centralized configuration for all processing parameters."""

    # File processing
    supported_extensions: List[str] = field(default_factory=lambda: ['.pkl', '.txt'])
    output_directory: str = 'processed_files'

    # Text filtering
    noise_threshold_buffer: int = 2
    max_word_frequency_threshold: int = 20
    min_word_length: int = 1
    max_word_length: int = 50

    # Template generation
    max_distance: int = 100
    min_cluster_size: int = 3
    max_chunks: int = 5
    cluster_window: int = 100
    density_window: int = 50

    # Analysis parameters
    repetition_operation: str = '>='
    debug_output: bool = True
    save_intermediate_results: bool = True


@dataclass
class TitleConfig:
    """Configuration specific to title analysis."""

    title_pattern: str
    title_chunks: List[str] = field(init=False)
    alpha_chunks: List[str] = field(init=False)
    digit_chunks: List[str] = field(init=False)

    def __post_init__(self):
        self.title_chunks = self.title_pattern.split('-')
        self.alpha_chunks = [chunk for chunk in self.title_chunks if chunk.isalpha()]
        self.digit_chunks = [chunk for chunk in self.title_chunks if chunk.isdigit()]


# ============================================================================
# ERROR HANDLING
# ============================================================================

class ProcessingError(Exception):
    """Base exception for all processing errors."""
    pass


class ValidationError(ProcessingError):
    """Raised when input validation fails."""
    pass


class FileOperationError(ProcessingError):
    """Raised when file operations fail."""
    pass


class AnalysisError(ProcessingError):
    """Raised when analysis operations fail."""
    pass


class TemplateGenerationError(ProcessingError):
    """Raised when template generation fails."""
    pass


# ============================================================================
# RESULT TYPES
# ============================================================================

@dataclass
class ProcessingResult:
    """Rich result type for processing operations."""

    success: bool
    data: Any = None
    error_message: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def success_result(cls, data: Any, metadata: Dict[str, Any] = None) -> 'ProcessingResult':
        return cls(success=True, data=data, metadata=metadata or {})

    @classmethod
    def error_result(cls, error_message: str, metadata: Dict[str, Any] = None) -> 'ProcessingResult':
        return cls(success=False, error_message=error_message, metadata=metadata or {})


class AnchorSelectionStrategy(Enum):
    """Strategies for selecting anchor positions."""
    FIRST = "first"
    DENSITY = "density"
    CLUSTER = "cluster"


# ============================================================================
# ABSTRACT INTERFACES
# ============================================================================

class FileSystemInterface(ABC):
    """Abstract interface for file system operations."""

    @abstractmethod
    def read_file(self, path: Path) -> List[str]:
        """Read file content as list of lines."""
        pass

    @abstractmethod
    def write_file(self, path: Path, content: Any, mode: str = 'w') -> None:
        """Write content to file."""
        pass

    @abstractmethod
    def list_files(self, directory: Path, extension: str = None) -> List[Path]:
        """List files in directory with optional extension filter."""
        pass

    @abstractmethod
    def ensure_directory(self, path: Path) -> None:
        """Ensure directory exists."""
        pass


class TextFilterInterface(ABC):
    """Abstract interface for text filtering strategies."""

    @abstractmethod
    def filter_text(self, text: str, title_config: TitleConfig) -> ProcessingResult:
        """Filter text and return processed lines."""
        pass


class ChunkAnalyzerInterface(ABC):
    """Abstract interface for chunk analysis."""

    @abstractmethod
    def extract_chunks(self, files: List[Path]) -> ProcessingResult:
        """Extract chunks from files."""
        pass

    @abstractmethod
    def find_constant_chunks(self, chunk_data: Dict, repetition_threshold: int) -> ProcessingResult:
        """Find chunks that appear consistently across files."""
        pass


# ============================================================================
# CONCRETE IMPLEMENTATIONS
# ============================================================================

class LocalFileSystem(FileSystemInterface):
    """Local file system implementation."""

    def __init__(self, logger: logging.Logger = None):
        self.logger = logger or logging.getLogger(__name__)

    def read_file(self, path: Path) -> List[str]:
        """Read file content as list of lines."""
        try:
            with open(path, 'r', encoding='utf-8') as file:
                return [line.strip() for line in file.readlines()]
        except Exception as e:
            raise FileOperationError(f"Failed to read file {path}: {e}")

    def write_file(self, path: Path, content: Any, mode: str = 'w') -> None:
        """Write content to file."""
        try:
            self.ensure_directory(path.parent)
            with open(path, mode, encoding='utf-8') as file:
                if isinstance(content, (list, tuple)):
                    file.write('\n'.join(str(item) for item in content))
                else:
                    file.write(str(content))
        except Exception as e:
            raise FileOperationError(f"Failed to write file {path}: {e}")

    def list_files(self, directory: Path, extension: str = None) -> List[Path]:
        """List files in directory with optional extension filter."""
        try:
            if not directory.exists():
                return []

            files = []
            for file_path in directory.iterdir():
                if file_path.is_file():
                    if extension is None or file_path.suffix == extension:
                        files.append(file_path)
            return sorted(files)
        except Exception as e:
            raise FileOperationError(f"Failed to list files in {directory}: {e}")

    def ensure_directory(self, path: Path) -> None:
        """Ensure directory exists."""
        try:
            path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise FileOperationError(f"Failed to create directory {path}: {e}")


class FrequencyBasedTextFilter(TextFilterInterface):
    """Advanced text filtering based on frequency analysis."""

    def __init__(self, config: ProcessingConfig, logger: logging.Logger = None):
        self.config = config
        self.logger = logger or logging.getLogger(__name__)

    def filter_text(self, text: str, title_config: TitleConfig) -> ProcessingResult:
        """Filter text using frequency-based adaptive filtering."""
        try:
            # Step 1: Analyze word frequencies
            word_frequencies = self._count_word_frequencies(text)

            # Step 2: Calculate noise threshold
            noise_threshold = self._calculate_noise_threshold(word_frequencies, title_config)

            # Step 3: Filter lines
            filtered_lines = self._filter_lines(text, word_frequencies, noise_threshold, title_config)

            metadata = {'total_words' : len(word_frequencies), 'noise_threshold': noise_threshold,
                'filtered_lines_count': len(filtered_lines)}

            return ProcessingResult.success_result(filtered_lines, metadata)

        except Exception as e:
            self.logger.error(f"Text filtering failed: {e}")
            return ProcessingResult.error_result(f"Text filtering failed: {e}")

    def _count_word_frequencies(self, text: str) -> Dict[str, int]:
        """Count frequency of each word in the text."""
        words = []
        for line in text.split('\n'):
            cleaned_line = self._clean_line(line)
            words.extend(cleaned_line.split())

        # Clean and count
        cleaned_words = [word.strip('.,!?;:"()[]{}') for word in words if word.strip('.,!?;:"()[]{}')]
        return Counter(cleaned_words)

    def _calculate_noise_threshold(self, word_frequencies: Dict[str, int], title_config: TitleConfig) -> int:
        """Calculate noise threshold based on title chunk frequencies."""
        title_freqs = []
        for chunk in title_config.title_chunks:
            if chunk in word_frequencies:
                title_freqs.append(word_frequencies[chunk])

        if title_freqs:
            return max(title_freqs) + self.config.noise_threshold_buffer
        else:
            return self.config.max_word_frequency_threshold

    def _filter_lines(self, text: str, word_frequencies: Dict[str, int], noise_threshold: int,
                      title_config: TitleConfig) -> List[List[str]]:
        """Filter text lines using combined criteria."""
        filtered_lines = []

        for line in text.split('\n'):
            cleaned_line = self._clean_line(line)
            words = cleaned_line.split()

            filtered_words = []
            for word in words:
                word = word.strip('.,!?;:"()[]{}')
                if word and self._should_keep_word(word, word_frequencies, noise_threshold, title_config):
                    filtered_words.append(word)

            if filtered_words:
                filtered_lines.append(filtered_words)

        return filtered_lines

    def _clean_line(self, line: str) -> str:
        """Basic line cleaning."""
        allowed_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 .,-')
        cleaned = ''.join(char if char in allowed_chars else ' ' for char in line)
        return ' '.join(cleaned.split())

    def _should_keep_word(self, word: str, word_frequencies: Dict[str, int], noise_threshold: int,
                          title_config: TitleConfig) -> bool:
        """Determine if word should be kept."""
        # Always keep title chunks
        if word in title_config.title_chunks:
            return True

        # Remove high frequency noise
        if word_frequencies.get(word, 0) > noise_threshold:
            return False

        # Remove pattern-based noise
        if self._is_pattern_noise(word):
            return False

        # Apply selective rules
        return self._apply_selective_rules(word, title_config)

    def _is_pattern_noise(self, word: str) -> bool:
        """Identify pattern-based noise."""
        # Long digits are noise
        if word.isdigit() and len(word) > 5:
            return True

        # Decimal numbers
        if '.' in word and word.replace('.', '').replace('-', '').isdigit():
            return True

        return False

    def _apply_selective_rules(self, word: str, title_config: TitleConfig) -> bool:
        """Apply selective rules for remaining words."""
        if word.isalpha():
            if len(word) == 1:
                return word in title_config.alpha_chunks
            if len(word) <= 3:
                return word.isupper()
            return word.isupper() or word.istitle()

        if word.isdigit():
            if len(word) == 1:
                return word in title_config.digit_chunks
            elif len(word) <= 3:
                return word in title_config.digit_chunks
            elif len(word) <= 5:
                return word in title_config.digit_chunks

        return False


class ChunkAnalyzer(ChunkAnalyzerInterface):
    """Analyzer for extracting and analyzing text chunks."""

    def __init__(self, file_system: FileSystemInterface, config: ProcessingConfig, logger: logging.Logger = None):
        self.file_system = file_system
        self.config = config
        self.logger = logger or logging.getLogger(__name__)

    def extract_chunks(self, files: List[Path]) -> ProcessingResult:
        """Extract chunks from all files."""
        try:
            chunk_line_mapping = {}
            all_chunks = []

            for file_path in files:
                lines = self.file_system.read_file(file_path)
                for line_num, line in enumerate(lines):
                    # Assume lines are already processed into chunks (words)
                    chunks = line.split() if isinstance(line, str) else line
                    for chunk in chunks:
                        if self._is_valid_chunk(chunk):
                            all_chunks.append(chunk)
                            if chunk not in chunk_line_mapping:
                                chunk_line_mapping[chunk] = []
                            chunk_line_mapping[chunk].append(line_num)

            result_data = {'chunk_line_mapping': chunk_line_mapping, 'all_chunks': all_chunks}

            metadata = {'files_processed': len(files), 'total_chunks': len(all_chunks),
                'unique_chunks'          : len(chunk_line_mapping)}

            return ProcessingResult.success_result(result_data, metadata)

        except Exception as e:
            self.logger.error(f"Chunk extraction failed: {e}")
            return ProcessingResult.error_result(f"Chunk extraction failed: {e}")

    def find_constant_chunks(self, chunk_data: Dict, repetition_threshold: int) -> ProcessingResult:
        """Find chunks that appear consistently across files."""
        try:
            all_chunks = chunk_data.get('all_chunks', [])
            chunk_repetitions = Counter(all_chunks)

            constant_chunks = {}
            for chunk, count in chunk_repetitions.items():
                if self._meets_repetition_criteria(count, repetition_threshold):
                    constant_chunks[chunk] = count

            metadata = {'total_unique_chunks': len(chunk_repetitions),
                        'constant_chunks_found': len(constant_chunks),
                'repetition_threshold'       : repetition_threshold}

            return ProcessingResult.success_result(constant_chunks, metadata)

        except Exception as e:
            self.logger.error(f"Constant chunk analysis failed: {e}")
            return ProcessingResult.error_result(f"Constant chunk analysis failed: {e}")

    def _is_valid_chunk(self, chunk: str) -> bool:
        """Validate if chunk should be processed."""
        if not chunk or len(chunk) > self.config.max_word_length:
            return False

        # Check if it's a valid alphanumeric chunk
        return chunk.isdigit() or chunk.isalpha() or chunk.isalnum()

    def _meets_repetition_criteria(self, count: int, threshold: int) -> bool:
        """Check if chunk count meets repetition criteria."""
        operation = self.config.repetition_operation
        if operation == '>=':
            return count >= threshold
        elif operation == '>':
            return count > threshold
        elif operation == '==':
            return count == threshold
        else:
            return count >= threshold


class TemplateGenerator:
    """Generates title templates from analyzed chunks."""

    def __init__(self, config: ProcessingConfig, logger: logging.Logger = None):
        self.config = config
        self.logger = logger or logging.getLogger(__name__)

    def generate_template(self, title_positions: Dict[str, List[int]], all_chunk_positions: Dict[str, List[int]],
                          strategy: AnchorSelectionStrategy = AnchorSelectionStrategy.CLUSTER) -> ProcessingResult:
        """Generate template with distance relationships."""
        try:
            # Step 1: Select optimal anchors
            selected_anchors = self._select_anchors(title_positions, strategy)

            if not selected_anchors:
                return ProcessingResult.error_result("No suitable anchors found")

            # Step 2: Calculate distance relationships
            template_distances = {}
            for title_chunk, anchor_line in selected_anchors.items():
                chunk_distances = self._calculate_distances(anchor_line, all_chunk_positions)
                if chunk_distances:
                    template_distances[title_chunk] = chunk_distances

            # Step 3: Filter and rank results
            final_template = self._filter_and_rank_distances(template_distances)

            metadata = {'strategy_used' : strategy.value,
                        'anchors_selected': len(selected_anchors),
                        'title_chunks_processed': len(template_distances)}

            return ProcessingResult.success_result(final_template, metadata)

        except Exception as e:
            self.logger.error(f"Template generation failed: {e}")
            return ProcessingResult.error_result(f"Template generation failed: {e}")

    def _select_anchors(self, title_positions: Dict[str, List[int]], strategy: AnchorSelectionStrategy) -> Dict[
        str, int]:
        """Select optimal anchor positions for each title chunk."""
        anchors = {}

        for title_chunk, positions in title_positions.items():
            if not positions:
                continue

            if strategy == AnchorSelectionStrategy.FIRST:
                anchors[title_chunk] = min(positions)
            elif strategy == AnchorSelectionStrategy.DENSITY:
                anchor = self._find_density_anchor(positions, title_positions)
                anchors[title_chunk] = anchor
            elif strategy == AnchorSelectionStrategy.CLUSTER:
                anchor = self._find_cluster_anchor(positions, title_positions)
                anchors[title_chunk] = anchor

        return anchors

    def _find_density_anchor(self, positions: List[int], all_positions: Dict[str, List[int]]) -> int:
        """Find position with highest density of other title chunks."""
        best_position = positions[0]
        max_density = 0

        for pos in positions:
            density = 0
            for other_positions in all_positions.values():
                for other_pos in other_positions:
                    if abs(other_pos - pos) <= self.config.density_window and other_pos != pos:
                        density += 1

            if density > max_density:
                max_density = density
                best_position = pos

        return best_position

    def _find_cluster_anchor(self, positions: List[int], all_positions: Dict[str, List[int]]) -> int:
        """Find anchor within largest cluster."""
        # Collect all positions
        all_pos = []
        for pos_list in all_positions.values():
            all_pos.extend(pos_list)
        all_pos.sort()

        # Find clusters
        clusters = self._find_position_clusters(all_pos)

        if not clusters:
            return positions[0]

        # Find largest cluster
        largest_cluster = max(clusters, key=len)

        # Find position from our title chunk closest to cluster center
        cluster_center = sum(largest_cluster) / len(largest_cluster)
        return min(positions, key=lambda x: abs(x - cluster_center))

    def _find_position_clusters(self, positions: List[int]) -> List[List[int]]:
        """Find clusters of positions within cluster window."""
        if not positions:
            return []

        clusters = []
        current_cluster = [positions[0]]

        for pos in positions[1:]:
            if pos - current_cluster[-1] <= self.config.cluster_window:
                current_cluster.append(pos)
            else:
                if len(current_cluster) >= self.config.min_cluster_size:
                    clusters.append(current_cluster)
                current_cluster = [pos]

        if len(current_cluster) >= self.config.min_cluster_size:
            clusters.append(current_cluster)

        return clusters

    def _calculate_distances(self, anchor_line: int, all_positions: Dict[str, List[int]]) -> Dict[int, List[str]]:
        """Calculate distances from anchor to all other chunks."""
        distances = {}

        for chunk, positions in all_positions.items():
            for pos in positions:
                distance = pos - anchor_line
                if 0 < abs(distance) <= self.config.max_distance:
                    if distance not in distances:
                        distances[distance] = []
                    distances[distance].append(chunk)

        return distances

    def _filter_and_rank_distances(self, template_distances: Dict) -> Dict:
        """Filter and rank distance relationships."""
        filtered_template = {}

        for title_chunk, distances in template_distances.items():
            # Sort by distance (closest first)
            sorted_distances = dict(sorted(distances.items(), key=lambda x: abs(x[0])))

            # Take only the closest chunks up to max_chunks
            closest_chunks = {}
            for distance, chunks in sorted_distances.items():
                closest_chunks[distance] = chunks
                if len(closest_chunks) >= self.config.max_chunks:
                    break

            if closest_chunks:
                filtered_template[title_chunk] = closest_chunks

        return filtered_template


# ============================================================================
# SERVICE LAYER
# ============================================================================

class DocumentProcessingService:
    """High-level service for document processing operations."""

    def __init__(self, file_system: FileSystemInterface, text_filter: TextFilterInterface,
                 chunk_analyzer: ChunkAnalyzerInterface, template_generator: TemplateGenerator,
                 config: ProcessingConfig, logger: logging.Logger = None):
        self.file_system = file_system
        self.text_filter = text_filter
        self.chunk_analyzer = chunk_analyzer
        self.template_generator = template_generator
        self.config = config
        self.logger = logger or logging.getLogger(__name__)

    def process_documents(self, input_directory: Path, title_pattern: str) -> ProcessingResult:
        """Process all documents in directory and generate title template."""
        try:
            self.logger.info(f"Starting document processing for directory: {input_directory}")

            # Step 1: Validate inputs
            if not input_directory.exists():
                return ProcessingResult.error_result(f"Input directory does not exist: {input_directory}")

            title_config = TitleConfig(title_pattern)

            # Step 2: Collect files
            files = []
            for ext in self.config.supported_extensions:
                files.extend(self.file_system.list_files(input_directory, ext))

            if not files:
                return ProcessingResult.error_result(f"No supported files found in {input_directory}")

            self.logger.info(f"Found {len(files)} files to process")

            # Step 3: Extract chunks
            chunk_result = self.chunk_analyzer.extract_chunks(files)
            if not chunk_result.success:
                return chunk_result

            # Step 4: Find constant chunks
            constant_result = self.chunk_analyzer.find_constant_chunks(chunk_result.data, len(files))
            if not constant_result.success:
                return constant_result

            # Step 5: Analyze title positions (simplified for this example)
            title_positions = self._analyze_title_positions(files, title_config)

            # Step 6: Generate template
            template_result = self.template_generator.generate_template(title_positions,
                    chunk_result.data.get('chunk_line_mapping', {}), AnchorSelectionStrategy.CLUSTER)

            if not template_result.success:
                return template_result

            # Combine all results
            final_result = {'template': template_result.data, 'chunk_analysis': chunk_result.data,
                            'constant_chunks': constant_result.data, 'title_positions': title_positions,
                            'files_processed': files}

            metadata = {'total_files': len(files), 'processing_steps_completed': 6, **chunk_result.metadata,
                **constant_result.metadata, **template_result.metadata}

            self.logger.info("Document processing completed successfully")
            return ProcessingResult.success_result(final_result, metadata)

        except Exception as e:
            self.logger.error(f"Document processing failed: {e}")
            return ProcessingResult.error_result(f"Document processing failed: {e}")

    def _analyze_title_positions(self, files: List[Path], title_config: TitleConfig) -> Dict[str, List[int]]:
        """Analyze positions of title chunks in files."""
        title_positions = {}

        for file_path in files:
            try:
                lines = self.file_system.read_file(file_path)
                for line_num, line in enumerate(lines):
                    for chunk in title_config.title_chunks:
                        if chunk in line:
                            if chunk not in title_positions:
                                title_positions[chunk] = []
                            title_positions[chunk].append(line_num)
            except Exception as e:
                self.logger.warning(f"Failed to analyze title positions in {file_path}: {e}")

        return title_positions


# ============================================================================
# FACTORY AND DEPENDENCY INJECTION
# ============================================================================

class ProcessingServiceFactory:
    """Factory for creating configured processing services."""

    @staticmethod
    def create_service(config: ProcessingConfig = None, logger: logging.Logger = None) -> DocumentProcessingService:
        """Create a fully configured processing service."""

        if config is None:
            config = ProcessingConfig()

        if logger is None:
            logging.basicConfig(level=logging.INFO)
            logger = logging.getLogger(__name__)

        # Create infrastructure components
        file_system = LocalFileSystem(logger)
        text_filter = FrequencyBasedTextFilter(config, logger)
        chunk_analyzer = ChunkAnalyzer(file_system, config, logger)
        template_generator = TemplateGenerator(config, logger)

        # Create and return service
        return DocumentProcessingService(file_system=file_system, text_filter=text_filter,
                chunk_analyzer=chunk_analyzer, template_generator=template_generator, config=config, logger=logger)


# ============================================================================
# MAIN APPLICATION
# ============================================================================

def main():
    """Main application entry point."""

    # Configure logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)

    try:
        # Create configuration
        config = ProcessingConfig(max_distance=100, min_cluster_size=3, max_chunks=5, debug_output=True)

        # Create service
        service = ProcessingServiceFactory.create_service(config, logger)

        # Process documents
        input_dir = Path("path/to/your/documents")
        title_pattern = "4005-RES-VAP-DWG-233-IC-07020-0"

        result = service.process_documents(input_dir, title_pattern)

        if result.success:
            logger.info("Processing completed successfully")
            logger.info(f"Metadata: {result.metadata}")

            # Save results if configured
            if config.save_intermediate_results:
                output_dir = Path(config.output_directory)
                service.file_system.ensure_directory(output_dir)
                service.file_system.write_file(output_dir / "processing_results.txt", str(result.data))
        else:
            logger.error(f"Processing failed: {result.error_message}")

    except Exception as e:
        logger.error(f"Application failed: {e}")
        raise


if __name__ == "__main__":
    main()
