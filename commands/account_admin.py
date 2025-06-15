"""
Staff commands for account management.
"""

from evennia.commands.default.muxcommand import MuxCommand
from evennia.accounts.accounts import AccountDB
from evennia import create_account, create_object
from evennia.utils import create
from django.conf import settings

class CmdCreatePlayerAccount(MuxCommand):
    """
    Create a new player account and character.
    
    Usage:
        @createplayer <n> = <password>
        
    Creates a new player account and an associated character of the same name.
    This command is staff-only and is used to create pre-made characters for
    the roster system.
    
    The account and character will be created with the same name, and the
    character will be automatically linked to the account.
    """
    
    key = "@createplayer"
    locks = "cmd:perm(Admin)"
    help_category = "Admin"
    
    def func(self):
        """
        Execute the command.
        """
        caller = self.caller
        
        if not self.args or "=" not in self.args:
            caller.msg("Usage: @createplayer <n> = <password>")
            return
            
        name, password = [part.strip() for part in self.args.split("=", 1)]
        
        # Validate the name
        if not name or len(name) < 3:
            caller.msg("Name must be at least 3 characters long.")
            return
            
        # Check if account already exists
        if AccountDB.objects.filter(username__iexact=name).exists():
            caller.msg(f"An account with the name '{name}' already exists.")
            return
            
        # Create the account
        try:
            account = create.create_account(
                name, 
                email="", 
                password=password,
                permissions=["Player"],
                typeclass=settings.BASE_ACCOUNT_TYPECLASS
            )
            
            # Create the character with the same name
            char = create.create_object(
                settings.BASE_CHARACTER_TYPECLASS,
                key=name,
                location=caller.location,
                home=caller.location
            )
            
            # Link character to account
            account.db._playable_characters.append(char)
            char.db.account = account
            
            # Set this as the default puppet for the account
            account.db._last_puppet = char
            
            # Set proper locks for the character
            # This matches the format from the working character:
            # call:false(); control:perm(Developer); delete:id(X) or perm(Admin);
            # drop:holds(); edit:pid(X) or perm(Admin); examine:perm(Builder);
            # get:false(); puppet:id(Y) or pid(X) or perm(Developer) or pperm(Developer);
            # teleport:perm(Admin); teleport_here:perm(Admin); tell:perm(Admin); view:all()
            char.locks.add(
                f"call:false();"
                f"control:perm(Developer);"
                f"delete:perm(Developer);"
                f"drop:holds();"
                f"edit:perm(Admin);"
                f"examine:perm(Builder);"
                f"get:false();"
                f"puppet:id({char.id}) or pid({account.id}) or perm(Developer) or pperm(Developer);"
                f"teleport:perm(Admin);"
                f"teleport_here:perm(Admin);"
                f"tell:perm(Admin);"
                f"view:all()"
            )
            
            caller.msg(f"Created account and character '{name}'.")
            
        except Exception as e:
            caller.msg(f"Error creating account: {e}")
            # Clean up if character was created but account failed
            if 'char' in locals():
                char.delete()
            return 