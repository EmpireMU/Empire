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
        valid_slots = ["concept", "culture", "vocation"]
        if slot not in valid_slots:
            self.msg(f"Invalid slot. Must be one of: {', '.join(valid_slots)}")
            return
            
        # Set the distinction (all distinctions are d8)
        char.distinctions.add(slot, name, trait_type="static", base=8, desc=desc)
        self.msg(f"Set {char.name}'s {slot} distinction to '{name}' (d8)")

class CmdBiography(CharacterLookupMixin, MuxCommand):
    """
    View or edit a character's biography information.
    
    Usage:
        biography [<character>]                    - View full biography
        biography/background <char> = <text>       - Set background
        biography/personality <char> = <text>      - Set personality
        biography/age <char> = <age>              - Set age
        biography/birthday <char> = <date>        - Set birthday
        biography/gender <char> = <gender>        - Set gender
        biography/name <char> = <full name>       - Set full name
        biography/notable <char> = <text>         - Set notable traits
        
    Examples:
        biography                    - View your own biography
        biography Ada               - View Ada's biography
        biography/background Ada = Born in the mountains...
        biography/personality Ada = Friendly and outgoing...
        biography/age Ada = 30
        biography/birthday Ada = December 25th
        biography/gender Ada = Female
        biography/name Ada = Empress Ada Lovelace
        biography/notable Ada = Master of disguise, speaks 5 languages
        
    Shows:
        - Description (set with 'desc' command)
        - Age (set with biography/age)
        - Birthday (set with biography/birthday)
        - Gender (set with biography/gender)
        - Background (set with biography/background)
        - Personality (set with biography/personality)
        - Distinctions (set with 'setdist' command):
          * Character Concept
          * Culture
          * Vocation
        - Notable Traits (set with biography/notable)
    """
    
    key = "biography"
    locks = "cmd:all();edit:perm(Builder)"  # Everyone can view, builders can edit
    help_category = "Character"
    
    def func(self):
        """Execute the command."""
        # Handle switches
        if self.switches:
            if not self.access(self.caller, "edit"):
                self.msg("You don't have permission to edit biographies.")
                return
                
            if not self.args or "=" not in self.args:
                self.msg(f"Usage: biography/{self.switches[0]} <character> = <value>")
                return
                
            try:
                char_name, value = self.args.split("=", 1)
                char = self.find_character(char_name.strip())
                if not char:
                    return
                    
                value = value.strip()
                switch = self.switches[0].lower()
                
                # Map switches to attributes
                switch_map = {
                    "background": "background",
                    "personality": "personality",
                    "age": "age",
                    "birthday": "birthday",
                    "gender": "gender",
                    "name": "full_name",
                    "notable": "notable_traits"
                }
                
                if switch not in switch_map:
                    self.msg(f"Invalid switch. Use one of: {', '.join(switch_map.keys())}")
                    return
                
                # Update the appropriate attribute
                setattr(char.db, switch_map[switch], value)
                self.msg(f"Updated {char.name}'s {switch}.")
                char.msg(f"{self.caller.name} updated your {switch}.")
                
            except Exception as e:
                self.msg(f"Error updating {switch}: {e}")
            return
            
        # If no switches, show biography
        if not self.args:
            self.show_biography(self.caller)
            return
            
        # View command
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
        
        # Add full name if it exists
        if char.db.full_name:
            msg += f"\n|wFull Name:|n {char.db.full_name}"
        
        # Add character concept first if it exists
        if hasattr(char, 'distinctions'):
            concept = char.distinctions.get("concept")
            if concept:
                msg += f"\n|wConcept:|n {concept.name}"
                if concept.desc:
                    msg += f" - {concept.desc}"
            else:
                msg += "\n|wConcept:|n Not set"
        
        # Add demographic information on one line
        msg += "\n"
        demographics = []
        if char.db.gender:
            demographics.append(f"|wGender:|n {char.db.gender}")
        if char.db.age:
            demographics.append(f"|wAge:|n {char.db.age}")
        if char.db.birthday:
            demographics.append(f"|wBirthday:|n {char.db.birthday}")
        msg += " | ".join(demographics) if demographics else "|wNo demographics set|n"
        
        # Add culture and vocation on one line if they exist
        if hasattr(char, 'distinctions'):
            culture = char.distinctions.get("culture")
            vocation = char.distinctions.get("vocation")
            culture_text = f"|wCulture:|n {culture.name}" if culture else "|wCulture:|n Not set"
            vocation_text = f"|wVocation:|n {vocation.name}" if vocation else "|wVocation:|n Not set"
            msg += f"\n{culture_text} | {vocation_text}"
        
        # Add main character information
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
        
        # Add notable traits if they exist
        if char.db.notable_traits:
            msg += f"\n\n|wNotable Traits:|n\n{char.db.notable_traits}"
        
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
        self.add(CmdDeleteTrait())
        self.add(CmdSetDistinction())
        self.add(CmdBiography())