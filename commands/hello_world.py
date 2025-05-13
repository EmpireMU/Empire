from evennia import Command
from evennia import CmdSet
from evennia import default_cmds


class CmdHelloWorld(Command):
    
    key = "hello"

    def func(self):
        caller = self.caller
        location = caller.location
        message = "Hello World!"
        location.msg_contents(message)
        return
    

class HelloWorldCmdSet(CmdSet):
    def at_cmdset_creation(self):
        self.add(CmdHelloWorld)