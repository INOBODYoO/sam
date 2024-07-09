import es

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
TAGS = {0: '#gray', 1: '#spec', 2: '#t', 3: '#ct'}
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

    # Check if the user is currently being filtered out for chat
    if sam.chat_filter.in_filter(userid):
        return userid, text, teamchat

    # Handle console messages
    if userid == -1 and text:
        msg('#human', '@#graySERVER #white: ' + text)
        return EMPTY

    # Retrieve the player object and their team information
    user = sam.get_player(userid)
    team = user.teamid

    # Ignore messages that start with a command prefix
    args = text.split()
    if is_command(args[0]):
        return userid, text, teamchat

    # Process center messages
    if text.startswith('@@') and not teamchat:
        sam.msg.center('#human', text[2:])
        return EMPTY

    # Process global and Admins only messages
    if text.startswith('@'):
        text = text[1:]  # Remove '@' to signify an admin-only message
        recipient = '#admins' if teamchat else '#human'
        prefix = TAGS[team] + user.name if teamchat else '#white'
        # Format the message for admin or public chat
        message = '%s #default:  #green%s' % (prefix, text) if teamchat else text
        tag = '#white@#grayADMINS' if teamchat else '#white@#graySERVER'
        msg(recipient, message, tag)
        return EMPTY

    # Determine if the admin group name should be displayed with the message
    group = sam.admins.get_admin_group(sam.get_steamid(userid))
    hide_admin_group = sam.settings('admins_chat').hide_admin_group
    group_name = ' #gray(%s#gray) ' % group.name if group and not hide_admin_group else ''

    # Add tags for dead or spectating players and format the message
    dead_spec_tags = '#default*DEAD* ' if user.isdead and team != 1 else ''
    dead_spec_tags += '#default*SPEC* ' if team == 1 and not teamchat else ''
    team_tag = '#default(%s) ' % TEAMS[team] if teamchat else ''
    formatted_text = '%s%s%s%s%s #default:  #beige%s' % (
        dead_spec_tags, team_tag, group_name, TAGS.get(team, '#default'), user.name, text)

    # Determine who should receive the message based on game settings
    users = set([TAGS[team]])
    if ALLTALK and not teamchat:
        users.add('#human')

    # Send the message to the determined recipients
    msg(users, formatted_text)
    return EMPTY

def is_command(text):
    """
    Checks whether the text is a command, variable, or starts with a command trigger
    """
    return text == 'motd' or text.startswith(('!', '/')) or \
           es.exists('saycommand', text) or es.exists('command', text)

def msg(users, text, _tag=False):
    """
    Used as a wrapper to send a message as the text sent by the user
    """

    if not sam.settings('admins_chat').allow_custom_chat_colors:
        text = sam.format_text(text, True)
    sam.msg.tell(users, text, prefix=False, nametag=_tag)
