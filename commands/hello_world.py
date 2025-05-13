from evennia import Command


class CmdHelloWorld(Command):
    
    key = "hello"

    def func(self):
        caller = self.caller
        location = self.location
        message = "Hello World!"
        location.msg_contents(message)
        return
    
