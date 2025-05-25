"""
Staff commands for editing character sheets.
"""
from evennia.commands.command import Command
from evennia.commands.default.muxcommand import MuxCommand
from evennia import CmdSet, create_object
from evennia.utils import dbserialize
from evennia.utils import evtable
from evennia.utils.search import search_object
from utils.command_mixins import CharacterLookupMixin, TraitCommand

UNDELETABLE_TRAITS = ["attributes", "skills"]

class CmdSetTrait(CharacterLookupMixin, MuxCommand):
    """
    Set a trait on a character sheet.

    Usage:
      settrait <character> = <category> <n> d<size> [description]

    Categories:
      attributes   - Core attributes (d4-d12, default d6)
        Represent innate capabilities like Strength, Agility, etc.
      skills       - Skills (d4-d12, default d4)
        Represent learned abilities and training
      signature_assets - Signature assets (d4-d12)
        Represent important items or companions

    Die Sizes:
      d4  - Untrained/Weak
      d6  - Average/Basic Training
      d8  - Professional/Well Trained
      d10 - Expert/Exceptional
      d12 - Master/Peak Human

    Examples:
      settrait Tom = attributes strength d8
        Sets Tom's Strength attribute to d8
      settrait Tom = skills fighting d6 "Expert in hand-to-hand combat"
        Sets Tom's Fighting skill to d6 with description
      settrait Tom = signature_assets sword d8 "Family heirloom blade"
        Creates a d8 Signature Asset representing Tom's sword
      settrait Jane = attributes agility d10 "Years of acrobatic training"
        Sets Jane's Agility to d10 with explanation of high rating

    Notes:
    - Setting a trait that already exists will overwrite it
    - Descriptions help justify the die rating and provide roleplay hooks
    - Attributes affect all related skill rolls
    - Skills can't normally exceed d12
    - Each die size represents a significant increase in capability
    """
    key = "settrait"
    help_category = "Character"
    locks = "cmd:perm(Admin)"

    def func(self):
        """Execute the command."""
        if not self.args or "=" not in self.args:
            self.msg("Usage: settrait <character> = <category> <n> d<size> [description]")
            return

        # Split into character and trait parts
        char_name, trait_part = [part.strip() for part in self.args.split("=", 1)]
        
        # Find the character using inherited method
        char = self.find_character(char_name)
        if not char:
            return

        # Parse trait information
        parts = trait_part.strip().split()
        if len(parts) < 3:
            self.msg("Usage: settrait <character> = <category> <n> d<size> [description]")
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
            char.character_attributes.add(name, name.title(), trait_type="static", base=die_size, desc=description)
        elif category == 'skills':
            char.skills.add(name, name.title(), trait_type="static", base=die_size, desc=description)
        elif category == 'signature_assets':
            char.signature_assets.add(name, name.title(), trait_type="static", base=die_size, desc=description)

        self.msg(f"Set {name} to d{die_size} for {char.name}")

class CmdDeleteTrait(CharacterLookupMixin, MuxCommand):
    """Delete a trait from a character.
    
    Usage:
        deletetrait <character> = <category> <trait>
        
    Categories:
        attributes - Core attributes
        skills - Learned abilities
        signature_assets - Important items/companions
        
    Examples:
        deletetrait Bob = attributes strength
        deletetrait Jane = skills fighting
        deletetrait Tom = signature_assets sword
    """
    key = "deletetrait"
    locks = "cmd:perm(Admin)"
    help_category = "Character"

    def func(self):
        """Execute the command."""
        if not self.args or "=" not in self.args:
            self.msg("Usage: deletetrait <character> = <category> <trait>")
            return

        char_name, rest = [part.strip() for part in self.args.split("=", 1)]
        
        # Find the character using inherited method
        char = self.find_character(char_name)
        if not char:
            return

        # Parse category and trait name
        try:
            category, trait_name = rest.strip().split(None, 1)
        except ValueError:
            self.msg("You must specify both a category and a trait name.")
            return
            
        category = category.lower()
        trait_name = trait_name.strip().lower()
          # Get the appropriate trait handler
        if category == 'attributes':
            handler = char.character_attributes
        elif category == 'skills':
            handler = char.skills
        elif category == 'signature_assets':
            handler = char.signature_assets
        else:
            self.msg("Invalid category. Must be one of: attributes, skills, signature_assets")
            return
            
        # Try to delete the trait - use case-insensitive lookup
        actual_key = None
        for key in handler.all():
            if key.lower() == trait_name.lower():
                actual_key = key
                break
        
        if actual_key:
            # Check if trait is undeletable
            if category in UNDELETABLE_TRAITS and trait_name in handler.all():
                self.msg(f"Cannot delete {category} trait '{actual_key}' - it is a required trait.")
                return
            
            handler.remove(actual_key)
            self.msg(f"Deleted {category} trait '{actual_key}' from {char.name}.")
        else:
            self.msg(f"No {category} trait found named '{trait_name}' on {char.name}.")

class CmdSetDistinction(CharacterLookupMixin, MuxCommand):
    """
    Set a distinction on a character.
    
    Usage:
        setdist <character> = <slot> : <n> : <description>
        
          Notes:
    - All distinctions are d8 (can be used as d4 to gain a plot point)
    """
    
    key = "setdist"
    locks = "cmd:perm(Builder)"  # Builders and above can use this
    help_category = "Building"
    
    def func(self):
        """Handle setting the distinction."""
        if not self.args or ":" not in self.args or "=" not in self.args:
            self.msg("Usage: setdist <character> = <slot> : <n> : <description>")
            return
            
        char_name, rest = self.args.split("=", 1)
        char_name = char_name.strip()
        
        try:
            slot, name, desc = [part.strip() for part in rest.split(":", 2)]
        except ValueError:
            self.msg("Usage: setdist <character> = <slot> : <n> : <description>")
            return
            
        # Find the character using inherited method
        char = self.find_character(char_name)
        if not char:
            return
            
        # Verify character has distinctions
        if not hasattr(char, 'distinctions'):
            self.msg(f"{char.name} does not have distinctions.")
            return
            
        # Validate slot
        valid_slots = ["concept", "culture", "reputation"]
        if slot not in valid_slots:
            self.msg(f"Invalid slot. Must be one of: {', '.join(valid_slots)}")
            return
            
        # Set the distinction (all distinctions are d8)
        char.distinctions.add(slot, name, trait_type="static", base=8, desc=desc)
        self.msg(f"Set {char.name}'s {slot} distinction to '{name}' (d8)")

class CmdBiography(CharacterLookupMixin, MuxCommand):
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
            
        # View command using inherited method
        char = self.find_character(self.args)
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

class CmdBackground(CharacterLookupMixin, MuxCommand):
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
    # Everyone can view, but editing requires Builder permission
    locks = "cmd:all();edit:perm(Builder)"
    help_category = "Character"
    
    def func(self):
        """Execute the command."""
        # If no arguments, show caller's background
        if not self.args:
            self.show_background(self.caller)
            return
            
        # Check if this is a view or edit command
        if "=" not in self.args:
            # View command using inherited method
            char = self.find_character(self.args)
            if not char:
                return
            self.show_background(char)
            return
            
        # Edit command - check permissions
        if not self.access(self.caller, "edit"):
            self.msg("You don't have permission to edit backgrounds.")
            return
            
        # Parse edit command
        try:
            char_name, text = self.args.split("=", 1)
            char = self.find_character(char_name.strip())
            if not char:
                return
                
            # Update the background
            char.db.background = text.strip()
            self.msg(f"Updated {char.name}'s background.")
            char.msg(f"{self.caller.name} updated your background.")
        except Exception as e:
            self.msg(f"Error updating background: {e}")
    
    def show_background(self, char):
        """Show a character's background."""
        background = char.db.background
        if not background:
            self.msg(f"{char.name} has no background set.")
            return
            
        self.msg(f"\n|w{char.name}'s Background:|n\n{background}")

class CmdPersonality(CharacterLookupMixin, MuxCommand):
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
    # Everyone can view, but editing requires Builder permission
    locks = "cmd:all();edit:perm(Builder)"
    help_category = "Character"
    
    def func(self):
        """Execute the command."""
        # If no arguments, show caller's personality 
        if not self.args:
            self.show_personality(self.caller)
            return
            
        # Check if this is a view or edit command
        if "=" not in self.args:
            # View command using inherited method
            char = self.find_character(self.args)
            if not char:
                return
            self.show_personality(char)
            return
            
        # Edit command - check permissions
        if not self.access(self.caller, "edit"):
            self.msg("You don't have permission to edit personalities.")
            return
            
        # Parse edit command
        try:
            char_name, text = self.args.split("=", 1)
            char = self.find_character(char_name.strip())
            if not char:
                return
                
            # Update the personality
            char.db.personality = text.strip()
            self.msg(f"Updated {char.name}'s personality.")
            char.msg(f"{self.caller.name} updated your personality.")
        except Exception as e:
            self.msg(f"Error updating personality: {e}")
    
    def show_personality(self, char):
        """Show a character's personality."""
        personality = char.db.personality
        if not personality:
            self.msg(f"{char.name} has no personality set.")
            return
            
        self.msg(f"\n|w{char.name}'s Personality:|n\n{personality}")

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
        self.add(CmdBiography())
        self.add(CmdBackground())
        self.add(CmdPersonality())