# Python Imports
from __future__ import with_statement
from datetime import datetime

import os
import random
import time

# EventScripts Imports
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


# Developer Mode Levels:
# 0 = All systems will run normally without any debug messages
#     and or debug like behaviors
# 1 = Python Exceptions, Systems errors, and other debug like messages
# 2 = Pages Setup Debug (Prints all page setups to console)
# 2.1 = Menus cache report (Prints all menus cache to console)
# 3 = Sandbox Mode (Anyone can access anything in the menu
#     even if not a Super or Regular Admin)
# 4 = Prints all settings updates to console '''
def debug(lvl, *message):
    if lvl == plugin.developer_mode:
        for line in message:
            print('[SAM-DEBUG] %s' % line)


# Turn off ES debug completely (if SAM debug is)
es.server.cmd('eventscripts_debug %s' % ('0' if bool(plugin.developer_mode) else '-1'))

# Global Variables
MODULES = ('players_manager', 'addons_monitor', 'admins_manager', 'settings_manager')
FILTERS = ('#all', '#human', '#ct', '#t', '#alive', '#dead', '#spec', '#bot')
HOME_PAGE_ADDONS = []

# Core Module Systems
print('[SAM]   - Initializing Core Systems')


class _Cache:
    def __init__(self):
        self.menus = {}
        self.users_active_menu = {}
        self.users_previous_menu = {}
        self.sounds = {}
        self.temp = {}


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
        self.save_database(self._load())

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
    def save_database(data):
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
        self.save_database(data)

    def info_window(self, userid, key):
        data = self._load()
        if key == self.gen:
            data = data[self.gen].copy()
            obj = self.default[key].copy()
        elif key in self.default[self.add].keys():
            data = data[self.add][key].copy()
            obj = self.default[self.add][key].copy()
        else:
            msg.hud(userid, 'Error: Could not retrieve %s settings.' % title(key))
            return
        lines = []
        for k, v in obj.items():
            lines.extend(('[ %s ]' % title(k),
                          '- Description:\n%s' % '\n'.join(v['desc']),
                          '- Default Value: %s' % v['default'],
                          '- Current Value: %s\n' % data[k]))
        msg.info(userid,
                 key if key == self.gen else title(key) + ' | Settings Help Page',
                 *lines)


settings = _SettingsSystem()


class _ChatFilterSystem:
    """ Chat Filter System

        Chat Filters are the main way to control the chat messages sent in the server, and
        also the only way to retrieve any kind of text input from the server's players.

        Instead of creating multiple filters, SAM will create a single main filter
        which will then check which filter keys are active, and execute their functions
        tunneling the valid users to them. The main filter is only active as long as
        there is at least one filter key registered, this is to avoid unnecessary
        looping through the chat messages and memory usage.
    """

    MAIN_FILTER_ACTIVE = False

    def __init__(self):
        self.registered = {}

    def register(self, filter_id, users):
        """ Registers a new chat filter """

        # Check if the filter is already registered
        if filter_id not in self.registered.keys():
            self.registered[filter_id] = ChatFilter(filter_id, users)
        else:
            # If the filter is registered, add the users to the filter
            for user in users:
                if user not in self.registered[filter_id].users:
                    self.registered[filter_id].users.append(user)
        # Start the main filter if it's not active
        if not self.MAIN_FILTER_ACTIVE:
            self._start_main_filter()
        return self.registered[filter_id]

    def delete(self, filter_id):
        """ Deletes a filter """

        # Check if the filter exists
        if filter_id in self.registered.keys():
            del self.registered[filter_id]
        # Check if the filter page is in memory
        if filter_id in cache.menus.keys():
            del cache.menus[filter_id]
        # Check if the main filter is active, if so, stop it
        if not len(self.registered.keys()):
            self._stop_main_filter()

    def remove_user(self, userid, filter_id):
        """ Removes a user from the filter """

        # Check if the filter exists
        if filter_id in self.registered.keys():
            f = self.registered[filter_id]
            # Check if the user is in the filter
            if isinstance(f.users, list) and userid in f.users:
                # Remove the user from the filter
                f.users.remove(userid)
                # Check if the filter has any users, if not, delete it
                if not len(f.users) and f.delete_on_empty:
                    self.delete(filter_id)
        # Check if the user active menu is the filter menu, if so, close it
        if userid in cache.users_active_menu.keys() \
                and cache.users_active_menu[userid]['menu_id'] == filter_id:
            handle_choice(10, userid, True)

    def in_filter(self, userid):
        """ Checks if the user is in any filter.
            Also a list of all the filters the user is in.
        """

        for filter_id, obj in self.registered.items():
            if obj.temporary and isinstance(obj.users, list) and userid in obj.users:
                return filter_id
        else:
            return False

    @staticmethod
    def _main_chat_filter(userid, text, teamchat):
        """ The Main filter listener

            The main filter loops through all registered filters and checks if the userid
            is in any of them, if so, it will send the user to the filter function.
        """

        registered = chat_filter.registered.copy()
        for filter_id in registered.keys():
            f = registered[filter_id]
            # If the filter is not temporary and the user is in a temporary filter
            # continue to the next filter
            if not f.temporary and chat_filter.in_filter(userid):
                continue
            elif isinstance(f.users, list):
                # In case the user list is empty, delete the filter
                if not f.users and f.delete_on_empty:
                    chat_filter.delete(filter_id)
                    continue
                # Continue if the user is not in the filter
                elif userid not in f.users:
                    continue
                chat_filter.remove_user(userid, filter_id)
            # Otherwise, checks if the filter in a filter of players
            elif f.users in FILTERS or f.users == '#admins':
                # If the not part of the filter group, continue
                if userid not in userid_list(f.users):
                    continue
            # Check if the user has the filter page open
            if userid in cache.users_active_menu.keys() \
                    and cache.users_active_menu[userid]['menu_id'] == filter_id:
                handle_choice(10, userid, True)
            # Prep the text, and check if the user is trying to cancel the filter
            text = text.strip('"')
            if f.cancel_option and text.lower() == '!cancel':
                if callable(f.cancel_option):
                    args = f.cancel_args
                    if args[0] == 'userid':
                        f.cancel_option(userid, *args[1:])
                    else:
                        f.cancel_option(*args)
                msg.hud(userid,
                        'Operation canceled!',
                        '(Reason: User chose to cancel the operation)')
            if f.function:
                return f.function(userid, text, teamchat)
            debug(1, 'Chat Filter System | %s filter is missing a function' % filter_id)
        else:
            return userid, text, teamchat

    def _start_main_filter(self):
        """ Starts the main filter """

        es.addons.registerSayFilter(self._main_chat_filter)
        self.MAIN_FILTER_ACTIVE = True
        debug(1, 'Chat Filter System | Main filter started')

    def _stop_main_filter(self):
        """ Stops the main filter """

        # Check if there are any filters registered
        if len(self.registered) or not self.MAIN_FILTER_ACTIVE:
            return
        # Remove the main filter
        es.addons.unregisterSayFilter(self._main_chat_filter)
        self.MAIN_FILTER_ACTIVE = False
        debug(1, 'Chat Filter System | Main filter stopped')

    def _delete_all_filters(self):
        """ Deletes all active filters """

        self.registered.clear()
        debug(1, 'Chat Filter System | Terminated all filters')
        self._stop_main_filter()


chat_filter = _ChatFilterSystem()


class ChatFilter(object):
    """ Chat Filter Class

        This class is used to create a chat filter, holding the filter's necessary
        properties and functions to call depending on the filter users outcome.
    """

    def __init__(self, filter_id, users):
        self.filter_id = filter_id
        self.function = False
        self.delete_on_empty = True
        self.cancel_option = False
        self.cancel_args = ()
        self.instructions = False
        self.temporary = True
        self.users = []

        # Sort users
        if isinstance(users, list) or users in FILTERS or users == '#admins':
            self.users = users
        elif isinstance(users, int):
            self.users.append(users)

    def instructions_page(self, *instructions):
        """ Adds instructions to the filter page

            - This page is meant to be a static page with a few instructions to
            indicate to the user what to do while the filter is active, the page will
            be closed once the user either cancels the operation or completes it.
            - The filter function is the function which each valid user will be sent to,
            to then proceed the operation designated for the filter
        """

        self.instructions = instructions
        menu = Menu(self.filter_id, self.instructions_page_HANDLE)
        menu.header_text = False
        menu.close_option = False
        menu.title(title(self.filter_id))
        menu.add_line(*instructions)
        if self.cancel_option:
            menu.separator()
            menu.add_option(1, 'Cancel Operation')
        menu.separator()
        menu.send(*self.users)

    def instructions_page_HANDLE(self, userid, choice, submenu):
        """ Handles the instructions page choice """

        # If the user chooses to cancel the operation
        if choice == 1:
            # Close the page on the user
            handle_choice(10, userid, True)
            # Remove the user from the filter
            chat_filter.remove_user(userid, self.filter_id)
            # Notify the user that the operation was cancelled
            msg.hud(userid, '%s | Operation Cancelled!' % title(self.filter_id))
            # If the filter has a cancel function, execute it
            if callable(self.cancel_option):
                args = self.cancel_args
                if args[0] == 'userid':
                    self.cancel_option(userid, *args[1:])
                else:
                    self.cancel_option(*args)


class _MessageSystem:
    """ Class with all message types functions """

    # TODO: (Message System)
    #   - Review tell(), reviews its arguments, and improve the code
    #   - Review the _sort_users() method and improve the code
    #   - Review the spam queue system and improve the code

    def __init__(self):
        self.spam_queue = []
        self.colors = {'blue': '71ACDF',
                       'green': '5CB85C',
                       'orange': 'F0AD4E',
                       'red': 'EF625D',
                       'black': '292B2C',
                       'white': 'FFFFFF',
                       'pink': 'FFC0CB',
                       'gray': 'A9A9A9',
                       'purple': '931CE2',
                       'yellow': 'FFFF00',
                       'cyan': '00FFFF',
                       't': 'FF3D3D',
                       'ct': '9BCDFF',
                       'spec': 'CDCDCD',
                       'default': 'FFB300'}

    @staticmethod
    def _sort_users(users):
        """ Sorts the users list and returns it """

        if users == 'BOT':
            return users
        elif users == '#admins':
            return userid_list('#admins')
        elif isinstance(users, int) or users in FILTERS:
            return users
        new = []
        for x in users:
            if str(x).startswith('#'):
                for userid in userid_list(x):
                    if userid not in new:
                        new.append(userid)
                continue
            x = get_userid(x)
            if x and x not in new:
                new.append(x)
            else: continue
        return new

    def _in_queue(self, text):
        """ Checks if the given text is in the spam queue """

        text_hash = hash(text)
        if text_hash in self.spam_queue:
            return True
        self.spam_queue.append(text_hash)
        delay_task(10,
                   'message_spam_queue_%s' % text_hash,
                   self.spam_queue.remove,
                   text_hash)
        return False

    def tell(self, users, text, prefix=True, tag=False, log=False):
        """ Chat message that can be sent to any player or group of players.
            The text can also be color coded

            e.g: #red{prefix} | #green{tag} | #whiteHello World """

        prefix = '#default%s #gray| ' % settings('chat_prefix') if prefix else '#default'
        tag = '#green%s #gray| ' % tag if tag else ''
        text2 = '%s%s#white%s' % (prefix, tag, text)
        if self._in_queue(text):
            return
        if log and ('#all' in users or '#human' in users):
            self.console(text, tag)
        usermsg.saytext2(self._sort_users(users), 0, '''%s''' % compile_text(text2))

    def hud(self, users, *text):
        """ A hudhint type message which appears
            in the bottom center of the player screen
        """

        usermsg.hudhint(self._sort_users(users),
                        compile_text('| SAM |\n' + '\n'.join(map(str, text)), True))

    def center(self, users, text):
        """ A type message which appears in the center of the player screen """

        usermsg.centermsg(self._sort_users(users), text)

    def side(self, users, *text):
        """ A type message which appears on the side of the player screen """

        usermsg.keyhint(self._sort_users(users), compile_text('\n'.join(map(str, text)),
                                                              remove_colors=True,
                                                              remove_special=False))

    def vgui_panel(self, users, panel_name, visible, data={}):
        """ VGUI panel type message, to send VGUI panels to users """

        usermsg.showVGUIPanel(self._sort_users(users), panel_name, visible, data)

    def motd(self, users, window_title, url_or_filepath, message_type=2):
        """ Message Of The Day type message, to send URL pages to
            users using the in-game MOTD window browser """
        usermsg.motd(self._sort_users(users),
                     message_type,
                     'SAM | %s' % window_title,
                     url_or_filepath)

    def info(self, users, window_title, *lines):
        """ Info type message, to send text to users using the in-game info window """
        with open(path.info_window_file, 'w') as f:
            f.write('\n'.join(lines))
        self.motd(self._sort_users(users),
                  window_title,
                  path.info_window_file.replace('\\', '/'), 3)

    @staticmethod
    def console(text, tag=None):
        """ Prints a message to the server console with SAM's prefix, a "tag" can be used
            to identify the system or addon from which the message is being sent

            E.g. SAM | PLAYERS MANAGER | X was kicked from the server. """

        print(compile_text('[%s][SAM] %s%s' %
                           (get_time('%H:%M:%S'),
                            tag.upper() + ' | ' if tag else '', text), True))


msg = _MessageSystem()


class _AddonsMonitor:
    """ Addons Monitor class """

    class AddonClass(str):
        def __init__(self, addon):
            self.basename = addon
            self.name = 'unknown_addon'
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
        """ Verify if all installed Addons are valid """
        # Loop over all installed Addons
        installed = self.addons_dir_list()

        for addon in installed:
            # Check if the metadata file is valid
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

            # Else update the Addon's info
            for key in metadata.keys():
                if key in ('state', 'locked') \
                        or metadata[key] == self.addons[addon].__dict__[key]:
                    continue
                self.addons[addon].__dict__[key] = metadata[key]

    def save_database(self):
        """ Save Addons Monitor database """
        database = {}
        for addon in self.addons.keys():
            database[addon] = self.addons[addon].__dict__.copy()
        databases.save('addons_monitor', database)

    @staticmethod
    def addons_dir_list():
        """ List of Addons in the addons folder """
        return (i for i in os.listdir(path.addons) if os.path.isdir(path.addons + i))

    def is_running(self, addon):
        """ Check if an Addon is running """
        if addon not in self.addons.keys():
            return False
        return self.addons[addon].state

    def import_addon(self, addon):
        """ Import an Addon """
        if not self.is_running(addon):
            debug(1, 'Could not import %s, addon is not running or is missing' % addon)
            return None
        return import_module('addons/' + addon)


addons_monitor = _AddonsMonitor()


class _AdminsSystem:
    """ Admins System

    This system is responsible for managing the server admins and groups.
    """

    def __init__(self):
        # Init admins and groups dictionaries
        self.admins = {}
        self.groups = {}
        # Set up the Permissions dictionaries
        self.addons_permissions = []
        self.admins_permissions = ['addons_monitor',
                                   'admins_manager',
                                   'players_manager',
                                   'kick_players',
                                   'rcon_command',
                                   'settings_manager']

    def __repr__(self):
        return str(type(self))

    def __str__(self):
        return self.__repr__()

    def __call__(self, arg=None):

        if not arg:
            return None
        # Check if arg is a userid, if so then convert it to a SteamID
        if isinstance(arg, int):
            arg = get_steamid(arg)
        # Check if argument is a valid admin
        if arg in self.admins.keys():
            return self.admins[arg]
        # Check if argument is a valid group
        elif arg in self.groups.keys():
            return self.groups[arg]
        # Check if argument is 'groups', if so then return the groups dict
        elif arg == 'groups':
            return self.groups
        # If there's no argument at all, then return the Admins dict
        elif not arg:
            return self.admins

    def is_admin(self, user):
        """ Function to return whether a user is a valid Admin """
        # If Developer mode is level 3, return True regardless
        if plugin.developer_mode == 3:
            return True
        # Check if user is a NoneType
        if user is None:
            return False
        # Check if the user corresponds to the userid, if the user exists and is active
        # get his steamid
        elif isinstance(user, int) and es.exists('userid', user):
            user = get_steamid(user)
        # In case the user in playerlib.Player class type gets the steamid
        elif isinstance(user, playerlib.Player):
            user = user.steamid
        # Return whether the steamid is in the Admins list
        return user in self.admins.keys()

    def is_allowed(self, user, permission, notify=True):
        """ Function to check whether an Admin has permission to do something """

        # Check if developer mode is level 3, if so then return True regardless
        if plugin.developer_mode == 3:
            return True
        # Get the Admin class object
        admin = self.__call__(user)
        # Check if is a valid Admin
        if not admin:
            return False
        # Check if Admin is a Super Admin
        if admin.super_admin:
            return 3 if permission == 'ban_level' else True
        # If permission is ban_level, then return the Admin Ban Level instead
        if permission == 'ban_level':
            return admin.ban_level
        # Otherwise, if the Admin has the permission assign, then return its state
        i = admin.permissions[permission] \
            if permission in admin.permissions.keys() else False
        # If its not an Admin Permission, then check if its an Addon Permission
        if not i:
            i = admin.addons_permissions[permission] \
                if permission in admin.addons_permissions.keys() else False
        # Notify the Admin if he doesn't have permission
        if not i and notify:
            msg.hud(user, 'You do not have permission to %s!' % title(permission))
        return i

    def is_super_admin(self, user):
        """ Function to check whether an Admin is a Super Admin """

        # Get the Admin class object
        admin = self.__call__(user)
        # Check if is a valid Admin
        if not admin:
            return False
        return admin.super_admin

    def list(self, arg=None):
        """ Function to return the list of Admins or Groups
            If arg is 'groups', then return the groups dict
            If arg is 'super_admins', then return the dict of Super Admins
            If arg is 'online', then return the dict of online Admins
            Otherwise return the Admins dict
        """
        if arg == 'groups':
            return self.groups.copy()
        elif arg == 'super_admins':
            return dict((x, y) for x, y in self.admins.copy().items() if y.super_admin)
        elif arg == 'online':
            return dict((x, y) for x, y in self.admins.copy().items()
                        if es.exists('userid', get_userid(x)))
        return self.admins.copy()

    def compare_immunity(self, admin1, admin2):
        """ Compares the immunity level between two Admins and returns
            whether the Admin1 has higher immunity than Admin2
        """

        # If Developer mode is level 3, return True regardless
        if plugin.developer_mode == 3:
            return True
        # Admin1 is most likely a menu user, therefore, get his steamid
        user = admin1
        admin1 = get_steamid(admin1)
        # Return true if Admin2 is not an actual an Admin or is actually Admin1
        if not self.is_admin(admin2) or admin1 == admin2:
            return True
        # Get both Admins objects
        admin1 = self.admins[admin1]
        admin2 = self.admins[admin2]

        # Check if Admin2 is a Super Admin
        if admin2.super_admin:
            msg.hud(user, 'Action denied! %s is immune to you.' % admin2.name)
            return False
        elif admin1.super_admin:
            return True

        # Function to get the immunity level of an Admin
        # (If the Admin is in a group, the higher immunity level will be returned)
        def get_immunity(admin):
            admin_imm = admin.immunity_level  # get the Admin own level
            group_imm = 0  # leave group level 0 by default
            # Replace the group level with the Admin Group level
            # in case the Admin is in a group
            if admin.group and admin.group in self.groups.keys():
                group_imm = self.groups[admin.group].immunity_level
            # Return the higher level
            return max(admin_imm, group_imm)

        # Compare the immunity levels between the two Admins
        result = get_immunity(admin1) > get_immunity(admin2)
        # Notify the Admin if he doesn't have permission
        if not result:
            msg.hud(user, 'Action denied! %s is immune to you.' % admin2.name)
        return result

    def new_admin(self, steamid, super_admin=False):
        """ Function to create a new Admin """

        # Create the Admin
        self.admins[steamid] = Admin(steamid, super_admin)
        # Save the database
        self.save_database()
        # Notify the Admin
        userid = get_userid(steamid)
        if userid:
            msg.hud(userid,
                    'You are now an Admin!',
                    'You may now start using !sam, to open the menu')

    def delete_admin(self, steamid):
        """ Function to delete an Admin """

        # Check if the Admin exists
        if steamid not in self.admins.keys():
            return
        # Delete the Admin
        del self.admins[steamid]
        # Save the database
        self.save_database()

    def new_group(self, group):
        """ Function to create a new Admin Group """

        # Check if the group already exists
        if group in self.groups.keys():
            return
        # Create the group
        self.groups[group] = Group(group)
        # Save the database
        self.save_database()

    def delete_group(self, group):
        """ Function to delete an Admin Group """

        # Check if the group exists
        if group not in self.groups.keys():
            return
        # Delete the group
        del self.groups[group]
        # Remove the group from all Admins
        for admin in self.admins.values():
            if admin.group == group:
                admin.group = False
        # Save the database
        self.save_database()

    def get_group_members(self, group):
        """ Function to get the members of an Admin Group """

        # Check if the group exists
        if group not in self.groups.keys():
            return []
        # Return the list of members
        return [admin.steamid for admin in self.admins.values() if admin.group == group]

    def save_database(self):
        """ Saves both Admins & Groups database at once """
        # Admins Database
        admins_db = {}
        for steamid in self.admins.keys():
            admins_db[steamid] = self.admins[steamid].__dict__.copy()
        databases.save('admins_database', admins_db)
        # Groups Database
        # We can skip Groups if none exists
        if not self.groups:
            return
        groups_db = {}
        for group in self.groups.keys():
            groups_db[group] = self.groups[group].__dict__.copy()
        databases.save('groups_database', groups_db)

    def register_addon_permission(self, permission):
        """ Internal function for Addons to add their own permissions """

        # Check if the permission is already registered
        if permission not in self.addons_permissions:
            self.addons_permissions.append(permission)
        # Assign the permission to all Admins and Groups
        for admin in self.admins.values():
            if permission not in admin.addons_permissions.keys():
                admin.addons_permissions[permission] = False
        for group in self.groups.values():
            if permission not in group.addons_permissions.keys():
                group.addons_permissions[permission] = False

    def _toggle_permission(self, object, permission):
        """ Toggles the state of the Admin/Group's permission """

        # Check if the permission still exists
        if permission in self.admins_permissions:
            # Check if the Admin or Group already has this permission assign
            # if so then just toggle its state
            if permission in object.permissions:
                object.permissions[permission] = not object.permissions[permission]
            # Otherwise, assign the permission to the Admin in disabled state
            else:
                object.permissions[permission] = False
        # Check whether it's a registered Addon permission
        elif permission in self.addons_permissions:
            # Check if the Admin or Group already has this permission assign
            if permission in object.addons_permissions:
                object.addons_permissions[permission] = \
                    not object.addons_permissions[permission]
            else:
                object.addons_permissions[permission] = False
        else:
            # If the given permission was not found, then make sure its removed remove it
            # from the Admin/Group permissions list.
            # This may happen if a permission was either removed from the default
            # Admins permissions or an Addon no longer uses the permission
            if permission in self.admins_permissions:
                self.admins_permissions.remove(permission)
            elif permission in self.addons_permissions:
                self.addons_permissions.remove(permission)

    def _initialize_database(self):
        """ Should be called only once to initialize the Admins database
            Converts the Admins and Groups dictionaries into
            Admins and Groups class objects
        """

        # Load the admins and groups databases
        admins_db = databases.load('admins_database')
        groups_db = databases.load('groups_database')

        # Convert the Admins database
        for steamid, data in admins_db.items():
            admin = Admin(steamid)
            admin.__dict__.update(data.copy())
            self.admins[steamid] = admin
        # Convert the Groups database
        for name, data in groups_db.items():
            group = Group(name)
            group.__dict__.update(data.copy())
            self.groups[name] = group


admins = _AdminsSystem()


class Admin(object):
    """ Admin Class object """

    def __init__(self, steamid, super_admin=False):
        player = get_userid(steamid)

        self.name = es.getplayername(player) if player else 'Unregistered'
        self.steamid = steamid
        self.admin_since = get_time('%d/%m/%Y')
        self.super_admin = super_admin
        self.ban_level = 0
        self.immunity_level = 0
        self.group = False
        self.permissions = dict((x, False)
                                for x in admins.admins_permissions)
        self.addons_permissions = dict((x, False)
                                       for x in admins.addons_permissions)

    def toggle_permission(self, permission):
        """ Channels this class through the AdminSystem's internal
            _toggle_permission function,
            which toggles admin/group's permission state
        """
        admins._toggle_permission(self, permission)


class Group(object):
    """ Admin Group Class object """

    def __init__(self, name):
        self.id = name
        self.name = name
        self.ban_level = 0
        self.immunity_level = 0
        self.color = 'default'
        self.permissions = dict((x, False)
                                for x in admins.admins_permissions)
        self.addons_permissions = dict((x, False)
                                       for x in admins.addons_permissions)

        # Attach the group color to the name
        self._attach_color()

    def toggle_permission(self, permission):
        """ Channels this class through the AdminSystem's internal
            _toggle_permission function,
            which toggles admin/group's permission state
        """
        admins._toggle_permission(self, permission)

    def _attach_color(self):
        """ Attaches the group color to the name """

        self.name = '#' + self.color + title(self.id) + '#default'


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
    """ Systems responsible for gathering various types of information about
        the player to be used in multiple other systems
    """

    class Player(object):
        def __init__(self, data):
            for key in data.keys():
                setattr(self, key, data[key])

    def __init__(self):
        # Load database
        self.data = databases.load('players_data')

        # Update active players
        for userid in userid_list('#human'):
            self.update(userid)

    def __call__(self, user):
        """ Return the Player info as a class object """
        target = None
        if isinstance(user, int):
            target = get_steamid(user)
        elif str(user).startswith('[U:') or str(user).startswith('STEAM_'):
            target = user
        return self.Player(self.data[target]) if target in self.data.keys() else None

    def list(self):
        return [self.Player(self.data[k]) for k in self.data.keys()]

    def update(self, userid):
        """ Updates the player info into the database """
        ply = get_player(userid)
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
        # Or add player to the database if not in yet
        else:
            self.data[ply.steamid] = i.copy()
        databases.save('players_data', self.data)


class Menu(object):
    """ Class system based on EventScripts popuplib library to create paged menus
        using SourceEngine's Radio Popups as the user interface.
    """

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
        self.max_lines = 7
        self.validate_all_lines = False
        self.timeout = 0
        self.blocked_options = []
        length = int(settings('menus_separator_line_length'))
        self.separator_line = '-' * length if length <= 40 else 40

    def title(self, text):
        """ Adds/Changes the title of the menu """
        self.title_text = ' :: ' + text

    def description(self, *lines):
        """ Adds/Changes the description of the menu
            Note: Multiple lines can be given as a list() """
        self.description_text = '\n'.join(lines)

    def footer(self, *lines):
        """ Adds/Changes the footer of the menu
            Note: Multiple lines can be given as a list() """
        self.footer_text = self.separator_line + '\n' + '\n'.join(lines)

    def add_line(self, *lines):
        """ Adds a new line to the menu
            Note: Multiple lines can be given as a list() """
        self.pages[self._current_page()].extend([str(line) for line in lines])

    def add_option(self, obj, text, blocked=False):
        """ Adds a new option to the menu """

        # Get the current page
        page = self._current_page()
        # Add the option to the current page
        self.pages[page].append({'object': obj,
                                 'text': text,
                                 'blocked': blocked,
                                 'choice': len(self.pages[page]) + 1,
                                 'page': page})

    def add_options(self, options_list):
        """ Adds multiple options to the menu

            Note: Each option must be a tuple with the following format:
                  (object, text, blocked=False)
        """

        for item in options_list:
            self.add_option(*item)

    def separator(self):
        """ Adds a seperator line to the menu """
        self.add_line(self.separator_line)

    def next_page(self):
        """ Adds a new page to the menu """

        self.pages[max(self.pages.keys()) + 1] = []

    def send(self, users, page=1):
        """ It's called once the menu is fully setup and ready to be sent to the user.
            Builds the given page with the menu title, description, lines, options, etc.,
            and sends it to the user/users.
        """

        debug(2, '[Initializing Menu Setup Process]')
        debug(2, '- Menu ID: %s' % self.menu_id)
        # Abort if users do not exist at all
        if not users:
            debug(2, '[Aborting Menu Setup Process: No Valid Users Found]')
            return
        debug(2, '- Menu Features:')
        debug(2, '   * Header: %s' % str(bool(self.header_text)))
        # Check if the page exists, otherwise set it to 1
        if page not in self.pages.keys():
            page = 1
        # Each page is built line by line, therefore, create a display list to
        # store all lines and options by order they were added
        display = []
        # First, let's add the header of the menu, by default, is SAM's title and current
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
        debug(2, '   * Setting up Lines & Options')
        # Forth, start adding the page lines and options
        # Build a new list of blocked options
        self.blocked_options = []
        # Check if the number of max lines is between the valid values
        if self.max_lines not in range(1, 8):
            self.max_lines = 7
        # Iterate through the page's lines and options
        option_number = 0
        for line in self.pages[page]:
            # If it's just a text line, we simply add the line
            if isinstance(line, str):
                display.append(line)
                # TODO: Investigate if its worth validating all lines anyway
                if self.validate_all_lines:
                    option_number += 1
                continue
            # If it's an option, we add one to the option_number to keep track which
            # options are being added
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
        # Is not, the first to add is the Previous Page option
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
        # If nothing was added to the page, we simply abort the process
        if not display:
            debug(2, '[Aborting Menu Setup Process: Empty Page]')
            return
        display = '\n'.join(display)
        debug(2, '>> Menu display build process complete!')
        # At this point, the page is complete, and we can cache it
        cache.menus[self.menu_id] = self
        debug(2, '>> Menu caching complete!')
        users = (users,) if isinstance(users, int) else userid_list(users)
        debug(2, '>> Sending Menu To Users:')
        # Send the page to each user
        for user in users:
            userid = int(user)
            debug(2, '   -------------------------')
            debug(2, '   userid - steamid')
            debug(2, '   -------------------------')
            debug(2, '   %s      - %s' % (user, get_steamid(user)))
            debug(2, '   -------------------------')
            # Make sure the user doesn't have an active page being refreshed
            _cancel_menu_refresh(userid)
            # Cache the menu as the user's new active menu
            cache.users_active_menu[userid] = {'menu_id': self.menu_id, 'page': page}
            # Display the menu to the user in-game
            es.showMenu(self.timeout,
                        userid,
                        compile_text(display.encode('utf-8'),
                                     remove_colors=True,
                                     remove_special=True,
                                     strip_text=False))
            # If the menu has not a timeout, we start the refresh process
            if self.timeout == 0:
                delay_task(1, 'refresh_%s_page' % userid, self._refresh_page, userid)
        debug(2, '[Menu Setup Process Complete]')
        debug(2.1, '[Menu Cache Report]:')
        for menu in cache.menus.values():
            debug(2.1, '   - %s' % menu.menu_id)
        debug(2.1, '-' * 40)

    def send_option(self, userid, option, page=None):
        """ Sends the given option to the given user """

        option = self.get_option_data(option, page)
        self.send(userid, option['page'])
        handle_choice(option['option_number'], userid)

    def get_option_data(self, obj, page=None):
        """ Returns the option data of the given object

            The data consists of a dictionary containing the following keys:
            'object': The object that was given to the function
            'text': The option text which is displayed in the page
            'blocked': If the option is blocked or not
            'option_number': The number of the option in the page
            'page': The page number where the option is located
        """

        # Function to look for the option in a given page
        def look_in_page(_obj, _page):
            # Get the page's options
            options = self.get_page_options(_page)
            # If the object is an integer, then we can just return the option
            if isinstance(_obj, int):
                return options[_obj - 1]
            # If the object is a string, then we need to look for the option
            for option in options:
                if option['object'] == obj:
                    return option
            # If the option wasn't found, then return None
            else:
                return None

        # If a page was given, then look for the option in that page
        if page:
            return look_in_page(obj, page)
        else:
            # If no page was given, then look for the option in all the pages
            for page in self.pages.keys():
                option = look_in_page(obj, page)
                if option == obj:
                    return option
            # If the option wasn't found, then return None
            return None

    def get_page_options(self, page=None):
        """ Returns the list of all the page's options """

        # If a page was not given, then get the current page
        if not page:
            page = self._current_page()
        return [i for i in self.pages[page] if isinstance(i, dict)]

    @staticmethod
    def _refresh_page(user):
        """ Refreshes the user's active menu by re-sending the page """

        if user not in cache.users_active_menu.keys():
            return
        menu = cache.users_active_menu[int(user)]
        if menu['menu_id'] in cache.menus.keys():
            cache.menus[menu['menu_id']].send(user, menu['page'])

    def _current_page(self):
        """ Returns the last edited page """

        page = max(self.pages.keys())
        # Check if the number of the page options higher or equal to the max lines
        # if so then initiate the next page
        if self.max_lines and len(self.get_page_options(page)) >= self.max_lines:
            page += 1
            self.pages[page] = []
        return page


# Core Functions
def load():
    # Initialize Admins database
    admins._initialize_database()

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
    # Terminate all chat filters
    chat_filter._delete_all_filters()

    # Close active menus from users
    for user in cache.users_active_menu.keys():
        handle_choice(10, user, True)
        msg.hud(user, 'Your page was closed because SAM is unloading.')

    # Clear cache
    cache.menus.clear()
    cache.users_active_menu.clear()

    # Delete core module commands
    cmds.delete('sam')
    cmds.delete('menu')
    cmds.delete('rcon')
    cmds.delete('admins')

    # Save databases
    admins.save_database()
    addons_monitor.save_database()
    databases.save('players_data', players.data)

    # Unload main modules
    msg.console('* Unloading Main Modules:')
    for module in MODULES:
        es.unload('sam/' + module)
        msg.console('* Unloaded %s Module' % title(module))

    msg.tell('#all', 'Unloaded', tag='#blue' + plugin.version)


# Home Page
def home_page(userid):
    """ Send SAM's home page to the user """

    # Check if user is an Admin
    if not admins.is_admin(userid):
        msg.hud(userid, 'You do not have permission to use this')
    menu = Menu('home_page', home_page_HANDLE)
    menu.title('Home Page')
    # Add main modules options
    for module in MODULES:
        menu.add_option(module, title(module))
    # Add Addons options
    if HOME_PAGE_ADDONS:
        menu.separator()
        menu.add_line('  :: Addons')
        menu.separator()
        for basename in HOME_PAGE_ADDONS:
            addon = addons_monitor(basename)
            if addon is None or not addon.state:
                HOME_PAGE_ADDONS.remove(basename)
                home_page(userid)
                continue
            menu.add_option(basename, addon.name)
    menu.send(userid)


def home_page_HANDLE(userid, choice, submenu):
    if choice in MODULES:
        import_module(choice).module_menu(userid)
        return
    elif choice in HOME_PAGE_ADDONS:
        addons_monitor.import_addon(choice).addon_menu(userid)


# Command Functions
def sam_CMD(userid, args):
    if not bool(admins.admins):
        import_module('admins_manager').first_admin_setup(userid)
        return
    home_page(userid)


def rcon_CMD(userid, args):
    """ RCON Command
        Admins can use the !rcon command to execute RCON commands
        and change server
        variables in the in-game chat.
        The RCON_COMMAND permission is required to use it.

        E.g !rcon sv_alltalk 1
    """

    # Check if the command is enabled and if the user has the permission to use it
    if not admins.is_allowed(userid, 'rcon_command') \
            or not settings('enable_!rcon_command'):
        return
    # Check if nothing was given
    if not args:
        # If no arguments were given, then send the syntax example to the user
        msg.tell(
            userid,
            '#blueSyntax Example:\n#orange!rcon <command/variable> {arguments/value}'
        )
        return
    # The first argument is the command/variable
    cmd = args.pop(0)
    # Join the rest of the arguments into a string with a space between each argument
    args = ' '.join(args) if args else None
    # Check if cmd is a valid variable
    if es.exists('variable', cmd):
        # If the command is sv_cheats, only Super Admins can change it
        # This is to prevent enabling cheats on the server
        if cmd == 'sv_cheats' and not admins.is_allowed(userid, 'super_admin'):
            msg.hud(userid, 'Only Super Admins can change sv_cheats command!')
            return
        # Check any arguments besides the command were given
        if args is None:
            msg.tell(userid, 'No arguments given!')
            return
        # Set the server variable to the given arguments
        es.ServerVar(cmd).set(args)
        msg.tell(userid, 'RCON: #blueSet #green%s #blueto #green%s' % (cmd, args))
        return
    # Check if cmd is a valid command
    elif es.exists('command', cmd):
        # Check if any arguments were given next to the command
        if args:
            # Execute the command with the given arguments
            es.server.insertcmd('%s %s' % (cmd, args))
        # If arguments are any bot-related or EventScripts settings
        elif cmd.startswith(('bot_', 'es_')):
            # Execute the command with the given arguments
            es.server.insertcmd(cmd)
        msg.tell(userid, 'RCON: #blueExecuted %s %s' % (str(cmd), str(args)))
        return
    else:
        msg.tell(userid, '#green\'%s\' #orangeis not a command or server variable.' % cmd)


def admins_CMD(userid, args):
    """ Admins Command
        This command will show a menu with all the admins online and their groups.
    """

    # Check if the command is enabled
    if not settings('enable_!admins_command'):
        return
    # Get a list of all admins online with their Admin Class object
    online_admins = admins.list(online=True)

    # Check if there are any admins online
    if not online_admins:
        msg.tell(userid, '#redThere are no #cyanAdmins #redonline')
        return

    # Start building the menu
    menu = Menu('admins_list')
    menu.header_text = False
    # Add a title to the menu
    # showing the number of admins online and the total number of admins
    menu.title('Admins Online (%s of %s)' % (len(online_admins), len(admins.list())))

    # Create a list with the name of all the Admins, and tag of Super Admin, if they are,
    # or a tag with the Admin group they are in if in any.
    # Then sort the list alphabetically
    admins = []
    super_admins = []

    for admin in online_admins:
        # Get the Admin Class object of the admin
        admin = admins.get_admin(admin)
        # Check if the admin is a Super Admin
        if admin.super_admin:
            super_admins.append(admin.name)
        else:
            if admin.group:
                admins.append('%s (%s)' % (admin.name, admins(admin.group).name))
            else:
                admins.append(admin.name)

    # Sort the lists alphabetically and add them to the menu
    menu.add_line('  :: Super Admins')
    menu.separator()
    for admin in sorted(super_admins):
        menu.add_option(admin, admin)
    menu.separator()
    menu.add_line('  :: Admins')
    menu.separator()
    for admin in sorted(admins):
        menu.add_option(admin, admin)

    # Send the menu to the user
    menu.send(userid)


# Core Functions
def get_userid(user):
    """ Returns the userid of the given user """

    # Use es.getuserid() method for a faster approach
    userid = es.getuserid(user)
    if userid and es.exists('userid', userid):
        return userid
    # Otherwise, if user is the new SteamID3 format, loop all players to see if any
    # matches the given SteamID3
    for player in playerlib.getPlayerList('#all'):
        if player.steamid == user:
            return player.userid
    return None


def get_steamid(user):
    """ Returns the steamid of the given user """

    return es.getplayersteamid(get_userid(user))


def get_player(user):
    """ Returns the Player Class object of the given user"""

    return playerlib.getPlayer(get_userid(user))


def player_list(*filters):
    """ Returns a list of players (as their Player Object) from the server

        A one or more filters can be given in order to return a compiled list of all
        the filters together:
        #all, #human, #bot, #dead, #alive, #un, #spec, #ct, #t, #admins
    """
    if not filters:
        return playerlib.getPlayerList('#all')
    elif len(filters) == 1:
        target = filters[0]
        if target == '#admins':
            return [i for i in playerlib.getPlayerList() if admins.is_admin(i.steamid)]
        return playerlib.getPlayerList(target if target in FILTERS else '#all')
    else:
        targets = []
        for f in filters:
            if f in FILTERS:
                targets.extend(playerlib.getPlayerList(f))
        return targets


def userid_list(*filters):
    """ Returns a list of all players userid from the server.
        One or more filters can be given in order to return a compiled list
        of all the filters together.
    """

    if not filters:
        return playerlib.getUseridList('#all')
    elif len(filters) == 1:
        target = filters[0]
        if target == '#admins':
            return [i for i in playerlib.getUseridList('#all') if admins.is_admin(i)]
        return playerlib.getUseridList(target if target in FILTERS else '#all')
    else:
        targets = []
        for f in filters:
            if f in FILTERS:
                targets.extend(playerlib.getUseridList(f))
        return targets


def change_team(userid, team_id):
    """ Moves the player to the given team """

    es.changeteam(userid, 1)
    if team_id == 2:
        es.changeteam(userid, 2)
        es.setplayerprop(userid, 'CCSPlayer.m_iClass', random.randint(1, 4))
        msg.vgui_panel(userid, 'class_ter', False, {})
    elif team_id == 3:
        es.changeteam(userid, 3)
        es.setplayerprop(userid, 'CCSPlayer.m_iClass', random.randint(5, 8))
        msg.vgui_panel(userid, 'class_ct', False, {})


def emit_sound(userid, sound, volume=1, attenuation=0.5):
    """ Emits a sound to the given userid """

    es.emitsound('player', userid, sound, volume, attenuation)


def import_module(module):
    """ Imports modules from the sam folder """

    return es.import_addon('sam/' + module)


def delay_task(seconds, name, function, args=()):
    """ Delays a task for the given number of seconds """

    gamethread.delayedname(seconds, 'sam_' + name, function, args)


def cancel_delay(name):
    """ Cancels a delayed task """

    gamethread.cancelDelayed('sam_' + name)


def get_time(frmt, from_stamp=None):
    """ Gets the current time in the given format

        Examples:
        %d/%m/%Y, %H:%M:%S = 06/12/2018, 09:55:22
        %d %B, %Y          = 12 June, 2018
    """

    return datetime.fromtimestamp(from_stamp if from_stamp
                                  else timestamp()).strftime(frmt)


def random(obj):
    """ Returns a random item from the given object """

    return random.choice(obj)


def timestamp():
    """ Returns the current timestamp """

    return time.time()


def percent_of(part, whole):
    """ Returns the percentage of the given part of the whole """

    return 100 * part / whole if part else 0


def title(text):
    """ Returns the given text with the first letter of each word capitalized """

    return text.title().replace('_', ' ') if text else 'None'


def compile_text(text, remove_colors=False, remove_special=True, strip_text=True):
    """ Compiles the given text making essential changes depending on where the text
        will be used. (e.g. whether is to the in-game chat or in menus)

        remove_colors: Removes all colors from the text, otherwise, color names will
                       be replaced with their RGB color code
        remove_special: Removes all special characters from the text
        strip_text: Strips the text from any spaces at the start and end
    """

    for color, code in msg.colors.items():
        # Remove the color from the text
        if remove_colors:
            text = text.replace('#' + color, '')
        # Replace the color with its RGB code
        else:
            text = text.replace('#' + color, '\x07' + code)
    # Remove all special characters
    if remove_special:
        # \n = New line
        # \r = Carriage return
        # \t = Tab
        for i in ('\\n', '\\r', '\\t'):
            text = text.replace(i, '')
    # Strip the text from any spaces at the start and end
    if strip_text:
        text = text.strip()
    return text


def read_file(file_path, default=None, default_file=None):
    """ Reads the given file and returns a list of lines """

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
    """ Writes the given lines to the given file """

    if not os.path.isfile(file_path):
        with open(file_path, 'w') as f:
            f.write('\n'.join(lines))


def _decache_player(userid):
    """ De-caches the player from the given userid and steamid """

    # Decache the player from any ongoing sounds
    if userid in cache.sounds.keys():
        del cache.sounds[userid]
    # Decache the player from any active menus
    if userid in cache.users_active_menu.keys():
        del cache.users_active_menu[userid]
    # Decache the player from any active chat filters
    for filter_id in chat_filter.registered.keys():
        chat_filter.remove_user(userid, filter_id)


# Page Functions
def handle_choice(choice, user, force_close=False):
    """ Handles the user's choice
        Used mostly to force a user to make certain choices
    """
    if not force_close:
        _process_user_choice(user, choice)
        return
    es.cexec(user, 'slot10')
    if user in cache.users_active_menu.keys():
        del cache.users_active_menu[user]
        _cancel_menu_refresh(user)


def send_menu(userid, menu_id, page=1):
    """ Sends the given menu to the user """

    if menu_id in cache.menus.keys():
        menu = cache.menus[menu_id]
        menu.send(userid, page)
    else:
        msg.console('Failed to send menu to %s. Menu with ID %s does not exist' %
                    (es.getplayername(userid), menu_id),
                    'Menu System')


def _cancel_menu_refresh(users):
    """ Cancels users menu refresh timer """

    # Check if the object is a valid filter
    if users in FILTERS:
        for userid in userid_list(users):
            cancel_delay('refresh_%s_page' % userid)
    else:
        cancel_delay('refresh_%s_page' % int(users))


def _process_user_choice(userid, choice):
    """ Function responsible for processing the user menu choices by either
        to executing a pre-defined function, sending the user to another page
        or closing the menu.
    """
    # Cancel the menu refresh
    _cancel_menu_refresh(userid)
    # Check if the user has an active menu, if not,
    # it means the menu has been closed to the user
    if userid not in cache.users_active_menu.keys():
        return
    # Get the user's active menu ID and the page the user was in
    user = cache.users_active_menu[userid]
    active_menu = user['menu_id']
    active_page = user['page']
    # Now cache it as the previous menu info
    cache.users_previous_menu[userid] = user.copy()
    # We can now remove the menu as the user's active menu
    del cache.users_active_menu[userid]
    # Check if the menu still exists
    # if not it's because the menu has been deleted for some reason
    if active_menu not in cache.menus.keys():
        return
    # Get the active menu class object
    menu = cache.menus[active_menu]
    # Check if the choice was 0 (meaning the 10th option) and the menu has a close option
    if choice == 10 and menu.close_option:
        # If the menu has a submenu and the submenu still exists, then send it to the user
        if menu.submenu and menu.submenu in cache.menus.keys():
            cache.menus[menu.submenu].send(userid, menu.submenu_page)
        # Otherwise, the user has simply closed the menu, and we can end the process
        return
    # If the choice is between 1 and 7
    elif choice <= len(menu.get_page_options(active_page)):
        # Check if the choice is a blocked option, or if the menu hasn't a callback block
        if choice in menu.blocked_options or not menu.callback:
            # If It's blocked, then notify the user
            if choice in menu.blocked_options:
                msg.hud(userid, 'This option is currently blocked')
            # Re-send the menu back to the user
            menu.send(userid, active_page)
            return

        class SubMenu:
            """ Class to save last active menu and user choice as the new submenu
                info to be carried away in the menu callback """

            def __init__(self, a, b, c, d):
                self.menu_id = a
                self.object = b
                self.choice = c
                self.page = d

            def send(self, userid):
                """ Sends back the last active menu, and page, to the user """
                self.object.send(userid, self.page)

        # If the option is not blocked, call the menu callback block with the choice
        # object, and with the SubMenu class as the new previous menu
        menu.callback(userid,
                      menu.get_option_data(choice, active_page)['object'],
                      SubMenu(menu.menu_id, menu, choice, active_page))
    # If the choice is 8 and higher than 1, then send the user to the previous page
    elif choice == 8 and active_page > 1:
        menu.send(userid, active_page - 1)
    # If the choice is 9, send the user to the next page
    elif choice == 9 and active_page + 1 in menu.pages.keys():
        menu.send(userid, active_page + 1)
    # Otherwise, just make sure the active page is sent back to the user
    else:
        menu.send(userid, active_page)


# Game Events
def server_shutdown(ev):
    """ Called whenever the server is shutting down """

    # Safely unload SAM on shutdown to make sure all data is saved properly
    es.server.cmd('es_unload sam')


def es_map_start(ev):
    """ Called whenever a map starts """

    # Clear Page System Cache
    cache.menus.clear()
    cache.users_active_menu.clear()
    cache.temp.clear()
    # Terminate all chat filters
    chat_filter._delete_all_filters()

    # Make necessary databases saves
    addons_monitor.save_database()
    admins.save_database()


def es_client_command(ev):
    """ Called whenever a user makes a menu choice """
    if ev['command'] == 'menuselect':
        _process_user_choice(int(ev['userid']), int(ev['commandstring']))


def player_activate(ev):
    # Update player info
    players.update(ev['userid'])


def player_disconnect(ev):
    userid = int(ev['userid'])
    steamid = ev['networkid']

    # Decache player from the various systems
    _decache_player(userid)

    # Update player info with last seen
    if steamid in players.data.keys():
        players.data[steamid]['last_seen'] = get_time('%m/%d/%Y at %H:%M:%S')


# Class Declaration
players = _PlayersProfileSystem()
