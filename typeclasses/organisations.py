"""
Organisation typeclass for managing noble houses, orders, guilds, etc.
"""
from evennia import DefaultObject
from evennia.typeclasses.tags import TagProperty
from evennia.utils.dbserialize import dbserialize
from evennia.utils.utils import lazy_property
from evennia.utils.search import search_object

class Organisation(DefaultObject):
    """
    An organisation represents a group like a noble house, knightly order, or guild.
    
    Organisations have:
    - A head (character)
    - Members with ranks (1-10, with custom names)
    - A public description
    - Optional secret status
    """
    
    MAX_RANKS = 10
    
    @lazy_property
    def members(self):
        """Get all members of this organisation."""
        return self.db.members
    
    @lazy_property
    def ranks(self):
        """Get all ranks in this organisation."""
        return self.db.ranks
    
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
        self.db.members = {}  # {character_id: rank_number}
        self.db.ranks = {}    # {rank_number: rank_name}
        self.db.head = None
        self.db.description = ""
        self.db.is_secret = False
    
    def add_member(self, character, rank=None):
        """
        Add a member to the organisation.
        
        Args:
            character: The character to add
            rank: Optional rank number (1-10) to assign
        """
        if not rank and self.ranks:
            # If no rank specified but ranks exist, use the lowest rank
            rank = min(self.ranks.keys())
        elif not rank:
            # If no ranks exist, use rank 1
            rank = 1
            
        if not isinstance(rank, int) or rank < 1 or rank > self.MAX_RANKS:
            raise ValueError(f"Rank must be a number between 1 and {self.MAX_RANKS}")
        
        # Store character ID as integer
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
            rank: The rank number (1-10) to set
        """
        if not isinstance(rank, int) or rank < 1 or rank > self.MAX_RANKS:
            raise ValueError(f"Rank must be a number between 1 and {self.MAX_RANKS}")
            
        if character.id not in self.db.members:
            self.add_member(character, rank)
        else:
            self.db.members[character.id] = rank
            character.db.organisations[self.id] = rank
    
    def get_rank(self, character):
        """
        Get a member's rank.
        
        Args:
            character: The character to get rank for
            
        Returns:
            Tuple of (rank_number, rank_name) or None if not a member
        """
        rank_num = self.db.members.get(character.id)
        if rank_num:
            return (rank_num, self.ranks.get(rank_num, f"Rank {rank_num}"))
        return None
    
    def set_rank_name(self, rank_num, rank_name):
        """
        Set the name for a rank number.
        
        Args:
            rank_num: The rank number (1-10)
            rank_name: The name to give this rank
        """
        if not isinstance(rank_num, int) or rank_num < 1 or rank_num > self.MAX_RANKS:
            raise ValueError(f"Rank must be a number between 1 and {self.MAX_RANKS}")
            
        self.db.ranks[rank_num] = rank_name
    
    def get_members(self):
        """
        Get all members of the organisation.
        
        Returns:
            List of (character, rank_number, rank_name) tuples
        """
        members = []
        for char_id, rank_num in self.db.members.items():
            # Search for character by ID using search_object
            chars = search_object(id=char_id)
            if chars:
                char = chars[0]
                rank_name = self.ranks.get(rank_num, f"Rank {rank_num}")
                members.append((char, rank_num, rank_name))
        return sorted(members, key=lambda x: x[1])  # Sort by rank number
        
    def delete(self):
        """
        Delete the organisation and clean up all references.
        This will:
        1. Remove all members from the organisation
        2. Clear the head reference
        3. Delete the organisation object
        """
        # Remove all members
        for char_id in list(self.db.members.keys()):
            chars = search_object(id=char_id)
            if chars:
                self.remove_member(chars[0])
        
        # Clear head reference
        if self.head:
            self.head = None
            
        # Delete the organisation
        super().delete() 