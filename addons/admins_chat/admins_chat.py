import es
import psyco

psyco.full()

sam = es.import_addon('sam')

# Configuration
sam.settings.addon_config('admins_chat', {
    'hide_admin_group': {
        'desc': ['If Admins are in Admin Groups, the group\'s name will be displayed',
                 'in the chat next to their name. (e.g [Mods] John: Hello World)',
                 'If this setting is enabled then it will not display the Admin\'s Group'],
        'default': False
    },
    'allow_custom_chat_colors': {
        'desc': ['Allows Admins to use custom chat colors',
                 '(e.g [Mods] John: #redHello #blueWorld)'],
        'default': True
    }
})

# Global Variables
empty = (0, 0, 0)
alltalk = es.ServerVar('sv_alltalk')
team_tags = {0: '#gray', 1: '#spec', 2: '#t', 3: '#ct'}
team_names = {1: 'Spectators', 2: 'Terrorists', 3: 'Counter-Terrorists'}


def admins_chat_FILTER(uid, text, teamchat):
    default = (uid, text, teamchat)

    # Message was sent from server console
    if str(uid) == '-1' and text:
        text = text.strip('"').strip()
        sam.msg.tell('#human', '@#graySERVER #white: ' + text)
        return empty

    # Ignore if player is not an Admin or if user is in a restricted chat filter
    if not sam.admins.is_admin(uid) or sam.chat_filters.in_filter(uid):
        return default

    # Mute System Support, ignore if player is muted
    # elif sam.import_addon('mute_system').is_muted(uid):
    # return empty

    # Gather user info
    text = text.strip('"')
    user = sam.get_player(uid)
    team = user.teamid
    group = sam.admins(user.steamid)['group']
    group = '#white(#%s%s#white) ' % (sam.admins(group)['color'], sam.title(group)) \
        if group and not sam.settings('admins_chat').hide_admin_group else ''
    users = [team_tags[team]]  # Message should always be sent to teammates regardless
    args = text.split()

    # Check for commands or special triggerses_Re
    if any((text.startswith('!'),
            text.startswith('/'),
            es.exists('saycommand', args[0]),
            es.exists('command', args[0]),
            args[0] == 'motd')):
        return default
    # Special trigger for center messages
    elif text.startswith('@@'):
        text = text.strip('@@').strip()
        sam.msg.center('#human', text)
        return empty
    # Special trigger for Global or Admins only message
    elif text.startswith('@'):
        text = text.strip('@').strip()
        if teamchat:
            sam.msg.tell('#admins', '%s #white: #green%s' % (team_tags[team] + user.name,
                                                             f(text)),
                                                             False,
                                                             '#white@#grayADMINS')
        else:
            sam.msg.tell('#human', '#white@#graySERVER #white: ' + f(text))
        return empty

    # If user is in Spectators
    if team == 1:
        if teamchat:
            sam.msg.tell(users, '#default(%s) %s%s #white: %s' % (team_names[team],
                                                                  team_tags[team],
                                                                  user.name,
                                                                  f(text)),
                         False)
            return empty
        if alltalk:
            users.append('#human')
        sam.msg.tell(users, '#default*SPEC* %s%s #white: %s' % (team_tags[team],
                                                                user.name,
                                                                f(text)),
                     False)
        return empty
    # If user is in either one of the Teams
    elif team in (2, 3):
        # Format the text before sending
        text = '#default%s%s%s%s%s #white: %s' % \
               ('*DEAD* ' if user.isdead else '',
                '(%s) ' % team_names[team] if teamchat else '',
                group,
                team_tags[team],
                user.name,
                f(text))

        # If user is alive and alltalk is off,
        # then user may only speak to alive players and teammates
        if not user.isdead and not alltalk:
            users.append('#alive')
        # If user is dead and alltalk off, then user may only speak to the dead
        elif user.isdead and not alltalk:
            users.append('#dead')
        # If alltalk is on, user may speak to everyone
        elif alltalk:
            users.append('#human')
        sam.msg.tell(users, text, False)
    return empty


def f(text):
    cfg = sam.settings('admins_chat')
    return text if cfg.allow_custom_chat_colors else sam.msg._compile(text, True)


def unload():
    sam.chat_filters.remove('admins_chat', admins_chat_FILTER)


sam.chat_filters.create('admins_chat', admins_chat_FILTER, False)
