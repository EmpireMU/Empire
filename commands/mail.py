"""
Custom mail commands for the game.
"""

from evennia.contrib.game_systems.mail.mail import CmdMailCharacter
from evennia.utils import crop, list_to_string

class CmdMailCharacter(CmdMailCharacter):
    """
    Send mail to other characters in the game.

    Usage:
        mail                            - List all messages
        mail <character> = <title>/<message>    - Send a new message
        mail/read <number>             - Read message <number>
        mail/delete <number>           - Delete message <number>
        mail/forward <number> = <target> - Forward message <number> to <target>
        mail/reply <number> = <title>/<message> - Reply to message <number>
        mail/ooc <character> = <title>/<message> - Send an OOC message (marked in yellow)

    The mail system allows you to send messages to other characters,
    even when they are offline. Each message includes a sender, 
    recipient, subject and message body.

    Adding /ooc to your mail will mark it as out-of-character 
    communication.
    """

    def func(self):
        """Implement function"""
        if "ooc" in self.switches:
            if not self.args or not self.rhs:
                self.caller.msg("Usage: mail/ooc <character> = <title>/<message>")
                return
                
            if "/" not in self.rhs:
                self.caller.msg("Usage: mail/ooc <character> = <title>/<message>")
                return
                
            recipient = self.lhs.strip()
            title, message = self.rhs.split("/", 1)
            
            # Add OOC marker and color to title
            title = f"|y(OOC)|n {title.strip()}"
            
            # Try to send the message
            r = self.get_recipient(recipient)
            if not r:
                self.caller.msg(f"Could not find '{recipient}'.")
                return
                
            if not r.access(self.caller, "mail"):
                self.caller.msg(f"You are not allowed to send mail to '{r}'.")
                return
                
            # Create and send the message
            super().create_message(self.caller, r, message.strip(), title=title)
            self.caller.msg(f"Mail sent to {r}: {title} - {message}")
            if hasattr(r, "msg") and r.has_account:
                r.msg(f"New mail from {self.caller}: {title}")
            return
            
        # For all other cases, use parent class behavior
        super().func() 