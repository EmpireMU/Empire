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
        caller = self.caller
        location = caller.location
        self.args = self.args.strip()
        self.dice = []
        self.dice = self.args.split()
        location.msg_contents(self.dice)
        location.msg_contents(self.args)

    def func(self):

        caller = self.caller
        location = caller.location
        
        results = "Results: "
        for die in self.dice:
            location.msg_contents(self.dice)
            location.msg_contents(die)
            results = results + str(randint(1, int(die)))
            return
        



        
        
    

class CortexCmdSet(CmdSet):
    def at_cmdset_creation(self):
        self.add(CmdCortexRoll)