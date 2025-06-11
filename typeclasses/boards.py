"""
Bulletin Board System

This module implements a bulletin board system using Evennia's message system.
Each board is a script that can contain posts, with configurable permissions
for reading and posting.
"""

from evennia import DefaultScript
from evennia import create_message, search_message
from evennia.utils.utils import make_iter
from evennia.utils import logger
from typing import Optional, List, Tuple
from datetime import datetime

class BulletinBoardScript(DefaultScript):
    """
    A bulletin board that can contain posts.
    
    This typeclass represents a bulletin board where characters can post and read
    messages. Each board maintains its own access controls.
    
    Attributes:
        subscribers (list): Characters subscribed to this board
        read_access (str): Lock string for who can read
        write_access (str): Lock string for who can write
        admin_access (str): Lock string for who can admin
    """
    
    def at_script_creation(self):
        """Called when script is first created."""
        super().at_script_creation()
        
        # Initialize subscriber list
        self.db.subscribers = []
        
        # Default locks - start with basic read access, other permissions can be customized per board
        self.locks.add("read:all();write:all();admin:perm(Admin)")
        
        # Initialize archive settings
        self.db.archive_posts = True  # Whether to automatically archive old posts
        self.db.max_posts = 50  # Maximum number of non-archived posts to keep
        
        # Make this script persistent and not repeating
        self.persistent = True
        self.interval = 0
        self.start_delay = False

    def subscribe(self, subscriber):
        """
        Subscribe a character to this board.
        
        Args:
            subscriber (Character): The character to subscribe
            
        Returns:
            bool: True if subscription was successful
        """
        if not self.access(subscriber, "read"):
            return False
            
        if subscriber not in self.db.subscribers:
            self.db.subscribers.append(subscriber)
        return True

    def unsubscribe(self, subscriber):
        """
        Unsubscribe a character from this board.
        
        Args:
            subscriber (Character): The character to unsubscribe
            
        Returns:
            bool: True if unsubscription was successful
        """
        if subscriber in self.db.subscribers:
            self.db.subscribers.remove(subscriber)
            return True
        return False

    def set_access(self, access_type: str, lockstring: str, caller=None) -> bool:
        """
        Set access rules for the board.
        
        Args:
            access_type (str): Type of access ('read', 'write', or 'admin')
            lockstring (str): The lock string to set
            caller (Object, optional): The one attempting to set access
            
        Returns:
            bool: True if access was set successfully
        """
        if caller and not self.access(caller, "admin"):
            return False
            
        try:
            if access_type == "read":
                self.locks.add(f"read:{lockstring}")
            elif access_type == "write":
                self.locks.add(f"write:{lockstring}")
            elif access_type == "admin":
                self.locks.add(f"admin:{lockstring}")
            else:
                return False
            return True
        except Exception:
            return False

    def create_post(self, poster, title, text):
        """Create a new post on this board.
        
        Args:
            poster (Character): The character making the post
            title (str): The title of the post
            text (str): The body of the post
            
        Returns:
            Msg: The created post message, or None if creation failed
        """
        if not self.access(poster, "write"):
            return None
            
        # Create the post
        post = create_message(
            senderobj=poster,  # Required sender object
            header=title,
            message=text,
            receivers=self,
            tags=[("board_post", "board_messages")]
        )
        
        # Check if we need to archive old posts
        if self.db.archive_posts and post:
            posts = self.get_posts(poster, include_archived=False)
            if len(posts) > self.db.max_posts:
                # Archive oldest non-pinned post
                for old_post, _ in reversed(posts):
                    if not old_post.db.pinned:
                        old_post.tags.add("archived", category="board_messages")
                        break
                        
        return post

    def edit_post(self, editor: "Character", post: "Msg", new_text: str) -> bool:
        """
        Edit an existing post.
        
        Args:
            editor: The character editing the post
            post: The post to edit
            new_text: The new content
            
        Returns:
            True if edit was successful
        """
        # Check if user has permission to edit this post
        if not (editor == post.senders[0] or self.access(editor, "admin")):
            return False
            
        # Update the message
        post.message = new_text
        post.db.last_edited = datetime.now()
        post.db.edited_by = editor
        return True

    def get_posts(self, reader: "Character", include_archived: bool = False) -> List[Tuple["Msg", bool]]:
        """
        Get all posts accessible to the character.
        
        Args:
            reader: The character requesting posts
            include_archived: Whether to include archived posts
            
        Returns:
            List of (post, is_unread) tuples
        """
        if not self.access(reader, "read"):
            return []
            
        # Get all messages where this board is a receiver
        posts = search_message(receiver=self)
        if not posts:
            return []
            
        # Filter to only board posts and check if they're unread
        filtered_posts = []
        for post in posts:
            # Check if it's a board post
            if not post.tags.has("board_post", category="board_messages"):
                continue
                
            # Skip archived posts unless explicitly included
            if not include_archived and post.tags.has("archived", category="board_messages"):
                continue
                
            # Check if post is unread
            is_unread = reader not in post.read_by if hasattr(post, "read_by") else True
            filtered_posts.append((post, is_unread))
            
        # Sort by date, pinned posts first
        filtered_posts.sort(key=lambda x: (not bool(getattr(x[0], 'pinned', False)), x[0].date_created), reverse=True)
        return filtered_posts

    def mark_read(self, reader: "Character", post: "Msg") -> None:
        """
        Mark a post as read by character.
        
        Args:
            reader: The character marking the post
            post: The post to mark
        """
        if not hasattr(post, "read_by"):
            post.read_by = []
        if reader not in post.read_by:
            post.read_by.append(reader)

    def delete_post(self, character: "Character", post: "Msg") -> bool:
        """
        Delete a post from the board.
        
        Args:
            character: The character attempting deletion
            post: The post to delete
            
        Returns:
            True if post was deleted successfully
        """
        # Check if user has permission to delete this post
        if not (character == post.senders[0] or self.access(character, "admin")):
            return False
            
        if self in post.receivers:
            try:
                post.delete()
                return True
            except Exception as e:
                return False
                
        return False

    def pin_post(self, character: "Character", post: "Msg", pin: bool = True) -> bool:
        """
        Pin or unpin a post.
        
        Args:
            character: The character attempting to pin
            post: The post to pin/unpin
            pin: True to pin, False to unpin
            
        Returns:
            True if operation was successful
        """
        if not self.access(character, "admin"):
            return False
            
        post.db.pinned = pin
        return True

    def _notify_new_post(self, post: "Msg", poster: "Character") -> None:
        """
        Notify relevant characters about a new post.
        
        Args:
            post: The created post
            poster: Who created the post
        """
        # Format the notification message
        header = f"|w[Board: {self.key}]|n"
        msg = f"{header} New post: |w{post.header}|n by |c{poster.key}|n"
        
        # Message options for proper handling
        options = {"type": "board_post"}
        
        # Notify all subscribers
        for subscriber in self.db.subscribers:
            if subscriber != poster and self.access(subscriber, "read"):
                if subscriber.has_account and subscriber.account.is_connected:
                    # Send to connected subscribers
                    subscriber.msg(text=(msg, options), from_obj=self)
                else:
                    # Store notification for offline subscribers
                    notifications = subscriber.db.offline_board_notifications or []
                    notifications.append((msg, options))
                    subscriber.db.offline_board_notifications = notifications 