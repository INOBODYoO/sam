import es

sam = es.import_addon('sam')

# Global Variables
TEAMS = {
    1: '#specSpectators',
    2: '#terrTerrorists',
    3: '#ctCounter-Terrorists'
}

# Create the Addon's configuration
sam.settings.module_config('teams_manager', {
    'enable_teams_command': {
        'description': ('Enables the !teams command.',
                        'Opens Teams Manager menu.'),
        'current_value': True
    },
    'enable_spec_command': {
        'description': ('Enables the !spec command.',
                        'Moves the player to the spectator team.'),
        'current_value': True
    },
    'enable_move_all_to_spectators_option': {
        'description': ('Enables the Move All To Spectators menu option.',),
        'current_value': True
    },
    'enable_move_spectators_to_teams_option': {
        'description': ('Enables the Move Spectators To Teams menu option.',),
        'current_value': True
    },
    'enable_swap_teams_option': {
        'description': ('Enables the Swap Teams menu option.',),
        'current_value': True
    },
    'enable_shuffle_teams_option': {
        'description': ('Enables the Shuffle Teams menu option.',),
        'current_value': True
    },
    'addon_name_in_notifications': {
        'description': ('Enables the addon name in notifications.',),
        'current_value': True
    }
})

def load():

    # Register the Addons own Admin Permission
    sam.admins.register_addon_permission('teams_manager')

    # Register Chat commands
    sam.cmds.chat('teams', teams_CMD)
    sam.cmds.chat('spec', spec_CMD)



def unload():

    # Unregister Chat commands
    sam.cmds.delete('!teams')


def addon_menu(userid, submenu='home_page'):

    if not sam.admins.is_allowed(userid, 'teams_manager'):
        if submenu == 'home_page':
            sam.home_page(userid)
        return

    menu = sam.Menu('teams_manager', teams_manager_HANDLE, submenu)
    menu.build_function = addon_menu
    menu.build_arguments_list = (userid, submenu)
    menu.rebuild_on_refresh = True
    menu.title('Teams Manager')

    options = {
        1: 'Move To Spectators',
        2: 'Move To Terrorists',
        3: 'Move To Counter-Terrorists',
        4: {
            'text': 'Move Everyone To Spectators',
            'setting': 'enable_move_all_to_spectators_option'
        },
        5: {
            'text': 'Move Spectators To Teams',
            'setting': 'enable_move_all_to_spectators_option'
        },
        6: {'text': 'Swap Teams', 'setting': 'enable_swap_teams_option'},
        7: {'text': 'Shuffle Teams', 'setting': 'enable_shuffle_teams_option'}
    }

    for key, value in options.items():
        if isinstance(value, dict):
            setting = not sam.settings('teams_manager').get(value['setting'])
            menu.add_option(key, value['text'], setting)
        else:
            menu.add_option(key, value)

    menu.footer(
        'Spectators: %s' % len(sam.userid_list('#spec')),
        'Terrorists: %s' % len(sam.userid_list('#t')),
        'Counter-Terrorists: %s' % len(sam.userid_list('#ct'))
    )

    # Send the menu
    menu.send(userid)


def teams_manager_HANDLE(userid, choice, submenu):

    # Get each team player list
    spec = sam.player_list('#spec')
    terr = sam.player_list('#t')
    ct = sam.player_list('#ct')

    if choice <= 3:

        menu = sam.Menu('tm_player_list', player_list_HANDLE, 'teams_manager')
        menu.build_function = teams_manager_HANDLE
        menu.build_arguments_list = (userid, choice, submenu)
        menu.title('Teams Manager')
        menu.description('Choose a player:')

        # Get the correct list of players based on the choice
        player_list = None
        if choice == 1:
            player_list = terr + ct
        elif choice in (2, 3):
            player_list = spec + ct if choice == 2 else spec + terr

        # Check if the player list is empty
        if not player_list:
            sam.msg.hud(
                userid, 'There are no players available at the moment!')
            submenu.send(userid, rebuild=True)
            return

        # Add the players to the menu
        for player in sorted(player_list, key=lambda x: x.name):
            menu.add_option((choice, player), player.name)

        # Send the menu
        menu.send(userid)
        return

    if choice == 4:
        move_all_to_spectators()

    elif choice == 5:
        move_spectators_to_teams()

    elif choice == 6:
        swap_teams()

    elif choice == 7:
        shuffle_teams()

    # Restart the game if there isn't any players alive
    _restart_game()

    # Re-send the menu to the user
    submenu.send(userid, rebuild=True)


def player_list_HANDLE(userid, choice, submenu):
    
    team, player = choice

    team_color = {1: '#spec', 2: '#t', 3: '#ct'}
    _msg('%s%s #beigehas been moved to %s' % (
        team_color[player.team], player.name, TEAMS[team]
    ))

    sam.change_team(player.userid, team)

    # Restart the game if there isn't any players alive
    _restart_game()

    # Re-send the menu to the user
    submenu.send(userid, rebuild=True)


# Addon Functions
def move_all_to_spectators(notify=True):
    """
    Moves all players from both teams to Spectators
    """

    for userid in sam.userid_list('#alive'):
        sam.change_team(userid, 1)

    _msg('All players have been moved to %s' % TEAMS[1], notify)


def move_spectators_to_teams(notify=True):
    """
    Moves all Spectators to both teams
    """

    # Teams Lists
    spec = sam.userid_list('#spec')
    terr = sam.userid_list('#t')
    ct = sam.userid_list('#ct')

    # Get both teams size
    terr_size = len(terr)
    ct_size = len(ct)

    # Calculate target size for lists terr and ct
    total_items = len(spec) + terr_size + ct_size
    target_size = total_items // 2

    # Distribute items from spec to terr and ct
    for userid in spec:
        # If terrorists are fewer or equal in number to counter-terrorists,
        # and haven't reached the target size, add to terrorists
        # otherwise add to counter-terrorists
        if terr_size < target_size and terr_size <= ct_size:
            sam.change_team(userid, 2)
            terr_size += 1
        else:
            sam.change_team(userid, 3)
            ct_size += 1

    # Restart game and notify
    _restart_game()
    _msg('Moved %s to %s and %s' % (TEAMS[1], TEAMS[2], TEAMS[3]), notify)


def swap_teams(notify=True):
    """
    Swaps the teams of the players
    """

    for player in sam.player_list('#alive'):
        if player.team == 2:
            sam.change_team(int(player), 3)
        elif player.team == 3:
            sam.change_team(int(player), 2)

    _restart_game()

    _msg('Teams have been swapped!', notify)


def shuffle_teams(notify=True):
    """
    Shuffles the teams of the players
    """

    # Get the list of all alive players
    alive = sam.userid_list('#alive')

    # Import the shuffle function, and shuffle the list of players
    from random import shuffle
    shuffle(alive)

    # Calculate the midpoint
    midpoint = len(alive) // 2

    # Assign the first half to team 2, the second half to team 3
    for player in alive[:midpoint]:
        sam.change_team(player, 2)
    for player in alive[midpoint:]:
        sam.change_team(player, 3)

    _msg('Teams have been shuffled!', notify)


def _restart_game():
    """
    Restarts the game if there aren't any players alive
    """

    if not sam.userid_list('#alive') and sam.userid_list('#t', '#ct'):
        es.server.insertcmd('mp_restartgame 1')


def _msg(message, notify=True):

    if notify:
        name = sam.settings('teams_manager').addon_name_in_notifications
        sam.msg.tell(
            '#human', '#beige' + message, nametag='Teams Manager' if name else False
        )

# Chat Commands
def teams_CMD(userid, args):
    
    # Check whether the command is enabled or the user has permission to use it
    if not sam.settings('teams_manager').enable_teams_command:
        sam.cmds.is_disabled(userid)
        return
    elif not sam.admins.is_allowed(userid, 'teams_manager'):
        sam.cmds.no_permission(userid)
        return
    
    addon_menu(userid, False)
    

def spec_CMD(userid, args):
    
    # Check whether the command is enabled or the user has permission to use it
    if not sam.settings('teams_manager').enable_spec_command:
        sam.cmds.is_disabled(userid)
        return
    elif not sam.admins.is_allowed(userid, 'teams_manager'):
        sam.cmds.no_permission(userid)
        return
    

    # Check if the player is already in the Spectator team
    if sam.get_player(userid).team == 1:
        sam.msg.hud(userid, 'You are already in %s' % TEAMS[1])
        return
    
    sam.change_team(userid, 1)
    sam.msg.hud(userid, 'You have been moved to %s' % TEAMS[1])
