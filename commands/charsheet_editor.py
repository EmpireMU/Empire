"""
Staff commands for editing character sheets.
"""
from evennia import Command
from evennia import CmdSet

UNDELETABLE_TRAITS = ["attributes", "skills"]

class CmdSetTrait(Command):
    """
    Set a trait on a character's sheet.
    
    Usage:
        settrait <character> = <trait> <value>
        
    Examples:
        settrait Bob = Attributes Cunning d8
        settrait Jane = Distinctions "Too Clever" d8
    
    This command allows staff to add or modify character traits.
    """
    
    key = "settrait"
    locks = "cmd:perm(Builder)"  # Builders and above can use this
    help_category = "Building"
    
    def func(self):
        """Handle the trait setting."""
        if not self.args or not self.rhs:
            self.caller.msg("Usage: settrait <character> = <trait> <value>")
            return
            
        char = self.caller.search(self.lhs)
        if not char:
            return
            
        # Parse the trait and value
        try:
            trait_name, value = self.rhs.split(" ", 1)
        except ValueError:
            self.caller.msg("You must specify both a trait name and value.")
            return
            
        # Update or create the trait
        if hasattr(char, 'traits'):
            try:
                char.traits.add(trait_name, value)
                self.caller.msg(f"Updated {char.name}'s {trait_name} to {value}.")
            except Exception as e:
                self.caller.msg(f"Error setting trait: {e}")
        else:
            self.caller.msg(f"{char.name} does not have trait support.")

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