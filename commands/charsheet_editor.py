"""
Staff commands for editing character sheets.
"""
from evennia import Command
from evennia import CmdSet
from utils.character_setup import initialize_traits

UNDELETABLE_TRAITS = ["attributes", "skills"]

class CmdSetTrait(Command):
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
    switch_options = ()  # No switches for this command
    
    def func(self):
        """Handle the trait setting."""
        if not self.args or not self.rhs:
            self.caller.msg(self.__doc__.strip())
            return
            
        char = self.caller.search(self.lhs)
        if not char:
            return
            
        # Parse the trait info
        try:
            category, trait_name, die_value = self.rhs.split(" ", 2)
            category = category.lower()
            trait_name = trait_name.strip('"').strip()
            
            # Parse die value (should be in format 'd6', 'd8', etc.)
            if die_value.startswith('d'):
                die_size = int(die_value[1:])
            else:
                die_size = int(die_value)
                
            if die_size not in [4, 6, 8, 10, 12]:
                self.caller.msg("Die size must be d4, d6, d8, d10, or d12.")
                return
                
        except ValueError:
            self.caller.msg("Usage: settrait <character> = <category> <trait> <die>")
            return
            
        # Validate category
        valid_categories = {
            'attributes': char.character_attributes,
            'skills': char.skills,
            'resources': char.resources,
            'signature_assets': char.signature_assets
        }
        
        if category not in valid_categories:
            self.caller.msg(f"Invalid category. Must be one of: {', '.join(valid_categories.keys())}")
            return
            
        # Get the trait handler for this category
        handler = valid_categories[category]
        
        try:
            # Add/update the trait
            handler.add(trait_name, trait_name.title(), trait_type="static", base=die_size)
            
            # Notify relevant parties
            self.caller.msg(f"Set {char.name}'s {category} trait '{trait_name}' to d{die_size}.")
            if char != self.caller:
                char.msg(f"{self.caller.name} sets your {category} trait '{trait_name}' to d{die_size}.")
        except Exception as e:
            self.caller.msg(f"Error setting trait: {e}")

class CmdDeleteTrait(Command):
    """
    Delete a trait from a character's sheet.
    
    Usage:
        deletetrait <character> = <trait>
        
    Example:
        deletetrait Bob = "Old Wound"
        
    Note: Attributes and Skills cannot be deleted.
    Only staff members with Builder permissions or higher can use this command.
    """
    
    key = "deletetrait"
    locks = "cmd:perm(Builder)"
    help_category = "Building"
    switch_options = ()  # No switches for this command
    
    def func(self):
        """Handle the trait deletion."""
        if not self.args or not self.rhs:
            self.caller.msg("Usage: deletetrait <character> = <trait>")
            return
            
        char = self.caller.search(self.lhs)
        if not char:
            return
            
        trait_name = self.rhs.strip()
        
        # Check if this is a protected trait type
        trait_type = trait_name.lower().split()[0]
        if trait_type in UNDELETABLE_TRAITS:
            self.caller.msg(f"You cannot delete {trait_type}. These are fundamental character traits.")
            return
            
        # Try to delete the trait
        if hasattr(char, 'traits'):
            try:
                if char.traits.remove(trait_name):
                    self.caller.msg(f"Deleted {trait_name} from {char.name}'s character sheet.")
                else:
                    self.caller.msg(f"{char.name} doesn't have a trait called '{trait_name}'.")
            except Exception as e:
                self.caller.msg(f"Error deleting trait: {e}")
        else:
            self.caller.msg(f"{char.name} does not have trait support.")

class CmdSetDistinction(Command):
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
    switch_options = ()  # No switches for this command
    
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
            char.distinctions.add(slot, name, trait_type="static", base=8, desc=desc)
            
            # Notify relevant parties
            self.caller.msg(f"Set {char.name}'s {slot} distinction to: {name} - {desc}")
            if char != self.caller:
                char.msg(f"{self.caller.name} sets your {slot} distinction to: {name} - {desc}")
            
        except Exception as e:
            self.caller.msg(f"Error setting distinction: {e}")

class CmdInitTraits(Command):
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
        else:
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
            self.caller.msg(f"{char.name}: {msg}")

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