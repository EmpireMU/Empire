"""
Organization utility functions.
"""

from evennia.utils.search import search_object
from evennia.utils import evtable
from typeclasses.organisations import Organisation
from typeclasses.characters import Character


def check_admin(caller):
    """Check if a caller has admin permissions.
    
    Args:
        caller: The command caller to check
        
    Returns:
        bool: True if admin, False otherwise
    """
    if not caller.check_permstring("Admin"):
        caller.msg("You don't have permission to perform this action.")
        return False
    return True


def validate_rank(rank_str, default=None, caller=None):
    """Validate rank numbers.
    
    Args:
        rank_str: The rank string to validate
        default: Default value if validation fails
        caller: Optional caller to send error messages to
        
    Returns:
        int or None: The validated rank number or None if invalid
    """
    try:
        rank = int(rank_str)
        if not 1 <= rank <= 10:
            if caller:
                caller.msg("Rank must be a number between 1 and 10.")
            return None
        return rank
    except (ValueError, TypeError):
        if default is not None:
            return default
        if caller:
            caller.msg("Rank must be a number between 1 and 10.")
        return None


def get_org(org_name, caller=None):
    """Find and validate an organization.
    
    Args:
        org_name: Name of the organization to find
        caller: Optional caller to send error messages to
        
    Returns:
        Organisation or None: The found organization or None if not found
    """
    org = caller.search(org_name, global_search=True) if caller else search_object(org_name)
    if not org:
        return None
        
    if not isinstance(org, Organisation):
        if caller:
            caller.msg(f"{org.name} is not an organization.")
        return None
        
    return org


def get_char(char_name, caller=None, check_resources=False):
    """Find and validate a character.
    
    Args:
        char_name: Name of the character to find
        caller: Optional caller to send error messages to
        check_resources: Whether to check if character can own resources
        
    Returns:
        Character or None: The found character or None if not found
    """
    char = caller.search(char_name, global_search=True) if caller else search_object(char_name)
    if not char:
        return None
        
    if check_resources and not hasattr(char, 'char_resources'):
        if caller:
            caller.msg(f"{char.name} cannot own resources.")
        return None
        
    return char


def get_org_and_char(org_name, char_name, caller=None):
    """Find both an organization and a character.
    
    Args:
        org_name: Name of the organization to find
        char_name: Name of the character to find
        caller: Optional caller to send error messages to
        
    Returns:
        tuple: (org, char) where either may be None if not found
    """
    org = get_org(org_name, caller)
    if not org:
        return None, None
        
    char = get_char(char_name, caller)
    if not char:
        return org, None
        
    return org, char


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


def get_unique_resource_name(name, existing_resources, caller=None):
    """Get a unique name for a resource, appending a number if needed.
    
    Args:
        name (str): Base name for the resource
        existing_resources (dict or TraitHandler): Existing resources to check against
        caller (optional): Caller to notify about name changes
        
    Returns:
        str: A unique name for the resource
    """
    if hasattr(existing_resources, 'traits'):
        # If it's a TraitHandler, get the traits dict
        existing_resources = existing_resources.traits
        
    # First try to strip any existing number suffix
    import re
    base_name = re.sub(r'\s+\d+$', '', name)
    
    # If the base name is available, use it
    if base_name not in existing_resources:
        if base_name != name and caller:
            caller.msg(f"Simplified resource name from '{name}' to '{base_name}'.")
        return base_name
        
    # Otherwise, find the next available number
    counter = 1
    while f"{base_name} {counter}" in existing_resources:
        counter += 1
        
    new_name = f"{base_name} {counter}"
    if new_name != name and caller:
        caller.msg(f"Resource name '{base_name}' already exists, using '{new_name}' instead.")
        
    return new_name 