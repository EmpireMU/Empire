"""
Utility functions for character setup and initialization.
"""
from typing import List, Tuple, Optional, Any
from .trait_definitions import TraitDefinition, ATTRIBUTES, SKILLS, DISTINCTIONS

def initialize_plot_points(character: Any, force: bool) -> Optional[str]:
    """Initialize plot points for a character."""
    if force or not character.traits.get("plot_points"):
        character.traits.add("plot_points", 1, min=0)
        return "Added plot points"
    return None

def initialize_trait_group(
    character: Any,
    trait_definitions: List[TraitDefinition],
    handler_name: str,
    force: bool
) -> List[str]:
    """Initialize a group of traits (attributes, skills, or distinctions)."""
    changes = []
    handler = getattr(character, handler_name)
    
    for trait in trait_definitions:
        if force or not handler.get(trait.key):
            handler.add(
                trait.key,
                trait.default_value,
                desc=trait.description,
                name=trait.name
            )
            changes.append(f"Added {handler_name[:-1]}: {trait.name}")
            
    return changes

def initialize_traits(character: Any, force: bool = False) -> Tuple[bool, str]:
    """
    Initialize or reinitialize all traits on a character.
    
    Args:
        character: The character object to initialize traits for
        force: If True, will reinitialize all traits even if they exist
    
    Returns:
        tuple: (success, message) where success is a boolean and message describes what was done
    """
    if not hasattr(character, 'traits'):
        return False, f"{character.name} does not support traits (wrong typeclass?)"
        
    changes = []
    
    # Initialize plot points
    plot_point_change = initialize_plot_points(character, force)
    if plot_point_change:
        changes.append(plot_point_change)
    
    # Initialize attributes
    changes.extend(initialize_trait_group(character, ATTRIBUTES, "character_attributes", force))
    
    # Initialize skills
    changes.extend(initialize_trait_group(character, SKILLS, "skills", force))
    
    # Initialize distinctions
    changes.extend(initialize_trait_group(character, DISTINCTIONS, "distinctions", force))
            
    if not changes:
        return True, "Character traits were already fully initialized"
    else:
        return True, "Initialized missing traits: " + ", ".join(changes) 