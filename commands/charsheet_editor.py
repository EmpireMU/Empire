"""
Staff commands for editing character sheets.
"""
from evennia.commands.command import Command
from evennia.commands.default.muxcommand import MuxCommand
from evennia import CmdSet, create_object
from evennia.utils import dbserialize
from evennia.utils import evtable

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
        
        # Display name mapping
        display_name = {
            'attributes': 'Attribute',
            'skills': 'Skill',
            'resources': 'Resource',
            'signature_assets': 'Signature Asset'
        }[category]
        
        try:
            handler = getattr(char, handler_name)
            if handler is None:  # Only return if handler is None, not if it's empty
                self.msg(f"Could not get {category} trait handler for {char.name}")
                return
        except AttributeError as e:
            self.msg(f"Could not get {category} trait handler for {char.name}")
            return
            
        # Add or update trait
        try:
            trait = handler.get(trait_key)
            if trait:
                trait.base = die_size
            else:
                handler.add(trait_key, value=f"d{die_size}")
                # Ensure .base is set correctly
                handler.get(trait_key).base = die_size
            self.caller.msg(f"Set {char.name}'s {display_name} '{trait_key}' to d{die_size}.")
            char.msg(f"{self.caller.name} sets your {display_name} '{trait_key}' to d{die_size}.")
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

class CmdResource(MuxCommand):
    """
    Manage a character's resources.
    
    Usage:
        resource [<character>]                    - List all resources
        resource <character> = add <name> d<size> - Add a new resource
        resource <character> = del <name> d<size> - Delete a specific resource
        
    Examples:
        resource Ada                    - List Ada's resources
        resource Ada = add "Political Capital" d8
        resource Ada = add "Political Capital" d8  # Adds another d8
        resource Ada = add "Political Capital" d6
        resource Ada = del "Political Capital" d8  # Removes one d8
        
    Resources are organizational dice pools that can have multiple instances
    of the same type with different die sizes. For example, a character might
    have three Political Capital of size d8 and two Political Capital of size d6.
    """
    
    key = "resource"
    locks = "cmd:perm(Builder)"  # Builders and above can use this
    help_category = "Building"
    
    def func(self):
        """Execute the command."""
        # If no arguments, show caller's resources
        if not self.args:
            self.show_resources(self.caller)
            return
            
        # Check if this is a view or edit command
        if "=" not in self.args:
            # View command
            char = self.caller.search(self.args)
            if not char:
                return
            self.show_resources(char)
            return
            
        # Parse edit command
        try:
            char_name, rest = self.args.split("=", 1)
            char = self.caller.search(char_name.strip())
            if not char:
                return
                
            # Split the rest into command and arguments
            parts = rest.strip().split(" ", 1)
            if len(parts) != 2:
                self.msg("Usage: resource <character> = add <name> d<size> or resource <character> = del <name> d<size>")
                return
                
            cmd, args = parts
            cmd = cmd.lower()
            
            if cmd not in ['add', 'del']:
                self.msg("Command must be 'add' or 'del'")
                return
                
            # Parse resource name and die size
            if not args.strip().endswith(('d4', 'd6', 'd8', 'd10', 'd12')):
                self.msg("Die size must be d4, d6, d8, d10, or d12")
                return
                
            # Split the last word (die size) from the name
            name_parts = args.rsplit(" ", 1)
            if len(name_parts) != 2:
                self.msg("Usage: resource <character> = add <name> d<size> or resource <character> = del <name> d<size>")
                return
                
            name, die_size = name_parts
            name = name.strip('"').strip()
            die_size = int(die_size[1:])  # Remove 'd' prefix
            
            # Create a unique key for this resource type and die size
            # Format: name_die_size (e.g., "Political Capital_d8")
            key = f"{name}_{die_size}"
            
            if cmd == 'add':
                # Get existing trait or create new one
                trait = char.resources.get(key)
                if trait:
                    # Increment count
                    value_str = str(trait.value)
                    count = 1
                    if value_str[0].isdigit():
                        try:
                            count = int(float(value_str.split('d')[0]))
                        except ValueError:
                            count = 1
                    new_count = count + 1
                    trait.value = f"{new_count}d{die_size}"
                    self.caller.msg(f"Added another {name} (d{die_size}) to {char.name}. Now has {new_count}.")
                    char.msg(f"{self.caller.name} added another {name} (d{die_size}). You now have {new_count}.")
                else:
                    # Create new trait with count=1
                    char.resources.add(key, value=f"1d{die_size}", name=name)
                    trait = char.resources.get(key)
                    if trait:
                        trait.base = die_size
                        # Ensure the value is stored as a string
                        trait.value = f"1d{die_size}"
                    self.caller.msg(f"Added {char.name}'s first {name} (d{die_size}).")
                    char.msg(f"{self.caller.name} added your first {name} (d{die_size}).")
            else:  # cmd == 'del'
                # Get existing trait
                trait = char.resources.get(key)
                if not trait:
                    self.msg(f"{char.name} doesn't have any {name} resources of size d{die_size}.")
                    return
                    
                # Decrement count or remove if last one
                value_str = str(trait.value)
                count = 1
                if value_str[0].isdigit():
                    try:
                        count = int(float(value_str.split('d')[0]))
                    except ValueError:
                        count = 1
                if count > 1:
                    new_count = count - 1
                    trait.value = f"{new_count}d{die_size}"
                    self.caller.msg(f"Removed one {name} (d{die_size}) from {char.name}. Now has {new_count}.")
                    char.msg(f"{self.caller.name} removed one {name} (d{die_size}). You now have {new_count}.")
                else:
                    char.resources.remove(key)
                    self.caller.msg(f"Removed {char.name}'s last {name} (d{die_size}).")
                    char.msg(f"{self.caller.name} removed your last {name} (d{die_size}).")
                
        except ValueError as e:
            self.msg(f"Error: {str(e)}")
            self.msg("Usage: resource <character> = add <name> d<size> or resource <character> = del <name> d<size>")
            return
            
    def show_resources(self, char):
        """Show a character's resources."""
        if not char.resources.all():
            self.msg(f"{char.name} has no resources.")
            return
            
        # Group resources by name
        resources_by_name = {}
        for key in char.resources.all():
            trait = char.resources.get(key)
            if trait:
                name = trait.name
                if name not in resources_by_name:
                    resources_by_name[name] = []
                resources_by_name[name].append(trait)
            
        # Build the display message
        msg = f"\n|w{char.name}'s Resources|n\n"
        
        # Create table
        table = evtable.EvTable(
            "|wResource|n",
            "|wDice|n",
            border="table",
            width=78
        )
        
        # Add rows
        for name, traits in sorted(resources_by_name.items()):
            # Count dice of each size
            dice_counts = {}
            for trait in traits:
                die_size = f"d{trait.base}"
                value_str = str(trait.value)
                count = 1
                if value_str[0].isdigit():
                    try:
                        count = int(float(value_str.split('d')[0]))
                    except ValueError:
                        count = 1
                dice_counts[die_size] = dice_counts.get(die_size, 0) + count
                
            # Format dice string (e.g., "2d8, 1d6")
            dice_str = ", ".join(f"{count}{size}" for size, count in sorted(dice_counts.items()))
            
            table.add_row(name, dice_str)
            
        msg += str(table)
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
        self.add(CmdBackground())
        self.add(CmdPersonality())
        self.add(CmdResource()) 