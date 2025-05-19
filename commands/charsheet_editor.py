"""
Staff commands for editing character sheets.
"""
from evennia.commands.command import Command
from evennia.commands.default.muxcommand import MuxCommand
from evennia import CmdSet, create_object
from evennia.utils import dbserialize
from evennia.utils import evtable
from evennia.utils.search import search_object

UNDELETABLE_TRAITS = ["attributes", "skills"]

class CmdSetTrait(MuxCommand):
    """
    Set a trait on a character sheet.

    Usage:
      settrait <character> = <category> <name> d<size>
      settrait <character> = <category> <name> d<size> <description>

    Categories:
      attributes   - Core attributes (d4-d12)
      skills       - Skills (d4-d12)
      signature_assets - Signature assets (d4-d12)

    Examples:
      settrait Tom = attributes strength d8
      settrait Tom = skills fighting d6 "Expert in hand-to-hand combat"
      settrait Tom = signature_assets sword d8 "Family heirloom"
    """
    key = "settrait"
    help_category = "Character"
    locks = "cmd:perm(Admin)"

    def func(self):
        """Execute the command."""
        if not self.args or "=" not in self.args:
            self.msg("Usage: settrait <character> = <category> <name> d<size> [description]")
            return

        # Split into character and trait parts
        char_name, trait_part = [part.strip() for part in self.args.split("=", 1)]
        
        # Find the character
        char = self.caller.search(char_name)
        if not char:
            return

        # Parse trait information
        parts = trait_part.strip().split()
        if len(parts) < 3:
            self.msg("Usage: settrait <character> = <category> <name> d<size> [description]")
            return

        category = parts[0].lower()
        if category not in ['attributes', 'skills', 'signature_assets']:
            self.msg("Invalid category. Must be one of: attributes, skills, signature_assets")
            return

        name = parts[1]
        die_size = parts[2]
        description = " ".join(parts[3:]) if len(parts) > 3 else ""

        # Validate die size
        if not die_size.startswith('d') or not die_size[1:].isdigit():
            self.msg("Die size must be in the format dN where N is a number (e.g., d4, d6, d8, d10, d12)")
            return

        die_size = int(die_size[1:])
        if die_size not in [4, 6, 8, 10, 12]:
            self.msg("Die size must be one of: d4, d6, d8, d10, d12")
            return

        # Set the trait
        if category == 'attributes':
            char.attributes.add(name, value=die_size, name=name, description=description)
        elif category == 'skills':
            char.skills.add(name, value=die_size, name=name, description=description)
        elif category == 'signature_assets':
            char.signature_assets.add(name, value=die_size, name=name, description=description)

        self.msg(f"Set {name} to d{die_size} for {char.name}")

class CmdDelTrait(MuxCommand):
    """
    Delete a trait from a character sheet.

    Usage:
      deltrait <character> = <category> <name>

    Categories:
      attributes   - Core attributes (d4-d12)
      skills       - Skills (d4-d12)
      signature_assets - Signature assets (d4-d12)

    Examples:
      deltrait Bob = attributes strength
      deltrait Bob = skills fighting
      deltrait Bob = signature_assets sword
    """
    key = "deltrait"
    help_category = "Character"
    locks = "cmd:perm(Admin)"

    def func(self):
        """Execute the command."""
        if not self.args or "=" not in self.args:
            self.msg("Usage: deltrait <character> = <category> <name>")
            return

        # Split into character and trait parts
        char_name, trait_part = [part.strip() for part in self.args.split("=", 1)]
        
        # Find the character
        char = self.caller.search(char_name)
        if not char:
            return

        # Parse trait information
        parts = trait_part.strip().split()
        if len(parts) != 2:
            self.msg("Usage: deltrait <character> = <category> <name>")
            return

        category = parts[0].lower()
        if category not in ['attributes', 'skills', 'signature_assets']:
            self.msg("Invalid category. Must be one of: attributes, skills, signature_assets")
            return

        name = parts[1]

        # Delete the trait
        if category == 'attributes':
            char.attributes.remove(name)
        elif category == 'skills':
            char.skills.remove(name)
        elif category == 'signature_assets':
            char.signature_assets.remove(name)

        self.msg(f"Deleted {name} from {char.name}'s {category}")

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

class CmdBiography(MuxCommand):
    """
    View a character's complete biography.
    
    Usage:
        biography [<character>]
        
    Examples:
        biography                    - View your own biography
        biography Ada               - View Ada's biography
        
    Shows:
        - Description (set with 'desc' command)
        - Background (set with 'background' command)
        - Personality (set with 'personality' command)
    """
    
    key = "biography"
    locks = "cmd:all()"  # Everyone can view
    help_category = "Character"
    
    def func(self):
        """Execute the command."""
        # If no arguments, show caller's biography
        if not self.args:
            self.show_biography(self.caller)
            return
            
        # View command
        char = self.caller.search(self.args)
        if not char:
            return
        self.show_biography(char)
            
    def show_biography(self, char):
        """Show a character's biography."""
        # Get the character's description using Evennia's built-in method
        desc = char.get_display_desc(self.caller)
        
        # Build the biography message
        msg = f"\n|w{char.name}'s Biography|n"
        msg += f"\n\n|wDescription:|n\n{desc}"
        msg += f"\n\n|wBackground:|n\n{char.db.background}"
        msg += f"\n\n|wPersonality:|n\n{char.db.personality}"
        
        # Add organization memberships
        orgs = char.organisations
        if orgs:
            msg += "\n\n|wOrganizations:|n"
            table = evtable.EvTable(
                "|wOrganization|n",
                "|wRank|n",
                border="table",
                width=78
            )
            
            # Add each organization and rank
            for org_id, rank in orgs.items():
                # Search for organization using its ID
                orgs_found = search_object(f"#{org_id}")
                if orgs_found:
                    org = orgs_found[0]
                    rank_name = org.get_member_rank_name(char)
                    table.add_row(org.name, rank_name)
            
            msg += f"\n{str(table)}"
        
        self.msg(msg)

class CmdBackground(MuxCommand):
    """
    View or edit a character's background.
    
    Usage:
        background [<character>]
        background <character> = <text>
        
    Examples:
        background                    - View your own background
        background Ada               - View Ada's background
        background Ada = Born in the mountains...
        
    Note: Use 'biography' to see all character information at once.
    """
    
    key = "background"
    locks = "cmd:all()"  # Everyone can view, but editing requires permissions
    help_category = "Character"
    
    def func(self):
        """Execute the command."""
        # If no arguments, show caller's background
        if not self.args:
            self.show_background(self.caller)
            return
            
        # Check if this is a view or edit command
        if "=" not in self.args:
            # View command
            char = self.caller.search(self.args)
            if not char:
                return
            self.show_background(char)
            return
            
        # Edit command - check permissions
        if not self.caller.check_permstring("Builder"):
            self.msg("You don't have permission to edit backgrounds.")
            return
            
        # Parse edit command
        try:
            char_name, text = self.args.split("=", 1)
            char = self.caller.search(char_name.strip())
            if not char:
                return
                
            # Update the background
            char.db.background = text.strip()
            self.msg(f"Updated {char.name}'s background.")
            char.msg(f"{self.caller.name} updated your background.")
            
        except ValueError:
            self.msg("Usage: background <character> = <text>")
            return
            
    def show_background(self, char):
        """Show a character's background."""
        msg = f"\n|w{char.name}'s Background|n"
        msg += f"\n\n{char.db.background}"
        self.msg(msg)

class CmdPersonality(MuxCommand):
    """
    View or edit a character's personality.
    
    Usage:
        personality [<character>]
        personality <character> = <text>
        
    Examples:
        personality                    - View your own personality
        personality Ada               - View Ada's personality
        personality Ada = Friendly and outgoing...
        
    Note: Use 'biography' to see all character information at once.
    """
    
    key = "personality"
    locks = "cmd:all()"  # Everyone can view, but editing requires permissions
    help_category = "Character"
    
    def func(self):
        """Execute the command."""
        # If no arguments, show caller's personality
        if not self.args:
            self.show_personality(self.caller)
            return
            
        # Check if this is a view or edit command
        if "=" not in self.args:
            # View command
            char = self.caller.search(self.args)
            if not char:
                return
            self.show_personality(char)
            return
            
        # Edit command - check permissions
        if not self.caller.check_permstring("Builder"):
            self.msg("You don't have permission to edit personalities.")
            return
            
        # Parse edit command
        try:
            char_name, text = self.args.split("=", 1)
            char = self.caller.search(char_name.strip())
            if not char:
                return
                
            # Update the personality
            char.db.personality = text.strip()
            self.msg(f"Updated {char.name}'s personality.")
            char.msg(f"{self.caller.name} updated your personality.")
            
        except ValueError:
            self.msg("Usage: personality <character> = <text>")
            return
            
    def show_personality(self, char):
        """Show a character's personality."""
        msg = f"\n|w{char.name}'s Personality|n"
        msg += f"\n\n{char.db.personality}"
        self.msg(msg)

class CharSheetEditorCmdSet(CmdSet):
    """
    Command set for editing character sheets.
    """
    
    def at_cmdset_creation(self):
        """
        Add commands to the command set
        """
        self.add(CmdSetTrait())
        self.add(CmdDelTrait())
        self.add(CmdSetDistinction())
        self.add(CmdBiography())
        self.add(CmdBackground())
        self.add(CmdPersonality()) 