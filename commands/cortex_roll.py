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
    if trait_info.name:  # Changed from trait_name to name to match TraitDie NamedTuple
        category_name = trait_info.category.title().rstrip('s') if trait_info.category else "Raw"
        # Build modifier suffix
        modifiers = []
        if trait_info.step_mod == 'U':
            modifiers.append("|g(U)|n")
        elif trait_info.step_mod == 'D':
            modifiers.append("|r(D)|n")
        mod_suffix = "".join(modifiers)
        
        # If we have an extra die from doubling, include both values
        if extra_value is not None:
            return f"|cd{value}, {extra_value}|n(d{die} {category_name}: {trait_info.name}{mod_suffix} |c(Doubled)|n)"
        return f"|cd{value}|n(d{die} {category_name}: {trait_info.name}{mod_suffix})"
    return f"|cd{value}|n(d{die})"

class CmdCortexRoll(Command):
    """
    Roll a pool of Cortex Prime dice against an optional difficulty.
    
    Usage:
        roll <trait1> <trait2> <trait3> ... [vs <difficulty>]
        
    Examples:
        roll explorer prowess fighting d8  (prime sets plus raw die)
        roll explorer acuity perception vs hard  (just prime sets)
        roll d12 d8 d6 vs 11  (just raw dice)
        roll explorer prowess fighting asset d10  (prime sets plus signature asset and raw die)
        
    This will roll the specified dice pool according to Cortex Prime rules:
    - Takes the two highest non-hitch dice for the total
    - Uses next highest non-hitch die as the effect die (d4 if none available)
    - Any 1s rolled are hitches and cannot be used for total or effect die
    - All 1s is a botch (catastrophic failure)
    - Supports d4, d6, d8, d10, and d12
    
    Prime Trait Sets:
    When using any trait from the prime sets (Attributes, Skills, or Distinctions),
    you must include one trait from each of these sets in your pool. Additionally,
    using any Signature Asset or Resource requires all three prime sets to be included.
    Raw dice (like 'd8') can always be added to any roll without affecting these requirements.
    
    Modifiers:
    - (U) steps up the die one size (d6 → d8)
    - (D) steps down the die one size (d8 → d6)
    - (double) uses the same trait twice
    
    You can use trait names (like 'prowess' or 'fighting') or raw dice (like 'd8').
    The command will look up trait values in this order:
    1. Attributes (prowess, finesse, etc.)
    2. Skills (fighting, influence, etc.)
    3. Distinctions (always d8)
    4. Resources (require all prime sets)
    5. Signature Assets (require all prime sets)
    
    Raw dice can be mixed freely with any of the above.
    
    Validation Rules:
    - Must include at least 2 dice
    - When using any prime trait (Attribute/Skill/Distinction), must use all three
    - When using a Resource or Signature Asset, must include all prime sets
    - Raw dice can be added to any roll
    - Maximum of 10 dice in a pool
    
    Difficulty ratings:
        Very Easy: 3
        Easy: 7
        Challenging: 11
        Hard: 15
        Very Hard: 19
        
    Beating a difficulty by 5 or more is a heroic success.
    """
    
    key = "roll"
    locks = "cmd:all()"  # Everyone can use this command
    help_category = "Game"
    arg_regex = r"\s.+|$"  # Require space between command and arguments, or no arguments
    
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
            return
            
        # Split and clean args, removing empty strings
        args = [arg.strip().lower() for arg in self.args.split() if arg.strip()]
        
        if not args:
            self.msg("What dice do you want to roll?")
            return
            
        # Check for difficulty
        self.difficulty = None
        if len(args) >= 2 and args[-2] == "vs":
            diff_val = args[-1]
            # Remove difficulty from dice list
            args = args[:-2]
            
            # Parse difficulty - either a number or named difficulty
            if diff_val.isdigit():
                self.difficulty = int(diff_val)
                # Validate reasonable difficulty range
                if not (1 <= self.difficulty <= 30):
                    self.msg(f"Difficulty must be between 1 and 30, not {self.difficulty}.")
                    return
            else:
                # Try to match named difficulty exactly first
                exact_match = None
                partial_matches = []
                for name, value in DIFFICULTIES.items():
                    if diff_val == name.lower():
                        exact_match = value
                        break
                    elif diff_val in name.lower():
                        partial_matches.append(name)
                
                if exact_match is not None:
                    self.difficulty = exact_match
                elif len(partial_matches) == 1:
                    self.difficulty = DIFFICULTIES[partial_matches[0]]
                elif len(partial_matches) > 1:
                    self.msg(f"Ambiguous difficulty '{diff_val}'. Matches: {', '.join(partial_matches)}")
                    return
                else:
                    self.msg(f"Unknown difficulty '{diff_val}'. Valid difficulties are: {', '.join(DIFFICULTIES.keys())}")
                    return
        
        # Validate dice pool size
        if not args:
            self.msg("You must specify at least two dice to roll.")
            return
            
        if len(args) > MAX_DICE_POOL:
            self.msg(f"You cannot roll more than {MAX_DICE_POOL} dice at once.")
            return
            
        if len(args) < 2:
            self.msg("You must roll at least two dice.")
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
                    return
                
                if len(arg) > 1 and arg[1:] in VALID_DIE_SIZES:
                    die = arg[1:]
                    dice_pool.append(TraitDie(die, None, None, None))
                else:
                    self.msg(f"Invalid die size: {arg}")
                    return
            else:
                # Check for invalid characters in trait names (allowing parentheses for modifiers)
                base_name = arg.split('(')[0] if '(' in arg else arg
                if not base_name.replace(' ', '').isalnum():
                    self.msg(f"Invalid character in trait name: {base_name}")
                    return
                    
                # Try to find trait
                trait_info = get_trait_die(self.caller, arg)
                if trait_info:
                    die_size, category, step_mod, doubled = trait_info
                    # Add the main trait die
                    base_arg = arg.split('(')[0].strip()
                    trait_die = TraitDie(die_size, category, base_arg, step_mod)
                    dice_pool.append(trait_die)
                    # If doubled, add an extra die of the same size (without trait info)
                    if doubled:
                        dice_pool.append(TraitDie(die_size, None, None, None))
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
                    if i + 1 < len(rolls) and trait_info.name and not self.trait_info[rolls[i+1][2]].name:
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
                if i + 1 < len(rolls) and trait_info.name and not self.trait_info[rolls[i+1][2]].name:
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
                if trait.category and trait.name:  # Skip raw dice and doubled dice (which have no category/name)
                    category_count[trait.category] += 1
                    category_names[trait.category].append(trait.name)
            
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


class CortexCmdSet(CmdSet):
    """
    Command set for Cortex Prime dice rolling.
    """
    key = "cortex"
    
    def at_cmdset_creation(self):
        """Add commands to the command set."""
        self.add(CmdCortexRoll())