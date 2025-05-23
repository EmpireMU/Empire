"""
Commands for managing Cortex Prime plot points.
"""

from evennia.commands.command import Command
from evennia.commands.default.muxcommand import MuxCommand
from evennia import CmdSet

class CmdGivePlotPoint(Command):
    """
    Award a plot point to a character.
    
    Usage:
        givepp <character>
        
    Gives one plot point to the specified character.
    Only staff members can use this command.
    """
    
    key = "givepp"
    aliases = ["awardpp"]
    locks = "cmd:perm(Builder)"  # Builders and above can use this
    help_category = "Game"
    
    def func(self):
        """Handle the plot point award."""
        if not self.args:
            self.caller.msg("Usage: givepp <character>")
            return
            
        char = self.caller.search(self.args.strip())
        if not char:
            return
            
        if not hasattr(char, 'traits'):
            self.caller.msg(f"{char.name} does not have trait support.")
            return
            
        try:
            # Get current plot points
            pp_trait = char.traits.get("plot_points")
            if not pp_trait:
                self.caller.msg(f"{char.name} does not have a plot points trait.")
                return
                
            # Add one plot point
            current = int(pp_trait.base)
            char.traits.add("plot_points", value=current + 1)
            
            # Notify relevant parties
            self.caller.msg(f"You give a plot point to {char.name}.")
            char.msg(f"{self.caller.name} gives you a plot point.")
            
        except Exception as e:
            self.caller.msg(f"Error giving plot point: {e}")

class CmdSpendPlotPoint(Command):
    """
    Spend a plot point.
    
    Usage:
        spendpp
        
    Spends one of your plot points. This is used to:
    - Step down a Distinction from d8 to d4
    - Add an extra die to your pool after seeing the initial roll
    - Create temporary assets or complications
    
    The GM will determine the mechanical effect.
    """
    
    key = "spendpp"
    locks = "cmd:all()"  # Everyone can use this command
    help_category = "Game"
    
    def func(self):
        """Handle the plot point spending."""
        char = self.caller
        if not hasattr(char, 'traits'):
            char = char.char
            
        if not hasattr(char, 'traits'):
            self.caller.msg("You don't have any plot points to spend.")
            return
            
        try:
            # Get current plot points
            pp_trait = char.traits.get("plot_points")
            if not pp_trait:
                self.caller.msg("You don't have any plot points to spend.")
                return
                
            current = int(pp_trait.base)
            if current < 1:
                self.caller.msg("You don't have any plot points to spend.")
                return
                
            # Spend one plot point
            char.traits.add("plot_points", current - 1)
            
            # Notify the player and staff
            self.caller.msg("You spend a plot point.")
            for obj in self.caller.location.contents:
                if obj.check_permstring("Builder") and obj != self.caller:
                    obj.msg(f"{char.name} spends a plot point.")
            
        except Exception as e:
            self.caller.msg(f"Error spending plot point: {e}")

class CmdCheckPlotPoints(Command):
    """
    Check how many plot points you or another character has.
    
    Usage:
        pp [character]
        
    Without arguments, shows your own plot points.
    Staff members can check other characters' plot points.
    """
    
    key = "pp"
    locks = "cmd:all();view_other:perm(Builder)"
    help_category = "Game"
    
    def func(self):
        """Show plot point count."""
        if not self.args:
            # Check own plot points
            char = self.caller
            if not hasattr(char, 'traits'):
                char = char.char
        else:
            # Staff checking other character
            if not self.access(self.caller, "view_other"):
                self.caller.msg("You can only check your own plot points.")
                return
            char = self.caller.search(self.args)
            if not char:
                return
                
        if not hasattr(char, 'traits'):
            self.caller.msg(f"{char.name} does not have any plot points.")
            return
            
        try:
            pp_trait = char.traits.get("plot_points")
            if not pp_trait:
                self.caller.msg(f"{char.name} does not have any plot points.")
                return
                
            current = int(pp_trait.base)
            self.caller.msg(f"{char.name} has {current} plot point{'s' if current != 1 else ''}.")
            
        except Exception as e:
            self.caller.msg(f"Error checking plot points: {e}")

class CmdSetRoomPlotPoints(MuxCommand):
    """
    Set plot points for all characters in the current room.
    
    Usage:
        setroompp <amount>
        setroompp <character> = <amount>
        
    Examples:
        setroompp 3     - Set plot points to 3 for all characters in the room
        setroompp Bob = 5  - Set Bob's plot points to 5
        
    Only staff members can use this command.
    """
    
    key = "setroompp"
    locks = "cmd:perm(Builder)"  # Builders and above can use this
    help_category = "Game"
    
    def func(self):
        """Handle the plot point setting."""
        if not self.args:
            self.caller.msg("Usage: setroompp <amount> or setroompp <character> = <amount>")
            return
            
        # Parse arguments
        try:
            if "=" in self.args:
                # Setting for specific character
                char_name, amount = self.args.split("=", 1)
                char = self.caller.search(char_name.strip())
                if not char:
                    return
                chars = [char]
            else:
                # Setting for all characters in room
                amount = self.args
                chars = [obj for obj in self.caller.location.contents if hasattr(obj, 'traits')]
                
            amount = int(amount.strip())
            if amount < 0:
                self.caller.msg("Plot points cannot be negative.")
                return
                
        except ValueError:
            self.caller.msg("Amount must be a number.")
            return
            
        # Set plot points
        success_count = 0
        for char in chars:
            try:
                if not hasattr(char, 'traits'):
                    continue
                    
                pp_trait = char.traits.get("plot_points")
                if not pp_trait:
                    continue
                    
                char.traits.add("plot_points", value=amount)
                success_count += 1
                
                # Notify the character if they're not the one setting
                if char != self.caller:
                    char.msg(f"{self.caller.name} sets your plot points to {amount}.")
                
            except Exception as e:
                self.caller.msg(f"Error setting plot points for {char.name}: {e}")
                
        # Report results to the GM
        if self.rhs:  # Using = syntax
            if success_count:
                self.caller.msg(f"Set {char.name}'s plot points to {amount}.")
        else:
            self.caller.msg(f"Set plot points to {amount} for {success_count} character{'s' if success_count != 1 else ''}.")

class CmdSetCharacterPlotPoints(MuxCommand):
    """
    Set a character's plot points to a specific value.
    
    Usage:
        setpp <character>=<amount>
        
    Examples:
        setpp Bob=2    - Set Bob's plot points to exactly 2
        
    Only staff members can use this command.
    Use this to set exact plot point values. For adding or removing
    single plot points, use 'givepp' or 'spendpp' instead.
    """
    
    key = "setpp"
    locks = "cmd:perm(Builder)"  # Builders and above can use this
    help_category = "Game"
    
    def func(self):
        """Handle the plot point setting."""
        if not self.args or not self.rhs:
            self.caller.msg("Usage: setpp <character>=<amount>")
            return
            
        char = self.caller.search(self.lhs)
        if not char:
            return
            
        # Validate amount
        try:
            amount = int(self.rhs)
            if amount < 0:
                self.caller.msg("Plot points cannot be negative.")
                return
        except ValueError:
            self.caller.msg("Plot point amount must be a number.")
            return
            
        # Set plot points
        if not hasattr(char, 'traits'):
            self.caller.msg(f"{char.name} does not have trait support.")
            return
            
        try:
            pp_trait = char.traits.get("plot_points")
            if not pp_trait:
                self.caller.msg(f"{char.name} does not have a plot points trait.")
                return
                
            char.traits.add("plot_points", value=amount)
            
            # Notify relevant parties
            self.caller.msg(f"Set {char.name}'s plot points to {amount}.")
            if char != self.caller:
                char.msg(f"{self.caller.name} sets your plot points to {amount}.")
            
        except Exception as e:
            self.caller.msg(f"Error setting plot points: {e}")

class PlotPointCmdSet(CmdSet):
    """
    Command set for plot point management.
    """
    
    def at_cmdset_creation(self):
        """
        Add commands to the command set
        """
        self.add(CmdGivePlotPoint())
        self.add(CmdSpendPlotPoint())
        self.add(CmdCheckPlotPoints())
        self.add(CmdSetRoomPlotPoints())
        self.add(CmdSetCharacterPlotPoints()) 