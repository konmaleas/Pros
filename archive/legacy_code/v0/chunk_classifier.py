class ChunkClassifier:
    """
    Classify chunks into semantic categories for template building.
    """

    @staticmethod
    def classify_chunk(chunk: list) -> str:
        """
        Classify a chunk into one of four categories.

        Returns: 'structural', 'measurement', 'metadata', 'noise'
        """
        chunk_str = ' '.join(chunk) if isinstance(chunk, list) else str(chunk)
        chunk_upper = chunk_str.upper()

        # 1. NOISE - Remove entirely
        if ChunkClassifier._is_noise(chunk, chunk_str, chunk_upper):
            return 'noise'

        # 2. STRUCTURAL LANDMARKS - High priority
        if ChunkClassifier._is_structural(chunk, chunk_str, chunk_upper):
            return 'structural'

        # 3. DOCUMENT METADATA - Moderate priority
        if ChunkClassifier._is_metadata(chunk, chunk_str, chunk_upper):
            return 'metadata'

        # 4. CONTENT MEASUREMENTS - Ignore for templates
        if ChunkClassifier._is_measurement(chunk, chunk_str, chunk_upper):
            return 'measurement'

        # Default to measurement if unclear
        return 'measurement'

    @staticmethod
    def _is_noise(chunk, chunk_str, chunk_upper):
        """Identify pure noise to remove."""
        # Single characters
        if len(chunk_str) <= 1:
            return True

        # Common OCR artifacts
        noise_patterns = ['|', '—', '–', '...', '___']
        if any(pattern in chunk_str for pattern in noise_patterns):
            return True

        # Excessive punctuation
        if len([c for c in chunk_str if not c.isalnum()]) > len(chunk_str) * 0.7:
            return True

        return False

    @staticmethod
    def _is_structural(chunk, chunk_str, chunk_upper):
        """Identify structural landmarks for templates."""
        # Project/building descriptors
        structural_keywords = ['HIGH', 'RISE', 'RESIDENTIAL', 'DEVELOPMENT', 'PROJECT',
                               'BUILDING', 'TOWER', 'COMPLEX', 'INDICATED', 'REFER',
                               'TYPOLOGY', 'CASES', 'TYPE', 'DRAWING', 'SHEET',
                               'LAYOUT', 'SCALE', 'TITLE', 'REFERENCE', 'GENERAL', 'NOTES']

        # Zone/classification codes with letters
        if any(keyword in chunk_upper for keyword in structural_keywords):
            return True

        # Zone codes (A.U1.5, etc.)
        if '.' in chunk_str and any(c.isalpha() for c in chunk_str):
            return True

        # Drawing references (CD, DWG, etc.)
        if chunk_upper in ['CD', 'DWG', 'IC', 'RES', 'VAP']:
            return True

        return False

    @staticmethod
    def _is_metadata(chunk, chunk_str, chunk_upper):
        """Identify document metadata."""
        # Dates
        if any(c.isdigit() for c in chunk_str) and len(chunk_str) == 4:
            try:
                year = int(chunk_str)
                if 1900 <= year <= 2100:
                    return True
            except:
                pass

        # Company/location info
        metadata_keywords = ['MAROUSI', 'THESSALONIKI', 'HELLINIKON', 'ATHENS', 'GREECE', 'SAMARAS', 'ASSOCIATES',
            'CONSULTING', 'ENGINEERS', 'S.A.', 'BJARKE', 'INGELS', 'GROUP', 'BIG', 'HILL', 'INTERNATIONAL', 'APPROVED',
            'CHECKED', 'VERIFIED', 'DESIGNER', 'ARCHITECT', 'CONSTRUCTION', 'SET', 'ISSUED', 'STATUS', 'PMC']

        if any(keyword in chunk_upper for keyword in metadata_keywords):
            return True

        # Addresses (postal codes, street numbers)
        if chunk_str.isdigit() and len(chunk_str) == 5:
            return True

        return False

    @staticmethod
    def _is_measurement(chunk, chunk_str, chunk_upper):
        """Identify measurements and technical specifications."""
        # Pure numbers (dimensions, quantities)
        if chunk_str.isdigit():
            return True

        # Room types/counts
        room_patterns = ['BR', 'BEDROOM', 'BATHROOM', 'KITCHEN']
        if any(pattern in chunk_upper for pattern in room_patterns):
            return True

        # Technical specifications
        measurement_keywords = ['CABINET', 'LINEAR', 'ROOM', 'CODE', 'UNIT', 'SUBCONSULTANT', 'MEP', 'LIGHTING',
            'ACOUSTICS', 'SUSTAINABILITY', 'LANDSCAPE']

        if any(keyword in chunk_upper for keyword in measurement_keywords):
            return True

        return False
