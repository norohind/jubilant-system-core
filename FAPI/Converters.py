def dehexify(hex_str: str) -> str:
    """Converts string with hex chars to string"""
    return bytes.fromhex(hex_str).decode('utf-8')
