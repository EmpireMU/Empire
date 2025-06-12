"""
Room management system.

This module contains commands for managing rooms, including ownership,
keys, and locking/unlocking exits.
"""

from evennia.commands.default.muxcommand import MuxCommand
from evennia.utils.search import search_object
from evennia.utils.utils import list_to_string
from utils.command_mixins import CharacterLookupMixin
from typeclasses.organisations import Organisation


class CmdRoomManagement(CharacterLookupMixin, MuxCommand):
    """
    Manage rooms and their exits
    
    Usage:
        room/owner <character/org>     - Add owner to current room
        room/unowner <character/org>   - Remove owner from current room
        room/owners                    - List current room's owners
        room/givekey <character>       - Give a key to current room
        room/removekey <character>     - Remove key from current room
        room/lock <exit>              - Lock an exit (must be owner)
        room/unlock <exit>            - Unlock an exit (must have key or be owner)
    """
    
    key = "room"
    locks = "cmd:all()"
    help_category = "Building"

    def _get_owner(self, owner_spec):
        """
        Helper method to find a character or organization.
        
        Usage: type:name
        Example: org:House Otrese or char:Bob
        """
        if not owner_spec or ":" not in owner_spec:
            self.msg("Usage: <type>:<n> where type is 'org' or 'char'")
            return None, None
            
        owner_type, name = owner_spec.split(":", 1)
        owner_type = owner_type.lower().strip()
        name = name.strip()
        
        if owner_type == "org":
            orgs = search_object(name, typeclass='typeclasses.organisations.Organisation')
            if not orgs:
                self.msg(f"Organization '{name}' not found.")
                return None, None
            return "org", orgs[0]
        elif owner_type == "char":
            char = self.find_character(name)
            if not char:
                return None, None
            return "char", char
        else:
            self.msg("Owner type must be 'org' or 'char'")
            return None, None

    def func(self):
        """Execute the command."""
        if not self.switches:
            self.msg("You must use a switch. See help room for usage.")
            return
            
        switch = self.switches[0]
        
        if switch in ["owner", "unowner"]:
            if not self.args:
                self.msg(f"Usage: room/{switch} <type>:<n>")
                return
                
            owner_type, owner = self._get_owner(self.args)
            if not owner:
                return
                
            room = self.caller.location
            
            # Get or initialize the dictionaries using Evennia's attribute system
            org_owners = room.attributes.get("org_owners", default={})
            character_owners = room.attributes.get("character_owners", default={})
                
            if switch == "owner":
                if owner_type == "org":
                    org_owners[owner.id] = owner.name
                    room.attributes.add("org_owners", org_owners)
                    self.msg(f"Added {owner.name} as an owner of this room.")
                else:
                    character_owners[owner.id] = owner
                    room.attributes.add("character_owners", character_owners)
                    self.msg(f"Added {owner.name} as an owner of this room.")
            else:  # unowner
                if owner_type == "org":
                    if owner.id in org_owners:
                        del org_owners[owner.id]
                        room.attributes.add("org_owners", org_owners)
                        self.msg(f"Removed {owner.name} as an owner of this room.")
                    else:
                        self.msg(f"{owner.name} is not an owner of this room.")
                else:
                    if owner.id in character_owners:
                        del character_owners[owner.id]
                        room.attributes.add("character_owners", character_owners)
                        self.msg(f"Removed {owner.name} as an owner of this room.")
                    else:
                        self.msg(f"{owner.name} is not an owner of this room.")
                        
        elif switch == "owners":
            room = self.caller.location
            org_owners = room.attributes.get("org_owners", default={})
            char_owners = room.attributes.get("character_owners", default={})
            
            if not org_owners and not char_owners:
                self.msg("This room has no owners.")
                return
                
            if org_owners:
                self.msg("Organization owners: " + list_to_string([name for id, name in org_owners.items()]))
            if char_owners:
                self.msg("Character owners: " + list_to_string([char.name for id, char in char_owners.items()]))
                
        elif switch in ["givekey", "removekey"]:
            if not self.args:
                self.msg(f"Usage: room/{switch} <character>")
                return
                
            char = self.find_character(self.args)
            if not char:
                return
                
            room = self.caller.location
            key_holders = room.attributes.get("key_holders", default={})
                
            if switch == "givekey":
                key_holders[char.id] = char
                room.attributes.add("key_holders", key_holders)
                self.msg(f"Gave {char.name} a key to this room.")
                char.msg(f"{self.caller.name} gave you a key to {room.name}.")
            else:  # removekey
                if char.id in key_holders:
                    del key_holders[char.id]
                    room.attributes.add("key_holders", key_holders)
                    self.msg(f"Removed {char.name}'s key to this room.")
                    char.msg(f"{self.caller.name} took your key to {room.name}.")
                else:
                    self.msg(f"{char.name} doesn't have a key to this room.")
                    
        elif switch in ["lock", "unlock"]:
            if not self.args:
                self.msg(f"Usage: room/{switch} <exit>")
                return
                
            exit = self.caller.search(self.args, location=self.caller.location)
            if not exit:
                return
                
            # Check if it's actually an exit
            if not exit.destination:
                self.msg("That's not an exit.")
                return
                
            # Check if caller has access to either room
            source_room = self.caller.location
            dest_room = exit.destination
            
            has_source_access = source_room.has_access(self.caller)
            has_dest_access = dest_room.has_access(self.caller)
            
            if not (has_source_access or has_dest_access):
                self.msg("You don't have access to either connected room.")
                return

            # Find the return exit in the destination room
            return_exits = [ex for ex in dest_room.exits if ex.destination == source_room]
            return_exit = return_exits[0] if return_exits else None
                
            if switch == "lock":
                # Modify the traverse lock
                exit.locks.add("traverse:roomaccess()")
                self.msg(f"Locked the {exit.name}.")
                
                # Also lock the return exit if it exists
                if return_exit:
                    return_exit.locks.add("traverse:roomaccess()")
                    self.msg(f"Also locked the {return_exit.name} leading back.")
            else:  # unlock
                # Modify the traverse lock
                exit.locks.add("traverse:all()")
                self.msg(f"Unlocked the {exit.name}.")
                
                # Also unlock the return exit if it exists
                if return_exit:
                    return_exit.locks.add("traverse:all()")
                    self.msg(f"Also unlocked the {return_exit.name} leading back.") 