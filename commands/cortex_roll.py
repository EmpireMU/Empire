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
        dice_string = self.args.strip()
        self.dice = dice_string.split()

    def func(self):

        caller = self.caller
        location = caller.location
        
        
        results = []
        for die in self.dice:
            message = die
            location.msg_contents(self.dice)
            location.msg_contents(die)
            results.append(str(randint(1, int(die))))
            return
        



        
        
    

class CortexCmdSet(CmdSet):
    def at_cmdset_creation(self):
        self.add(CmdCortexRoll)