"""
Organization commands for managing organizations and their members.
"""

from evennia.commands.default.muxcommand import MuxCommand
from evennia import CmdSet
from evennia.utils import evtable
from evennia.utils.search import search_object
from typeclasses.organisations import Organisation


class CmdOrg(MuxCommand):
    """
    View and manage organizations.
    
    Usage:
        org <organization>                    - View organization info
        org/create <name>                     - Create new organization (Staff only)
        org/member <organization> = <character>[,rank] - Add/set member (Staff only)
        org/remove <organization> = <character> - Remove member (Staff only)
        org/rankname <organization> = <rank>,<name> - Set rank name (Staff only)
        
    Examples:
        org House Otrese
        org/create House Anadun
        org/member House Otrese = Koline,3    - Add Koline as Noble Family
        org/member House Otrese = Koline,2    - Promote Koline to Minister
        org/remove House Otrese = Koline
        org/rankname House Otrese = 5,Knight
    """
    
    key = "org"
    locks = "cmd:all()"
    help_category = "Organizations"
    switch_options = ("create", "member", "remove", "rankname")
    
    def func(self):
        """Execute the command."""
        if not self.args:
            self.caller.msg("Usage: org <organization>")
            return
            
        # Handle switches
        if self.switches:
            if self.switches[0] == "create":
                self.create_org()
            elif self.switches[0] == "member":
                self.manage_member()
            elif self.switches[0] == "remove":
                self.remove_member()
            elif self.switches[0] == "rankname":
                self.set_rank_name()
            return
            
        # Default: show organization info
        self.show_org_info()
        
    def create_org(self):
        """Create a new organization."""
        if not self.args:
            self.caller.msg("Usage: org/create <name>")
            return
            
        if not self.caller.check_permstring("Admin"):
            self.caller.msg("You don't have permission to create organizations.")
            return
            
        # Create the organization
        org = Organisation.objects.create(
            key=self.args,
            location=self.caller.location
        )
        
        self.caller.msg(f"Created organization: {org.name}")
        
    def manage_member(self):
        """Add or update a member's rank."""
        if not self.args or "=" not in self.args:
            self.caller.msg("Usage: org/member <organization> = <character>[,rank]")
            return
            
        if not self.caller.check_permstring("Admin"):
            self.caller.msg("You don't have permission to manage members.")
            return
            
        # Parse arguments
        org_name, rest = [part.strip() for part in self.args.split("=", 1)]
        
        # Parse character and optional rank
        if "," in rest:
            char_name, rank = [part.strip() for part in rest.split(",", 1)]
            try:
                rank = int(rank)
            except ValueError:
                self.caller.msg("Rank must be a number between 1 and 10.")
                return
        else:
            char_name = rest
            rank = 4  # Default to Senior Servant
            
        # Find the organization
        org = self.caller.search(org_name, global_search=True)
        if not org:
            return
            
        if not isinstance(org, Organisation):
            self.caller.msg(f"{org.name} is not an organization.")
            return
            
        # Find the character
        char = self.caller.search(char_name, global_search=True)
        if not char:
            return
            
        # Check if already a member
        current_rank = org.get_member_rank(char)
        if current_rank:
            # Update rank
            if org.set_rank(char, rank):
                self.caller.msg(f"Changed {char.name}'s rank to {org.get_member_rank_name(char)}.")
            else:
                self.caller.msg("Failed to set rank.")
        else:
            # Add new member
            if org.add_member(char, rank):
                self.caller.msg(f"Added {char.name} to {org.name} as {org.get_member_rank_name(char)}.")
            else:
                self.caller.msg("Failed to add member.")
            
    def remove_member(self):
        """Remove a member from an organization."""
        if not self.args or "=" not in self.args:
            self.caller.msg("Usage: org/remove <organization> = <character>")
            return
            
        if not self.caller.check_permstring("Admin"):
            self.caller.msg("You don't have permission to remove members.")
            return
            
        # Parse arguments
        org_name, char_name = [part.strip() for part in self.args.split("=", 1)]
        
        # Find the organization
        org = self.caller.search(org_name, global_search=True)
        if not org:
            return
            
        if not isinstance(org, Organisation):
            self.caller.msg(f"{org.name} is not an organization.")
            return
            
        # Find the character
        char = self.caller.search(char_name, global_search=True)
        if not char:
            return
            
        # Remove member
        if org.remove_member(char):
            self.caller.msg(f"Removed {char.name} from {org.name}.")
        else:
            self.caller.msg("Failed to remove member.")
            
    def set_rank_name(self):
        """Set the name for a rank."""
        if not self.args or "=" not in self.args:
            self.caller.msg("Usage: org/rankname <organization> = <rank>,<name>")
            return
            
        if not self.caller.check_permstring("Admin"):
            self.caller.msg("You don't have permission to set rank names.")
            return
            
        # Parse arguments
        org_name, rest = [part.strip() for part in self.args.split("=", 1)]
        
        # Parse rank and name
        if "," not in rest:
            self.caller.msg("Usage: org/rankname <organization> = <rank>,<name>")
            return
            
        rank, name = [part.strip() for part in rest.split(",", 1)]
        try:
            rank = int(rank)
        except ValueError:
            self.caller.msg("Rank must be a number between 1 and 10.")
            return
            
        # Find the organization
        org = self.caller.search(org_name, global_search=True)
        if not org:
            return
            
        if not isinstance(org, Organisation):
            self.caller.msg(f"{org.name} is not an organization.")
            return
            
        # Set rank name
        if org.set_rank_name(rank, name):
            self.caller.msg(f"Set rank {rank} to '{name}' in {org.name}.")
        else:
            self.caller.msg("Failed to set rank name.")
            
    def show_org_info(self):
        """Show organization information."""
        # Find the organization
        org = self.caller.search(self.args, global_search=True)
        if not org:
            return
            
        if not isinstance(org, Organisation):
            self.caller.msg(f"{org.name} is not an organization.")
            return
            
        # Create info table
        table = evtable.EvTable(
            "|wName|n",
            "|wRank|n",
            border="table",
            width=78
        )
        
        # Add members
        for member, rank_num, rank_name in org.get_members():
            table.add_row(member.name, rank_name)
            
        # Show info
        self.caller.msg(f"\n|y{org.name}|n")
        self.caller.msg(f"Description: {org.db.description}")
        self.caller.msg("\nMembers:")
        self.caller.msg(str(table))


class OrgCmdSet(CmdSet):
    """
    Command set for organization commands.
    """
    
    def at_cmdset_creation(self):
        """Add commands to the set."""
        self.add(CmdOrg()) 