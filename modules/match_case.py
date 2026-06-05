def operations(x: int, y: int, operators: str) -> bool:
    match operators:
        case '>':
            return x > y
        case '>=':
            return x >= y
        case '<':
            return x < y
        case '<=':
            return x <= y
        case '==':
            return x == y
