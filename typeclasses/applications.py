"""
Applications for character roster system.
"""

from evennia.scripts.scripts import DefaultScript
from evennia.utils import create
from evennia.utils.utils import make_iter
from django.conf import settings

class Application(DefaultScript):
    """
    An application to play a character.
    
    Important attributes:
        email (str): The email address of the applicant
        char_name (str): The name of the character being applied for
        app_text (str): The application text
        ip_address (str): The IP address of the applicant
    """
    
    def at_script_creation(self):
        """
        Called when the script is first created.
        """
        self.db.email = ""
        self.db.char_name = ""
        self.db.app_text = ""
        self.db.ip_address = ""
        
        # Only staff should be able to see/edit applications
        self.locks.add(
            "examine:perm(Admin);edit:perm(Admin);delete:perm(Admin);control:perm(Admin)"
        )
        
        # Set up persistent mode
        self.persistent = True
        
    def get_display_name(self, looker=None, **kwargs):
        """
        Returns the display name of the application - used in listings.
        """
        return f"Application #{self.id}: {self.db.char_name}" 