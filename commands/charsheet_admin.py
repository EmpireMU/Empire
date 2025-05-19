"""
Administrative commands for managing character sheets.
These commands are for staff use only and should not be used in normal gameplay.
"""
from evennia.commands.default.muxcommand import MuxCommand
from evennia import CmdSet
from utils.character_setup import initialize_traits

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
    Only administrators can use this command.
    """
    
    key = "inittraits"
    locks = "cmd:perm(Admin)"  # Admin and above can use this
    help_category = "Building"
    switch_options = ("all",)
    
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
            
        # Check if this is a confirmation
        if self.caller.attributes.has('init_traits_confirming'):
            success, msg = initialize_traits(char)
            self.caller.msg(msg)
            self.caller.attributes.remove('init_traits_confirming')
            return
            
        # First time through - ask for confirmation
        self.caller.msg(f"|yWARNING: This will initialize traits for {char.name}.|n")
        self.caller.msg("|yThis may affect existing traits. Type 'inittraits' again to confirm.|n")
        self.caller.attributes.add('init_traits_confirming', True, category='temp')
        return  # Add this to prevent the command from continuing

class CmdWipeTraits(MuxCommand):
    """
    Wipe and reinitialize a character's traits.
    
    Usage:
        wipetraits <character>
        wipetraits/all
        
    Examples:
        wipetraits Bob     - Wipe and reinitialize Bob's traits
        wipetraits/all     - Wipe and reinitialize all characters' traits
        
    This will:
    1. Remove all existing traits
    2. Reinitialize with default traits:
       - Plot Points (starts at 1)
       - Attributes (all start at d6)
       - Skills (all start at d4)
       - Distinction slots (all d8)
    
    Only administrators can use this command.
    """
    
    key = "wipetraits"
    locks = "cmd:perm(Admin)"  # Admin and above can use this
    help_category = "Building"
    switch_options = ("all",)  # Define valid switches
    
    def func(self):
        """Handle trait wiping and reinitialization."""
        if "all" in self.switches:
            # Wipe all characters
            from evennia.objects.models import ObjectDB
            from typeclasses.characters import Character
            chars = ObjectDB.objects.filter(db_typeclass_path__contains="characters.Character")
            count = 0
            for char in chars:
                if hasattr(char, 'traits'):  # Verify it's actually a character
                    success, msg = self._wipe_and_init(char)
                    if success:
                        count += 1
                        self.caller.msg(f"{char.name}: {msg}")
            self.caller.msg(f"\nWiped and reinitialized traits for {count} character{'s' if count != 1 else ''}.")
            return
            
        # Wipe specific character
        if not self.args:
            self.caller.msg("Usage: wipetraits <character> or wipetraits/all")
            return
            
        char = self.caller.search(self.args)
        if not char:
            return
            
        if not hasattr(char, 'traits'):
            self.caller.msg(f"{char.name} does not support traits (wrong typeclass?).")
            return
            
        success, msg = self._wipe_and_init(char)
        self.caller.msg(msg)
        
    def _wipe_and_init(self, char):
        """Helper method to wipe and reinitialize traits for a character."""
        try:
            # Ensure trait handlers are initialized
            _ = char.traits
            _ = char.distinctions
            _ = char.character_attributes
            _ = char.skills
            _ = char.resources
            _ = char.signature_assets
            
            # Wipe all traits
            for handler_name in ['traits', 'distinctions', 'character_attributes', 'skills', 'resources', 'signature_assets']:
                handler = getattr(char, handler_name, None)
                if handler:
                    # Get all trait keys and remove them
                    for key in handler.all():
                        handler.remove(key)
            
            # Force reinitialize traits
            success, msg = initialize_traits(char, force=True)
            if success:
                return True, "Traits wiped and reinitialized"
            return False, msg
            
        except Exception as e:
            return False, f"Error: {e}"

class CharSheetAdminCmdSet(CmdSet):
    """
    Command set for administrative character sheet management.
    """
    
    def at_cmdset_creation(self):
        """
        Add commands to the command set
        """
        self.add(CmdInitTraits())
        self.add(CmdWipeTraits()) 