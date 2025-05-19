"""
Staff commands for editing character sheets.
"""
from evennia.commands.command import Command
from evennia.commands.default.muxcommand import MuxCommand
from evennia import CmdSet, create_object
from evennia.utils import dbserialize

UNDELETABLE_TRAITS = ["attributes", "skills"]

class CmdSetTrait(MuxCommand):
    """
    Set a trait on a character's sheet.
    
    Usage:
        settrait <character> = <category> <trait> <die>
        
    Examples:
        settrait Bob = attributes prowess d8
        settrait Jane = skills fighting d10
        settrait Tom = resources wealth d6
        settrait Alice = signature_assets "Magic Sword" d8
        
    Categories:
        attributes       - Core attributes (d4-d12)
        skills          - Learned abilities (d4-d12)
        resources       - Organizational resources (d4-d12)
        signature_assets - Notable items/allies (d4-d12)
        
    This command allows staff to add or modify character traits.
    Note: For distinctions, use the 'setdist' command instead.
    """
    
    key = "settrait"
    locks = "cmd:perm(Builder)"  # Builders and above can use this
    help_category = "Building"
    
    def func(self):
        """Execute the command."""
        if not self.args:
            self.msg("Usage: settrait <character> = <category> <trait_key> <die_size>")
            return
            
        # Get character
        char = self.caller.search(self.lhs)
        if not char:
            return
            
        # Parse trait information
        try:
            category, trait_key, die_value = self.rhs.split(" ", 2)
            category = category.lower()
            trait_key = str(trait_key.strip('"').strip())  # Ensure trait key is a string
            die_size = int(die_value[1:])  # Remove 'd' prefix
        except ValueError:
            self.msg("Usage: settrait <character> = <category> <trait_key> <die_size>")
            return
            
        # Validate category
        valid_categories = ['attributes', 'skills', 'resources', 'signature_assets']
        if category not in valid_categories:
            self.msg(f"Category must be one of: {', '.join(valid_categories)}")
            return
            
        # Get appropriate trait handler
        handler_name = {
            'attributes': 'character_attributes',
            'skills': 'skills',
            'resources': 'resources',
            'signature_assets': 'signature_assets'
        }[category]
        
        handler = getattr(char, handler_name)
        if not handler:
            self.msg(f"Could not get {category} trait handler for {char.name}")
            return
            
        # Add or update trait
        try:
            trait = handler.get(trait_key)
            if trait:
                trait.base = die_size
            else:
                handler.add(trait_key, value=die_size)
            self.caller.msg(f"Set {char.name}'s {category} trait '{trait_key}' to d{die_size}.")
            char.msg(f"{self.caller.name} sets your {category} trait '{trait_key}' to d{die_size}.")
        except Exception as e:
            self.msg(f"Error setting trait: {e}")

class CmdDeleteTrait(MuxCommand):
    """
    Delete a trait from a character's sheet.
    
    Usage:
        deltrait <character> = <category> <trait>
        
    Examples:
        deltrait Bob = resources wealth
        deltrait Jane = signature_assets "Magic Sword"
        
    Categories:
        attributes       - Core attributes (d4-d12)
        skills          - Learned abilities (d4-d12)
        resources       - Organizational resources (d4-d12)
        signature_assets - Notable items/allies (d4-d12)
        
    Warning: Deleting traits from Prime Sets (attributes, skills, distinctions)
    may affect character balance. Use with caution.
    """
    
    key = "deltrait"
    locks = "cmd:perm(Admin)"  # Admin and above can use this
    help_category = "Building"
    
    def func(self):
        """Execute the command."""
        if not self.args:
            self.msg("Usage: deltrait <character> = <category> <trait_key>")
            return
            
        # Get character
        char = self.caller.search(self.lhs)
        if not char:
            return
            
        # Parse trait information
        try:
            category, trait_key = self.rhs.split(" ", 1)
            category = category.lower()
            trait_key = str(trait_key.strip('"').strip())  # Ensure trait key is a string
        except ValueError:
            self.msg("Usage: deltrait <character> = <category> <trait_key>")
            return
            
        # Validate category
        valid_categories = ['attributes', 'skills', 'resources', 'signature_assets']
        if category not in valid_categories:
            self.msg(f"Category must be one of: {', '.join(valid_categories)}")
            return
            
        # Get appropriate trait handler
        handler_name = 'character_attributes' if category == 'attributes' else category
        handler = getattr(char, handler_name)
        if not handler:
            self.msg(f"Could not get {category} trait handler for {char.name}")
            return
            
        # Check if trait exists
        trait = handler.get(trait_key)
        if not trait:
            self.msg(f"{char.name} doesn't have a {category} trait called '{trait_key}'.")
            return
            
        # Warn about Prime Set traits
        if category in ['attributes', 'skills']:
            self.msg(f"|rWARNING: You are about to delete a Prime Set trait ({category}). This may affect character balance.|n")
            self.msg("Type 'deltrait' again to confirm.")
            return
            
        # Delete the trait
        try:
            handler.remove(trait_key)
            self.caller.msg(f"Deleted {char.name}'s {category} trait '{trait_key}'.")
            char.msg(f"{self.caller.name} deleted your {category} trait '{trait_key}'.")
        except Exception as e:
            self.msg(f"Error deleting trait: {e}")

class CmdSetDistinction(MuxCommand):
    """
    Set a character's distinction name and description.
    
    Usage:
        setdist <character> = <slot> : <name> : <description>
        
    Examples:
        setdist Bob = concept : Bold Explorer : Always seeking the next horizon
        setdist Jane = culture : Islander : Born and raised on the Storm Isles
        setdist Tom = reputation : Mysterious : No one knows their true motives
        
    The three distinction slots are:
    - concept (character concept)
    - culture (cultural background)
    - reputation (how others see them)
    
    Each distinction is always d8 (or d4 for a plot point).
    Only staff members can use this command.
    """
    
    key = "setdist"
    locks = "cmd:perm(Builder)"  # Builders and above can use this
    help_category = "Building"
    
    def func(self):
        """Handle setting the distinction."""
        if not self.args or ":" not in self.args or "=" not in self.args:
            self.caller.msg("Usage: setdist <character> = <slot> : <name> : <description>")
            return
            
        char_name, rest = self.args.split("=", 1)
        char_name = char_name.strip()
        
        try:
            slot, name, desc = [part.strip() for part in rest.split(":")]
        except ValueError:
            self.caller.msg("You must provide a slot, name, and description separated by colons (:)")
            return
            
        # Find the character
        char = self.caller.search(char_name)
        if not char:
            return
            
        # Validate slot
        valid_slots = {'concept', 'culture', 'reputation'}
        if slot.lower() not in valid_slots:
            self.caller.msg(f"Invalid distinction slot. Must be one of: {', '.join(valid_slots)}")
            return
            
        # Set the distinction
        if not hasattr(char, 'distinctions'):
            self.caller.msg(f"{char.name} does not have distinction support.")
            return
            
        try:
            # All distinctions are d8
            char.distinctions.add(slot, value=8, desc=desc, name=name)
            
            # Notify relevant parties
            self.caller.msg(f"Set {char.name}'s {slot} distinction to '{name}'.")
            if char != self.caller:
                char.msg(f"{self.caller.name} sets your {slot} distinction to '{name}'.")
            
        except Exception as e:
            self.caller.msg(f"Error setting distinction: {e}")

class CharSheetEditorCmdSet(CmdSet):
    """
    Command set for editing character sheets.
    """
    
    def at_cmdset_creation(self):
        """
        Add commands to the command set
        """
        self.add(CmdSetTrait())
        self.add(CmdDeleteTrait())
        self.add(CmdSetDistinction()) 