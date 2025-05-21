"""
Commands for Cortex Prime dice rolling.
"""

from evennia import Command
from evennia import CmdSet
from utils.cortex import (
    DIFFICULTIES,
    TraitDie,
    get_trait_die,
    validate_dice_pool,
    roll_die,
    process_results,
    get_success_level,
    format_roll_result
)
from collections import defaultdict

# Constants for validation
MAX_DICE_POOL = 10  # Maximum number of dice that can be rolled at once
VALID_DIE_SIZES = {'4', '6', '8', '10', '12'}  # Set for O(1) lookup

def format_colored_roll(value, die, trait_info, extra_value=None):
    """
    Format a single die roll with color.
    
    Args:
        value: The value rolled on the main die
        die: The die size
        trait_info: The TraitDie object with trait information
        extra_value: If not None, this is the value of the extra die from doubling
    """
    if trait_info.key:  # Changed from trait_name to key to match TraitDie NamedTuple
        # Display name mapping
        display_names = {
            'distinctions': 'Distinction',
            'character_attributes': 'Attribute',
            'skills': 'Skill',
            'char_resources': 'Resource',
            'signature_assets': 'Signature Asset'
        }
        category_name = display_names.get(trait_info.category, trait_info.category.title().rstrip('s')) if trait_info.category else "Raw"
        
        # Build modifier suffix
        modifiers = []
        if trait_info.step_mod == 'U':
            modifiers.append("|g(U)|n")
        elif trait_info.step_mod == 'D':
            modifiers.append("|r(D)|n")
        mod_suffix = "".join(modifiers)
        
        # Get the trait object to check for name
        trait = None
        if trait_info.category == 'distinctions':
            trait = trait_info.caller.distinctions.get(trait_info.key)
        elif trait_info.category == 'character_attributes':
            trait = trait_info.caller.character_attributes.get(trait_info.key)
        elif trait_info.category == 'skills':
            trait = trait_info.caller.skills.get(trait_info.key)
        elif trait_info.category == 'char_resources':
            trait = trait_info.caller.char_resources.get(trait_info.key)
        elif trait_info.category == 'signature_assets':
            trait = trait_info.caller.signature_assets.get(trait_info.key)
            
        # Use trait name if available, otherwise use key
        display_name = trait.name if trait and hasattr(trait, 'name') else trait_info.key
        
        # If we have an extra die from doubling, include both values
        if extra_value is not None:
            return f"|c{value}, {extra_value}|n(d{die} {category_name}: {display_name}{mod_suffix} |c(Doubled)|n)"
        return f"|c{value}|n(d{die} {category_name}: {display_name}{mod_suffix})"
    return f"|c{value}|n(d{die})"

class CmdCortexRoll(Command):
    """
    Roll dice using the Cortex Prime system.
    
    Usage:
        roll <trait1> [<trait2>...] [vs <difficulty>]
        roll/step <trait1> [<trait2>...] - Step up the highest die
        
    Examples:
        roll strength fighting - Roll Strength + Fighting dice
        roll strength d8 - Roll Strength + a d8
        roll strength fighting signature_sword vs 12 - Roll against difficulty 12
        roll/step strength fighting - Step up highest die by one size
        
    Dice Mechanics:
    - Each trait adds its die to the pool (e.g., d6, d8, d10, d12)
    - Roll all dice and sum the two highest
    - If rolling against difficulty, must beat the target number
    - Distinctions can be used as d8 or d4 (d4 gives you a plot point)
    - Plot points can be spent to:
      * Step up the size of one die
      * Keep an additional die in the total
    
    Special Rules:
    - Rolling 1 on any die is a "hitch" (minor complication)
    - Matching dice can be used for special effects
    - Effect die (highest unused die) determines impact
    - Difficulty numbers:
      * 8 - Easy task
      * 12 - Moderate challenge
      * 16 - Difficult feat
      * 20 - Extreme challenge
    """
    
    key = "roll"
    locks = "cmd:all()"  # Everyone can use this command
    help_category = "Game"
    switch_options = ()  # No switches for this command
    
    def at_pre_cmd(self):
        """
        Called before command validation and parsing.
        Can be used to do setup or prevent command execution.
        
        Returns:
            True if command should be prevented, None to allow execution
        """
        # For now just check if character can roll dice (not incapacitated etc)
        # Add your character state validation here if needed
        return None
        
    def parse(self):
        """Parse the dice input and difficulty."""
        if not self.args:
            self.msg("What dice do you want to roll?")
            self.dice = None
            return
            
        # Split and clean args, removing empty strings
        args = []
        current_arg = []
        in_quotes = False
        
        # Parse args, handling quoted strings
        for word in self.args.split():
            if word.startswith('"'):
                in_quotes = True
                current_arg.append(word[1:])
            elif word.endswith('"'):
                in_quotes = False
                current_arg.append(word[:-1])
                args.append(' '.join(current_arg))
                current_arg = []
            elif in_quotes:
                current_arg.append(word)
            else:
                args.append(word)
                
        if current_arg:  # Handle any remaining words
            args.append(' '.join(current_arg))
            
        # Clean up args
        args = [arg.strip().lower() for arg in args if arg.strip()]
        
        if not args:
            self.msg("What dice do you want to roll?")
            self.dice = None
            return
            
        # Check for difficulty
        self.difficulty = None
        try:
            vs_index = args.index("vs")
            if vs_index < len(args) - 1:  # Make sure there's a value after "vs"
                # Get all words after "vs" as the difficulty value
                diff_val = ' '.join(args[vs_index + 1:])
                # Remove difficulty and "vs" from dice list
                args = args[:vs_index]
                
                # Parse difficulty - either a number or named difficulty
                if diff_val.isdigit():
                    self.difficulty = int(diff_val)
                    # Validate reasonable difficulty range
                    if not (1 <= self.difficulty <= 30):
                        self.msg(f"Difficulty must be between 1 and 30, not {self.difficulty}.")
                        self.dice = None
                        return
                else:
                    # Try to match named difficulty exactly first
                    exact_match = None
                    partial_matches = []
                    
                    # First check for exact matches
                    for name, value in DIFFICULTIES.items():
                        if diff_val == name.lower():
                            exact_match = value
                            break
                    
                    if exact_match is not None:
                        self.difficulty = exact_match
                    else:
                        # Special handling for "very" prefix
                        if diff_val == "very":
                            self.msg("Please specify 'very easy' or 'very hard'.")
                            self.dice = None
                            return
                            
                        # Check for partial matches
                        for name, value in DIFFICULTIES.items():
                            name_lower = name.lower()
                            if diff_val in name_lower:
                                # Only add to partial matches if it's not just the "very" prefix
                                if not (diff_val == "very" and name_lower.startswith("very")):
                                    partial_matches.append(name)
                        
                        if len(partial_matches) == 1:
                            self.difficulty = DIFFICULTIES[partial_matches[0]]
                        elif len(partial_matches) > 1:
                            self.msg(f"Ambiguous difficulty '{diff_val}'. Matches: {', '.join(partial_matches)}")
                            self.dice = None
                            return
                        else:
                            self.msg(f"Unknown difficulty '{diff_val}'. Valid difficulties are: {', '.join(DIFFICULTIES.keys())}")
                            self.dice = None
                            return
        except ValueError:
            # No "vs" found, that's fine
            pass
        
        # Validate dice pool size
        if not args:
            self.msg("You must specify at least one die to roll.")
            self.dice = None
            return
            
        if len(args) > MAX_DICE_POOL:
            self.msg(f"You cannot roll more than {MAX_DICE_POOL} dice at once.")
            self.dice = None
            return
        
        # Process dice/traits
        dice_pool = []
        
        for arg in args:
            # Validate argument
            if not arg:  # Skip empty arguments
                continue
                
            # Check if it's a raw die (must match pattern 'd' followed by a valid die size)
            if arg.startswith('d'):
                # Check for step modifiers on raw dice
                if '(' in arg:
                    self.msg("Raw dice (like 'd8') cannot be stepped up or down. Only traits can be modified.")
                    self.dice = None
                    return
                
                if len(arg) > 1 and arg[1:] in VALID_DIE_SIZES:
                    die = arg[1:]
                    dice_pool.append(TraitDie(die, None, None, None, self.caller))
                else:
                    self.msg(f"Invalid die size: {arg}")
                    self.dice = None
                    return
            else:
                # Check for invalid characters in trait names (allowing parentheses for modifiers)
                base_name = arg.split('(')[0] if '(' in arg else arg
                if not base_name.replace(' ', '').isalnum():
                    self.msg(f"Invalid character in trait name: {base_name}")
                    self.dice = None
                    return
                    
                # Try to find trait
                trait_info = get_trait_die(self.caller, arg)
                if trait_info:
                    die_size, category, step_mod, doubled = trait_info
                    # Add the main trait die
                    base_arg = arg.split('(')[0].strip()
                    trait_die = TraitDie(die_size, category, base_arg, step_mod, self.caller)
                    dice_pool.append(trait_die)
                    # If doubled, add an extra die of the same size (without trait info)
                    if doubled:
                        dice_pool.append(TraitDie(die_size, None, None, None, self.caller))
                else:
                    self.msg(f"Unknown trait or invalid die: {arg}")
                    self.dice = None
                    return
        
        # Validate the dice pool
        error = validate_dice_pool(dice_pool)
        if error:
            self.msg(error)
            self.dice = None
            return
        
        # Store dice and trait information
        self.dice = [die.size for die in dice_pool]
        self.trait_info = dice_pool

    def func(self):
        """Execute the dice roll."""
        if not self.dice:
            return
            
        try:
            # Roll all dice and track results with their indices
            rolls = [(roll_die(int(die)), die, i) for i, die in enumerate(self.dice)]
            
            # Check for botch (all 1s)
            all_values = [value for value, _, _ in rolls]
            if all(value == 1 for value in all_values):
                result_msg = f"|r{self.caller.key} BOTCHES! All dice came up 1s!|n\n"
                
                # Format rolls for botch message
                formatted_rolls = []
                i = 0
                while i < len(rolls):
                    trait_info = self.trait_info[rolls[i][2]]
                    if i + 1 < len(rolls) and trait_info.key and not self.trait_info[rolls[i+1][2]].key:
                        # This is a doubled trait
                        formatted_rolls.append(format_colored_roll(rolls[i][0], rolls[i][1], trait_info, rolls[i+1][0]))
                        i += 2
                    else:
                        formatted_rolls.append(format_colored_roll(rolls[i][0], rolls[i][1], trait_info))
                        i += 1
                        
                result_msg += f"Rolled: {', '.join(formatted_rolls)}"
                self.caller.location.msg_contents(result_msg)
                return
            
            # Process results
            total, effect_die, hitches = process_results(rolls)
            
            # Format individual roll results with trait names
            roll_results = []
            i = 0
            while i < len(rolls):
                trait_info = self.trait_info[rolls[i][2]]
                if i + 1 < len(rolls) and trait_info.key and not self.trait_info[rolls[i+1][2]].key:
                    # This is a doubled trait
                    roll_results.append(format_colored_roll(rolls[i][0], rolls[i][1], trait_info, rolls[i+1][0]))
                    i += 2
                else:
                    roll_results.append(format_colored_roll(rolls[i][0], rolls[i][1], trait_info))
                    i += 1
            
            # Build output message
            result_msg = f"{self.caller.key} rolls: {', '.join(roll_results)}\n"
            result_msg += f"Total: |w{total}|n | Effect Die: |w{effect_die}|n"
            
            # Add warning if effect die defaulted to d4
            if len(self.dice) == 2:
                result_msg += " |y(defaulted to d4 - only two dice rolled)|n"
            
            # Track traits used from each category for GM notification
            category_count = defaultdict(int)
            category_names = defaultdict(list)
            for trait in self.trait_info:
                if trait.category and trait.key:  # Skip raw dice and doubled dice (which have no category/key)
                    category_count[trait.category] += 1
                    category_names[trait.category].append(trait.key)
            
            # Send private notifications about multiple traits from same category
            for category, count in category_count.items():
                if count > 1:
                    notice = f"|yNote: Using multiple {category} traits ({', '.join(category_names[category])})|n"
                    # Send to the player
                    self.caller.msg(notice)
                    # Send to GMs in the room
                    for obj in self.caller.location.contents:
                        if obj.check_permstring("Builder") and obj != self.caller:
                            obj.msg(f"|y{self.caller.name} is using multiple {category} traits ({', '.join(category_names[category])})|n")
            
            # Add difficulty check if applicable
            if self.difficulty is not None:
                success, heroic = get_success_level(total, self.difficulty)
                result_msg += f"\nDifficulty: |w{self.difficulty}|n - "
                if success:
                    if heroic:
                        result_msg += f"|g{self.caller.key} achieves a HEROIC SUCCESS!|n"
                    else:
                        result_msg += "Success"
                else:
                    result_msg += "|yFailure|n"
            
            if hitches:
                result_msg += f"\n|yHitches: {len(hitches)} (rolled 1 on: d{', d'.join(hitches)})|n"
            
            # Send result to room
            self.caller.location.msg_contents(result_msg)
            
        except Exception as e:
            self.msg(f"Error during dice roll: {e}")
            return
            
    def at_post_cmd(self):
        """
        Called after command execution, even if it failed.
        Can be used for cleanup or to trigger other actions.
        """
        # For now just cleanup any temporary attributes if needed
        pass

    def get_trait_dice(self, trait_info):
        """Get the dice for a trait."""
        if trait_info.category == 'character_attributes':
            trait = trait_info.caller.character_attributes.get(trait_info.key)
        elif trait_info.category == 'skills':
            trait = trait_info.caller.skills.get(trait_info.key)
        elif trait_info.category == 'signature_assets':
            trait = trait_info.caller.signature_assets.get(trait_info.key)
        elif trait_info.category == 'char_resources':
            trait = trait_info.caller.char_resources.get(trait_info.key)
        else:
            return None
            
        if not trait:
            return None
            
        return [trait.base]

class CortexCmdSet(CmdSet):
    """
    Command set for Cortex Prime dice rolling.
    """
    key = "cortex"
    
    def at_cmdset_creation(self):
        """Add commands to the command set."""
        self.add(CmdCortexRoll())