"""
Character sheet commands for viewing and editing character information.
"""

from evennia import Command, CmdSet
from evennia.utils import evtable
from evennia.utils.search import search_object

def get_trait_display(trait):
    """
    Get display information for a trait.
    
    Args:
        trait: The trait object to display
        
    Returns:
        Tuple of (display_name, die_size, description)
    """
    if not trait:
        return "", "", ""
        
    # Get the display name, falling back to key if name not set
    try:
        display_name = trait.name
    except AttributeError:
        display_name = trait.key
    
    # Get the die size from the value
    die_size = f"d{trait.value}" if hasattr(trait, 'value') else ""
    
    # Get the description, falling back to empty string if not set
    # Resources don't have descriptions, so we handle that case
    try:
        description = trait.desc
    except AttributeError:
        description = ""
    
    return display_name, die_size, description

def format_trait_section(title, traits, show_desc=False):
    """
    Format a section of traits for the character sheet.
    
    Args:
        title: The section title
        traits: List of trait objects
        show_desc: Whether to show descriptions
        
    Returns:
        Formatted string for the section
    """
    if not traits:
        return ""
        
    # Create header
    section = f"|y{title}|n\n"
    
    # Create table
    # Only show description column for Resources and Signature Assets
    show_desc = show_desc and title in ["Resources", "Signature Assets"]
    
    table = evtable.EvTable(
        "|wTrait|n",
        "|wDie|n",
        "|wDescription|n" if show_desc else None,
        border="table",
        width=78
    )
    
    # Add rows
    for trait in sorted(traits, key=lambda x: str(x.key)):
        display_name, die_size, description = get_trait_display(trait)
        if show_desc:
            table.add_row(display_name, die_size, description)
        else:
            table.add_row(display_name, die_size)
    
    return section + str(table) + "\n"

def format_distinctions_short(distinctions):
    """
    Format distinctions in a compact form for the sheet header.
    
    Args:
        distinctions: List of distinction trait objects
    """
    if not distinctions:
        return ""
    
    # Create header
    section = "|yDistinctions|n\n"
    
    # Create table
    table = evtable.EvTable(border="table", width=78)
    
    # Convert trait objects to display strings
    dist_displays = [f"{get_trait_display(d)[0]} (d8)" for d in sorted(distinctions, key=lambda x: x.key)]
    table.add_row(*dist_displays)
    
    return section + str(table) + "\n"

def format_distinctions_full(distinctions):
    """
    Format distinctions with full descriptions for the sheet footer.
    
    Args:
        distinctions: List of distinction trait objects
    """
    if not distinctions:
        return ""
    
    # Create header
    section = "|yDistinction Details|n\n"
    
    # Create table
    table = evtable.EvTable(
        "|wDistinction|n",
        "|wDescription|n",
        border="table",
        width=78
    )
    
    # Add rows
    for dist in sorted(distinctions, key=lambda x: x.key):
        display_name, _, description = get_trait_display(dist)
        table.add_row(display_name, description)
    
    return section + str(table) + "\n"

class CmdSheet(Command):
    """
    View a character sheet.
    
    Usage:
        sheet [character]
        
    Without arguments, shows your own character sheet.
    Staff members can view other characters' sheets by specifying their name.
    
    Sheet Sections:
    1. Basic Information
       - Character name
       - Plot Points (used for special actions)
    
    2. Distinctions (d8 or d4)
       - Character Concept: Core identity
       - Cultural Background: Heritage and upbringing
       - Reputation: How others see you
       Note: Using d4 instead of d8 earns a Plot Point
    
    3. Prime Sets (Core dice pools)
       - Attributes (d4-d12): Natural capabilities
         * Physical (Strength, Agility, etc.)
         * Mental (Intelligence, Willpower, etc.)
         * Social (Presence, Manipulation, etc.)
       - Skills (d4-d12): Trained abilities
         * Combat (Fighting, Shooting, etc.)
         * Physical (Athletics, Stealth, etc.)
         * Mental (Medicine, Science, etc.)
         * Social (Persuasion, Deception, etc.)
    
    4. Additional Sets
       - Resources: Organization-provided dice pools
       - Signature Assets: Personal items/companions
    
    Die Size Guide:
       d4: Untrained/Weak
       d6: Average/Basic Training
       d8: Professional/Well Trained
       d10: Expert/Exceptional
       d12: Master/Peak Human
    """
    
    key = "sheet"
    # Allow viewing own sheet always, require Builder permission to view others
    locks = "cmd:all();view_other:perm(Builder)"
    help_category = "Character"
    switch_options = ()  # No switches for this command
    
    def func(self):
        """Display the character sheet."""
        if not self.args:
            # View own sheet
            char = self.caller
            # If caller is an account, get their character
            if hasattr(self.caller, 'char'):
                char = self.caller.char
        else:
            # Staff checking other character
            if not self.access(self.caller, "view_other"):
                self.caller.msg("You can only view your own character sheet.")
                return
            char = self.caller.search(self.args)
            if not char:
                return
                
        # Get all traits
        if not hasattr(char, 'traits'):
            self.caller.msg(f"{char.name} has no character sheet.")
            return
            
        # Build the character sheet
        sheet = [f"|c{char.name}'s Character Sheet|n\n"]
        
        # Plot Points
        pp = char.traits.get("plot_points")
        if pp:
            sheet.append(f"|wPlot Points:|n {pp.base}\n")
        
        # Get trait objects for each category
        # We need the full trait objects to access their properties
        distinctions = [char.distinctions.get(key) for key in char.distinctions.all()]
        attributes = [char.character_attributes.get(key) for key in char.character_attributes.all()]
        skills = [char.skills.get(key) for key in char.skills.all()]
        assets = [char.signature_assets.get(key) for key in char.signature_assets.all()]
        resources = [char.char_resources.get(key) for key in char.char_resources.all()]
        
        # Format each section
        if distinctions:
            sheet.append(format_distinctions_short(distinctions))
        
        # Prime Sets
        sheet.append("\n|rPrime Sets|n")
        sheet.append("-" * 78 + "\n")
        
        if attributes:
            sheet.append(format_trait_section("Attributes", attributes))
            
        if skills:
            sheet.append(format_trait_section("Skills", skills))
        
        # Additional Sets
        sheet.append("\n|gAdditional Sets|n")
        sheet.append("-" * 78 + "\n")
        
        if resources:
            sheet.append(format_trait_section("Resources", resources, show_desc=True))
            
        if assets:
            sheet.append(format_trait_section("Signature Assets", assets, show_desc=True))
        
        # Distinction Details
        if distinctions:
            sheet.append("\n" + format_distinctions_full(distinctions))
        
        # Send the sheet
        self.caller.msg("\n".join(sheet))


class CharSheetCmdSet(CmdSet):
    """
    Command set for viewing character sheets.
    """
    
    def at_cmdset_creation(self):
        """
        Add commands to the command set
        """
        self.add(CmdSheet()) 