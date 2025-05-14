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
        self.dice = self.args.split()

    def func(self):

        caller = self.caller
        location = caller.location
        
        results = "Results: "
        for i in self.dice:
            location.msg_contents(self.dice[i])
            results = results + "+(" + self.dice[i] + ")" + str(randint(1, int(self.dice[i])))
            return
        



        
        
    

class CortexCmdSet(CmdSet):
    def at_cmdset_creation(self):
        self.add(CmdCortexRoll)