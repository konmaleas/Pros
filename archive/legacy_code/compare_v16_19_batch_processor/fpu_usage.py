# Usage:
def test_files(path: Path):
    """Test function to find min and max files"""
    files = [str(f) for f in path.glob('*.pdf')]
    
    print(f"Total files: {len(files)}")
    print("=" * 60)
    
    print("\nFinding MAX file:")
    print("-" * 60)
    max_file = find_file_by_number(files, max)
    
    print("\n" + "=" * 60)
    print("\nFinding MIN file:")
    print("-" * 60)
    min_file = find_file_by_number(files, min)
    
    print("\n" + "=" * 60)
    print("FINAL RESULTS:")
    print("=" * 60)
    print(f"Max: {Path(max_file).name if max_file else None}")
    print(f"Min: {Path(min_file).name if min_file else None}")
    
    return {
        'max': Path(max_file).name if max_file else None,
        'min': Path(min_file).name if min_file else None
    }


# Run it:
if __name__ == "__main__":
    p = Path("/media/konstantinos/8T/Projects/2213 AMANZOE_V24/DETAILS")
    result = test_files(p)
