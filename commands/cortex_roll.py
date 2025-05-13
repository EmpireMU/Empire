from evennia import Command
from evennia import CmdSet
from random import randint


class CmdCortexRoll(Command):
    """
    A command to roll dice.
    """
    
    key = "roll"

    def parse(self):
        self.dice = self.args.strip.split("+")
        return

    def func(self):
        
        if not args:
            self.caller.msg("What dice do you want to roll?")
            return
        results = []
        i = 0
        for die in dice:
            i += 1
            results[i] = randint(1, die)
            return
        



        caller = self.caller
        location = caller.location
        message = results
        location.msg_contents(message)
    

class CortexCmdSet(CmdSet):
    def at_cmdset_creation(self):
        self.add(CmdCortexRoll)