"""
Utility functions for character setup and initialization.
"""

def initialize_traits(character, force=False):
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
    if force or not character.traits.get("plot_points"):
        character.traits.add("plot_points", 1, min=0)
        changes.append("Added plot points")
        
    # Initialize attributes (all start at d6 - "typical person")
    ATTRIBUTES = [
        ("prowess", "Prowess", "Strength, endurance and ability to fight"),
        ("finesse", "Finesse", "Dexterity and agility"),
        ("leadership", "Leadership", "Capacity as a leader"),
        ("social", "Social", "Charisma and social navigation"),
        ("acuity", "Acuity", "Perception and information processing"),
        ("erudition", "Erudition", "Learning and recall ability")
    ]
    
    for attr_key, attr_name, attr_desc in ATTRIBUTES:
        if force or not character.character_attributes.get(attr_key):
            character.character_attributes.add(attr_key, 6, desc=attr_desc)
            changes.append(f"Added attribute: {attr_name}")
            
    # Initialize skills (start at d4 - "untrained")
    SKILLS = [
        ("administration", "Administration", "Organizing affairs of large groups"),
        ("arcana", "Arcana", "Knowledge of magic"),
        ("athletics", "Athletics", "General physical feats"),
        ("dexterity", "Dexterity", "Precision physical feats"),
        ("diplomacy", "Diplomacy", "Protocol and high politics"),
        ("direction", "Direction", "Leading in non-combat"),
        ("exploration", "Exploration", "Wilderness and ruins"),
        ("fighting", "Fighting", "Melee combat"),
        ("influence", "Influence", "Personal persuasion"),
        ("learning", "Learning", "Education and research"),
        ("making", "Making", "Crafting and building"),
        ("medicine", "Medicine", "Healing and medical knowledge"),
        ("perception", "Perception", "Awareness and searching"),
        ("performance", "Performance", "Entertainment arts"),
        ("presentation", "Presentation", "Style and bearing"),
        ("rhetoric", "Rhetoric", "Public speaking"),
        ("seafaring", "Seafaring", "Sailing and navigation"),
        ("shooting", "Shooting", "Ranged combat"),
        ("warfare", "Warfare", "Military leadership and strategy")
    ]
    
    for skill_key, skill_name, skill_desc in SKILLS:
        if force or not character.skills.get(skill_key):
            character.skills.add(skill_key, 4, desc=skill_desc)
            changes.append(f"Added skill: {skill_name}")
            
    # Initialize distinction slots (all d8)
    DISTINCTIONS = [
        ("concept", "Character Concept", "Core character concept (e.g. Bold Adventurer)"),
        ("culture", "Cultural Background", "Character's cultural origin"),
        ("reputation", "Reputation", "How others perceive the character")
    ]
    
    for dist_key, dist_name, dist_desc in DISTINCTIONS:
        if force or not character.distinctions.get(dist_key):
            character.distinctions.add(dist_key, 8, desc=dist_desc)
            changes.append(f"Added distinction slot: {dist_name}")
            
    if not changes:
        return True, "Character traits were already fully initialized"
    else:
        return True, "Initialized missing traits: " + ", ".join(changes) 