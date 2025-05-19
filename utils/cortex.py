"""
Cortex Prime game system utilities.
"""

from typing import List, Tuple, Optional, Dict, NamedTuple
from collections import defaultdict
from random import randint

# Define difficulty ratings as constants
DIFFICULTIES = {
    "very easy": 3,
    "easy": 7,
    "challenging": 11,
    "hard": 15,
    "very hard": 19
}

# Define die size progression
DIE_SIZES = ['4', '6', '8', '10', '12']

def step_die(die_size: str, steps: int) -> str:
    """
    Step a die up or down by the specified number of steps.
    
    Args:
        die_size: The current die size (e.g., "8" for d8)
        steps: Number of steps (positive for up, negative for down)
        
    Returns:
        New die size after stepping
    """
    try:
        current_index = DIE_SIZES.index(die_size)
        new_index = max(0, min(len(DIE_SIZES) - 1, current_index + steps))
        return DIE_SIZES[new_index]
    except ValueError:
        return die_size  # Return original if invalid

class TraitDie(NamedTuple):
    """Represents a die in the pool with its trait information."""
    size: str  # The die size (e.g., "8" for d8)
    category: Optional[str]  # The trait category (e.g., "attributes")
    name: Optional[str]  # The trait name (e.g., "prowess")
    step_mod: Optional[str]  # Step modifier (U for up, D for down, None for no mod)

def get_trait_die(character, trait_spec: str) -> Optional[Tuple[str, str, str, bool]]:
    """
    Get the die size and category for a trait specification.
    Handles step up/down modifiers in the form trait_name(U) or trait_name(D),
    and doubling in the form trait_name(double).
    
    Args:
        character: The character object to check traits on
        trait_spec: The trait specification (e.g., "prowess" or "prowess(U)" or "prowess(double)")
        
    Returns:
        Tuple of (die_size, category_name, step_mod, doubled) or None if not found
        doubled indicates if an extra die of the same size should be added
    """
    if not hasattr(character, 'character_attributes'):
        return None
        
    # Parse trait specification for modifiers
    trait_name = trait_spec
    step_mod = None
    doubled = False
    if '(' in trait_spec and ')' in trait_spec:
        trait_name, mod = trait_spec.split('(', 1)
        mod = mod.rstrip(')')
        if mod in ('U', 'D'):
            step_mod = mod
        elif mod.lower() == 'double':
            doubled = True
        trait_name = trait_name.strip()
        
    # Try each trait category in order
    categories = [
        ('attributes', character.character_attributes),
        ('skills', character.skills),
        ('distinctions', character.distinctions),
        ('resources', character.resources),
        ('signature_assets', character.signature_assets)
    ]
    
    for category_name, handler in categories:
        trait = handler.get(trait_name)
        if trait:
            die_size = str(trait.base)
            # Apply step modification if present
            if step_mod:
                die_size = step_die(die_size, 1 if step_mod == 'U' else -1)
            return die_size, category_name, step_mod, doubled
            
    return None

def validate_dice_pool(dice: List[TraitDie]) -> Optional[str]:
    """
    Validate the dice pool according to Cortex Prime rules.
    
    Args:
        dice: List of TraitDie objects representing the dice pool
        
    Returns:
        Error message if invalid, None if valid
        
    Rules:
    - When using any traits (including Resources/Assets), all three Prime sets are required:
      * One Attribute
      * One Skill
      * One Distinction
    - Raw dice can be rolled individually
    """
    # Track which prime trait sets are used
    has_attribute = False
    has_skill = False
    has_distinction = False
    requires_prime_sets = False  # True if prime sets are required
    
    for die in dice:
        if die.category:  # It's a trait, not a raw die
            if die.category == 'attributes':
                has_attribute = True
                requires_prime_sets = True
            elif die.category == 'skills':
                has_skill = True
                requires_prime_sets = True
            elif die.category == 'distinctions':
                has_distinction = True
                requires_prime_sets = True
            elif die.category in ('signature_assets', 'resources'):
                requires_prime_sets = True  # Signature Assets and Resources require prime sets
    
    # If prime sets are required (due to any trait use), check all three are present
    if requires_prime_sets:
        missing_sets = []
        if not has_attribute:
            missing_sets.append("Attribute")
        if not has_skill:
            missing_sets.append("Skill")
        if not has_distinction:
            missing_sets.append("Distinction")
            
        if missing_sets:
            if len(missing_sets) == 1:
                return f"When using traits, you must include a {missing_sets[0]}."
            else:
                missing = ", ".join(missing_sets[:-1]) + f" and {missing_sets[-1]}"
                return f"When using traits, you must include an {missing}."
        
    return None

def roll_die(sides: int) -> int:
    """Roll a single die."""
    return randint(1, int(sides))

def process_results(rolls: List[Tuple[int, str, int]]) -> Tuple[int, str, List[str]]:
    """
    Process the dice results according to Cortex Prime rules.
    
    Args:
        rolls: List of (value, die_size, index) tuples
        
    Returns:
        Tuple of (total, effect_die, hitches) where:
        - total is the sum of the two highest non-hitch dice
        - effect_die is the next highest non-hitch die (or d4 if none)
        - hitches is a list of dice that rolled 1
    """
    # Identify hitches (1s)
    hitches = [die for value, die, _ in rolls if value == 1]
    
    # Remove hitches from consideration for total and effect
    valid_rolls = [(value, die) for value, die, _ in rolls if value > 1]
    
    # Sort valid rolls by value, highest first
    valid_rolls.sort(key=lambda x: x[0], reverse=True)
    
    if len(valid_rolls) < 2:
        return 0, "d4", hitches  # Default to d4 if not enough valid dice
        
    # Get two highest for total
    total = valid_rolls[0][0] + valid_rolls[1][0]
    
    # Get effect die (next highest after the two used for total)
    effect_die = "d4"  # Default
    if len(valid_rolls) > 2:
        effect_die = f"d{valid_rolls[2][1]}"
        
    return total, effect_die, hitches

def get_success_level(total: int, difficulty: Optional[int]) -> Tuple[bool, bool]:
    """
    Determine success and if it's heroic.
    
    Args:
        total: The total of the two highest dice
        difficulty: The target difficulty number or None
        
    Returns:
        Tuple of (success, heroic) where:
        - success is True if total >= difficulty
        - heroic is True if total >= difficulty + 5
        
    Example: Against difficulty 11
    - 10 or less = Failure
    - 11-15 = Success
    - 16+ = Heroic Success
    """
    if difficulty is None:
        return True, False
        
    success = total >= difficulty
    heroic = total >= (difficulty + 5)
    return success, heroic

def format_roll_result(value: int, die: str, trait: TraitDie) -> str:
    """
    Format a single die roll result with trait information.
    
    Args:
        value: The number rolled
        die: The die size
        trait: The TraitDie object with trait information
        
    Returns:
        Formatted string like "7(d8)" or "7(d8 Attribute: prowess)"
    """
    if trait.category:
        category_name = trait.category.title().rstrip('s')  # Remove trailing 's' and capitalize
        return f"{value}(d{die} {category_name}: {trait.name})"
    return f"{value}(d{die})" 