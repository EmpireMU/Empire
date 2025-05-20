"""
Organizations

Organizations represent groups like noble houses, guilds, or factions.
They can have members with different ranks and provide resources to their members.
"""

from evennia.objects.objects import DefaultObject
from evennia.utils import lazy_property
from evennia.utils.search import search_object
from .objects import ObjectParent
from evennia.contrib.rpg.traits import TraitHandler


class Organisation(ObjectParent, DefaultObject):
    """
    An organization that characters can join.
    Organizations can have different ranks and provide resources to members.
    """
    
    MAX_RANKS = 10
    
    @lazy_property
    def members(self):
        """
        Get all members of this organization.
        Returns a dict of {char_id: rank_number}
        """
        return self.attributes.get('members', default={}, category='organisation')
        
    @property
    def resources(self):
        """
        Get all resources owned by this organization.
        Returns a list of Resource objects.
        """
        return search_object('resource', attribute_name='owner', attribute_value=self.dbref)
        
    def at_object_creation(self):
        """
        Called when the organization is first created.
        """
        super().at_object_creation()
        
        # Initialize member list
        self.attributes.add('members', {}, category='organisation')
        
        # Set up organization properties
        self.db.description = "No description has been set."
        
        # Initialize default ranks
        self.db.ranks = {
            1: "Head of House",
            2: "Minister",
            3: "Noble Family",
            4: "Senior Servant"
        }
        
    def create_resource(self, name, die_size=6, description=None):
        """
        Create a new resource owned by this organization.
        
        Args:
            name (str): The name of the resource
            die_size (int): The die size (4-12)
            description (str, optional): Description of the resource
            
        Returns:
            Resource: The created resource object, or None if creation failed
        """
        from evennia.utils.create import create_object
        from typeclasses.resources import Resource
        
        try:
            resource = create_object(
                typeclass=Resource,
                key=name,
                location=self.location
            )
            if resource:
                resource.die_size = die_size
                if description:
                    resource.db.description = description
                resource.set_owner(self)  # This will also set origin
                return resource
        except Exception:
            return None
            
    def transfer_resource(self, resource, target):
        """
        Transfer a resource to another character or organization.
        
        Args:
            resource: The resource to transfer
            target: The character or organization to transfer to
            
        Returns:
            bool: True if transfer successful, False otherwise
        """
        if not resource or not target:
            return False
            
        # Verify we own the resource
        if resource.owner != self:
            return False
            
        # Transfer ownership
        resource.set_owner(target, transfer_from=self)
        return True
        
    def add_member(self, character, rank=4):
        """
        Add a character to the organization.
        
        Args:
            character: The character to add
            rank: The rank to give them (default: Senior Servant)
        """
        if not character.check_permstring("Admin"):
            return False
            
        # Add to organization's member list
        members = self.members
        members[character.id] = rank
        self.attributes.add('members', members, category='organisation')
        
        # Add to character's organization list
        orgs = character.attributes.get('organisations', default={}, category='organisations')
        orgs[self.id] = rank
        character.attributes.add('organisations', orgs, category='organisations')
        return True
        
    def remove_member(self, character):
        """
        Remove a character from the organization.
        
        Args:
            character: The character to remove
        """
        if not character.check_permstring("Admin"):
            return False
            
        # Remove from organization's member list
        members = self.members
        if character.id in members:
            del members[character.id]
            self.attributes.add('members', members, category='organisation')
        
        # Remove from character's organization list
        orgs = character.attributes.get('organisations', default={}, category='organisations')
        if self.id in orgs:
            del orgs[self.id]
            character.attributes.add('organisations', orgs, category='organisations')
        return True
            
    def set_rank(self, character, rank):
        """
        Set a character's rank in the organization.
        
        Args:
            character: The character to set rank for
            rank: The new rank number (1-10)
        """
        if not character.check_permstring("Admin"):
            return False
            
        if not isinstance(rank, int) or rank < 1 or rank > self.MAX_RANKS:
            return False
            
        # Update organization's member list
        members = self.members
        if character.id in members:
            members[character.id] = rank
            self.attributes.add('members', members, category='organisation')
            
            # Update character's organization list
            orgs = character.attributes.get('organisations', default={}, category='organisations')
            orgs[self.id] = rank
            character.attributes.add('organisations', orgs, category='organisations')
            return True
            
        return False
        
    def set_rank_name(self, rank, name):
        """
        Set the name for a rank number.
        
        Args:
            rank: The rank number (1-10)
            name: The name to give this rank
        """
        if not isinstance(rank, int) or rank < 1 or rank > self.MAX_RANKS:
            return False
            
        ranks = self.db.ranks or {}
        ranks[rank] = name
        self.db.ranks = ranks
        return True
        
    def get_rank_name(self, rank):
        """
        Get the name of a rank number.
        
        Args:
            rank: The rank number
            
        Returns:
            The rank name or None if invalid
        """
        return self.db.ranks.get(rank)
        
    def get_member_rank(self, character):
        """
        Get a character's rank in the organization.
        
        Args:
            character: The character to check
            
        Returns:
            The rank number or None if not a member
        """
        return self.members.get(character.id)
        
    def get_member_rank_name(self, character):
        """
        Get a character's rank name in the organization.
        
        Args:
            character: The character to check
            
        Returns:
            The rank name or None if not a member
        """
        rank = self.get_member_rank(character)
        if rank is not None:
            return self.get_rank_name(rank)
        return None

    def get_members(self):
        """
        Get all members of the organisation.
        
        Returns:
            List of (character, rank_number, rank_name) tuples
        """
        members = []
        for char_id, rank_num in self.members.items():
            # Search for character using Evennia's search with dbref
            chars = search_object(f"#{char_id}")
            if chars:
                char = chars[0]
                rank_name = self.get_rank_name(rank_num) or f"Rank {rank_num}"
                members.append((char, rank_num, rank_name))
        return sorted(members, key=lambda x: x[1])  # Sort by rank number
        
    def delete(self):
        """
        Delete the organisation and clean up all references.
        """
        # Remove all members
        for char_id in list(self.members.keys()):
            chars = search_object(f"#{char_id}")
            if chars:
                self.remove_member(chars[0])
                
        # Delete all owned resources
        for resource in self.resources:
            resource.delete()
        
        # Delete the organisation
        super().delete() 