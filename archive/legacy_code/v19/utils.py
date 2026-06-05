import re
from typing import List


def split_title_chunks(title: str) -> List[str]:
    """
    Split title on all non-alphanumeric delimiters.
    
    Handles multiple delimiter types: hyphens, underscores, spaces, dots, etc.
    
    Args:
        title: The title string to split
        
    Returns:
        List of chunks (non-empty strings only)
        
    Examples:
        >>> split_title_chunks("LAN-ARC_FD-101 00")
        ['LAN', 'ARC', 'FD', '101', '00']
        
        >>> split_title_chunks("NCM-DD-B1-DR-ARC-4408-P1")
        ['NCM', 'DD', 'B1', 'DR', 'ARC', '4408', 'P1']
    """
    chunks = [chunk for chunk in re.split(r'[^a-zA-Z0-9]+', title) if chunk]
    return chunks
