from pathlib import Path
from collections import Counter
from string import punctuation
import re
from typing import List, Optional, Callable


def find_split_symbol(files: List[str]) -> Optional[str]:
    """Find the most common delimiter in filenames"""
    symbols = []
    for file in files:
        for char in Path(file).stem:
            if char in punctuation or char.isspace():
                symbols.append(char)
    
    if not symbols:
        return None
    
    counter = Counter(symbols)
    return counter.most_common(1)[0][0]


def find_file_by_number(files: List[str], selector: Callable = max) -> Optional[str]:
    """Find min/max file based on position-aware unique identifying numbers"""
    
    if not files:
        return None
    
    # Step 1: Find the delimiter
    delimiter = find_split_symbol(files)
    if not delimiter:
        print("No delimiter found")
        return None
    
    # Step 2: Split all files by delimiter
    splits = [Path(f).stem.split(delimiter) for f in files]
    max_segments = max(len(s) for s in splits) if splits else 0
    
    # Step 3: For each position, collect numbers and count occurrences
    position_numbers = {}  # {position: Counter of numbers at that position}
    
    for pos in range(max_segments):
        numbers_at_pos = []
        for split in splits:
            if pos < len(split):
                # Extract all numbers from this specific segment
                nums = re.findall(r'\d+', split[pos])
                numbers_at_pos.extend(nums)
        
        if numbers_at_pos:
            position_numbers[pos] = Counter(numbers_at_pos)
    
    # Step 4: Find the position with the most unique numbers (count=1)
    best_position = None
    max_unique_count = 0
    
    for pos, counter in position_numbers.items():
        # Count how many numbers appear only once at this position
        unique_count = sum(1 for count in counter.values() if count == 1)
        if unique_count > max_unique_count:
            max_unique_count = unique_count
            best_position = pos
    
    if best_position is None:
        print("No position with unique numbers found")
        return None
    
    print(f"Delimiter: '{delimiter}'")
    print(f"Best position (most unique numbers): {best_position}")
    print(f"Unique numbers at position {best_position}: {max_unique_count}")
    
    # Debug: show what counter looks like at best position
    print(f"Numbers at position {best_position}: {position_numbers[best_position].most_common(10)}")
    
    # Step 5: Extract the identifying number from the best position
    def get_identifier_at_position(filename: str) -> int:
        segments = Path(filename).stem.split(delimiter)
        if best_position >= len(segments):
            return -1
        
        # Extract all numbers from the identified position
        nums = re.findall(r'\d+', segments[best_position])
        # Return the last number in this segment (usually the identifier)
        return int(nums[-1]) if nums else -1
    
    # Debug: show some examples
    print("\nSample extractions:")
    sample = files[:5]
    for f in sample:
        print(f"{Path(f).name} -> {get_identifier_at_position(f)}")
    
    return selector(files, key=get_identifier_at_position)

