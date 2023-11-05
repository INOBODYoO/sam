import es
import psyco

psyco.full()

sam = es.import_addon('sam')

# Configuration
sam.settings.module_config('admins_chat', {
    'hide_admin_group': {
        'description': ('Hides admin group names in chat messages',),
        'current_value': False
    },
    'allow_custom_chat_colors': {
        'description': ('Enable custom chat colors for admins',),
        'current_value': True
    }
})


# Global Variables
EMPTY = (0, 0, 0)
ALLTALK = es.ServerVar('sv_alltalk')
TAGS = {0: '#gray', 1: '#spec', 2: '#terro', 3: '#ct'}
TEAMS = {1: 'Spectator', 2: 'Terrorists', 3: 'Counter-Terrorists'}

def load():

    # Register the filter
    f = sam.chat_filter.register('admins_chat')
    f.function = admins_chat_FILTER
    f.users.append('#admins')
    f.temporary = False

def unload():

    # Delete the filter
    sam.chat_filter.delete('admins_chat')

def admins_chat_FILTER(userid, text, teamchat):

    # Ignore if the user is in a temporary filter
    if sam.chat_filter.in_filter(userid):
        return userid, text, teamchat

    # If the message was sent from the server console, then send a global server message
    if userid == -1 and text:
        msg('#human', '@#graySERVER #white: ' + text)
        return EMPTY

    # Get the user info
    user = sam.get_player(userid)
    team = user.teamid

    # Make sure the first argument is not a registered command, or using a command trigger
    args = text.split()
    if is_command(args[0]):
        return userid, text, teamchat

    # Special trigger for center messages
    elif text.startswith('@@') and not teamchat:
        sam.msg.center('#all', text.strip('@@'))
        return EMPTY

    # Special trigger for server messages
    elif text.startswith('@'):
        text = text.strip('@')

        # If used in team chat, then sends message to admins only
        if teamchat:
            msg('#admins',
                '%s #default:  #green%s' % (TAGS[team] + user.name, text),
                '#white@#grayADMINS')
        
        # If used in all chat, then sends message to everyone,
        # regardless of their team and state
        else:
            msg('#human', '#white' + text, '#white@#graySERVER')
        return EMPTY

    # If the user is an Admin group, get the group name
    group = sam.admins.get_admin_group(sam.get_steamid(userid))
    if group and not sam.settings('admins_chat').hide_admin_group:
        group = ' #silver(%s#silver) ' % group.name
    else:
        group = ''

    # Format the text with all the necessary tags    
    text = ''.join(
        (
            # Add the dead tag if the user is dead
            '#default*DEAD*' if user.isdead and team != 1 else '',
            # Add the Spectators tag if the user is a spectator
            '#default*SPEC*' if team == 1 and not teamchat else '',
            # Add the team name tag if the user has spoken in team chat
            '#default(%s)' % TEAMS[team] if teamchat else ' ',
            # Add the group name tag if the user is an Admin group
            group,
            # Add the user's team color before the user name
            TAGS[team] if team in TAGS else '#default',
            # Add the user name
            user.name,
            # Add the unique Admins chat color
            ' #default:  #beige',
            # Add the text
            text
        )
    )

    # Get the users to send the message to
    users = set([TAGS[team]])

    # If alltalk is on, user may speak to everyone
    if ALLTALK and not teamchat:
        users.add('#all')

    # Send the message
    msg(users, text)
    return EMPTY


def is_command(text):
    """
    Checks whether the text is a command, variable, or starts with a command trigger
    """

    return text == 'motd' or text.startswith('!') or text.startswith('/') or \
           es.exists('saycommand', text) or es.exists('command', text)

def msg(users, text, _tag=False):
    """
    Used as a wrapper to send a message as the text sent by the user
    """

    # Check if Admins are allowed to use custom chat colors
    cfg = sam.settings('admins_chat')
    text = text if cfg.allow_custom_chat_colors else sam.compile_text(text, True)
    # Send the message

    sam.msg.tell(users, text, prefix=False, tag=_tag)