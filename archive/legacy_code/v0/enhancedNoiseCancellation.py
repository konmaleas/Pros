from modules.string_manipulation import singling_symbols, replacer_2
from dataclasses import dataclass
import operator
from typing import Callable
import spacy


@dataclass
class NoiseCancellation:
    """
    A class designed to filter and clean text chunks by removing unwanted elements.

    This class provides methods to:
    1. Remove grammatical noise (articles, prepositions, etc.)
    2. Apply custom filtering based on string properties (length, content, type)
    3. Process output from clear_file_ method for comprehensive text cleaning

    Attributes:
        chunks (list[str] or list[list[str]]): List of text chunks to be processed and filtered
                                              Can handle both flat lists and nested lists from clear_file_
    """
    chunks: list

    @classmethod
    def from_clear_file(cls, text: str):
        """
        Create NoiseCancellation instance directly from text using clear_file_ logic.
        
        Args:
            text (str): Raw text to process
            
        Returns:
            NoiseCancellation: Instance with processed chunks ready for filtering
        """
        processed_chunks = cls.clear_file_(text)
        # Flatten the list of word lists into a single list of words
        flattened_chunks = [word for word_list in processed_chunks for word in word_list if word.strip()]
        return cls(flattened_chunks)

    @staticmethod
    def clear_file_(text: str) -> list:
        """
        Process raw text into cleaned word lists (integrated from PdfToText).
        
        This method:
        1. Splits text by newlines
        2. Processes each line using replacer_2 and singling_symbols
        3. Splits processed lines into words
        4. Filters out empty words
        5. Returns list of word lists for non-empty lines
        
        Args:
            text (str): Raw text to process
            
        Returns:
            list[list[str]]: List of word lists, one per non-empty line
        """
        lst = []
        for line in text.split('\n'):
            # Note: You'll need to ensure replacer_2 and singling_symbols are available
            # These functions should be imported or defined in your module
            processed_line_str = singling_symbols(replacer_2(line, ' ', preserve=[',', '.']))
            
            # Split the processed string by space
            words = processed_line_str.split(' ')
            
            # Filter out empty strings from the 'words' list
            filtered_words = [word for word in words if word.strip()]
            
            # Append to lst only if the filtered_words list is not empty
            if filtered_words:
                lst.append(filtered_words)
        return lst

    def process_nested_chunks(self) -> 'NoiseCancellation':
        """
        Convert nested list structure (from clear_file_) into flat list for processing.
        
        Returns:
            NoiseCancellation: New instance with flattened chunks
        """
        if self.chunks and isinstance(self.chunks[0], list):
            flattened = [word for word_list in self.chunks for word in word_list if word.strip()]
            return NoiseCancellation(flattened)
        return self

    def exclude_noise(self, exclusions: list) -> list:
        """
        Remove grammatical noise words using spaCy's part-of-speech tagging.

        This method:
        1. Handles both flat and nested chunk structures
        2. Joins all chunks into a single text for spaCy processing
        3. Analyzes each token's part-of-speech (POS) tag
        4. Excludes tokens whose POS tags are in the exclusions list
        5. Returns cleaned tokens as a new list

        Args:
            exclusions (list): List of POS tags to exclude (e.g., ['ADP', 'DET'])

        Returns:
            list: Filtered list of tokens with noise words removed
        """
        # Ensure we have a flat list of chunks
        if self.chunks and isinstance(self.chunks[0], list):
            flat_chunks = [word for word_list in self.chunks for word in word_list]
        else:
            flat_chunks = self.chunks

        nlp = spacy.load("en_core_web_sm")
        doc = nlp(' '.join(flat_chunks))

        lst = []
        for token in doc:
            if token.pos_ in exclusions:
                continue
            lst.append(token.text)
        return lst

    def custom_exclusions(self, strings: list[str],
                          operation: operator,
                          size: int, length_mode: bool,
                          check_func: Callable[[str], bool],
                          exceptions: list[str] = None) -> list:
        """
        Apply custom filtering logic based on string properties and conditions.
        Handles both flat and nested chunk structures.

        Args:
            strings (list[str]): List of specific strings to include/exclude
            operation (operator): Comparison operator (eq, lt, gt, le, ge, ne)
            size (int): Threshold value for length comparison
            length_mode (bool): True for length-based, False for content-based filtering
            check_func (Callable[[str], bool]): Function to test chunk properties
            exceptions (list[str], optional): Strings to KEEP regardless of other criteria

        Returns:
            list: Filtered chunks based on the specified criteria
        """
        # Ensure we have a flat list of chunks
        if self.chunks and isinstance(self.chunks[0], list):
            flat_chunks = [word for word_list in self.chunks for word in word_list]
        else:
            flat_chunks = self.chunks

        if exceptions is None:
            exceptions = []

        lst = []
        for chunk in flat_chunks:
            # First check: if chunk is in exceptions list, always keep it
            if chunk in exceptions:
                lst.append(chunk)
                continue

            # Apply the check function to determine if this chunk should be evaluated
            if check_func(chunk):
                # Perform length comparison using the provided operator
                if operation(len(chunk), size):
                    if length_mode:
                        # Length-based exclusion: skip chunks that match the length condition
                        continue
                    # Content-based exclusion: skip chunks that are NOT in the strings list
                    if chunk not in strings:
                        continue
            # If we reach here, keep the chunk
            lst.append(chunk)
        return lst

    def full_pipeline_processing(self, text: str, filters: list = None) -> list:
        """
        Complete processing pipeline: clear_file_ + noise cancellation + custom filters.
        
        Args:
            text (str): Raw text to process
            filters (list, optional): List of filter tuples to apply
                                     Defaults to standard grammatical noise removal
            
        Returns:
            list: Fully processed and filtered chunks
        """
        if filters is None:
            filters = [
                # Remove grammatical noise
                ('exclude_noise', [exclusions()], {}),
                # Remove single alphabetic characters
                ('custom_exclusions', ([], operator.eq, 1, True, str.isalpha), {}),
                # Remove short numeric strings, keep '0'
                ('custom_exclusions', (['0'], operator.lt, 3, True, str.isdigit), {}),
            ]
        
        # Process text using clear_file_ method
        processed_chunks = self.clear_file_(text)
        
        # Create instance with processed chunks
        noise_cancellation = NoiseCancellation(processed_chunks)
        
        # Apply filters
        return apply_filters(processed_chunks, filters)


def exclusions() -> list:
    """Define standard grammatical elements to exclude during noise removal."""
    return ['ADP', 'DET', 'CCONJ', 'AUX', 'SCONJ', 'X', 'PRON', 'PART']


def apply_filters(chunks, filters):
    """
    Apply a sequence of filtering operations to a list of chunks.
    Enhanced to handle nested structures from clear_file_.
    
    Args:
        chunks (list): Initial list of chunks (can be nested from clear_file_)
        filters (list): List of filter operation tuples
        
    Returns:
        list: Final filtered chunks after applying all filters
    """
    result = chunks

    for method_name, args, kwargs in filters:
        noise_cancellation = NoiseCancellation(result)
        method = getattr(noise_cancellation, method_name)
        result = method(*args, **kwargs)

    return result


# Usage example:
def example_usage():
    """
    Example of how to use the enhanced NoiseCancellation with clear_file_ integration.
    """
    # Sample text (like what would come from PDF extraction)
    sample_text = """The quick brown fox jumps over the lazy dog.
    This is a test of the text processing system.
    123 Main Street, Suite 100
    Phone: (555) 123-4567"""
    
    # Method 1: Direct processing with full pipeline
    nc = NoiseCancellation([])
    filtered_result = nc.full_pipeline_processing(sample_text)
    
    # Method 2: Step-by-step processing
    nc_from_text = NoiseCancellation.from_clear_file(sample_text)
    
    # Apply custom filters
    filters = [
        ('exclude_noise', [exclusions()], {}),
        ('custom_exclusions', ([], operator.eq, 1, True, str.isalpha), {}),
    ]
    
    final_result = apply_filters(nc_from_text.chunks, filters)
    
    return filtered_result, final_result
