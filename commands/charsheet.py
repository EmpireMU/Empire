"""
Commands for viewing character sheets.
"""
from evennia import Command
from evennia import CmdSet
from evennia.utils import evtable
from evennia.utils.ansi import ANSIString

def format_trait_section(title, traits, show_desc=False):
    """Format a section of traits with a title and optional descriptions."""
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
    for trait in sorted(traits, key=lambda x: x.name):
        if show_desc:
            table.add_row(
                trait.name.title(),
                f"d{trait.base}",
                trait.desc if hasattr(trait, 'desc') else ""
            )
        else:
            table.add_row(
                trait.name.title(),
                f"d{trait.base}"
            )
    
    return section + str(table) + "\n"

def format_distinctions_short(distinctions):
    """Format distinctions in a compact form for the sheet header."""
    if not distinctions:
        return ""
    
    # Create header
    section = "|yDistinctions|n\n"
    
    # Create table
    table = evtable.EvTable(border="table", width=78)
    
    # Add all distinctions in one row
    dist_list = [f"{d.name.title()} (d8)" for d in sorted(distinctions, key=lambda x: x.name)]
    table.add_row(*dist_list)
    
    return section + str(table) + "\n"

def format_distinctions_full(distinctions):
    """Format distinctions with full descriptions for the sheet footer."""
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
    for dist in sorted(distinctions, key=lambda x: x.name):
        table.add_row(
            dist.name.title(),
            dist.desc if hasattr(dist, 'desc') else ""
        )
    
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
            if not hasattr(self.caller, 'traits'):
                char = self.caller.char
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
        
        # Distinctions (short form)
        distinctions = list(char.distinctions.all())
        if distinctions:
            sheet.append(format_distinctions_short(distinctions))
        
        # Prime Sets
        sheet.append("\n|rPrime Sets|n")
        sheet.append("-" * 78 + "\n")
        
        # Attributes
        attributes = list(char.character_attributes.all())
        if attributes:
            sheet.append(format_trait_section("Attributes", attributes))
            
        # Skills
        skills = list(char.skills.all())
        if skills:
            sheet.append(format_trait_section("Skills", skills))
        
        # Additional Sets
        sheet.append("\n|gAdditional Sets|n")
        sheet.append("-" * 78 + "\n")
        
        # Resources
        resources = list(char.resources.all())
        if resources:
            sheet.append(format_trait_section("Resources", resources, show_desc=True))
        
        # Signature Assets
        assets = list(char.signature_assets.all())
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