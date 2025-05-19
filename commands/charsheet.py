"""
Commands for viewing character sheets.
"""
from evennia import Command
from evennia import CmdSet
from evennia.utils import evtable
from evennia.utils.ansi import ANSIString
from evennia.utils.search import search_object

def get_trait_display(trait):
    """
    Convert a trait object into display strings.
    
    Args:
        trait: A trait object with key, base, and optional desc attributes
        
    Returns:
        tuple: (display_name, die_size, description)
    """
    # Use trait.name if available, otherwise fall back to key
    display_name = trait.name if hasattr(trait, 'name') else str(trait.key).title()
    die_size = f"d{trait.base}"  # Format die size as d8, d10, etc.
    description = trait.desc if hasattr(trait, 'desc') else ""
    return display_name, die_size, description

def format_trait_section(title, traits, show_desc=False):
    """
    Format a section of traits with a title and optional descriptions.
    
    Args:
        title: Section title (e.g., "Attributes", "Skills")
        traits: List of trait objects
        show_desc: Whether to show descriptions (only used for Resources and Assets)
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
    
    The sheet displays:
    - Plot Points
    - Distinctions (short form)
    - Prime Sets (Attributes, Skills)
    - Additional Sets (Resources, Signature Assets)
    - Distinction Details (full descriptions)
    """
    
    key = "sheet"
    locks = "cmd:all()"  # Everyone can use this command
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
            # If caller is a DefaultObject, try to get the character
            elif hasattr(self.caller, 'get_display_desc'):
                char = self.caller
            else:
                self.caller.msg("You must be a character to view a character sheet.")
                return
        else:
            # Staff checking other character
            if not self.caller.check_permstring("Builder"):
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
        
        if assets:
            sheet.append(format_trait_section("Signature Assets", assets, show_desc=True))
        
        # Distinction Details
        if distinctions:
            sheet.append("\n" + format_distinctions_full(distinctions))
            
        # Organizations
        if hasattr(char, 'db') and char.db.organisations:
            sheet.append("\n|yOrganisations|n")
            sheet.append("-" * 78 + "\n")
            
            table = evtable.EvTable(
                "|wOrganisation|n",
                "|wRank|n",
                border="table",
                width=78
            )
            
            for org_id, rank in char.db.organisations.items():
                orgs = search_object(f"#{org_id}")
                if orgs:
                    org = orgs[0]
                    # Show if not secret, or if viewer is staff, or if viewer is the character
                    if (not org.is_secret or 
                        self.caller.check_permstring("Builder") or 
                        self.caller == char):
                        table.add_row(org.name, rank or "Member")
            
            if table.nrows > 0:
                sheet.append(str(table))
        
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