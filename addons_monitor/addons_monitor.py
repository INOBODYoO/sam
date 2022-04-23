import os
import es
import psyco
psyco.full()

# Global Variables
sam = es.import_addon('sam')
addons = sam.databases.load('addons_data')

def load():

    # Must load empty script
    es.load('sam/addons')

    # Update & Initialize Addons
    for addon, data in _addons_default_data().items():
        if addon not in addons:
            addons[addon] = data
            continue
        for val in ('name', 'description', 'version', 'incompatible'):
            addons[addon][val] = data[val]
        if addons[addon]['state']:
            es.load('sam/addons/' + addon)

def unload():

    # Unload Addons
    for addon in addons.keys():
        if addons[addon]['state']:
            es.unload('sam/addons/' + addon)

    # Save database
    sam.databases.save('addons_data', addons)

    # Unload empty script
    es.unload('sam/addons')

def module_page(uid, send=True):
    if not sam.admins.can(uid, 'addons_monitor'):
        sam.home_page(uid)
        return
    page = sam.PageSetup('addons_monitor', addons_monitor_HANDLE, 'home_page')
    page.title('Addons Monitor')
    for name in sorted(addons.keys()):
        addon = addons[name]
        text = addon['name'] + ' '
        if addon['state']:
            text = text + '[running]'
        page.option(name, text, addon['locked'] and not sam.admins.can(uid, 'super_admin'))
    page.footer('Locked Addons can only be',
                'accessed by Super Admins')
    if send:
        page.send(uid)

def addons_monitor_HANDLE(uid, choice, prev_page=None):
    addon = addons[choice]
    page = sam.PageSetup('monitor', monitor_HANDLE, 'addons_monitor')
    page.title('Addons Monitor')
    page.description(' - NAME: ' + addon['name'],
                     ' - VERSION: %s' % addon['version'],
                     ' - DESCRIPTION:\n' + '\n'.join(addon['description']))
    page.newline('Toggle Addon State:')
    page.option((choice, 'state'), '[enabled] |  disabled'\
                if addon['state'] else 'enabled  | [disabled]')
    if sam.admins.can(uid, 'super_admin'):
        page.newline('Toggle Lock State:')
        page.option((choice, 'locked'), '[locked] |  unlocked'
                    if addon['locked'] else 'locked   | [unlocked]')
    if choice in sam.settings.default['Addons Settings']:
        page.separator()
        page.option((choice, 'settings_help'), 'Settings Help Window')
    if bool(addon['incompatible']):
        page.footer('Incompatible Addons:\n',
                    ', '.join(addon['incompatible']))
    page.send(uid)

def monitor_HANDLE(uid, choice, prev_page):
    addon, key = choice
    if key == 'settings_help':
        sam.settings.info_window(uid, addon)
    else:
        if key == 'state':
            if addons[addon]['state']:
                es.unload('sam/addons/' + addon)
                if addon in sam.HOME_PAGE_ADDONS:
                    sam.HOME_PAGE_ADDONS.remove(addon)
            else:
                es.load('sam/addons/' + addon)
        addons[addon][key] = not addons[addon][key]
    sam.home_page(uid)
    sam.handle_choice(3, uid)
    addons_monitor_HANDLE(uid, addon)

def _addons_default_data():
    return {
        'example_addon': {
            'name': 'Example Addon',
            'version': 'dev',
            'description': ('Developer Addon Template'),
            'state': False,
            'locked': False,
            'incompatible': ()
        },
        'admins_chat': {
            'name': 'Admins Chat',
            'version': '1.0.b',
            'description': ('Special chat for admins'),
            'state': True,
            'locked': False,
            'incompatible': ()
        },
        'damage_display': {
            'description': ('Displays damage taken/given to attackers/victims'),
            'locked': False,
            'name': 'Damage Display',
            'state': False,
            'version': 1.0,
            'incompatible': ()
        },
        'bots_manager': {
            'description': ('Various options to control bots'),
            'locked': False,
            'name': 'Bots Manager',
            'state': False,
            'version': 1.0,
            'incompatible': ()
        },
        'join_leave_messages': {
            'description': ('Notifications when players join/leave the server'),
            'locked': False,
            'name': 'Join & Leave messages',
            'state': True,
            'version': 1.0,
            'incompatible': ()
        },
        'ban_manager': {
            'description': ('Players banning management'),
            'locked': True,
            'name': 'Ban Manager',
            'state': True,
            'version': 1.0,
            'incompatible': ()
        },
        'server_rules': {
            'description': ('Page to display the server rules'),
            'locked': False,
            'name': 'Server Rules',
            'state': False,
            'version': 1.0,
            'incompatible': ()
        },
        'bomb_countdown': {
            'description': ('Bomb countdown timer'),
            'locked': False,
            'name': 'Bomb Countdown',
            'state': False,
            'version': '1.0',
            'incompatible': ()
        }
    }
    '''
        ,
        ,
        'high_ping_kicker': {
            'description': ('Kicks players after 3 warnings when the ping is too high'),
            'locked': False,
            'name': 'High Ping Kicker',
            'enabled': False,
            'version': 1.0
        },
        'map_manager': {
            'description': ('Options to change server map'),
            'locked': False,
            'name': 'Map Manager',
            'enabled': True,
            'version': 1.0
        },
        'mute_system': {
            'description': ('System to mute players chat/voice'),
            'locked': False,
            'name': 'Mute System',
            'enabled': True,
            'version': 1.0
        },
        'no_player_collision': {
            'description': ('Removes players collision'),
            'locked': False,
            'name': 'No Player Collision',
            'enabled': False,
            'version': 1.0
        },
        'objects_spawner': {
            'description': ('object_spawner_desc'),
            'locked': False,
            'name': 'Objects Spawner',
            'enabled': False,
            'version': 1.0
        },
        'round_end_sounds': {
            'description': ('Plays a sound at the end of the round'),
            'locked': False,
            'name': 'Round End Sounds',
            'enabled': False,
            'version': 1.0
        },
        'round_start_money': {
            'description': ('Gives X amount of money to players on round start'),
            'locked': False,
            'name': 'Round Start Money',
            'enabled': False,
            'version': 1.0
        },
        'server_rules': {
            'description': ('Simple page to display rules'),
            'locked': False,
            'name': 'Server Rules',
            'enabled': False,
            'version': 1.0
        },
        'sound_player': {
            'description': ('Allows Admins to play sounds to players'),
            'locked': False,
            'name': 'Sound Player',
            'enabled': False,
            'version': 1.0
        },
        'spawn_protection': {
            'description': ('Protects players from any damage on spawn'),
            'locked': False,
            'name': 'Spawn Protection',
            'enabled': False,
            'version': 1.0
        },
        'teams_management': {
            'description': ('Menu to manage teams or move player'),
            'locked': True,
            'name': 'Teams Management',
            'enabled': True,
            'version': 1.0
        },
        'teams_switcher': {
            'description': ('Switches both teams at X number of rounds'),
            'locked': False,
            'name': 'Teams Switcher',
            'enabled': False,
            'version': 1.0
        },
        'rankme': {
            'description': ('Ranking system (Kills, Deaths, KDR, etc)'),
            'locked': False,
            'name': 'RankME',
            'enabled': False,
            'version': 1.0
        },
        'auto_respawn': {
            'description': ('Auto respawns players upon death'),
            'locked': False,
            'name': 'Auto Respawn',
            'enabled': False,
            'version': '1.0'
        },
    }'''