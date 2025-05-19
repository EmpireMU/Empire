"""
Organisation typeclass for managing noble houses, orders, guilds, etc.
"""
from evennia import DefaultObject
from evennia.typeclasses.tags import TagProperty
from evennia.utils.dbserialize import dbserialize
from evennia.utils.utils import lazy_property

class Organisation(DefaultObject):
    """
    An organisation represents a group like a noble house, knightly order, or guild.
    
    Organisations have:
    - A head (character)
    - Members with ranks
    - A public description
    - Optional secret status
    """
    
    @lazy_property
    def members(self):
        """Get all members of this organisation."""
        return self.db.members or {}
    
    @lazy_property
    def ranks(self):
        """Get all ranks in this organisation."""
        return self.db.ranks or {}
    
    @property
    def head(self):
        """Get the head of this organisation."""
        return self.db.head
    
    @head.setter
    def head(self, value):
        """Set the head of this organisation."""
        self.db.head = value
    
    @property
    def description(self):
        """Get the public description of this organisation."""
        return self.db.description or "No description available."
    
    @description.setter
    def description(self, value):
        """Set the public description of this organisation."""
        self.db.description = value
    
    @property
    def is_secret(self):
        """Check if this organisation is secret."""
        return self.db.is_secret or False
    
    @is_secret.setter
    def is_secret(self, value):
        """Set whether this organisation is secret."""
        self.db.is_secret = bool(value)
    
    def at_object_creation(self):
        """Initialize the organisation."""
        self.db.members = {}  # {character_id: rank_id}
        self.db.ranks = {}    # {rank_id: rank_name}
        self.db.head = None
        self.db.description = ""
        self.db.is_secret = False
    
    def add_member(self, character, rank=None):
        """
        Add a member to the organisation.
        
        Args:
            character: The character to add
            rank: Optional rank to assign
        """
        if not rank and self.ranks:
            # If no rank specified but ranks exist, use the lowest rank
            rank = min(self.ranks.keys())
        
        self.db.members[character.id] = rank
        character.db.organisations = character.db.organisations or {}
        character.db.organisations[self.id] = rank
    
    def remove_member(self, character):
        """
        Remove a member from the organisation.
        
        Args:
            character: The character to remove
        """
        if character.id in self.db.members:
            del self.db.members[character.id]
            if character.db.organisations:
                del character.db.organisations[self.id]
    
    def set_rank(self, character, rank):
        """
        Set a member's rank.
        
        Args:
            character: The character to set rank for
            rank: The rank to set
        """
        if character.id in self.db.members:
            self.db.members[character.id] = rank
            character.db.organisations[self.id] = rank
    
    def get_rank(self, character):
        """
        Get a member's rank.
        
        Args:
            character: The character to get rank for
            
        Returns:
            The rank name or None if not a member
        """
        rank_id = self.db.members.get(character.id)
        if rank_id:
            return self.ranks.get(rank_id)
        return None
    
    def add_rank(self, rank_id, rank_name):
        """
        Add a new rank to the organisation.
        
        Args:
            rank_id: Unique identifier for the rank
            rank_name: Display name for the rank
        """
        self.db.ranks[rank_id] = rank_name
    
    def remove_rank(self, rank_id):
        """
        Remove a rank from the organisation.
        
        Args:
            rank_id: The rank to remove
        """
        if rank_id in self.db.ranks:
            del self.db.ranks[rank_id]
            # Update members with this rank
            for char_id, rank in list(self.db.members.items()):
                if rank == rank_id:
                    del self.db.members[char_id]
    
    def get_members(self):
        """
        Get all members of the organisation.
        
        Returns:
            List of (character, rank) tuples
        """
        members = []
        for char_id, rank in self.db.members.items():
            char = self.search(char_id, global_search=True)
            if char:
                members.append((char, self.ranks.get(rank)))
        return members 