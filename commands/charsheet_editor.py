"""
Staff commands for editing character sheets.
"""
from evennia.commands.command import Command
from evennia.commands.default.muxcommand import MuxCommand
from evennia import CmdSet, create_object
from utils.character_setup import initialize_traits

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
            self.msg("Usage: @trait <character> = <category> <trait_key> <die_size>")
            return
            
        # Get character
        char = self.caller.search(self.lhs)
        if not char:
            return
            
        # Check if character supports traits
        if not hasattr(char, 'traits'):
            self.caller.msg(f"{char.name} does not support traits (wrong typeclass?).")
            return
            
        # Parse trait information
        try:
            category, trait_key, die_value = self.rhs.split(" ", 2)
            category = category.lower()
            trait_key = trait_key.strip('"').strip()
            die_size = int(die_value[1:])  # Remove 'd' prefix
        except ValueError:
            self.msg("Usage: @trait <character> = <category> <trait_key> <die_size>")
            return
            
        # Validate category
        if category not in ('attributes', 'skills', 'distinctions', 'resources', 'signature_assets'):
            self.msg("Category must be one of: attributes, skills, distinctions, resources, signature_assets")
            return
            
        # Get appropriate trait handler
        handler = getattr(char, category)
        
        # Add or update trait
        try:
            handler.add(key=trait_key, value=die_size)
            self.caller.msg(f"Set {char.name}'s {category} trait '{trait_key}' to d{die_size}.")
            char.msg(f"{self.caller.name} sets your {category} trait '{trait_key}' to d{die_size}.")
        except Exception as e:
            self.msg(f"Error setting trait: {e}")

class CmdDeleteTrait(MuxCommand):
    """
    Delete a trait from a character's sheet.
    
    Usage:
        @deltrait <character> = <trait_key>
    """
    
    key = "@deltrait"
    locks = "cmd:all()"
    help_category = "Character"
    
    def func(self):
        """Execute the command."""
        if not self.args:
            self.msg("Usage: @deltrait <character> = <trait_key>")
            return
            
        # Get character
        char = self.caller.search(self.lhs)
        if not char:
            return
            
        # Get trait key
        trait_key = self.rhs.strip()
        
        # Try to remove from each category
        for category in ('attributes', 'skills', 'distinctions', 'resources', 'signature_assets'):
            handler = getattr(char, category, None)
            if handler and handler.get(trait_key):
                if handler.remove(trait_key):
                    self.caller.msg(f"Deleted {trait_key} from {char.name}'s character sheet.")
                    return
                    
        self.caller.msg(f"{char.name} doesn't have a trait called '{trait_key}'.")

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
            char.distinctions.add(key=slot, value=8, desc=desc)
            
            # Notify relevant parties
            self.caller.msg(f"Set {char.name}'s {slot} distinction to '{name}'.")
            if char != self.caller:
                char.msg(f"{self.caller.name} sets your {slot} distinction to '{name}'.")
            
        except Exception as e:
            self.caller.msg(f"Error setting distinction: {e}")

class CmdInitTraits(MuxCommand):
    """
    Initialize or reinitialize a character's traits.
    
    Usage:
        inittraits <character>
        inittraits/all
        
    Examples:
        inittraits Bob     - Initialize Bob's traits
        inittraits/all     - Initialize all characters' traits
        
    This will set up default traits if they don't exist:
    - Plot Points (starts at 1)
    - Attributes (all start at d6)
    - Skills (all start at d4)
    - Distinction slots (all d8)
    
    Existing traits will not be modified.
    Only staff members can use this command.
    """
    
    key = "inittraits"
    locks = "cmd:perm(Builder)"  # Builders and above can use this
    help_category = "Building"
    switch_options = ("all",)  # Define valid switches
    
    def func(self):
        """Handle trait initialization."""
        if "all" in self.switches:
            # Initialize all characters
            from evennia.objects.models import ObjectDB
            from typeclasses.characters import Character
            chars = ObjectDB.objects.filter(db_typeclass_path__contains="characters.Character")
            count = 0
            for char in chars:
                if hasattr(char, 'traits'):  # Verify it's actually a character
                    success, msg = initialize_traits(char)
                    if success:
                        count += 1
                        self.caller.msg(f"{char.name}: {msg}")
            self.caller.msg(f"\nInitialized traits for {count} character{'s' if count != 1 else ''}.")
            return
            
        # Initialize specific character
        if not self.args:
            self.caller.msg("Usage: inittraits <character> or inittraits/all")
            return
            
        char = self.caller.search(self.args)
        if not char:
            return
            
        if not hasattr(char, 'traits'):
            self.caller.msg(f"{char.name} does not support traits (wrong typeclass?).")
            return
            
        success, msg = initialize_traits(char)
        self.caller.msg(msg)

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
        self.add(CmdInitTraits()) 