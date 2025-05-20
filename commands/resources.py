"""
Resource commands for managing organization and character resources.
"""

from evennia.commands.default.muxcommand import MuxCommand
from evennia import CmdSet
from evennia.utils.search import search_object
from evennia.utils.evtable import EvTable


class CmdResource(MuxCommand):
    """
    View and manage resources.
    
    Usage:
        resource [<name>]                    - View resource info or list all owned
        resource/create <name> = <die_size>  - Create new resource (Staff/Org only)
        resource/transfer <name> = <target>  - Transfer resource to target
        resource/delete <name>               - Delete resource (Staff only)
        
    When multiple resources share the same name, you can specify which one
    by including the owner's name in brackets:
        resource "Political Capital [House Otrese]"
        resource/transfer "Wealth [Koline]" = "House Anadun"
        
    Examples:
        resource                          - List all resources you own
        resource House Guard              - View details of House Guard resource
        resource/create Guard Pool = 8    - Create d8 resource named "Guard Pool"
        resource/transfer Guard = Koline  - Transfer to character Koline
        resource/delete Guard             - Delete the resource
    """
    
    key = "resource"
    aliases = ["res"]
    locks = "cmd:all()"
    help_category = "Resources"
    
    def parse_resource_name(self, name):
        """
        Parse a resource name that might include owner specification.
        
        Args:
            name (str): Resource name, optionally with [owner] suffix
            
        Returns:
            tuple: (base_name, owner_name or None)
        """
        name = name.strip()
        if '[' in name and name.endswith(']'):
            base_name, owner_part = name.rsplit('[', 1)
            owner_name = owner_part[:-1].strip()  # Remove the closing bracket
            return base_name.strip(), owner_name
        return name, None
        
    def find_resources(self, name):
        """
        Find all resources matching a name, optionally filtered by owner.
        
        Args:
            name (str): Resource name to search for, optionally with [owner]
            
        Returns:
            list: List of matching resources
        """
        base_name, owner_name = self.parse_resource_name(name)
        
        # Search for resources with this name
        resources = search_object(base_name, typeclass="typeclasses.resources.Resource")
        if not resources:
            self.caller.msg(f"No resource found named '{base_name}'.")
            return []
            
        # If owner specified, filter by owner
        if owner_name:
            owners = search_object(owner_name)
            if not owners:
                self.caller.msg(f"No owner found named '{owner_name}'.")
                return []
            owner = owners[0]
            resources = [r for r in resources if r.owner == owner]
            if not resources:
                self.caller.msg(f"No resource named '{base_name}' owned by {owner_name}.")
                return []
                
        return resources
        
    def show_resource_list(self, resources, title=None):
        """
        Show a list of resources in a table format.
        
        Args:
            resources (list): List of resources to show
            title (str, optional): Title for the table
        """
        table = EvTable(
            "|wName|n",
            "|wOwner|n",
            "|wDie|n",
            border="table",
            width=78
        )
        
        # Group by name, owner, and die size
        resource_groups = {}
        for res in resources:
            key = (res.name, res.owner.dbref if res.owner else None, res.die_size)
            if key not in resource_groups:
                resource_groups[key] = []
            resource_groups[key].append(res)
            
        # Add rows
        for (name, owner_dbref, die_size), group in sorted(resource_groups.items()):
            owner_name = group[0].owner.name if group[0].owner else "No owner"
            count = len(group)
            if count > 1:
                table.add_row(
                    f"{name} (x{count})",
                    owner_name,
                    f"d{die_size}"
                )
            else:
                table.add_row(
                    name,
                    owner_name,
                    f"d{die_size}"
                )
                
        if title:
            self.caller.msg(f"\n{title}")
        self.caller.msg(str(table))
        
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
        
        if switch == "create":
            self.create_resource()
        elif switch == "transfer":
            self.transfer_resource()
        elif switch == "delete":
            self.delete_resource()
        else:
            self.caller.msg(f"Unknown switch: {switch}")
            
    def list_resources(self):
        """List all resources owned by the caller."""
        owner = self.caller
        if hasattr(self.caller, 'char'):
            owner = self.caller.char
            
        resources = owner.resources
        if not resources:
            self.caller.msg("You don't own any resources.")
            return
            
        self.show_resource_list(resources, "|wYour Resources:|n")
        
    def view_resource(self):
        """View details of a specific resource."""
        if not self.args:
            self.caller.msg("Usage: resource <name>")
            return
            
        resources = self.find_resources(self.args)
        if not resources:
            return
            
        if len(resources) == 1:
            self.caller.msg(resources[0].return_appearance(self.caller))
        else:
            self.show_resource_list(resources, f"Resources named '{self.args}':")
            self.caller.msg("\nSpecify which one using [owner] after the name:")
            self.caller.msg(f'resource "{resources[0].name} [Owner Name]"')
        
    def create_resource(self):
        """Create a new resource."""
        if not self.args or "=" not in self.args:
            self.caller.msg("Usage: resource/create <name> = <die_size>")
            return
            
        # Check permissions - only staff and organizations can create
        if not self.caller.check_permstring("Builder"):
            if not hasattr(self.caller, "create_resource"):
                self.caller.msg("You don't have permission to create resources.")
                return
                
        name, die_size = [part.strip() for part in self.args.split("=", 1)]
        
        try:
            die_size = int(die_size)
        except ValueError:
            self.caller.msg("Die size must be a number (4, 6, 8, 10, or 12).")
            return
            
        # Create through organization if possible
        if hasattr(self.caller, "create_resource"):
            resource = self.caller.create_resource(name, die_size)
        else:
            # Staff creating directly
            from evennia.utils.create import create_object
            from typeclasses.resources import Resource
            
            resource = create_object(
                typeclass=Resource,
                key=name,
                location=self.caller.location
            )
            if resource:
                try:
                    resource.die_size = die_size
                    resource.set_owner(self.caller)
                except ValueError as e:
                    resource.delete()
                    self.caller.msg(str(e))
                    return
                    
        if resource:
            self.caller.msg(f"Created resource: {resource.name} (d{resource.die_size})")
        else:
            self.caller.msg("Failed to create resource.")
            
    def transfer_resource(self):
        """Transfer a resource to another character or organization."""
        if not self.args or "=" not in self.args:
            self.caller.msg("Usage: resource/transfer <name> = <target>")
            return
            
        name, target = [part.strip() for part in self.args.split("=", 1)]
        
        resources = self.find_resources(name)
        if not resources:
            return
            
        # If multiple resources found, show list and ask for specification
        if len(resources) > 1:
            self.show_resource_list(resources, f"Multiple resources found named '{name}':")
            self.caller.msg("\nSpecify which one using [owner] after the name:")
            self.caller.msg(f'resource/transfer "{name} [Owner Name]" = {target}')
            return
            
        resource = resources[0]
            
        # Check ownership
        owner = self.caller
        if hasattr(self.caller, 'char'):
            owner = self.caller.char
            
        if resource.owner != owner and not self.caller.check_permstring("Builder"):
            self.caller.msg("You don't own that resource.")
            return
            
        # Find target
        targets = search_object(target)
        if not targets:
            self.caller.msg(f"Target '{target}' not found.")
            return
            
        target = targets[0]
        
        # Handle transfer through organization if applicable
        if hasattr(owner, "transfer_resource"):
            success = owner.transfer_resource(resource, target)
        else:
            # Direct transfer
            resource.set_owner(target, transfer_from=owner)
            success = True
            
        if success:
            self.caller.msg(f"Transferred {resource.name} to {target.name}.")
        else:
            self.caller.msg("Failed to transfer resource.")
            
    def delete_resource(self):
        """Delete a resource."""
        if not self.args:
            self.caller.msg("Usage: resource/delete <name>")
            return
            
        # Only staff can delete resources
        if not self.caller.check_permstring("Builder"):
            self.caller.msg("You don't have permission to delete resources.")
            return
            
        resources = self.find_resources(self.args)
        if not resources:
            return
            
        # If multiple resources found, show list and ask for specification
        if len(resources) > 1:
            self.show_resource_list(resources, f"Multiple resources found named '{self.args}':")
            self.caller.msg("\nSpecify which one using [owner] after the name:")
            self.caller.msg(f'resource/delete "{self.args} [Owner Name]"')
            return
            
        resource = resources[0]
        name = resource.name
        resource.delete()
        self.caller.msg(f"Deleted resource: {name}")


class ResourceCmdSet(CmdSet):
    """
    Command set for resource management.
    """
    
    def at_cmdset_creation(self):
        """Add commands to the set."""
        self.add(CmdResource()) 