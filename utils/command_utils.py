"""
Command parsing utility functions.
"""

def parse_equals(args, usage_msg=None, caller=None):
    """Parse = separated arguments.
    
    Args:
        args: String to parse
        usage_msg: Optional usage message if parsing fails
        caller: Optional caller to send error messages to
        
    Returns:
        tuple: (left, right) parts or (None, None) if parsing fails
    """
    if "=" not in args:
        if caller and usage_msg:
            caller.msg(f"Usage: {usage_msg}")
        return None, None
    return [part.strip() for part in args.split("=", 1)]


def parse_comma(text, expected_parts=2, usage_msg=None, caller=None):
    """Parse comma-separated arguments.
    
    Args:
        text: String to parse
        expected_parts: Number of expected parts
        usage_msg: Optional usage message if parsing fails
        caller: Optional caller to send error messages to
        
    Returns:
        list or None: List of parts or None if parsing fails
    """
    try:
        parts = [part.strip() for part in text.split(",", expected_parts - 1)]
        if len(parts) != expected_parts:
            if caller and usage_msg:
                caller.msg(f"Usage: {usage_msg}")
            return None
        return parts
    except (ValueError, IndexError):
        if caller and usage_msg:
            caller.msg(f"Usage: {usage_msg}")
        return None 