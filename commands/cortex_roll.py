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
        self.dice = self.args.split()

    def func(self):
        
        results = "Results: "
        for die in self.dice:
            results = results + "+(" + die + ")" + str(randint(1, int(die)))
        

        caller = self.caller
        location = caller.location
        location.msg_contents(results)


        
        
    

class CortexCmdSet(CmdSet):
    def at_cmdset_creation(self):
        self.add(CmdCortexRoll)