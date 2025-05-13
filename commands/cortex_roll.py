from evennia import Command
from evennia import CmdSet
from random import randint


class CmdCortexRoll(Command):
    """
    A command to roll dice.
    """
    
    key = "roll"

    def parse(self):
        if not self.args:
            self.caller.msg("What dice do you want to roll?")
            return
        dice_string = self.args.strip().lower()
        self.dice = dice_string.split("+")

    def func(self):
        
        
        results = []
        i = 0
        for die in self.dice:
            i += 1
            results[i] = str(randint(1, die))
            return
        



        caller = self.caller
        location = caller.location
        message = results
        location.msg_contents(message)
    

class CortexCmdSet(CmdSet):
    def at_cmdset_creation(self):
        self.add(CmdCortexRoll)