"""
Organisation commands for managing noble houses, orders, guilds, etc.
"""
from evennia.commands.default.muxcommand import MuxCommand
from evennia import CmdSet
from evennia.utils.create import create_object
from evennia.utils.search import search_object
from evennia.utils.utils import inherits_from
from typeclasses.organisations import Organisation

class CmdOrg(MuxCommand):
    """
    View organisation information.
    
    Usage:
        org <organisation>
    """
    key = "org"
    help_category = "Organisations"
    
    def func(self):
        """Execute the command."""
        if not self.args:
            self.caller.msg("Usage: org <organisation>")
            return
            
        # Search for the organisation
        orgs = search_object(self.args, typeclass=Organisation)
        if not orgs:
            self.caller.msg(f"No organisation found matching '{self.args}'")
            return
            
        org = orgs[0]
        
        # Display organisation info
        self.caller.msg(f"\n{org.key}\n")
        self.caller.msg(f"\nDescription:\n{org.description}\n")
        
        # Get members sorted by rank
        members = org.get_members()
        if members:
            self.caller.msg("\nMembers:")
            for char, rank_num, rank_name in members:
                self.caller.msg(f"{char.key} - {rank_name}")
        else:
            self.caller.msg("\nNo members.")

        # Debug output
        self.caller.msg("\nDebug Information:")
        self.caller.msg(f"Organization Members: {org.db.members}")
        for char_id in org.db.members:
            char = org.search(char_id, global_search=True)
            if char:
                self.caller.msg(f"Character {char.key} Organizations: {char.db.organisations}")

class CmdOrgAdmin(MuxCommand):
    """
    Administer organisations.
    
    Usage:
        orgadmin/create <name>
        orgadmin/head <organisation> = <character>
        orgadmin/desc <organisation> = <description>
        orgadmin/secret <organisation> = <True/False>
        orgadmin/add <organisation> = <character>[,rank]
        orgadmin/remove <organisation> = <character>
        orgadmin/rank <organisation> = <character>,<rank>
        orgadmin/rankname <organisation> = <rank>,<name>
        orgadmin/delete <organisation>
    """
    key = "orgadmin"
    help_category = "Organisations"
    switch_options = ("create", "head", "desc", "secret", "remove", "rank", "rankname", "delete")
    
    def func(self):
        """Execute the command."""
        if not self.switches:
            self.caller.msg("Usage: orgadmin/<switch> <args>")
            return
            
        if not self.caller.check_permstring("Admin"):
            self.caller.msg("You don't have permission to use this command.")
            return
            
        try:
            if self.switches[0] == "create":
                self.create_org()
            elif self.switches[0] == "head":
                self.set_head()
            elif self.switches[0] == "desc":
                self.set_desc()
            elif self.switches[0] == "secret":
                self.set_secret()
            elif self.switches[0] == "remove":
                self.remove_member()
            elif self.switches[0] == "rank":
                self.set_rank()
            elif self.switches[0] == "rankname":
                self.set_rank_name()
            elif self.switches[0] == "delete":
                self.delete_org()
        except Exception as e:
            self.caller.msg(f"Error: {str(e)}")
    
    def create_org(self):
        """Create a new organisation."""
        if not self.args:
            self.caller.msg("Usage: orgadmin/create <name>")
            return
            
        # Check if org already exists
        existing = search_object(self.args, typeclass=Organisation)
        if existing:
            self.caller.msg(f"An organisation named '{self.args}' already exists.")
            return
            
        # Create the organisation
        org = create_object(typeclass="typeclasses.organisations.Organisation", key=self.args)
        self.caller.msg(f"Created organisation: {org.key}")
    
    def set_head(self):
        """Set the head of an organisation."""
        if not self.args or "=" not in self.args:
            self.caller.msg("Usage: orgadmin/head <organisation> = <character>")
            return
            
        org_name, char_name = [part.strip() for part in self.args.split("=", 1)]
        
        # Find the organisation
        orgs = search_object(org_name, typeclass=Organisation)
        if not orgs:
            self.caller.msg(f"No organisation found matching '{org_name}'")
            return
        org = orgs[0]
        
        # Find the character
        chars = search_object(char_name)
        if not chars:
            self.caller.msg(f"No character found matching '{char_name}'")
            return
        char = chars[0]
        
        # Set the head
        org.head = char
        self.caller.msg(f"Set {char.key} as head of {org.key}")
    
    def set_desc(self):
        """Set an organisation's description."""
        if not self.args or "=" not in self.args:
            self.caller.msg("Usage: orgadmin/desc <organisation> = <description>")
            return
            
        org_name, desc = [part.strip() for part in self.args.split("=", 1)]
        
        # Find the organisation
        orgs = search_object(org_name, typeclass=Organisation)
        if not orgs:
            self.caller.msg(f"No organisation found matching '{org_name}'")
            return
        org = orgs[0]
        
        # Set the description
        org.description = desc
        self.caller.msg(f"Updated description for {org.key}")
    
    def set_secret(self):
        """Set an organisation's secret status."""
        if not self.args or "=" not in self.args:
            self.caller.msg("Usage: orgadmin/secret <organisation> = <True/False>")
            return
            
        org_name, value = [part.strip() for part in self.args.split("=", 1)]
        
        # Find the organisation
        orgs = search_object(org_name, typeclass=Organisation)
        if not orgs:
            self.caller.msg(f"No organisation found matching '{org_name}'")
            return
        org = orgs[0]
        
        # Set the secret status
        try:
            org.is_secret = value.lower() == "true"
            self.caller.msg(f"Set {org.key} secret status to {org.is_secret}")
        except ValueError:
            self.caller.msg("Value must be 'True' or 'False'")
    
    def remove_member(self):
        """Remove a member from an organisation."""
        if not self.args or "=" not in self.args:
            self.caller.msg("Usage: orgadmin/remove <organisation> = <character>")
            return
            
        org_name, char_name = [part.strip() for part in self.args.split("=", 1)]
        
        # Find the organisation
        orgs = search_object(org_name, typeclass=Organisation)
        if not orgs:
            self.caller.msg(f"No organisation found matching '{org_name}'")
            return
        org = orgs[0]
        
        # Find the character
        chars = search_object(char_name)
        if not chars:
            self.caller.msg(f"No character found matching '{char_name}'")
            return
        char = chars[0]
        
        # Remove the member
        org.remove_member(char)
        self.caller.msg(f"Removed {char.key} from {org.key}")
    
    def set_rank(self):
        """Set a member's rank."""
        if not self.args or "=" not in self.args:
            self.caller.msg("Usage: orgadmin/rank <organisation> = <character>,<rank>")
            return
            
        org_name, rest = [part.strip() for part in self.args.split("=", 1)]
        
        # Parse character and rank
        if "," not in rest:
            self.caller.msg("Usage: orgadmin/rank <organisation> = <character>,<rank>")
            return
            
        char_name, rank = [part.strip() for part in rest.split(",", 1)]
        try:
            rank = int(rank)
        except ValueError:
            self.caller.msg("Rank must be a number between 1 and 10")
            return
        
        # Find the organisation
        orgs = search_object(org_name, typeclass=Organisation)
        if not orgs:
            self.caller.msg(f"No organisation found matching '{org_name}'")
            return
        org = orgs[0]
        
        # Find the character
        chars = search_object(char_name)
        if not chars:
            self.caller.msg(f"No character found matching '{char_name}'")
            return
        char = chars[0]
        
        # Set the rank
        try:
            org.set_rank(char, rank)
            rank_info = org.get_rank(char)
            self.caller.msg(f"Set {char.key}'s rank in {org.key} to {rank_info[1]}")
        except ValueError as e:
            self.caller.msg(str(e))

        # Debug output
        self.caller.msg("\nDebug Information:")
        self.caller.msg(f"Organization Members: {org.db.members}")
        self.caller.msg(f"Character {char.key} Organizations: {char.db.organisations}")
    
    def set_rank_name(self):
        """Set the name for a rank number."""
        if not self.args or "=" not in self.args:
            self.caller.msg("Usage: orgadmin/rankname <organisation> = <rank>,<name>")
            return
            
        org_name, rest = [part.strip() for part in self.args.split("=", 1)]
        
        # Parse rank and name
        if "," not in rest:
            self.caller.msg("Usage: orgadmin/rankname <organisation> = <rank>,<name>")
            return
            
        rank, name = [part.strip() for part in rest.split(",", 1)]
        try:
            rank = int(rank)
        except ValueError:
            self.caller.msg("Rank must be a number between 1 and 10")
            return
        
        # Find the organisation
        orgs = search_object(org_name, typeclass=Organisation)
        if not orgs:
            self.caller.msg(f"No organisation found matching '{org_name}'")
            return
        org = orgs[0]
        
        # Set the rank name
        try:
            org.set_rank_name(rank, name)
            self.caller.msg(f"Set rank {rank} in {org.key} to '{name}'")
        except ValueError as e:
            self.caller.msg(str(e))
            
    def delete_org(self):
        """Delete an organisation and clean up all references."""
        if not self.args:
            self.caller.msg("Usage: orgadmin/delete <organisation>")
            return

        # Find the organisation
        orgs = search_object(self.args, typeclass=Organisation)
        if not orgs:
            self.caller.msg(f"No organisation found matching '{self.args}'")
            return
        org = orgs[0]

        # Check for confirmation flag
        confirming = self.caller.db.org_delete_confirming
        if confirming and confirming == org.key:
            org.delete()
            self.caller.msg(f"Deleted organisation: {org.key}")
            del self.caller.db.org_delete_confirming
            return

        # First time: warn and set flag
        self.caller.msg(f"|yWARNING: This will delete {org.key} and remove all members. This cannot be undone!|n")
        self.caller.msg("|yType the same command again to confirm deletion.|n")
        self.caller.db.org_delete_confirming = org.key

class CmdClearOrgMemberships(MuxCommand):
    """
    Clear a character's organization memberships.
    
    Usage:
        clearorgs <character>
        
    Examples:
        clearorgs Bob     - Clear Bob's organization memberships
    """
    
    key = "clearorgs"
    help_category = "Organisations"
    
    def func(self):
        """Execute the command."""
        if not self.caller.check_permstring("Admin"):
            self.caller.msg("You don't have permission to use this command.")
            return
            
        if not self.args:
            self.caller.msg("Usage: clearorgs <character>")
            return
            
        char = self.caller.search(self.args)
        if not char:
            return
            
        if not hasattr(char, 'db.organisations'):
            self.caller.msg(f"{char.name} does not have any organization memberships.")
            return
            
        # Debug message before initialization
        self.caller.msg(f"Before initialization: {char.db.organisations}")
            
        # Ensure db.organisations is initialized
        if char.db.organisations is None:
            char.db.organisations = {}
            
        # Debug message after initialization
        self.caller.msg(f"After initialization: {char.db.organisations}")
            
        # Debug output
        self.caller.msg(f"\nDebug Information for {char.name}:")
        self.caller.msg(f"Current Organizations: {char.db.organisations}")
        self.caller.msg(f"Organization IDs: {list(char.db.organisations.keys())}")
        for org_id in char.db.organisations:
            org = char.search(org_id, global_search=True)
            self.caller.msg(f"Organization {org_id}: {'Found' if org else 'Not Found'}")
            
        # Clean up organization memberships for deleted organizations
        for org_id in list(char.db.organisations.keys()):
            org = char.search(org_id, global_search=True)
            if not org:
                del char.db.organisations[org_id]
            
        # Clear organization memberships
        char.db.organisations = {}
        self.caller.msg(f"Cleared organization memberships for {char.name}.")

class OrgCmdSet(CmdSet):
    """Command set for organisation commands."""
    key = "OrgCmdSet"
    
    def at_cmdset_creation(self):
        """Populate the command set."""
        self.add(CmdOrg())
        self.add(CmdOrgAdmin())
        self.add(CmdClearOrgMemberships()) 