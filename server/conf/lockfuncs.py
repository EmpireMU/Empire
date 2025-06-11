"""

Lockfuncs

Lock functions are functions available when defining lock strings,
which in turn limits access to various game systems.

All functions defined globally in this module are assumed to be
available for use in lockstrings to determine access. See the
Evennia documentation for more info on locks.

A lock function is always called with two arguments, accessing_obj and
accessed_obj, followed by any number of arguments. All possible
arguments should be handled with *args, **kwargs. The lock function
should handle all eventual tracebacks by logging the error and
returning False.

Lock functions in this module extend (and will overload same-named)
lock functions from evennia.locks.lockfuncs.

"""

# def myfalse(accessing_obj, accessed_obj, *args, **kwargs):
#    """
#    called in lockstring with myfalse().
#    A simple logger that always returns false. Prints to stdout
#    for simplicity, should use utils.logger for real operation.
#    """
#    print "%s tried to access %s. Access denied." % (accessing_obj, accessed_obj)
#    return False

def orgmember(accessing_obj, accessed_obj, *args, **kwargs):
    """
    Check if accessing_obj is a member of the specified organization and optionally has minimum rank.
    
    Usage:
        orgmember(House Otrese) - returns True if accessing_obj is a member of House Otrese (rank 10 or better)
        orgmember(House Otrese, 5) - returns True if accessing_obj has rank 5 or better (lower number)
    """
    if not args:
        return False
        
    org_name = args[0]
    min_rank = int(args[1]) if len(args) > 1 else 10
    
    # Get the character if an account is accessing
    character = accessing_obj
    if hasattr(accessing_obj, 'character'):
        character = accessing_obj.character
    
    # Find the organization by name
    from evennia.utils.search import search_object
    orgs = search_object(org_name, typeclass='typeclasses.organisations.Organisation')
    if not orgs:
        return False
    org = orgs[0]
    
    # Get the character's organisations and check membership by org ID
    char_orgs = character.organisations
    if org.id in char_orgs:
        rank = char_orgs[org.id]
        return rank <= min_rank
    
    return False
