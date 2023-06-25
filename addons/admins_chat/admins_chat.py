import es
import psyco

psyco.full()

sam = es.import_addon('sam')

# Configuration
sam.settings.addon_config('admins_chat', {
    'hide_admin_group': {
        'description': [
            'If Admins are part of Admin Groups, the group\'s name will be displayed',
            'in the chat next to their name. For example: [Mods] John: Hello World.',
            'If this setting is enabled, the Admin\'s group name will not be displayed.'
        ],
        'current_value': False
    },
    'allow_custom_chat_colors': {
        'description': [
            'Allows Admins to use custom chat colors in their chat messages.',
            'For example: [Mods] John: #redHello #blueWorld.'
        ],
        'current_value': True
    }
})

# Global Variables
EMPTY = (0, 0, 0)
ALLTALK = es.ServerVar('sv_alltalk')
TAGS = {0: '#gray', 1: '#spec', 2: '#t', 3: '#ct'}
TEAMS = {1: 'Spectators', 2: 'Terrorists', 3: 'Counter-Terrorists'}

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

    # Message was sent from server console
    if str(userid) == '-1' and text:
        msg('#human', '@#graySERVER #white: ' + text)
        return EMPTY

    # Check if the player is in a temporary filter
    if sam.chat_filter.in_filter(userid):
        return userid, text, teamchat

    # Mute System Support, ignore if player is muted
    # if sam.import_addon('mute_system').is_muted(userid):
    #   return EMPTY

    # Gather user info
    user = sam.get_player(userid)
    team = user.teamid
    users = set(TAGS[team])
    args = text.split()
    group = sam.admins.get_admin_group(userid)
    
    if group and not sam.settings('admins_chat').hide_admin_group:
        group = '#white(%s#white) ' % group.name
    else:
        group = ''

    # Check for commands or special triggers
    if is_command(args[0]):
        return userid, text, teamchat
    # Special trigger for center messages
    elif text.startswith('@@') and not teamchat:
        sam.msg.center('#all', text.strip('@@'))
        return EMPTY
    elif text.startswith('@'):
        text = text.strip('@')
        # Prints the message only to Admins
        if teamchat:
            msg('#admins',
                '%s #default:  #green%s' % (TAGS[team] + user.name, text),
                '#white@#grayADMINS')
        # Prints a Server message to everyone
        else:
            msg('#human', '#white' + text, '#white@#graySERVER')
        return EMPTY

    # If alltalk is on, user may speak to everyone
    if ALLTALK and not teamchat:
        users.add('#all')

    # If user is in either one of the Teams
    if team in (2,3):
        # Format the text before sending it
        tags = ''.join(('*DEAD* ' if user.isdead else '',
                        '(%s) ' % TEAMS[team] if teamchat else '',
                        TAGS[team],
                        user.name))
        new_text = '#default%s #default:  #white%s' % (tags, text)
        # If the user is dead, he may only speak to dead players
        # and if he is alive, he may only speak to living players
        if not ALLTALK:
            users.add('#dead' if user.isdead else '#alive')
        msg(users, new_text)
    # If user is in Spectators
    elif team == 1:
        if teamchat:
            msg(users, '#default(%s) %s #default:  #white%s' % (TEAMS[team],
                                                                TAGS[team] + user.name,
                                                                text))
            return EMPTY
        msg(users,
            '#default*SPEC* %s #default:  #white%s' % (TAGS[team] + user.name, text))
    return EMPTY


def is_command(text):
    """ Checks whether the text is a command, variable, or starts with a command trigger
    """

    return any((text.startswith('!'),
                text.startswith('/'),
                es.exists('saycommand', text),
                es.exists('command', text),
                text == 'motd'))

def msg(users, text, _tag=False):
    """ Used as a wrapper to send a message as the text sent by the user """

    # Check if Admins are allowed to use custom chat colors
    cfg = sam.settings('admins_chat')
    text = text if cfg.allow_custom_chat_colors else sam.compile_text(text, True)
    # Send the message
    sam.msg.tell(users, text, prefix=False, tag=_tag)