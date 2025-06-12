"""
Room

Rooms are simple containers that has no location of their own.

"""

from evennia.objects.objects import DefaultRoom

from .objects import ObjectParent


class Room(ObjectParent, DefaultRoom):
    """
    Rooms are like any Object, except their location is None
    (which is default). They also use basetype_setup() to
    add locks so they cannot be puppeted or picked up.
    (to change that, use at_object_creation instead)

    See mygame/typeclasses/objects.py for a list of
    properties and methods available on all Objects.
    """

    def at_object_creation(self):
        """Called when object is first created."""
        super().at_object_creation()
        
        # Initialize ownership and key holders
        self.db.org_owners = {}  # {id: org_name}
        self.db.character_owners = {}  # {id: character_obj}
        self.db.key_holders = {}  # {id: character_obj}

    @property
    def org_owners(self):
        """Get organization owners as {id: org_name}"""
        return self.db.org_owners or {}

    @property
    def character_owners(self):
        """Get character owners as {id: character_obj}"""
        return self.db.character_owners or {}

    @property
    def key_holders(self):
        """Get characters who have keys to this room as {id: character_obj}"""
        return self.db.key_holders or {}

    def has_access(self, character):
        """
        Check if a character has access to this room (owner or key holder)
        
        Args:
            character: The character to check
            
        Returns:
            bool: True if character has access
        """
        if character.id in self.character_owners:
            return True
            
        if character.id in self.key_holders:
            return True
            
        # Check organization ownership
        char_orgs = character.organisations if hasattr(character, 'organisations') else {}
        for org_id, org_name in self.org_owners.items():
            if org_id in char_orgs:
                return True
                
        return False
