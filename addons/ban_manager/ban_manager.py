#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import es

sam = es.import_addon('sam')

# Global Variables
DATABASE = sam.databases.load('banned_players_database')
LOGS = sam.databases.load('ban_logs')
DATE_FORMAT = '%d/%m/%Y at %H:%M:%S'
BAN_LENGTH = {
    1: (
        ('5 Minutes', 300),
        ('30 Minutes', 1800),
        ('1 Hour', 3600),
        ('3 Hours', 10800),
        ('12 Hours', 43200),
        ('1 Day', 86400)
    ),
    2: (
        ('3 Days', 259200),
        ('1 Week', 604800),
        ('1 Month', 2629746),
        ('3 Months', 7889238),
        ('6 Months', 15778476),
        ('1 Year', 31556952)
    )
}

def load():

    # Check if the reasons file exists
    check_for_reasons_file()

    # Check for expired bans
    check_bans()

    # Make sure any banned players are kicked
    for player in sam.player_list('#human'):
        if is_banned(player.steamid):
            kick(player.steamid, False)

def unload():

    # Save databases
    save_database()


def addon_menu(userid, args=None):

    # Check if the user has permission to use Ban Manager
    if not sam.admins.is_allowed(userid, 'ban_level'):
        sam.msg.hud(userid, 'You don\'t have permission to use Ban Manager')
        sam.home_page(userid)
        return
    
    # Check for expired bans
    check_bans()
    
    menu = sam.Menu('ban_manager', ban_manager_HANDLE, 'home_page')
    menu.title('Ban Manager')
    menu.description('Choose an option:')
    menu.add_option(1, 'Ban a Player')
    menu.add_option(2, 'Banned Players List (%s)' % len(DATABASE))
    menu.add_option(3, 'Ban History')
    menu.send(userid)

def ban_manager_HANDLE(userid, choice, submenu):

    # Simple wrapper function to return to the addon menu
    def r(userid, text):
        sam.msg.hud(userid, text)
        addon_menu(userid)

    if choice == 1:
        
        menu = sam.Menu('bm_player_list', player_list_HANDLE, submenu)
        menu.title('Ban Manager')
        menu.description('Choose a player to ban:')

        # Just a simple wrapper function to be used as a condition to list players
        def condition(player):
            return is_player_valid(player.steamid, admin=sam.get_steamid(userid),
                                   bypass_checks={'all': True})

        # Construct a list of valid player profiles in two groups: online and offline.
        # Valid players are non-super admins, admins higher than the menu user,
        # and already banned players.
        menu.construct_players_profile_list(condition_function=condition)

        menu.send(userid)
        return

    # Banned Players List option
    elif choice == 2:

        # Return if there aren't any banned players
        if not DATABASE:
            r(userid, 'Currently, there aren\'t any players banned.')
            return
        
        menu = sam.Menu('banned_list', ban_profile, submenu)
        menu.title('Ban Manager')
        menu.description('Choose a banned player:')
    
        # List all banned players
        for player in DATABASE.values():
            menu.add_option(player, player['name'])

        menu.send(userid)

    elif choice == 3:

        # Return if there aren't any bans in the logs database
        if not LOGS:
            r(userid, 'Currently, there aren\'t any logged bans.')
            return

        menu = sam.Menu('ban_history_year', ban_history_year_HANDLE, submenu)
        menu.title('Ban Manager')
        menu.description('Choose a year:')

        # List all the years in the logs database
        for year in LOGS:
            menu.add_option(year, year)

        menu.send(userid)

# Player Ban Process
def player_list_HANDLE(userid, choice, submenu):

    menu = sam.Menu('bm_ban_length', ban_length_HANDLE, submenu)
    menu.title('Ban Manager')
    menu.description('Choose ban length:')

    # Get the admin ban level
    admin_ban_level = sam.admins.is_allowed(userid, 'ban_level')

    # List each ban length group to the menu
    for length_group in BAN_LENGTH:
        # Make sure the admin has the required ban level
        if admin_ban_level >= length_group:
            menu.add_line('[Ban Level %s]' % length_group)
            for text, seconds in BAN_LENGTH[length_group]:
                menu.add_option([choice, text, seconds], text)

            # Upon adding all the options, make sure the next group
            # is added on a new page
            if admin_ban_level > length_group:
                menu.next_page()

    # Add the permanent ban option if the admin has the required ban level
    if admin_ban_level == 3:
        menu.add_line('[Ban Level 3]')
        menu.add_option([choice, 'Permanent', 0.0], 'Permanent')

    # Let the admin know its ban level on the footer
    menu.footer('You have access to Ban Level %s' % admin_ban_level)
    menu.send(userid)


def ban_length_HANDLE(userid, choice, submenu):

    menu = sam.Menu('bm_ban_reason', ban_reason_HANDLE, submenu)
    menu.title('Ban Manager')
    menu.description('Choose ban reason:')

    # List all the reason as options
    for line in get_reasons_list():
        menu.add_option((choice, line), line)

    menu.send(userid)


def ban_reason_HANDLE(userid, choice, submenu):

    player, length_text, length = choice[0]

    # Get the ban length in seconds, or permanent if 0
    length = 'permanent' if length == 0 else length + sam.timestamp()

    # Construct the ban info dictionary
    ban_info = {
        'steamid': player.steamid,
        'name': player.name,
        'admin': es.getplayername(userid),
        'date': sam.get_time(DATE_FORMAT),
        'expiry_date': length,
        'length_text': length_text,
        'reason': choice[1]
    }

    # Execute the ban process
    ban(ban_info)

    # Send the user the the ban profile page using the ban info dictionary
    addon_menu(userid)
    ban_profile(userid, ban_info)

# Ban History Menus
def ban_history_year_HANDLE(userid, choice, submenu):

    menu = sam.Menu('ban_history_month', ban_history_month_HANDLE, submenu)
    menu.title('Ban Manager')
    menu.description(
        'Bans in %s' % choice,
        'Choose a month:'
    )

    # List all the months in the chosen year
    for month in LOGS[choice]:
        menu.add_option((choice, month), month)

    menu.send(userid)

def ban_history_month_HANDLE(userid, choice, submenu):

    # Extract the year and month from the choice
    year, month = choice

    # Retrieve the ban logs for the selected year and month
    ban_logs = LOGS[year][month]

    # If there's only one ban log for the selected month, display the ban profile directly
    if len(ban_logs) == 1:
        ban_profile(userid, ban_logs[0], submenu)
        sam.msg.hud(userid, 'Found only one ban in %s %s' % (month, year))
        return

    menu = sam.Menu('ban_history_player_list', ban_history_player_list_HANDLE, submenu)
    menu.max_lines = 6
    menu.title('Ban Manager')
    menu.description('Bans in %s %s' % (month, year), 'Choose a player:')

    # Use a set to keep track of players already added to the menu
    players = set()

    for ban_info in ban_logs:
        if ban_info['steamid'] not in players:
            players.add(ban_info['steamid'])
            # Count the number of bans for the current player
            ban_count = sum(ban['steamid'] == ban_info['steamid'] for ban in ban_logs)
            # Add the player to the menu with the ban count next to their name
            menu.add_option((ban_logs, ban_info['steamid'], year, month), 
                            '%s (%s)' % (ban_info['name'], ban_count))

    menu.footer('Note: The number next to the player\'s',
                'name indicates their total bans this month.')
    # Send the menu to the user
    menu.send(userid)

def ban_history_player_list_HANDLE(userid, choice, submenu):

    # Extract the ban logs, player's steamid, year and month from the choice
    ban_logs, steamid, year, month = choice

    # If there's only one ban log for the selected player,
    # display the ban profile directly
    if len(ban_logs) == 1:
        ban_profile(userid, ban_logs[0], submenu)
        return

    # Sort the ban logs in reverse order by date
    ban_logs = sorted(ban_logs, key=lambda x: x['date'], reverse=True)

    menu = sam.Menu('ban_history_players_bans', ban_history_player_bans, submenu)
    menu.max_lines = 6
    menu.title('Ban Manager')
    menu.description('%s\'s Bans in %s %s' % (ban_logs[0]['name'], month, year), 
                     ' ', 
                     'Choose a ban log:')

    for ban_info in ban_logs:
        if ban_info['steamid'] == steamid:
            menu.add_option(ban_info, ban_info['date'])

    # Send the menu to the user
    menu.send(userid)

def ban_history_player_bans(userid, choice, submenu):

    ban_profile(userid, choice, submenu)

# Ban Profile
def ban_profile(userid, ban_info, submenu='ban_manager'):
    """
    Displayes a page with all the info about the given ban
    """

    info = sam.DynamicAttributes(ban_info)
    steamid = info.steamid

    menu = sam.Menu('ban_profile', ban_profile_HANDLE, submenu)
    menu.title('Ban Profile')
    menu.description(
        'PLAYER: ' + info.name,
        'STEAMID: ' + steamid
    )
    menu.add_line(
        'Length: ' + info.length_text,
        'Date: ' + info.date,
        'Expiry Date: ' + get_expiry_date(info.expiry_date),
        'Admin: ' + info.admin,
        'Reason:\n - ' + info.reason
    )

    # If the ban is currently active, add the unban option
    if is_banned(steamid) and ban_info == DATABASE[steamid]:
        menu.separator()
        # Get the admin ban level
        admin_ban_level = sam.admins.is_allowed(userid, 'ban_level')

        # Block the unban option if the admin doesn't have the required ban level
        menu.add_option(ban_info, 'Unban Player', admin_ban_level < 3)
        if admin_ban_level > 3:
            menu.footer('Only Admins with Ban Level 3 may Unban')

    menu.send(userid)


def ban_profile_HANDLE(userid, choice, submenu):

    # If choice was not to unban, return the same page
    if not isinstance(choice, dict):
        submenu.send(userid)
        return

    # Double check if the player is banned
    if not is_banned(choice['steamid']):
        sam.msg.hud(userid, '%s is no longer banned!' % choice['name'])
        addon_menu(userid)
        return

    # Unban the player
    unban(choice['steamid'])

    # Notify all admins
    sam.msg.tell(
        '#admins',
        '#red%s #beigeban removed by #cyan%s#beige.' %\
        (choice['name'], es.getplayername(userid)),
        nametag='#greenBAN MANAGER'
    )
    
    # Return user to the addon menu
    addon_menu(userid)


# Addon Functions
def ban(ban_info):
    """
    Ban a player and log the ban to the database.
    """

    # Get the player's steamid
    steamid = ban_info['steamid']

    # Remove player from ban list if already banned
    if steamid in DATABASE:
        del DATABASE[steamid]

    # Ban Info Copy
    ban_info_copy = dict(ban_info)

    # Register player ban to the addon's database, and save
    DATABASE[steamid] = ban_info_copy
    
    # Add the current year and month to the logs
    year = sam.get_time('%Y')
    month = sam.get_time('%B')
    if year not in LOGS:
        LOGS[year] = {}
    if month not in LOGS[year]:
        LOGS[year][month] = []

    # Add the ban to the logs database, in the correct year and month
    LOGS[year][month].append(ban_info)

    # Save the databases
    save_database()

    # Kick player if he is online
    kick(steamid)

    # Register ban to the player's ban history
    player = sam.profile_system.get_player(steamid)
    if player:
        player.ban_history.append(ban_info_copy)

        # Save the player's profile database upon confirming the ban
        sam.profile_system.save_database()

def unban(steamid):
    """
    Unbans the player of the given steamid
    """

    if steamid in DATABASE:
        del DATABASE[steamid]
        save_database()


def kick(steamid, notify=True, player_userid=None):
    """
    Function used to kick a player from the server upon the ban process is completed
    """

    # Get the player object and the ban info
    player = sam.get_player(steamid if not player_userid else player_userid)
    ban_info = DATABASE.get(steamid)

    # Make sure the player is online and banned
    if not (player, ban_info):
        return
    
    if ban_info['expiry_date'] == 'permanent':
        # Kick reason shown to the kicked player
        text1 = 'You are permanently banned from the server!'
        # Chat message shown to the other players
        text2 = '#red%s #beigehas been #orangepermanently banned #beigefrom the server!'
    else:
        # Kick reason shown to the kicked player
        text1 = 'You were banned from from the server for %s. (Reason: %s)' %\
                (ban_info['length_text'], ban_info['reason'])
        # Chat message shown to the other players
        text2 = '#red%s #beigehas been #orangebanned ' % ban_info['name'] + \
                '#beigefrom the server for #orange%s#beige! #silver(Reason: %s)'\
                % (ban_info['length_text'], ban_info['reason'])

    # Kick the player
    player.kick(text1)

    # Notify the other players
    if notify:
        sam.msg.tell('#human', text2)


def is_player_valid(player, admin=None, bypass_checks={}):
    """
    Checks if a player can be banned by an admin.
    """

    # Check if we bypass all checks
    if bypass_checks.get('all', False):
        return True

    # Check if the player is the admin
    if admin and not (bypass_checks.get('admin', False) and player == admin):
        return False

    # Check if the player is a super admin
    if not bypass_checks.get('super_admin', False) and sam.admins.is_super_admin(player):
        return False

    # Check if the player has higher immunity than the admin
    if not bypass_checks.get('immunity', False) \
        and not sam.admins.compare_immunity(admin, player):
        return False
    
    # Check if the player is already banned
    if not bypass_checks.get('banned', False) and is_banned(player):
        return False

    # If all checks pass, return True
    return True


def is_banned(steamid, notify_expired=False):
    """
    Returns True if the player is banned, False otherwise.
    """

    ban_info = DATABASE.get(steamid)

    # If the player is not in the ban database, return False
    if not ban_info:
        return False

    # If the ban is permanent, return True
    if ban_info['expiry_date'] == 'permanent'\
        or ban_info['expiry_date'] > sam.timestamp():
        return True

    # Notify all admins
    if notify_expired:
        sam.msg.tell(
            '#admins',
            '#red%s #beigeban has expired.' % ban_info['name'],
            nametag='#greenBAN MANAGER'
        )    
    
    # Unban the player
    unban(steamid)
        
    return False

def banned_list():
    """
    Retuns a list of all banned players
    """

    return [steamid for steamid in DATABASE if is_banned(steamid)]

def get_expiry_date(expiry_date):
    """
    Helper function to get the correct expiry date text
    """

    if expiry_date == 'permanent':
        return 'Permanent'
    else:
        return sam.get_time(DATE_FORMAT, expiry_date)

def check_bans():
    """
    Checks the ban database for expired bans and removes them
    """

    # Get the current timestamp
    current_time = sam.timestamp()

    # Loop through the bans in the database
    for steamid, ban_info in DATABASE.items():
        expiry_date = ban_info['expiry_date']
        # Check if the ban has expired
        if expiry_date != 'permanent' and expiry_date <= current_time:
            unban(steamid)

def get_reasons_list():
    """
    Returns a list of all the reasons in the reasons file
    """

    # Check if the reasons file exists
    check_for_reasons_file()

    # Return the reasons list
    return sam.read_file(sam.path.core + '/required/ban_reasons.txt')
    
def check_for_reasons_file():
    """
    Checks if the reasons file exists and creates it if not
    """

    file_path = sam.path.core + '/required/ban_reasons.txt'

    if not os.path.exists(file_path):
        sam.write_file(
            file_path, 
            [
                '// SAM - Ban Reasons File',
                '//',
                '// This file contains a list of reasons that Admins can choose from when banning a player.',
                '// To add or remove a reason, simply add or remove a line from this file.',
                '// The file is read in real-time, so you don\'t need to restart the server or reload the plugin.',
                '//',
                '// You will be asked what reason to choose during the ban process.',
                '// If you want to add a new reason, make sure to keep it short and descriptive.',
                '//',
                '// Note: Lines starting with // will be ignored.',
                '//\n',
                'Disrespected/insulted players',
                'Disrespected/insulted Admins/Moderators',
                'Used wall-hack cheating',
                'Used Aim-bot cheating',
                'Abuse of Voice Chat (Loud noises, play music, etc)',
                'Intentional chat Spam',
                'Intentional abuse of a known game/map bug'
            ]
        )

def save_database():
    """
    Saves both bans and LOGS databases
    """

    sam.databases.save('banned_players_database', DATABASE)
    sam.databases.save('ban_logs', LOGS)


# Game Events
def player_activate(ev):
    """
    Called when a player connects to the server
    """

    steamid = ev['es_steamid']

    # Check if the player is banned
    if is_banned(steamid):
        kick(steamid, False)

def es_map_start(ev):
    """
    Called when a new map is loaded
    """

    # Check for expired bans
    check_bans()