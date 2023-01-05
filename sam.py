from __future__ import with_statement

import os
import random as rdm
import time
from datetime import datetime

import cmdlib
import es
import gamethread
import playerlib
import psyco
import simplejson as json
import usermsg
psyco.full()

# Script Info
plugin = es.AddonInfo()
plugin.name = 'S.A.M (Server Administration Menu) [Remastered]'
plugin.version = '0.0.1'
plugin.basename = 'sam'
plugin.author = 'NOBODY'
plugin.description = 'AllInOne tool for addons monitoring & server/players administration'
plugin.url = 'https://github.com/INOBODYoO/sam'
plugin.developer_mode = 1

''' Developer Mode Levels:
    1 = Python Exceptions / eventscripts_debug set to 0
    2 = Pages Setup Debug
    3 = Sandbox Mode (Anyone can access anything in the menu
                      even if not a Super or Regular Admin)
    4 = Prints all settings updates to console '''


def debug(lvl, *message):
    if lvl == plugin.developer_mode:
        for line in message:
            print('[SAM][DEBUG] %s' % line)


# Turn off ES debug completely (if SAM debug is)
es.server.cmd('eventscripts_debug %s' % ('0' if bool(plugin.developer_mode) else '-1'))

# Global Variables
MODULES = ('players_manager', 'admins_manager', 'addons_monitor', 'settings_manager')
FILTERS = ('#all', '#human', '#ct', '#t', '#alive', '#dead', '#spec', '#bot')
HOME_PAGE_ADDONS = []

# Core Module Systems
print('[SAM]   - Initializing Core Systems')


class _Cache:
    def __init__(self):
        self.menus = {}
        self.users_active_menu = {}
        self.sounds = {}


cache = _Cache()


class _Path:
    def __init__(self):
        self.core = es.getAddonPath('sam')
        self.addons = self.core + '/addons/'
        self.sounds = 'cstrike/sound/sam_sounds/'
        self.settings = self.core + '/required/settings.json'
        self.databases = self.core + '/required/databases/'
        self.info_window_file = self.core + '/required/info_window (ignore this file).txt'


path = _Path()


class _DatabaseSystem:
    # Create directories
    def __init__(self):
        if not os.path.exists(path.databases):
            os.makedirs(path.databases)
        if not os.path.exists(path.databases + 'addons/'):
            os.makedirs(path.databases + 'addons/')

    @staticmethod
    def load(db_file, bypass=False):
        if not bypass:
            db_file = path.databases + db_file + '.json'
        if os.path.isfile(db_file):
            with open(db_file, 'r') as f:
                return json.load(f)
        return {}

    @staticmethod
    def save(db_file, data, bypass=False):
        if not bypass:
            db_file = path.databases + db_file + '.json'
        if not bool(data) and os.path.isfile(db_file):
            os.remove(db_file)
            return
        try:
            with open(db_file, 'w') as f:
                json.dump(data, f, indent=4, sort_keys=True)
        except AttributeError:
            return


databases = _DatabaseSystem()


class _SettingsSystem:

    def __init__(self):
        self.gen = 'General Settings'
        self.add = 'Addons Settings'
        self.default = {
            'General Settings': {
                'chat_prefix': {
                    'desc': ['Prefix in the beginning of every chat message',
                             '(Can be color coded, take default as an example)'],
                    'default': '#redSAM',
                },
                'anti_spam_chat_messages': {
                    'desc': ['Repetitive messages sent by SAM will be blocked for a few',
                             'seconds to avoid spamming the chat'],
                    'default': True,
                },
                'enable_!rcon_command': {
                    'desc': [
                        'Enables !rcon command. (Requires "Rcon Command" permission)',
                        'Allow Admins to execute almost any kind of server',
                        'commands/variables through the game chat'
                    ],
                    'default': True,
                },
                'enable_!admins_command': {
                    'desc': ['Opens a page with a list of all Admins currently online'],
                    'default': True,
                },
                'enable_menus_clock': {
                    'desc': [
                        'Displays a clock in the top right corner of all pages.',
                        '(Local time, which is the time from where the server is hosted)'
                    ],
                    'default': True,
                },
                'pages_separator_line_length': {
                    'desc': ['The Length of pages separator lines (Max is 40)'],
                    'default': 40,
                },
            },
            'Addons Settings': {},
        }

        # Create database
        self._save(self._load())

    def __repr__(self):
        return str(self.__call__())

    def __str__(self):
        return self.__repr__()

    def __call__(self, arg=None):
        config = self._load()

        class Config(object):
            def __init__(self, obj):
                self.__dict__.update(obj.copy())

            def __getattr__(self, attr):
                return self.__dict__[attr]

        if arg is None:
            return Config(config[self.gen])
        elif arg in config.keys():
            return config[arg]
        elif arg in config[self.gen].keys():
            return config[self.gen][arg]
        elif arg in config[self.add].keys():
            return Config(config[self.add][arg])

    def _load(self):
        data = databases.load(path.settings, True)
        if not data:
            data['Addons Settings'] = {}
            data[self.gen] = dict([(k, v['default'])
                                   for k, v in self.default[self.gen].items()])
        default = self.default[self.gen]
        config = data[self.gen]
        if config == default:
            return data
        for cmd in default.keys():
            if cmd not in config.keys():
                config[cmd] = default[cmd]['default']
        return data

    @staticmethod
    def _save(data):
        databases.save(path.settings, data, True)

    def addon_config(self, addon, config):
        data = self._load()
        if addon not in data[self.add].keys():
            data[self.add][addon] = dict([(k, v['default']) for k, v in config.items()])
        else:
            self.default[self.add][addon] = config.copy()
            for k, v in config.items():
                if k not in data[self.add][addon].keys():
                    data[self.add][addon][k] = v['default']
        self._save(data)

    def info_window(self, uid, key):
        data = self._load()
        if key == self.gen:
            data = data[self.gen].copy()
            obj = self.default[key].copy()
        elif key in self.default[self.add].keys():
            data = data[self.add][key].copy()
            obj = self.default[self.add][key].copy()
        else:
            msg.hud(uid, 'Error: Could not retrieve %s settings.' % title(key))
            return
        lines = []
        for k, v in obj.items():
            lines.extend(('[ %s ]' % title(k),
                          '- Description:\n%s' % '\n'.join(v['desc']),
                          '- Default Value: %s' % v['default'],
                          '- Current Value: %s\n' % data[k]))
        msg.info(uid,
                 key if key == self.gen else title(key) + ' | Settings Help Page',
                 *lines)


settings = _SettingsSystem()


class _ChatFiltersSystem:

    def __init__(self):
        self.filters = {}

    class _Filter(object):
        def __init__(self, name, block, remove_on_empty, users):
            self.name = name
            self.block = block
            self.remove_on_empty = remove_on_empty
            self.users = users

    def create(self, name, block, remove_on_empty=False, *users):
        users = [u for u in users if isinstance(u, int)]
        if name in self.filters.keys():
            self.filters[name].users.extend(users)
            return
        self.filters[name] = self._Filter(name, block, remove_on_empty, users)
        es.addons.registerSayFilter(block)

    def remove(self, name, block):
        if name in self.filters.keys():
            del self.filters[name]
        try:
            es.addons.unregisterSayFilter(block)
        except ValueError:
            pass

    def remove_user(self, uid, name):
        if name in self.filters.keys():
            f = self.filters[name]
            if uid in f.users:
                f.users.remove(uid)
            if f.remove_on_empty and len(f.users) == 0:
                self.remove(name, f.block)

    def is_allowed(self, uid, name):
        return name in self.filters.keys() and uid in self.filters[name].users

    def in_filter(self, uid):
        for name in self.filters.keys():
            if uid in self.filters[name].users:
                return True
        return False

    def remove_all_filters(self):
        for k, v in self.filters.items():
            try:
                es.addons.unregisterSayFilter(v.block)
            except ValueError:
                pass
        self.filters.clear()


chat_filters = _ChatFiltersSystem()


class _MessageSystem:
    ''' Class with all message types functions '''

    def __init__(self):
        self.spam_queue = []
        self.colors = {'blue': '71ACDF',
                       'green': '5cb85c',
                       'orange': 'f0ad4e',
                       'red': 'EF625D',
                       'black': '292b2c',
                       'white': 'FFFFFF',
                       'pink': 'ffc0cb',
                       'gray': 'a9a9a9',
                       'purple': '931CE2',
                       'yellow': 'ffff00',
                       'cyan': '00ffff',
                       't': 'ff3d3d',
                       'ct': '9bcdff',
                       'spec': 'cdcdcd',
                       'default': 'ffb300'}

    def _compile(self, text, remove=False, special=True):
        ''' Compiles the given text making 3 essential changes:
            - Replaces color tags (e.g #blue) with color codes for colorful chat messages
            - Removes special characters like Newline (e.g \\n) from the text
            - Strips white spaces from the text

            * If the remove argument is true then removes the color tags
            instead of replacing them, this is so if the text is sent to console
            or hudhints the text appears clean without the tags.

            * If the special argument is False then special characters won't be removed
        '''
        if remove:
            for color in self.colors.keys():
                text = text.replace('#' + color, '')
        else:
            for color, code in self.colors.items():
                text = text.replace('#' + color, '\x07' + code)
        if special:
            for i in ('\\n', '\\r', '\\t'):
                text = text.replace(i, '')
        return text.strip()

    @staticmethod
    def _sort_users(users):
        if isinstance(users, int) or users in FILTERS:
            return users
        elif users == '#admins':
            return player_list('#admins')
        new = []
        for x in users:
            if str(x).startswith('#'):
                for ply in player_list(x):
                    if ply not in new:
                        new.append(ply)
                continue
            x = int(x)
            if es.exists('userid', x) and x not in new:
                new.append(x)
        return new

    def _in_queue(self, text):
        text_hash = hash(text)
        if text_hash in self.spam_queue:
            return True
        self.spam_queue.append(text_hash)
        delay_task(10, 'message_spam_queue_%s' % text_hash, self.spam_queue.remove, text_hash)
        return False

    def tell(self, users, text, prefix=True, tag=False, log=False):
        ''' Chat message that can be sent to any player or group of players
            The text can be color coded

            e.g: #red{prefix} | #green{tag} | #whiteHello World '''

        prefix = '#default%s #gray| ' % settings('chat_prefix') if prefix else '#default'
        tag = '#green%s #gray| ' % tag if tag else ''
        text2 = '%s%s#white%s' % (prefix, tag, text)
        if self._in_queue(text):
            return
        if log and ('#all' in users or '#human' in users):
            self.console(text, tag)
        usermsg.saytext2(self._sort_users(users), 0, '''%s''' % self._compile(text2))

    def hud(self, users, *text):
        ''' A hudhint type message which appears in the bottom center of the player screen '''
        usermsg.hudhint(self._sort_users(users),
                        self._compile('| SAM |\n' + '\n'.join(map(str, text)), True))

    def center(self, users, text):
        usermsg.centermsg(self._sort_users(users), text)

    def side(self, users, *text):
        usermsg.keyhint(self._sort_users(users),
                        self._compile('\n'.join(map(str, text)),
                                      remove=True,
                                      special=False))

    def vgui_panel(self, users, panel_name, visible, data=None):
        if data is None:
            data = {}
        usermsg.showVGUIPanel(self._sort_users(users), panel_name, visible, data)

    def motd(self, users, window_title, url_or_filepath, message_type=2):
        ''' Message Of The Day type message, to send URL pages to
            users using the in-game MOTD window browser '''
        usermsg.motd(self._sort_users(users),
                     message_type,
                     'SAM | %s' % window_title,
                     url_or_filepath)

    def info(self, users, window_title, *lines):
        with open(path.info_window_file, 'w') as f:
            f.write('\n'.join(lines))
        self.motd(self._sort_users(users),
                  window_title,
                  path.info_window_file.replace('\\', '/'), 3)

    def console(self, text, tag=None):
        ''' Prints a message to the server console with SAM's prefix, a "tag" can be used
            to identify the system or addon from which the message is being sent

            e.g. SAM | PLAYERS MANAGER | X was kicked from the server. '''
        print(self._compile('[%s][SAM] %s%s' %
                            (get_time('%H:%M:%S'),
                             tag.upper() + ' | ' if tag else '',
                             text),
                            True))


msg = _MessageSystem()


class _AdminsSystem:

    def __init__(self):
        self.admins = databases.load('admins_data')
        self.groups = databases.load('admins_groups')
        self.addons_flags = []
        self.flags = ['addons_monitor',
                      'admins_manager',
                      'players_manager',
                      'kick_players',
                      'rcon_command',
                      'settings_manager']

        # Update admin groups with new flags if any new flag exists
        for k, v in self.groups.items():
            keys = v.keys()
            for group in (self.flags, self.addons_flags):
                for i in group:
                    if i not in keys:
                        v[i] = False

    def __repr__(self):
        return str(self.admins)

    def __str__(self):
        return self.__repr__()

    def __call__(self, tar=None, key=None):
        if self.is_admin(tar):
            return self.admins[tar][key] if key else self.admins[tar]
        if tar == 'groups':
            return self.groups
        if tar in self.groups.keys():
            return self.groups[tar][key] if key else self.groups[tar]
        return self.admins

    def list(self, arg=None):
        return sorted(self.groups.keys()) if arg == 'groups' else self.admins.keys()

    def items(self, arg=None):
        return sorted(self.groups.items()) if arg == 'groups' else self.admins.items()

    def is_admin(self, user):
        if user is None:
            return None
        elif plugin.developer_mode == 3:
            return True
        elif isinstance(user, int) and es.exists('userid', user):
            user = getsid(user)
        elif isinstance(user, playerlib.Player):
            user = user.steamid
        return user in self.admins.keys()

    def can(self, uid, flag, notify=True):
        ''' Check whether an Admin is allowed to

            uid: userid
            flag:
        '''
        if plugin.developer_mode == 3:
            return True
        sid = getsid(uid)
        if not self.is_admin(sid):
            return False
        admin = self.admins[sid]
        if flag == 'super_admin':
            return admin['super_admin']
        if admin['super_admin']:
            return 3 if flag == 'ban_level' else True
        group = admin['group']
        group = self.groups[group] if group and group in self.groups.keys() else None
        if flag in self.flags:
            x = admin[flag] or (group[flag] if group else False)
            if not x and notify:
                msg.hud(uid, 'You don\'t have flag to use %s' % title(flag))
            return x
        elif flag == 'ban_level':
            return max(admin['ban_level'], group['ban_level'] if group else 0)

    def immunity_check(self, uid, adm2):
        if plugin.developer_mode == 3:
            return True
        sid = getsid(uid)
        if not self.is_admin(adm2) or sid == adm2:
            return True
        adm1 = self.admins[sid]
        adm2 = self.admins[adm2]
        if adm2['super_admin']:
            msg.hud(uid, 'Action denied! %s is a Super Admin.' % adm2['name'])
            return False
        elif adm1['super_admin']:
            return True

        def group_immunity(adm):
            return self.groups[adm['group']]['immunity_level'] if adm['group'] else 0

        adm1_g = group_immunity(adm1)
        adm2_g = group_immunity(adm2)
        check = max(adm1['immunity_level'], adm1_g) > max(adm2['immunity_level'], adm2_g)
        if not check:
            msg.hud(uid,
                    'Action denied! %s has higher immunity level than you' % adm2['name'])
        return check

    def update_admin(self, admin):
        uid = getuid(admin)
        if uid is None:
            return
        admin = get_player(uid)
        data = self.admins[admin.steamid]
        data['name'] = admin.name.encode('utf-8')
        for flag in self.flags:
            if flag not in data.keys():
                data[flag] = False
        for i in data.keys():
            if i not in self.flags and i not in ('name', 'since', 'immunity_level',
                                                 'super_admin', 'ban_level', 'group'):
                del data[i]


admins = _AdminsSystem()


class _AddonsMonitor:
    class AddonClass(str):
        def __init__(self, addon):
            self.basename = addon
            self.name = 'unkown_addon'
            self.state = False
            self.locked = False
            self.version = '0.0'
            self.description = []

        def __repr__(self):
            return str(type(self))

        def __str__(self):
            return self.__repr__()

        def __call__(self, key):
            return self.__dict__[key]

    def __init__(self):

        # Init Addons dictionary instance
        self.addons = {}

        # Installed Addons verification
        self._verify_installed_addons()

        # Get Addons Monitor database
        database = databases.load('addons_monitor')

        # Get all Addons state and lock condition
        for addon in database.keys():
            if addon not in self.addons.keys():
                continue
            for key in ('state', 'locked'):
                self.addons[addon].__dict__[key] = database[addon][key]

    def __repr__(self):
        return str(self.addons)

    def __str__(self):
        return self.__repr__()

    def __call__(self, addon=None):
        return self.addons[addon] if addon in self.addons.keys() else None

    def _verify_installed_addons(self):
        # Loop over all installed Addons
        installed = self.addons_dir_list()

        for addon in installed:
            # Check if metadata file is valid
            metadata = path.addons + addon + '/metadata.json'
            if not os.path.isfile(metadata):
                debug(1, '[Addons Monitor] Failed to install/update %s \
                          addon, missing metadata.json file' % title(addon))
                continue
            metadata = databases.load(metadata, bypass=True)
            if not metadata:
                debug(1, '[Addons Monitor] Failed to install/update %s,\
                          invalid metadata.json file' % title(addon))
                continue

            # Confirm installation by saving copying metadata
            if addon not in self.addons.keys():
                self.addons[addon] = self.AddonClass(addon)
                self.addons[addon].__dict__.update(metadata.copy())
                continue

            # Else update the Addon's infos
            for key in metadata.keys():
                if key in ('state', 'locked') \
                        or metadata[key] == self.addons[addon].__dict__[key]:
                    continue
                self.addons[addon].__dict__[key] = metadata[key]

    def save_database(self):
        database = {}
        for addon in self.addons.keys():
            database[addon] = self.addons[addon].__dict__.copy()
        databases.save('addons_monitor', database)

    @staticmethod
    def addons_dir_list():
        ''' List of Addons in the addons folder '''
        return (i for i in os.listdir(path.addons) if os.path.isdir(path.addons + i))

    def is_running(self, addon):
        if addon not in self.addons.keys():
            return False
        return self.addons[addon].state

    def import_addon(self, addon):
        if not self.is_running(addon):
            debug(1, 'Could not import %s, addon is not running or is missing' % addon)
            return None
        return import_module('addons/' + addon)


addons_monitor = _AddonsMonitor()


class _CommandsSystem:

    def chat(self, command, block):
        self.delete(command)
        cmdlib.registerSayCommand('!' + command, block, 'SAM chat command')
        cmdlib.registerSayCommand('!sam_' + command, block, 'SAM chat command')

    def client(self, command, block):
        self.delete(command)
        cmdlib.registerClientCommand('sam_' + command, block, 'SAM client command')

    def server(self, command, block):
        self.delete(command)
        cmdlib.registerServerCommand('sam_' + command, block, 'SAM console command')

    @staticmethod
    def delete(command):
        if es.exists('saycommand', '!' + command):
            cmdlib.unregisterSayCommand('!' + command)
            cmdlib.unregisterSayCommand('!sam_' + command)
        command = 'sam_' + command
        if es.exists('clientcommand', command):
            cmdlib.unregisterClientCommand(command)
        if es.exists('variable', command) or es.exists('command', command):
            cmdlib.unregisterServerCommand(command)


cmds = _CommandsSystem()


class _PlayersProfileSystem:
    ''' Systems responsiple for gathering various types of information about
        the player to be used in multiple other systems
    '''

    class Player(object):
        def __init__(self, data):
            for key in data.keys():
                setattr(self, key, data[key])

    def __init__(self):
        # Load database
        self.data = databases.load('players_data')

        # Update active players
        for uid in userid_list('#human'):
            self.update(uid)

    def __call__(self, user):
        ''' Return the Player info as class object '''
        target = None
        if isinstance(user, int):
            target = getsid(user)
        elif str(user).startswith('[U:') or str(user).startswith('STEAM_'):
            target = user
        return self.Player(self.data[target]) if target in self.data.keys() else None

    def list(self):
        return [self.Player(self.data[k]) for k in self.data.keys()]

    def update(self, uid):
        ''' Updates the player info into the database '''
        ply = get_player(uid)
        if ply.steamid == 'BOT':
            return
        i = {'name': ply.name.encode('utf-8'),
             'steamid': ply.steamid,
             'first_seen': get_time('%d/%m/%Y'),
             'last_seen': get_time('%d/%m/%Y at %H:%M:%S'),
             'ban_history': [],
             'kick_history': [],
             'mute_history': [],
             'reports': []}

        # Update any new keys and values
        if ply.steamid in self.data.keys():
            d = self.data[ply.steamid]
            for k, v in i.items():
                if k not in self.data[ply.steamid].keys():
                    d[k] = v
            d['name'] = ply.name.encode('utf-8')
        # Or add player to database if not in yet
        else:
            self.data[ply.steamid] = i.copy()
        databases.save('players_data', self.data)


class Menu(object):
    ''' Class system based on EventScripts Popuplib library to create paged menus
        using SourceEngine's Radio Popups as the user interface.  '''

    def __init__(self, menu_id, callback=None, submenu=None):
        self.menu_id = menu_id
        self.callback = callback
        self.submenu = False
        self.submenu_page = 1
        if isinstance(submenu, str):
            self.submenu = submenu
        elif submenu:
            self.submenu = submenu.menu_id
            self.submenu_page = submenu.page
        self.title_text = False
        self.header_text = True
        self.footer_text = False
        self.description_text = False
        self.close_option = True
        self.pages_counter = True
        self.pages = {1: []}
        self.maxlines = 7
        self.validate_all_lines = False
        self.timeout = 0
        self.blocked_options = []
        length = int(settings('menus_separator_line_length'))
        self.separator_line = '-' * length if length <= 40 else 40

    def title(self, text):
        ''' Adds/Changes the title of the menu '''
        self.title_text = ' :: ' + text

    def description(self, *lines):
        ''' Adds/Changes the description of the menu
            Note: Multiple lines can be given as a list() '''
        self.description_text = '\n'.join(lines)

    def footer(self, *lines):
        ''' Adds/Changes the footer of the menu
            Note: Multiple lines can be given as a list() '''
        self.footer_text = self.separator_line + '\n' + '\n'.join(lines)

    def add_line(self, *lines):
        ''' Adds a new line to the menu
            Note: Multiple lines can be given as a list() '''
        self.pages[self._current_page()].extend([str(line) for line in lines])

    def add_option(self, obj, text, blocked=False):
        ''' Adds a new option to the menu  '''

        # Get the current page
        page = self._current_page()
        # Add the option to the list of lines of the current page
        self.pages[page].append({'object': obj,
                                 'text': text,
                                 'blocked': blocked,
                                 'choice': len(self.pages[page]) + 1,
                                 'page': page})

    def add_multiple_options(self, obj):
        ''' Adds multiple options, can either from a list or a dict'''

        if isinstance(obj, dict):
            for k, v in obj.items():
                self.add_option(v, k)
            return
        for i in obj:
            self.add_option(i, i)

    def separator(self):
        ''' Adds a seperator line to the menu '''
        self.add_line(self.separator_line)

    def next_page(self):
        ''' Initializes the next page in the menu.
            Say one requires a page to have just 3 options, but yet has more options
            to be added on a different page.
        '''
        self.pages[max(self.pages.keys()) + 1] = []

    def send(self, users, page=1):
        ''' Should be called once the menu is fully setup and ready to be sent to the user
            Builds the given page with the menu title, description, lines, options, etc.,
            and sends it to the user/users.
        '''
        debug(2, '[Initializing Menu Setup Process]')
        debug(2, '- Menu ID: %s' % self.menu_id)
        # Abort if users do not exist at all
        if not users:
            debug(2, '[Aborting Menu Setup Process: No Valid Users Found]')
            return
        debug(2, '- Menu Features:')
        debug(2, '   * Header: %s' % str(bool(self.header_text)))
        # Each page text are built line by line, therefore create a display list to
        # store all lines and options by order they were added
        display = []
        # First, lets add the header of the menu, by default is SAM's title and current
        # version, also a local clock if enabled
        if bool(self.header_text):
            display.append(
                'SAM v%s %s\n \n' %
                (plugin.version,
                 ' ' * 30 + get_time('%H:%M') if settings('enable_menus_clock') else ''))
        debug(2, '   * Title: %s' % str(bool(self.title_text)))
        # Second, we add the title of the menu
        if bool(self.title_text):
            total_of_pages = len(self.pages.keys())
            if total_of_pages > 1:
                display.append('%s   (%s/%s)' % (self.title_text, page, total_of_pages)
                               if self.pages_counter else self.title_text)
            else:
                display.append(self.title_text)
        debug(2, '   * Description: %s' % str(bool(self.description_text)))
        # Third, we add the description of the menu
        if bool(self.description_text):
            display.extend((self.separator_line, self.description_text))
        display.append(self.separator_line)
        debug(2, '   * Settting up Lines & Options')
        # Forth, start adding the page lines and options
        # Build a new list of blocked options
        self.blocked_options = []
        # Check if the number of max lines is between the valid values
        if self.maxlines not in range(1, 8):
            self.maxlines = 7
        # Iterate through the page's lines and options
        option_number = 0
        for line in self.pages[page]:
            # If it's just a text line we simply add the line
            if isinstance(line, str):
                display.append(line)
                # TODO: Investigate if its worth validating all lines anyway
                if self.validate_all_lines:
                    option_number += 1
                continue
            # If it's an option, we add one to the option_number to keep track which
            # options is being added
            option_number += 1
            # It its blocked add it the blocked_options list
            if line['blocked']:
                self.blocked_options.append(option_number)
            # Add the option text, if blocked then appears as a normal text line
            display.append('%s%s. %s' % ('' if line['blocked'] else '->',
                                         option_number,
                                         line['text']))
        debug(2, '   * Blocked Options: %s' % len(self.blocked_options))
        debug(2, '   * Footer: %s' % str(bool(self.footer_text)))
        # Add the footer of the menu
        if self.footer_text:
            display.append(self.footer_text)
        if self.close_option:
            display.append(self.separator_line)
        # Is not the first to add the previous page option
        if page > 1:
            debug(2, '- Previous Page: %s' % self.submenu)
            display.append('->8. Previous Page')
        # Check if there's a page next to the given one and add the next page option if so
        if page + 1 in self.pages.keys():
            debug(2, '- Next Page Option Set')
            display.append('->9. Next Page')
        debug(2, '- Close Option: %s' % str(self.close_option))
        # Check if the close option should be added
        if self.close_option:
            # Check if the there's a submenu to the active menu, if so the user goes back
            # to the submenu, otherwise we just close the menu on the user
            text = '0. %s' % ('Previous Menu' if self.submenu else 'Close Menu')
            display.append(text)
        # If nothing was added to the page we simply abort the process
        if not display:
            debug(2, '[Aborting Menu Setup Process: Empty Page]')
            return
        display = '\n'.join(display)
        debug(2, '>> Menu display build process complete!')
        # At this point the page is complete, and we can cache it
        cache.menus[self.menu_id] = self
        debug(2, '>> Menu caching complete!')
        users = (users,) if isinstance(users, int) else userid_list(users)
        debug(2, '>> Sending Menu To Users:')
        # Send the page to each user
        for user in users:
            uid = int(user)
            debug(2, '   -------------------------')
            debug(2, '   userid - steamid')
            debug(2, '   -------------------------')
            debug(2, '   %s      - %s' % (user, getsid(user)))
            debug(2, '   -------------------------')
            # Make sure the user doesn't have an active page being refreshed
            _cancel_menu_refresh(uid)
            # Cache the menu as the user's new active menu
            cache.users_active_menu[uid] = {'menu_id': self.menu_id, 'page': page}
            # Display the menu to the user in-game
            es.showMenu(self.timeout, uid, display.encode('utf-8'))
            # If there's no timeout to the page then create a loop to refresh the page to
            # the user, so it maintains active until the user chooses something, or closes
            # the page
            if self.timeout == 0:
                delay_task(1, 'refresh_%s_page' % uid, self._refresh_page, uid)
        debug(2, '[Page Setup Process Complete]')

    def send_option(self, uid, option, page=None):
        option = self.get_option_data(option, page)
        self.send(uid, option['page'])
        handle_choice(option['option_number'], uid)

    def get_option_data(self, obj, page=None):
        ''' Returns a dictionary containing all the data from the option.
            The object can be the number that the user must select to choose the option.
            It can also be the actual object from the option,
            which is given in the menu's callback block once the user makes a selection.

            The dictionary contains:
            'object': The object that is given in the menu's callback block.
            'text': The option text that appears in the page.
            'blocked': A boolean value indicating whether the option is blocked.
            'option_number': The number that the user must select to choose the option.
            'page': The page of the menu the option is on
        '''

        def look_in_page(_obj, _page):
            options = self.get_page_options(_page)
            # If obj is integer, then must be the option number
            if isinstance(_obj, int):
                return options[_obj - 1]
            # Alternativaly loop through all options and compare if the object is the same
            for option in options:
                if option['object'] == obj:
                    return option
            else:
                return None

        # If a page was given
        if page:
            return look_in_page(obj, page)
        else:
            # If a page wasn't given then look for the option in all the menu pages
            for page in self.pages.keys():
                option = look_in_page(obj, page)
                if option == obj:
                    return option
            else:
                return None

    def get_page_options(self, page=None):
        ''' Returns the list of all the page's options '''

        # If a page was not given, then get the current page
        if not page:
            page = self._current_page()
        return [i for i in self.pages[page] if isinstance(i, dict)]

    @staticmethod
    def _refresh_page(user):
        ''' Simply gets the user's current active page and re-sends it '''

        if user not in cache.users_active_menu.keys():
            return
        menu = cache.users_active_menu[int(user)]
        if menu['menu_id'] in cache.menus.keys():
            cache.menus[menu['menu_id']].send(user, menu['page'])

    def _current_page(self):
        ''' Returns the current page that is being added lines and options '''

        page = max(self.pages.keys())
        # Check if the number of the page options higher or equal to the max lines
        # if so then initiate the next page
        if self.maxlines and len(self.get_page_options(page)) >= self.maxlines:
            page += 1
            self.pages[page] = []
        return page


# Core Functions
def load():
    # Initialize core commands
    cmds.chat('sam', sam_CMD)
    cmds.chat('rcon', rcon_CMD)
    cmds.chat('admins', admins_CMD)
    cmds.client('menu', sam_CMD)

    # Load main modules
    msg.console('* Loading Main Modules:')
    for module in MODULES:
        es.load('sam/' + module)
        msg.console('  - Loaded %s Module' % title(module))

    # Make plugin version public
    es.setinfo('sam_version', plugin.version)
    es.makepublic('sam_version')
    msg.tell('#all', 'Loaded', tag='#blue' + plugin.version)


def unload():
    # Close active menus from users
    for user in cache.users_active_menu.keys():
        handle_choice(10, user, True)
        msg.hud(user, 'Your page was closed since SAM is unloading.')

    # Terminate all chat filters
    chat_filters.remove_all_filters()

    # Clear cache
    cache.menus.clear()
    cache.users_active_menu.clear()

    # Delete core module commands
    cmds.delete('sam')
    cmds.delete('menu')
    cmds.delete('rcon')
    cmds.delete('admins')

    # Save databases
    databases.save('admins_data', admins.admins)
    databases.save('admins_groups', admins.groups)
    databases.save('players_data', players.data)

    # Unload main modules
    msg.console('* Unloading Main Modules:')
    for module in MODULES:
        es.unload('sam/' + module)
        msg.console('* Unloaded %s Module' % title(module))

    msg.tell('#all', 'Unloaded', tag='#blue' + plugin.version)


# Home Page
def home_page(uid):
    menu = Menu('home_page', home_page_HANDLE)
    menu.title('Home Page')
    for module in MODULES:
        menu.add_option(module, title(module))
    if HOME_PAGE_ADDONS:
        menu.separator()
        menu.add_line('  :: Addons')
        menu.separator()
        for basename in HOME_PAGE_ADDONS:
            addon = addons_monitor(basename)
            if addon is None or not addon.state:
                HOME_PAGE_ADDONS.remove(basename)
                home_page(uid)
                continue
            menu.add_option(basename, addon.name)
    menu.send(uid)


def home_page_HANDLE(uid, choice, submenu):
    if choice in MODULES:
        import_module(choice).module_menu(uid)
        return
    elif choice in HOME_PAGE_ADDONS:
        addons_monitor.import_addon(choice).addon_menu(uid)


# Command Functions
def sam_CMD(uid, args):
    if not bool(admins.admins):
        import_module('admins_manager').first_admins_setup(uid)
        return
    if admins.is_admin(uid):
        home_page(uid)
    else:
        msg.hud(uid, 'You don\'t have permission to use this')


def rcon_CMD(uid, args):
    if not admins.can(uid, 'rcon_command') or not settings('enable_!rcon_command'):
        return
    if not args:
        msg.tell(uid, '#blueSyntax Example:\n#orange!rcon <command/variable> {arguments/value}')
        return
    cmd = args.pop(0)
    args = ' '.join(args) if args else None
    if es.exists('variable', cmd):
        if cmd == 'sv_cheats' and not admins.can(uid, 'super_admin'):
            msg.hud(uid, 'Only Super Admins can change sv_cheats command!')
            return
        if args is None:
            msg.tell(uid, 'No arguments given!')
            return
        es.ServerVar(cmd).set(args)
        msg.tell(uid, 'RCON: #blueSet #green%s #blueto #green%s' % (cmd, args))
        return
    elif es.exists('command', cmd):
        if args:
            es.server.insertcmd('%s %s' % (cmd, args))
        elif cmd.startswith(('bot_', 'es_')):
            es.server.insertcmd(cmd)
        msg.tell(uid, 'RCON: #blueExecuted %s %s' % (str(cmd), str(args)))
        return
    else:
        msg.tell(uid, '#green\'%s\' #orangeis not a command or server variable.' % cmd)


def admins_CMD(uid, args):
    if not settings('enable_!admins_command'):
        return
    lis1 = [admins(i.steamid) for i in player_list('#human') if admins.is_admin(i)]
    if not lis1:
        msg.tell(uid, '#redThere are no #cyanAdmins #redonline')
        return
    menu = Menu('admins_list')
    menu.header_text = False
    menu.title('Admins Online (%s of %s)' % (len(lis1), len(admins.list())))
    lis2 = []
    for i in lis1:
        text = i['name']
        if i['super_admin']:
            menu.add_option(i, text + ' [Super Admin]')
        else:
            lis2.append('%s [%s]' % (title(i['group']), text) if i['group'] else text)
    for i in sorted(lis2):
        menu.add_option(i, i)
    menu.send(uid)


# Core Functions
def getuid(user):
    if str(user).startswith('[U:') or str(user).startswith('STEAM_'):
        for ply in player_list('#all'):
            if ply.steamid == user:
                return int(ply)
    elif es.exists('userid', user):
        return user
    return None


def getsid(user):
    return es.getplayersteamid(getuid(user))


def get_player(user):
    try:
        return playerlib.getPlayer(getuid(user))
    except:
        return None


def player_list(*filters):
    if not filters:
        return playerlib.getPlayerList('#all')
    elif len(filters) == 1:
        target = filters[0]
        if target == '#admins':
            return [i for i in playerlib.getPlayerList('#human') if admins.is_admin(i)]
        return playerlib.getPlayerList(target if target in FILTERS else '#all')
    else:
        targets = []
        for f in filters:
            if f in FILTERS:
                targets.extend(playerlib.getPlayerList(f))
        return targets


def userid_list(*filters):
    if not filters:
        return playerlib.getUseridList('#human')
    elif len(filters) == 1:
        target = filters[0]
        if target == '#admins':
            return [i for i in playerlib.getUseridList('#human') if admins.is_admin(i)]
        return playerlib.getUseridList(target if target in FILTERS else '#all')
    else:
        targets = []
        for f in filters:
            if f in FILTERS:
                targets.extend(playerlib.getUseridList(f))
        return targets


def change_team(uid, team_id):
    
    es.changeteam(uid, 1)
    if team_id == 2:
        es.changeteam(uid, 2)
        es.setplayerprop(uid, 'CCSPlayer.m_iClass', random.randint(1, 4))
        msg.vgui_panel(uid, 'class_ter', False, {})
    elif team_id == 3:
        es.changeteam(uid, 3)
        es.setplayerprop(uid, 'CCSPlayer.m_iClass', random.randint(5, 8))
        msg.vgui_panel(uid, 'class_ct', False, {})


def emit_sound(target, sound, volume=1, attenuation=0.5):
    es.emitsound('player', target, sound, volume, attenuation)


def play_sound(users, sound, volume=1.0):
    # TODO: Need to finish the funtion
    pass


def stop_sound(uid):
    # TODO: Need to finish the funtion
    pass


def import_module(module):
    return es.import_addon('sam/' + module)


def delay_task(seconds, name, function, args=()):
    gamethread.delayedname(seconds, 'sam_' + name, function, args)


def cancel_delay(name):
    gamethread.cancelDelayed('sam_' + name)


def get_time(frmt, from_stamp=None):
    ''' Examples:
        %d/%m/%Y, %H:%M:%S = 06/12/2018, 09:55:22
        %d %B, %Y          = 12 June, 2018
    '''
    return datetime.fromtimestamp(from_stamp if from_stamp else timestamp()).strftime(frmt)


def random(obj):
    return rdm.choice(obj)


def timestamp():
    return time.time()


def percentof(part, whole):
    return 100 * part / whole if part else 0


def title(text):
    return text.title().replace('_', ' ') if text else 'None'


def read_file(file_path, default=None, default_file=None):
    if not os.path.isfile(file_path) and default_file:
        write_file(default)
    lines = []
    with open(file_path, 'r') as f:
        for line in f.readlines():
            line = line.strip().replace('\n', '')
            if not line.startswith('//') and not line.startswith(' ') and line != '':
                lines.append(line)
    return lines


def write_file(file_path, lines):
    if not os.path.isfile(file_path):
        with open(file_path, 'w') as f:
            f.write('\n'.join(lines))


# Page Functions
def handle_choice(choice, user, force_close=False):
    if not force_close:
        _process_user_choice(user, choice)
        return
    es.cexec(user, 'slot10')
    if user in cache.users_active_menu.keys():
        del cache.users_active_menu[user]
        _cancel_menu_refresh(user)


def send_page(uid, menu_id, page=1):
    # Check if page exists
    if menu_id not in cache.menus.keys():
        return
    # Send page to user
    cache.menus[menu_id].send(uid, page)


def handle_choice(choice, user, force_close=False):
    if not force_close:
        _process_user_choice(user, choice)
        return
    es.cexec(user, 'slot10')
    if user in cache.users_active_menu.keys():
        del cache.users_active_menu[user]
        _cancel_menu_refresh(user)


def _cancel_menu_refresh(tar):
    if tar in FILTERS:
        for uid in userid_list(tar):
            cancel_delay('refresh_%s_page' % uid)
    else:
        cancel_delay('refresh_%s_page' % int(tar))


def _process_user_choice(uid, choice):
    ''' This function processes the user's last active menu choice.
        - If the choice is between 1 and 7 then the active menu
          call-back block is called.
        - If the choice is 9, then the active menu's next page is sent to the user
        - If the choice is 8, then the active menu's previous page is sent to the user
        - If the choice is 10 and there is a submenu attached to the active menu
          then the submenu is sent to the user, otherwise the user simply closed the menu
    '''
    # Cancel the menu refresh
    _cancel_menu_refresh(uid)
    # Check if the user has an active menu, if not,
    # it means the menu has been closed to the user
    if uid not in cache.users_active_menu.keys():
        return
    # Get the user's active menu ID and the page the user was in
    user = cache.users_active_menu[uid]
    active_menu = user['menu_id']
    active_page = user['page']
    # We can now remove the menu as the users active menu
    del cache.users_active_menu[uid]
    # Check is the menu still exists if not
    # it's because the menu has been deleted for some reason
    if active_menu not in cache.menus.keys():
        return
    # Get the active menu class object
    menu = cache.menus[active_menu]
    # Check if the choice was 0 (meaning the 10th option) and the menu has a close option
    if choice == 10 and menu.close_option:
        # If the menu has a submenu and the submenu still exists then send it to the user
        if menu.submenu and menu.submenu in cache.menus.keys():
            cache.menus[menu.submenu].send(uid, menu.submenu_page)
        # Otherwise the user has simply closed the menu
        return
    # Is the choice is between 1 and 7?
    elif choice <= len(menu.get_page_options(active_page)):
        # Check if the choice is a blocked option, or if the menu hasn't a callback block
        if choice in menu.blocked_options or not menu.callback:
            # If It's blocked, then notify the user
            if choice in menu.blocked_options:
                msg.hud(uid, 'This option is currently blocked')
            # Re-send the menu back to the user
            menu.send(uid, active_page)
            return

        class SubMenu:
            ''' Class to save last active menu and user choice as the new submenu
                info to be carried away in the menu callback '''

            def __init__(self, a, b, c, d):
                self.menu_id = a
                self.page = d
                self.object = b
                self.choice = c

            def send(self, uid):
                ''' Returns last active menu and page the same page the user was in '''
                self.object.send(uid, self.page)

        # If the option is not blocked, call the menu callback block with the choice
        # object, and with the SubMenu class as the new previous menu
        menu.callback(uid,
                      menu.get_option_data(choice, active_page)['object'],
                      SubMenu(menu.menu_id, menu, choice, active_page))
    # If the choice is 8 and higher than 1, then send the user to the previous page
    elif choice == 8 and active_page > 1:
        menu.send(uid, active_page - 1)
    # If the choice is 9 send the user to the next page
    elif choice == 9 and active_page + 1 in menu.pages.keys():
        menu.send(uid, active_page + 1)
    # Otherwise just make sure the active page is sent back to the user
    else:
        menu.send(uid, active_page)


def _decache_player(uid, sid):
    if uid in cache.sounds.keys():
        del cache.sounds[uid]
    if uid in cache.users_active_menu.keys():
        del cache.users_active_menu[uid]
    for chat_filter in chat_filters.filters.keys():
        f = chat_filters.filters[chat_filter]
        if uid in f.users:
            chat_filters.remove_user(uid, chat_filter)


# Game Events
def server_shutdown(ev):
    # Safely unload SAM on shutdown to make sure all data is saved properly
    es.server.cmd('es_unload sam')


def es_map_start(ev):
    # Clear Page System Cache
    cache.menus.clear()
    cache.users_active_menu.clear()

    # Remove all unnecessary chat filters
    for name in chat_filters.filters.keys():
        _filter = chat_filters.filters[name]
        del _filter.users[:]
        chat_filters.remove(name, _filter.block)

    # Save Addons Monitor database
    addons_monitor.save_database()


def es_client_command(ev):
    # Called when player chooses a page add_option
    if ev['command'] == 'menuselect':
        _process_user_choice(int(ev['userid']), int(ev['commandstring']))


def player_activate(ev):
    uid = ev['userid']
    # Update player info
    players.update(uid)


def player_disconnect(ev):
    # Decache player from the various systems
    uid = int(ev['userid'])
    sid = ev['networkid']

    _decache_player(uid, sid)

    # Update player last seen time
    if sid in players.data.keys():
        players.data[sid]['last_seen'] = get_time('%m/%d/%Y at %H:%M:%S')


# Class Declaration
players = _PlayersProfileSystem()
