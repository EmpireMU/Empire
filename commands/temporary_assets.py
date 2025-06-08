"""
Commands for managing temporary assets.
"""

from evennia.commands.default.muxcommand import MuxCommand
from evennia import CmdSet
from utils.command_mixins import CharacterLookupMixin

class CmdTemporaryAsset(CharacterLookupMixin, MuxCommand):
    """
    Add, remove, or list temporary assets.
    
    Usage:
        asset/add <name>=<die size>     - Add a temporary asset
        asset/remove <name>             - Remove a temporary asset
        asset                           - List your temporary assets
        
    Examples:
        asset/add High Ground=8         - Add "High Ground" as a d8 asset
        asset/remove High Ground        - Remove the "High Ground" asset
        asset                           - List all your temporary assets
        
    Temporary assets are short-term advantages that can be used in rolls.
    They are marked with (T) in roll outputs to distinguish them from
    permanent assets.
    """
    
    key = "asset"
    aliases = ["assets"]
    locks = "cmd:all()"
    help_category = "Game"
    switch_options = ("add", "remove")
    
    def func(self):
        """Handle all temporary asset functionality based on switches."""
        char = self.caller
        if not hasattr(char, 'temporary_assets'):
            char = char.char
            
        if not hasattr(char, 'temporary_assets'):
            self.caller.msg("You cannot use temporary assets.")
            return
            
        if not self.switches:  # No switch - list assets
            assets = char.temporary_assets.all()
            if not assets:
                self.caller.msg("You have no temporary assets.")
                return
                
            self.caller.msg("|wTemporary Assets:|n")
            for key in assets:
                asset = char.temporary_assets.get(key)
                self.caller.msg(f"  {asset.name}: d{int(asset.value)}")
                
        elif "add" in self.switches:
            if not self.args or "=" not in self.args:
                self.caller.msg("Usage: asset/add <name>=<die size>")
                return
                
            name, die_size = self.args.split("=", 1)
            name = name.strip()
            try:
                die_size = int(die_size.strip())
                if die_size not in [4, 6, 8, 10, 12]:
                    self.caller.msg("Die size must be 4, 6, 8, 10, or 12.")
                    return
            except ValueError:
                self.caller.msg("Die size must be a number (4, 6, 8, 10, or 12).")
                return
                
            # Add the asset with both value and base set
            char.temporary_assets.add(
                name.lower().replace(" ", "_"),
                value=die_size,
                base=die_size,  # Add base value
                name=name
            )
            
            self.caller.msg(f"Added temporary asset '{name}' (d{die_size}).")
            self.caller.location.msg_contents(
                f"{char.name} creates a temporary asset: {name} (d{die_size}).",
                exclude=[self.caller]
            )
            
        elif "remove" in self.switches:
            if not self.args:
                self.caller.msg("Usage: asset/remove <name>")
                return
                
            name = self.args.strip()
            key = name.lower().replace(" ", "_")
            
            # Check if asset exists
            asset = char.temporary_assets.get(key)
            if not asset:
                self.caller.msg(f"You don't have a temporary asset named '{name}'.")
                return
                
            # Remove the asset
            char.temporary_assets.remove(key)
            
            self.caller.msg(f"Removed temporary asset '{name}'.")
            self.caller.location.msg_contents(
                f"{char.name} removes their temporary asset: {name}.",
                exclude=[self.caller]
            )

class TemporaryAssetCmdSet(CmdSet):
    """Command set for temporary asset management."""
    
    def at_cmdset_creation(self):
        """Add commands to the command set."""
        self.add(CmdTemporaryAsset()) 