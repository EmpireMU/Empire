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
        self.args = self.args.strip()
        caller = self.caller
        location = caller.location
        location.msg_contents(self.args)
        self.dice = self.args.split("+")

    def func(self):

        caller = self.caller
        location = caller.location
        location.msg_contents(self.dice)
        
        
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