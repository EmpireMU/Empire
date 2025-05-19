"""
Commands for managing organisations.
"""
from evennia.commands.default.muxcommand import MuxCommand
from evennia import CmdSet
from evennia.utils import evtable
from evennia.utils.utils import lazy_property
from evennia.utils.create import create_object

class CmdOrg(MuxCommand):
    """
    View information about an organisation.
    
    Usage:
        org <organisation>
        
    Shows public information about an organisation, including its description
    and member list (if not secret).
    """
    
    key = "org"
    locks = "cmd:all()"
    help_category = "Organisations"
    
    def func(self):
        """Display organisation information."""
        if not self.args:
            self.caller.msg("Usage: org <organisation>")
            return
            
        # Search for organisation by name (case-insensitive)
        from evennia.objects.models import ObjectDB
        orgs = ObjectDB.objects.filter(
            db_typeclass_path__contains="organisations.Organisation"
        )
        self.caller.msg(f"Debug: Found {orgs.count()} organisations")
        for o in orgs:
            self.caller.msg(f"Debug: {o.db_key} ({o.db_typeclass_path})")
            
        org = orgs.filter(db_key__iexact=self.args).first()
        
        if not org:
            self.caller.msg(f"Could not find organisation '{self.args}'.")
            return
            
        # Check if organisation is secret and viewer is neither staff nor member
        if org.is_secret and not self.caller.check_permstring("Builder"):
            # Check if caller is a member
            if not (hasattr(self.caller, 'db') and 
                   self.caller.db.organisations and 
                   org.id in self.caller.db.organisations):
                self.caller.msg("No such organisation exists.")
                return
            
        # Build the display
        display = [f"|c{org.name}|n\n"]
        
        # Description
        display.append(f"\n|wDescription:|n\n{org.description}\n")
        
        # Head
        if org.head:
            display.append(f"\n|wHead:|n {org.head.name}")
        
        # Members - only show if not secret or viewer is staff/member
        if not org.is_secret or self.caller.check_permstring("Builder"):
            members = org.get_members()
            if members:
                display.append("\n|wMembers:|n")
                table = evtable.EvTable(
                    "|wName|n",
                    "|wRank|n",
                    border="table",
                    width=78
                )
                for char, rank in sorted(members, key=lambda x: x[0].name):
                    table.add_row(char.name, rank or "Member")
                display.append(str(table))
        
        self.caller.msg("\n".join(display))

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
        orgadmin/addrank <organisation> = <rank_id>,<rank_name>
        orgadmin/removerank <organisation> = <rank_id>
    """
    
    key = "orgadmin"
    aliases = ["orga"]
    locks = "cmd:perm(Builder)"
    help_category = "Organisations"
    switch_options = ("create", "head", "desc", "secret", "add", "remove", "rank", "addrank", "removerank")
    
    def func(self):
        """Handle organisation administration."""
        if not self.args and not self.switches:
            self.caller.msg("Usage: orgadmin/[create|head|desc|secret|add|remove|rank|addrank|removerank]")
            return
            
        # Handle different switches
        try:
            if "create" in self.switches:
                self.create_org(self.args)
            elif "head" in self.switches:
                self.set_head(self.args)
            elif "desc" in self.switches:
                self.set_desc(self.args)
            elif "secret" in self.switches:
                self.set_secret(self.args)
            elif "add" in self.switches:
                self.add_member(self.args)
            elif "remove" in self.switches:
                self.remove_member(self.args)
            elif "rank" in self.switches:
                self.set_rank(self.args)
            elif "addrank" in self.switches:
                self.add_rank(self.args)
            elif "removerank" in self.switches:
                self.remove_rank(self.args)
            else:
                self.caller.msg("Invalid switch. See help orgadmin for usage.")
        except Exception as e:
            self.caller.msg(f"Error: {e}")
    
    def create_org(self, name):
        """Create a new organisation."""
        from typeclasses.organisations import Organisation
        from evennia.objects.models import ObjectDB
        
        # Check if organisation already exists by name and typeclass
        if ObjectDB.objects.filter(
            db_key__iexact=name,
            db_typeclass_path__contains="organisations.Organisation"
        ).exists():
            self.caller.msg(f"An organisation named {name} already exists.")
            return
            
        # Create the organisation
        org = create_object(
            typeclass="typeclasses.organisations.Organisation",
            key=name
        )
        self.caller.msg(f"Created organisation: {name}")
    
    def set_head(self, args):
        """Set the head of an organisation."""
        org_name, char_name = args.split("=", 1)
        org = self.caller.search(org_name.strip(), global_search=True)
        if not org:
            return
            
        char = self.caller.search(char_name.strip(), global_search=True)
        if not char:
            return
            
        org.head = char
        self.caller.msg(f"Set {char.name} as head of {org.name}")
    
    def set_desc(self, args):
        """Set an organisation's description."""
        org_name, desc = args.split("=", 1)
        org = self.caller.search(org_name.strip(), global_search=True)
        if not org:
            return
            
        org.description = desc.strip()
        self.caller.msg(f"Updated description for {org.name}")
    
    def set_secret(self, args):
        """Set an organisation's secret status."""
        org_name, value = args.split("=", 1)
        org = self.caller.search(org_name.strip(), global_search=True)
        if not org:
            return
            
        try:
            is_secret = value.strip().lower() == "true"
            org.is_secret = is_secret
            self.caller.msg(f"Set {org.name} secret status to {is_secret}")
        except ValueError:
            self.caller.msg("Value must be True or False")
    
    def add_member(self, args):
        """Add a member to an organisation."""
        org_name, char_info = args.split("=", 1)
        org = self.caller.search(org_name.strip(), global_search=True)
        if not org:
            return
            
        # Parse character and optional rank
        parts = char_info.split(",", 1)
        char_name = parts[0].strip()
        rank = parts[1].strip() if len(parts) > 1 else None
        
        char = self.caller.search(char_name, global_search=True)
        if not char:
            return
            
        org.add_member(char, rank)
        self.caller.msg(f"Added {char.name} to {org.name}")
    
    def remove_member(self, args):
        """Remove a member from an organisation."""
        org_name, char_name = args.split("=", 1)
        org = self.caller.search(org_name.strip(), global_search=True)
        if not org:
            return
            
        char = self.caller.search(char_name.strip(), global_search=True)
        if not char:
            return
            
        org.remove_member(char)
        self.caller.msg(f"Removed {char.name} from {org.name}")
    
    def set_rank(self, args):
        """Set a member's rank in an organisation."""
        org_name, char_info = args.split("=", 1)
        org = self.caller.search(org_name.strip(), global_search=True)
        if not org:
            return
            
        char_name, rank = char_info.split(",", 1)
        char = self.caller.search(char_name.strip(), global_search=True)
        if not char:
            return
            
        org.set_rank(char, rank.strip())
        self.caller.msg(f"Set {char.name}'s rank in {org.name} to {rank.strip()}")
    
    def add_rank(self, args):
        """Add a rank to an organisation."""
        org_name, rank_info = args.split("=", 1)
        org = self.caller.search(org_name.strip(), global_search=True)
        if not org:
            return
            
        rank_id, rank_name = rank_info.split(",", 1)
        org.add_rank(rank_id.strip(), rank_name.strip())
        self.caller.msg(f"Added rank {rank_name.strip()} to {org.name}")
    
    def remove_rank(self, args):
        """Remove a rank from an organisation."""
        org_name, rank_id = args.split("=", 1)
        org = self.caller.search(org_name.strip(), global_search=True)
        if not org:
            return
            
        org.remove_rank(rank_id.strip())
        self.caller.msg(f"Removed rank {rank_id.strip()} from {org.name}")

class OrgCmdSet(CmdSet):
    """Command set for organisation commands."""
    
    def at_cmdset_creation(self):
        """Add commands to the set."""
        self.add(CmdOrg())
        self.add(CmdOrgAdmin()) 