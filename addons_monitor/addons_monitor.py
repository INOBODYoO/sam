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
    p = sam.PageSetup('addons_monitor', addons_monitor_HANDLE, 'home_page')
    p.title('Addons Monitor')
    for name in sorted(addons.keys()):
        addon = addons[name]
        text = addon['name'] + ' '
        if addon['state']:
            text = text + '[running]'
        p.option(name, text, addon['locked'] and not sam.admins.can(uid, 'super_admin'))
    p.footer('Locked Addons can only be',
                'accessed by Super Admins')
    if send: p.send(uid)

def addons_monitor_HANDLE(uid, choice, prev_page):
    addon = addons[choice]
    p = sam.PageSetup('monitor', monitor_HANDLE, prev_page)
    p.title('Addons Monitor')
    p.description(' - NAME: ' + addon['name'],
                     ' - VERSION: %s' % addon['version'],
                     ' - DESCRIPTION:\n' + '\n'.join(addon['description'])
                     if addon['description'] else '')
    p.newline('Toggle Addon State:')
    p.option((choice, 'state', prev_page), '[enabled] |  disabled'\
                if addon['state'] else 'enabled  | [disabled]')
    if sam.admins.can(uid, 'super_admin'):
        p.newline('Toggle Lock State:')
        p.option((choice, 'locked', prev_page), '[locked] |  unlocked'
                    if addon['locked'] else 'locked   | [unlocked]')
    if choice in sam.settings.default['Addons Settings']:
        p.separator()
        p.option((choice, 'settings_help', prev_page), 'Settings Help Window')
    if bool(addon['incompatible']):
        p.footer('Incompatible Addons:\n',
                    ', '.join(addon['incompatible']))
    p.send(uid)

def monitor_HANDLE(uid, choice, prev_page):
    addon, key, previous = choice
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
    addons_monitor_HANDLE(uid, addon, previous)

def _addons_default_data():
    return {
        'example_addon': {
            'name': 'Example Addon',
            'version': 'dev',
            'description': ('Developer Addon Template',),
            'state': False,
            'locked': False,
            'incompatible': ()
        },
        'admins_chat': {
            'name': 'Admins Chat',
            'version': '1.0.b',
            'description': ('Special chat for admins',),
            'state': True,
            'locked': False,
            'incompatible': ()
        },
        'damage_display': {
            'description': ('Displays damage taken/given to attackers/victims',),
            'locked': False,
            'name': 'Damage Display',
            'state': False,
            'version': 1.0,
            'incompatible': ()
        },
        'bots_manager': {
            'description': ('Various options to control bots',),
            'locked': False,
            'name': 'Bots Manager',
            'state': False,
            'version': 1.0,
            'incompatible': ()
        },
        'join_leave_messages': {
            'description': ('Notifications when players join/leave the server',),
            'locked': False,
            'name': 'Join & Leave messages',
            'state': True,
            'version': 1.0,
            'incompatible': ()
        },
        'ban_manager': {
            'description': ('Players banning management',),
            'locked': True,
            'name': 'Ban Manager',
            'state': True,
            'version': 1.0,
            'incompatible': ()
        },
        'server_rules': {
            'description': ('Page to display the server rules',),
            'locked': False,
            'name': 'Server Rules',
            'state': False,
            'version': 1.0,
            'incompatible': ()
        },
        'bomb_countdown': {
            'description': ('Bomb countdown timer',),
            'locked': False,
            'name': 'Bomb Countdown',
            'state': False,
            'version': '1.0',
            'incompatible': ()
        },
        'no_collision': {
            'description': ('Removes players physical collision',),
            'locked': False,
            'name': 'No Collision',
            'state': False,
            'version': 1.0,
            'incompatible': ()
        },
        'high_ping_kicker': {
            'description': ('Kick high ping players after a few warnings',),
            'locked': False,
            'name': 'High Ping Kicker',
            'state': False,
            'version': 1.0,
            'incompatible': ()
        },
        'tests_addon': {
            'description': False,
            'locked': True,
            'name': 'Tests Addon',
            'state': True,
            'version': 1.0,
            'incompatible': ()
        },
        'objects_spawner': {
            'description': ('Tool to spawn, move, rotate & color objects in real-time'),
            'locked': False,
            'name': 'Objects Spawner',
            'state': False,
            'version': 1.0,
            'incompatible': ()
        },
    }
    '''
        'map_manager': {
            'description': ('Options to change server map',),
            'locked': False,
            'name': 'Map Manager',
            'enabled': True,
            'version': 1.0
        },
        'mute_system': {
            'description': ('System to mute players chat/voice',),
            'locked': False,
            'name': 'Mute System',
            'enabled': True,
            'version': 1.0
        },
        'objects_spawner': {
            'description': ('object_spawner_desc',),
            'locked': False,
            'name': 'Objects Spawner',
            'enabled': False,
            'version': 1.0
        },
        'round_end_sounds': {
            'description': ('Plays a sound at the end of the round',),
            'locked': False,
            'name': 'Round End Sounds',
            'enabled': False,
            'version': 1.0
        },
        'round_start_money': {
            'description': ('Gives X amount of money to players on round start',),
            'locked': False,
            'name': 'Round Start Money',
            'enabled': False,
            'version': 1.0
        },
        'server_rules': {
            'description': ('Simple page to display rules',),
            'locked': False,
            'name': 'Server Rules',
            'enabled': False,
            'version': 1.0
        },
        'sound_player': {
            'description': ('Allows Admins to play sounds to players',),
            'locked': False,
            'name': 'Sound Player',
            'enabled': False,
            'version': 1.0
        },
        'spawn_protection': {
            'description': ('Protects players from any damage on spawn',),
            'locked': False,
            'name': 'Spawn Protection',
            'enabled': False,
            'version': 1.0
        },
        'teams_management': {
            'description': ('Menu to manage teams or move player',),
            'locked': True,
            'name': 'Teams Management',
            'enabled': True,
            'version': 1.0
        },
        'teams_switcher': {
            'description': ('Switches both teams at X number of rounds',),
            'locked': False,
            'name': 'Teams Switcher',
            'enabled': False,
            'version': 1.0
        },
        'rankme': {
            'description': ('Ranking system (Kills, Deaths, KDR, etc)',),
            'locked': False,
            'name': 'RankME',
            'enabled': False,
            'version': 1.0
        },
        'auto_respawn': {
            'description': ('Auto respawns players upon death',),
            'locked': False,
            'name': 'Auto Respawn',
            'enabled': False,
            'version': '1.0'
        },
    }'''