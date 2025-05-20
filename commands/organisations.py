"""
Organization commands for managing organizations and their members.
"""

from evennia.commands.default.muxcommand import MuxCommand
from evennia import CmdSet, create_object
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
        org/delete <organization>             - Delete organization (Staff only)
        
    Examples:
        org House Otrese
        org/create House Anadun
        org/member House Otrese = Koline,3    - Add Koline as Noble Family
        org/member House Otrese = Koline,2    - Promote Koline to Minister
        org/remove House Otrese = Koline
        org/rankname House Otrese = 5,Knight
        org/delete House Otrese               - Delete the organization
    """
    
    key = "org"
    locks = "cmd:all()"
    help_category = "Organizations"
    switch_options = ("create", "member", "remove", "rankname", "delete")
    
    # Permission and validation helpers
    def _check_admin(self):
        """Helper method to check admin permissions."""
        if not self.caller.check_permstring("Admin"):
            self.msg("You don't have permission to perform this action.")
            return False
        return True
        
    def _validate_rank(self, rank_str, default=None):
        """Helper method to validate rank numbers."""
        try:
            rank = int(rank_str)
            if not 1 <= rank <= 10:
                self.msg("Rank must be a number between 1 and 10.")
                return None
            return rank
        except (ValueError, TypeError):
            if default is not None:
                return default
            self.msg("Rank must be a number between 1 and 10.")
            return None
            
    # Object search helpers
    def _get_org(self, org_name):
        """Helper method to find and validate an organization."""
        org = self.caller.search(org_name, global_search=True)
        if not org:
            return None
            
        if not isinstance(org, Organisation):
            self.msg(f"{org.name} is not an organization.")
            return None
            
        return org
        
    def _get_character(self, char_name):
        """Helper method to find a character."""
        char = self.caller.search(char_name, global_search=True)
        if not char:
            return None
        return char
        
    def _get_org_and_char(self, org_name, char_name):
        """Helper method to find both an organization and a character."""
        org = self._get_org(org_name)
        if not org:
            return None, None
            
        char = self._get_character(char_name)
        if not char:
            return org, None
            
        return org, char
        
    # Argument parsing helpers
    def _parse_equals(self, usage_msg):
        """Helper method to parse = separated arguments."""
        if "=" not in self.args:
            self.msg(f"Usage: {usage_msg}")
            return None, None
        return [part.strip() for part in self.args.split("=", 1)]
        
    def _parse_comma(self, text, expected_parts=2, usage_msg=None):
        """Helper method to parse comma-separated arguments."""
        try:
            parts = [part.strip() for part in text.split(",", expected_parts - 1)]
            if len(parts) != expected_parts:
                if usage_msg:
                    self.msg(f"Usage: {usage_msg}")
                return None
            return parts
        except (ValueError, IndexError):
            if usage_msg:
                self.msg(f"Usage: {usage_msg}")
            return None
            
    # Member management helpers
    def _is_member(self, org, char):
        """Helper method to check if a character is a member of an organization."""
        return org.get_member_rank(char) is not None
        
    def _update_member_rank(self, org, char, rank):
        """Helper method to update a member's rank."""
        if org.set_rank(char, rank):
            self.msg(f"Changed {char.name}'s rank to '{org.get_member_rank_name(char)}'.")
            return True
        self.msg(f"Failed to set rank. Make sure the rank (1-10) is valid.")
        return False
        
    def _add_new_member(self, org, char, rank):
        """Helper method to add a new member to an organization."""
        if org.add_member(char, rank):
            self.msg(f"Added {char.name} to '{org.name}' as '{org.get_member_rank_name(char)}'.")
            return True
        self.msg(f"Failed to add member. Make sure the rank (1-10) is valid.")
        return False
        
    # Main command methods
    def func(self):
        """Execute the command."""
        if not self.args:
            self.msg("Usage: org <organization>")
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
            elif self.switches[0] == "delete":
                self.delete_org()
            return
            
        # Default: show organization info
        self.show_org_info()
        
    def at_post_cmd(self):
        """Clean up any temporary attributes."""
        # Only clean up if the command wasn't successful
        if hasattr(self.caller, 'db') and hasattr(self.caller.db, 'delete_org_confirming'):
            if not self.caller.db.delete_org_confirming:
                del self.caller.db.delete_org_confirming
        
    def create_org(self):
        """Create a new organization."""
        if not self.args:
            self.msg("Usage: org/create <name>")
            return
            
        if not self.caller.check_permstring("Admin"):
            self.msg("You don't have permission to create organizations.")
            return
            
        # Create the organization
        try:
            org = create_object(
                typeclass=Organisation,
                key=self.args,
                location=self.caller.location,
                home=self.caller.location
            )
            if org:
                self.msg(f"Created organization: {org.name}")
            else:
                self.msg("Failed to create organization.")
        except Exception as e:
            self.msg(f"Error creating organization: {e}")
            
    def delete_org(self):
        """Delete an organization."""
        if not self._check_admin():
            return
            
        # Find the organization
        org = self._get_org(self.args)
        if not org:
            return
            
        # Check if this is a confirmation
        confirming = self.caller.db.delete_org_confirming
        if confirming:
            # Delete the organization
            name = org.name
            org.delete()
            self.msg(f"Deleted organization: {name}")
            del self.caller.db.delete_org_confirming
            return
            
        # First time through - ask for confirmation
        self.msg(f"|yWARNING: This will delete the organization '{org.name}' and remove all member references.|n")
        self.msg("|yThis action cannot be undone. Type 'org/delete' again to confirm.|n")
        self.caller.db.delete_org_confirming = True
        
    def manage_member(self):
        """Add or update a member's rank."""
        if not self._check_admin():
            return
            
        # Parse arguments
        parts = self._parse_equals("org/member <organization> = <character>[,rank]")
        if not parts:
            return
        org_name, rest = parts
        
        # Parse character and optional rank
        char_name, *rank_parts = [part.strip() for part in rest.split(",", 1)]
        rank = self._validate_rank(rank_parts[0] if rank_parts else "4", default=4)
        if rank is None:
            return
            
        # Find the organization and character
        org, char = self._get_org_and_char(org_name, char_name)
        if not org or not char:
            return
            
        # Check if already a member
        if self._is_member(org, char):
            self._update_member_rank(org, char, rank)
        else:
            self._add_new_member(org, char, rank)
            
    def remove_member(self):
        """Remove a member from an organization."""
        if not self._check_admin():
            return
            
        # Parse arguments
        parts = self._parse_equals("org/remove <organization> = <character>")
        if not parts:
            return
        org_name, char_name = parts
        
        # Find the organization and character
        org, char = self._get_org_and_char(org_name, char_name)
        if not org or not char:
            return
            
        # Check if member
        if not self._is_member(org, char):
            self.msg(f"{char.name} is not a member of '{org.name}'.")
            return
            
        # Remove member
        if org.remove_member(char):
            self.msg(f"Removed {char.name} from '{org.name}'.")
        else:
            self.msg("Failed to remove member. This should not happen - please report this error.")
            
    def set_rank_name(self):
        """Set the name for a rank."""
        if not self._check_admin():
            return
            
        # Parse arguments
        parts = self._parse_equals("org/rankname <organization> = <rank>,<name>")
        if not parts:
            return
        org_name, rest = parts
        
        # Parse rank and name
        rank_parts = self._parse_comma(rest, 2, "org/rankname <organization> = <rank>,<name>")
        if not rank_parts:
            return
            
        rank = self._validate_rank(rank_parts[0])
        if rank is None:
            return
            
        # Find the organization
        org = self._get_org(org_name)
        if not org:
            return
            
        # Set rank name
        if org.set_rank_name(rank, rank_parts[1]):
            self.msg(f"Set rank {rank} to '{rank_parts[1]}' in '{org.name}'.")
        else:
            self.msg("Failed to set rank name.")
            
    def show_org_info(self):
        """Show organization information."""
        # Find the organization
        org = self._get_org(self.args)
        if not org:
            return
            
        # Get members
        members = list(org.get_members())
        if not members:
            self.msg(f"\n|y{org.name}|n")
            self.msg(f"Description: {org.db.description}")
            self.msg("\nThis organization has no members.")
            return
            
        # Create info table
        table = evtable.EvTable(
            "|wName|n",
            "|wRank|n",
            border="table",
            width=78
        )
        
        # Add members
        for member, rank_num, rank_name in members:
            table.add_row(member.name, rank_name)
            
        # Show info
        self.msg(f"\n|y{org.name}|n")
        self.msg(f"Description: {org.db.description}")
        self.msg(f"\nMembers ({len(members)}):")
        self.msg(str(table))


class CmdResource(MuxCommand):
    """
    View and manage resources.
    
    Usage:
        resource [<name>]                    - View resource info or list all owned
        resource/org <org> = <name>,<die_size>  - Create resource for an organization
        resource/char <char> = <name>,<die_size>  - Create resource for a character
        resource/transfer <name> = <target>  - Transfer resource to target
        
    Examples:
        resource                          - List all resources you own
        resource House Guard              - View details of House Guard resource
        resource/org HouseOtrese = Guard Pool,8    - Create d8 resource for org
        resource/org "House Otrese" = "Guard Pool",8  - Names with spaces need quotes
        resource/char Koline = "Personal Guard",6  - Create d6 resource for character
        resource/transfer Guard = Koline  - Transfer to character Koline
        
    When multiple resources share the same name, you can specify which one
    by including a number after the name:
        resource "Political Capital 2"
        resource/transfer "Wealth 3" = "House Anadun"
    """
    
    key = "resource"
    aliases = ["res"]
    locks = "cmd:all()"
    help_category = "Resources"
    
    def _get_org(self, org_name):
        """Helper method to find and validate an organization."""
        from typeclasses.organisations import Organisation
        org = self.caller.search(org_name, global_search=True)
        if not org:
            return None
            
        if not isinstance(org, Organisation):
            self.msg(f"{org.name} is not an organization.")
            return None
            
        return org
        
    def _get_char(self, char_name):
        """Helper method to find and validate a character."""
        from typeclasses.characters import Character
        char = self.caller.search(char_name, global_search=True)
        if not char:
            return None
            
        if not hasattr(char, 'char_resources'):
            self.msg(f"{char.name} cannot own resources.")
            return None
            
        return char
        
    def func(self):
        """Handle resource management."""
        if not self.args and not self.switches:
            # List all owned resources
            self.list_resources()
            return
            
        if not self.switches:
            # View specific resource
            self.view_resource()
            return
            
        # Handle switches
        switch = self.switches[0]
        
        if switch == "org":
            self.create_org_resource()
        elif switch == "char":
            self.create_char_resource()
        elif switch == "transfer":
            self.transfer_resource()
        else:
            self.msg(f"Unknown switch: {switch}")
            
    def list_resources(self):
        """List all resources owned by the caller."""
        owner = self.caller
        if hasattr(self.caller, 'char'):
            owner = self.caller.char
            
        # Get resources from trait handler
        resources = None
        if hasattr(owner, 'char_resources') and owner.char_resources:
            resources = owner.char_resources.traits
        elif hasattr(owner, 'org_resources') and owner.org_resources:
            resources = owner.org_resources.traits
            
        if not resources:
            self.msg("You don't own any resources.")
            return
            
        # Create table
        from evennia.utils.evtable import EvTable
        table = EvTable(
            "|wName|n",
            "|wDie|n",
            border="table",
            width=78
        )
        
        # Add rows
        for name, trait in sorted(resources.items()):
            table.add_row(name, f"d{trait.current}")
            
        self.msg(f"|wYour Resources:|n\n{table}")
        
    def view_resource(self):
        """View details of a specific resource."""
        if not self.args:
            self.msg("Usage: resource <n>")
            return
            
        owner = self.caller
        if hasattr(self.caller, 'char'):
            owner = self.caller.char
            
        # Get resources from trait handler
        resources = None
        if hasattr(owner, 'char_resources') and owner.char_resources:
            resources = owner.char_resources.traits
        elif hasattr(owner, 'org_resources') and owner.org_resources:
            resources = owner.org_resources.traits
            
        if not resources:
            self.msg("You don't own any resources.")
            return
            
        name = self.args.strip()
        if name not in resources:
            self.msg(f"No resource found named '{name}'.")
            return
            
        die_size = resources[name].current
        self.msg(f"|c{name}|n\nA d{die_size} resource owned by {owner.name}.")
        
    def create_org_resource(self):
        """Create a new resource for an organization."""
        if not self.args or "=" not in self.args:
            self.msg("Usage: resource/org <org> = <name>,<die_size>")
            return
            
        # Check admin permissions
        if not self.caller.check_permstring("Admin"):
            self.msg("You don't have permission to create resources.")
            return
            
        # Parse org name and resource details
        org_name, rest = [part.strip() for part in self.args.split("=", 1)]
        
        # Parse resource name and die size
        try:
            name, die_size = [part.strip() for part in rest.split(",", 1)]
            die_size = int(die_size)
        except ValueError:
            self.msg("Usage: resource/org <org> = <name>,<die_size>")
            self.msg("Die size must be a number (4, 6, 8, 10, or 12).")
            return
            
        # Find the organization
        org = self._get_org(org_name)
        if not org:
            return
            
        # Create the resource
        try:
            org.add_org_resource(name, die_size)
            self.msg(f"Created resource: {name} (d{die_size}) for {org.name}")
        except ValueError as e:
            self.msg(str(e))
            
    def create_char_resource(self):
        """Create a new resource for a character."""
        if not self.args or "=" not in self.args:
            self.msg("Usage: resource/char <character> = <name>,<die_size>")
            return
            
        # Check admin permissions
        if not self.caller.check_permstring("Admin"):
            self.msg("You don't have permission to create resources.")
            return
            
        # Parse character name and resource details
        char_name, rest = [part.strip() for part in self.args.split("=", 1)]
        
        # Parse resource name and die size
        try:
            name, die_size = [part.strip() for part in rest.split(",", 1)]
            die_size = int(die_size)
        except ValueError:
            self.msg("Usage: resource/char <character> = <name>,<die_size>")
            self.msg("Die size must be a number (4, 6, 8, 10, or 12).")
            return
            
        # Find the character
        char = self._get_char(char_name)
        if not char:
            return
            
        # Create the resource
        try:
            char.add_resource(name, die_size)
            self.msg(f"Created resource: {name} (d{die_size}) for {char.name}")
        except ValueError as e:
            self.msg(str(e))
            
    def transfer_resource(self):
        """Transfer a resource to another character or organization."""
        if not self.args or "=" not in self.args:
            self.msg("Usage: resource/transfer <name> = <target>")
            return
            
        name, target = [part.strip() for part in self.args.split("=", 1)]
        
        # Find target
        from evennia.utils.search import search_object
        targets = search_object(target)
        if not targets:
            self.msg(f"Target '{target}' not found.")
            return
            
        target = targets[0]
        
        # Get owner
        owner = self.caller
        if hasattr(self.caller, 'char'):
            owner = self.caller.char
            
        try:
            owner.transfer_resource(name, target)
            self.msg(f"Transferred {name} to {target.name}.")
        except ValueError as e:
            self.msg(str(e))


class OrgCmdSet(CmdSet):
    """
    Command set for organization management.
    """
    
    def at_cmdset_creation(self):
        """Add commands to the set."""
        self.add(CmdOrg())
        self.add(CmdResource())  # Add resource management commands 