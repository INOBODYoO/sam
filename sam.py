# -*- coding: utf-8 -*-
# Python Imports
from __future__ import with_statement

import os
import random
import re
import time
from datetime import datetime

# EventScripts Imports
import cmdlib
import es
import gamethread
import playerlib
import psyco
import simplejson as json
import usermsg

psyco.full()

# Plugin Info & Global Variables
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
# 4 = Prints all settings updates to console
def debug(lvl, *message):
    if lvl == plugin.developer_mode:
        for line in message:
            print('[SAM-DEBUG] %s' % line)


# Turn off ES debug completely (if SAM debug is)
es.server.cmd('eventscripts_debug %s' % ('0' if bool(plugin.developer_mode) else '-1'))

MODULES = ('players_manager', 'addons', 'admins_manager', 'settings_manager')
FILTERS = ('#all', '#human', '#ct', '#t', '#alive', '#dead', '#spec', '#bot')
HOME_PAGE_ADDONS = []

print('[SAM]   - Initializing Core Systems')

class _Cache:
    sounds = {}
    temp = {}

cache = _Cache()


class _Path:
    core = es.getAddonPath('sam').replace('/', '\\')
    addons = core + '\\addons\\'
    sounds = 'cstrike\\sound\\sam_sounds\\'
    settings = core + '\\required\\settings.json'
    databases = core + '\\required\\databases\\'
    help_window_file = core + '\\required\\help_window (ignore this file).'

path = _Path()

class DynamicAttributes(object):
    """
    Converts a dictionary into a class with dynamic attributes.
    """

    def __init__(self, obj, subkeys=None):
        """
        Initializes the class with the given dictionary and subkeys to return.
        """
        if not isinstance(obj, dict):
            raise TypeError("obj must be a dictionary")

        if subkeys is None:
            self.__dict__.update(obj)
        else:
            converted = {}
            for key, value in obj.iteritems():
                if isinstance(value, dict):
                    converted[key] = dict((subkey, value.get(subkey)) for subkey in subkeys)
                else:
                    converted[key] = value
            self.__dict__.update(converted)

    def __getattr__(self, attr):
        """
        Gets the value of the given attribute.
        """
        return self.__dict__[attr]

    def __setattr__(self, attr, value):
        """
        Sets the value of the given attribute.
        """
        self.__dict__[attr] = value

    def get(self, attr, default=None):
        """
        Gets the value of the given attribute as a string.
        """
        return str(self.__dict__.get(attr, default))


class _DatabaseSystem:
    """
    Database System
    """

    def __init__(self):
        # Create directories
        databases_dir = path.databases
        addons_dir = databases_dir + 'addons\\'
        if not os.path.exists(databases_dir):
            os.makedirs(databases_dir)
        if not os.path.exists(addons_dir):
            os.makedirs(addons_dir)

    @staticmethod
    def load(db_file, bypass=False):
        """
        Loads a JSON database file
        """
        
        if not bypass:
            db_file = path.databases + db_file + '.json'
        if os.path.isfile(db_file):
            with open(db_file, 'r') as f:
                return json.load(f)
        return {}

    @staticmethod
    def save(db_file, data, bypass=False):
        """
        Saves a JSON database file
        """
        
        if not bypass:
            db_file = path.databases + db_file + '.json'
        if not bool(data) and os.path.isfile(db_file):
            os.remove(db_file)
            return
        try:
            with open(db_file, 'w') as f:
                json.dump(data, f, indent=4, sort_keys=True)
        except:
            debug(1, 'Error saving data to file %s' % db_file.split('\\')[:-1])


databases = _DatabaseSystem()


class _SettingsSystem:
    """
    Settings System
    Handles all settings related functions, configurations, and database
    """

    def __init__(self):
        
        # Categories
        self.general = 'General Settings'
        self.modules = 'Modules & Addons Settings'

        # Setup the default general settings
        default = {
            'chat_prefix': {
                'description': [
                    'Prefix displayed at the beginning of every chat message.',
                    'Can include color coding. Example: #redSAM',
                    'If set to False, then no prefix will be displayed.',
                ],
                'current_value': '#redSAM',
            },
            'anti_spam_chat_messages': {
                'description': [
                    'Enable blocking of repetitive messages sent by SAM',
                    'for a few seconds to prevent chat spamming.',
                ],
                'current_value': False,
            },
            'enable_!rcon_command': {
                'description': [
                    'Enable the !rcon command, allowing admins with the "RCON Command"',
                    'permission to execute a wide range of server commands and',
                    'variables through the in-game chat.',
                ],
                'current_value': True,
            },
            'enable_!admins_command': {
                'description': [
                    'Enable the !admins command, which opens a page displaying a list',
                    'of all admins currently online.',
                ],
                'current_value': True,
            },
            'enable_menus_clock': {
                'description': [
                    'Display a clock in the top right corner of all pages.',
                    'The displayed time is based on the local time of the server host.',
                ],
                'current_value': True,
            },
            'menus_separator_line_length': {
                'description': [
                    'Specify the length of the separator lines in menus and pages.',
                    'The maximum allowed value is 40.',
                ],
                'current_value': 40,
            }
        }

        # Load the database
        self.settings = databases.load(path.settings, bypass=True)
        
        # Is not empty, then update the settings
        if self.settings:
            
            # Remove old settings
            for key in self.settings[self.general].keys():
                if key not in default.keys():
                    del self.settings[self.general][key]

            # Update general settings by adding new settings and updating descriptions
            for key, val in default.items():
                if key not in self.settings[self.general].keys():
                    self.settings[self.general][key] = val
                elif val['description'] != self.settings[self.general][key]['description']:
                    self.settings[self.general][key]['description'] = val['description']
        
        # If the database is empty, then set the default settings
        else: self.settings = {self.general: default.copy(), self.modules: {}}
        
        # Save database
        self.save_database()

    def __repr__(self):

        return str(self.__call__())

    def __str__(self):

        return self.__repr__()

    def __call__(self, arg=None):

        # Update settings from the database
        self.update_settings()
    
        # If theres no argument, return the general settings dictionary
        if arg is None:
            return DynamicAttributes(self.settings[self.general])

        # If the argument is one of the main categories, return the category dictionary
        elif arg in self.settings.keys():
            return self.settings[arg]

        # If the argument is one of the general settings, return the setting value
        elif arg in self.settings[self.general].keys():
            return self.settings[self.general][arg]['current_value']

        # If the argument is one of the addons, return the addon settings
        elif self.settings[self.modules].keys():
            return DynamicAttributes(self.settings[self.modules][arg], 'current_value')
    
    def update_settings(self):
        """
        Updates settings from the database
        """
        
        # Load the database
        database = databases.load(path.settings, bypass=True)
        
        # Update the values of the general settings
        for key, val in database[self.general].items():
            self.settings[self.general][key]['current_value'] = val['current_value']
            
        # Update the values of the addons settings
        m = self.modules
        for addon in database[m].keys():
            for key, val in database[m][addon].items():
                self.settings[m][addon][key]['current_value'] = val['current_value']
     
    def save_database(self, update=False):
        """
        Saves the settings database
        """

        # Make sure we save anything changed to the database, before saving it
        if update:
            self.update_settings()
        
        # Save the database
        databases.save(path.settings, self.settings, bypass=True)

    def module_config(self, module, settings):
        """
        Allows modules & addons to create and update their own settings individually
        """

        # Check if the module is already registered
        if module in self.settings[self.modules].keys():
 
            config = self.settings[self.modules][module]
            
            # Remove old settings
            for key in config.keys():
                if key not in settings.keys():
                    del config[key]
            
            # Update settings by adding new settings and updating descriptions
            for key, val in settings.items():
                if key not in config.keys():
                    config[key] = val
                elif val['description'] != config[key]['description']:
                    config[key]['description'] = val['description']
        
        # If the module is not registered, then register it
        else: self.settings[self.modules][module] = settings.copy()

        # Save database
        self.save_database()

    def help_window(self, userid, section):
        """
        Function to display a help window for the user to consult the given section's
        settings desciptions and current values
        """
        
        # Get the given section's settings, or return if the section is invalid
        if section == self.general:
            settings = self.settings[self.general]
        elif section in self.settings[self.modules].keys():
            settings = self.settings[self.modules][section]
        else:
            msg.hud(userid,
                    'Invalid settings section name: %s' % section,
                    tag='Settings System')
            return

        titled = title(section)
        seperator = '-' * 34
        
        # Add the settings help window disclaimer
        lines = [
            seperator,
            'This window is intended for consulting the descriptions and',
            'current values of each setting, and cannot be modified.',
            'To modify these settings, you can use the menu or manually update',
            'the settings file located at:',
            path.settings,
            seperator + '\n \n'
        ]

        # For each setting add its title, description, and current value
        for setting, data in settings.items():
            lines.extend(
                [
                    seperator,
                    '[%s]' % setting.upper(),
                    seperator,
                    'CURRENT VALUE: %s' % data['current_value'],
                    'DESCRIPTION:',
                    '\n'.join(data['description']),
                    ' '
                ]
            )

        # Display the help window
        msg.info(userid, titled, *lines)


settings = _SettingsSystem()

class _ChatFilterSystem:
    """
    Class to manage chat filters
    Instead of creating multiple chat filters, this class has a main filter listener
    that will check all registered filters and execute their functions accordingly.
    """

    def __init__(self):
        self.filters = {}
        self.main_filter_status = False

    def register(self, filter_id):
        """
        Register a new chat filter
        """

        if filter_id not in self.filters:
            self.filters[filter_id] = _ChatFilter(filter_id)
        if not self.main_filter_status:
            self._start_main_filter()
        return self.filters[filter_id]

    def delete(self, filter_id):
        """
        Delete a chat filter
        """
        self.filters.pop(filter_id, None)
        self.delete_menu(filter_id)
        if not self.filters and self.main_filter_status:
            self._stop_main_filter()

    def remove_user(self, userid, filter_id):
        """
        Remove a user from a chat filter
        """

        if filter_id in self.filters.keys():
            f = self.filters[filter_id]
            if userid not in self._get_users(f.users):
                return
            f.users.remove(userid)
            if not f.users and f.delete_on_empty:
                self.delete(filter_id)
            active = menu_system.get_active_menu(userid)
            if active and active.menu_id == filter_id:
                menu_system.handle_choice(10, userid, True)

    def in_filter(self, userid):
        """
        Check if a user is in any active chat filter
        """

        for filter_id, obj in self.filters.items():
            if obj.temporary and isinstance(obj.users, list) and userid in obj.users:
                return filter_id
        return False

    def _main_chat_filter(self, userid, text, teamchat):
        """
        This is the main chat filter listener
        Its only active when there's at least one chat filter registered.
        """

        for f in self.filters.values():
            if not f.temporary and self.in_filter(userid):
                continue
            users = self._get_users(f.users)
            if userid not in users:
                continue
            if f.temporary:
                self.remove_user(userid, f.filter_id)
            text = text.strip('"')
            if f.cancel_option and text.lower() == '!cancel':
                if callable(f.cancel_option):
                    args = f.cancel_args
                    if args[0] == 'userid':
                        f.cancel_option(userid, *args[1:])
                    else:
                        f.cancel_option(*args)
                msg.hud(userid, 'Operation canceled!', tag='Chat Filter System')
                return 0, 0, 0
            if f.function:
                return f.function(userid, text, teamchat)
            debug(1, 'Chat Filter System | %s filter is missing a function' % f.filter_id)
        return userid, text, teamchat

    def _get_users(self, user_list):
        """
        Get the set of valid user IDs from the given user list
        """
        users = set()
        for u in user_list:
            if isinstance(u, int) and get_userid(u):
                users.add(u)
            elif u in FILTERS or u == '#admins':
                users.update(userid_list(u))
        return users

    def _start_main_filter(self):
        """
        Start the main chat filter listener
        """

        es.addons.registerSayFilter(self._main_chat_filter)
        self.main_filter_status = True
        debug(1, 'Chat Filter System | Main filter started')

    def _stop_main_filter(self):
        """
        Stop the main chat filter listener
        """

        if self.filters or not self.main_filter_status:
            return
        es.addons.unregisterSayFilter(self._main_chat_filter)
        self.main_filter_status = False
        debug(1, 'Chat Filter System | Main filter stopped')

    def delete_menu(self, filter_id):
        """
        Delete the menu associated with the given filter ID
        """

        if menu_system.exists(filter_id):
            del menu_system.menus[filter_id]

    def _delete_all_filters(self):
        """
        Delete all chat filters
        """

        self.filters.clear()
        debug(1, 'Chat Filter System | Terminated all filters')
        self._stop_main_filter()

chat_filter = _ChatFilterSystem()


class _ChatFilter:

    def __init__(self, filter_id):
        self.filter_id = filter_id
        self.function = False
        self.delete_on_empty = True
        self.cancel_option = False
        self.cancel_args = ()
        self.instructions = False
        self.temporary = True
        self.users = []

    def instructions_page(self, *instructions):
        """
        Display the instructions page for the chat filter
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
        menu.send(chat_filter._get_users(self.users))

    def instructions_page_HANDLE(self, userid, choice, submenu):
        """
        Handle the choice made on the instructions page menu
        """

        if choice == 1:
            menu_system.handle_choice(10, userid, True)
            chat_filter.remove_user(userid, self.filter_id)
            msg.hud(userid, '%s | Operation Cancelled!' % title(self.filter_id))
            if callable(self.cancel_option):
                args = self.cancel_args
                if args[0] == 'userid':
                    self.cancel_option(userid, *args[1:])
                else:
                    self.cancel_option(*args)


class _MessageSystem:
    """
    Class with all message types functions
    """

    def __init__(self):
        self.spam = []
        self.colors = {
            'blue': '0000FF', 'green': '00FF00', 'orange': 'FFA500',
            'red': 'FF0000', 'black': '000000', 'white': 'FFFFFF',
            'pink': 'FFC0CB', 'gray': '808080', 'purple': '800080',
            'yellow': 'FFFF00', 'cyan': '00FFFF', 'gold': 'FFD700',
            'silver': 'C0C0C0', 'brown': 'A52A2A', 'navy': '000080',
            'teal': '008080', 'olive': '808000', 'magenta': 'FF00FF',
            'lime': '00FF00', 'aqua': '00FFFF', 'maroon': '800000',
            'coral': 'FF7F50', 'terro': 'FF3D3D', 'ct': '9BCDFF',
            'spec': 'CDCDCD', 'default': 'FFB300', 'violet': 'EE82EE',
            'indigo': '4B0082', 'turquoise': '40E0D0', 'salmon': 'FA8072',
            'lavender': 'E6E6FA', 'plum': 'DDA0DD', 'khaki': 'F0E68C',
            'peach': 'FFDAB9', 'sienna': 'A0522D', 'olivedrab': '6B8E23',
            'slategray': '708090', 'crimson': 'DC143C', 'tomato': 'FF6347',
            'orchid': 'DA70D6', 'chartreuse': '7FFF00', 'steelblue': '4682B4',
            'peru': 'CD853F', 'darkslategray': '2F4F4F', 'firebrick': 'B22222',
            'rosybrown': 'BC8F8F', 'darkolivegreen': '556B2F', 'beige': 'F5F5DC',
        }


    @staticmethod
    def sort_users(users):
        """
        Returns a sorted list of user IDs based on the input
        """

        if users == 'BOT':
            return users
        elif users == '#admins':
            return userid_list('#admins')
        elif isinstance(users, int) or users in FILTERS:
            return users

        sorted_users = []
        for x in users:
            if str(x).startswith('#'):
                for userid in userid_list(x):
                    if userid not in sorted_users:
                        sorted_users.append(userid)
                continue
            x = get_userid(x)
            if x and x not in sorted_users:
                sorted_users.append(x)

        return sorted_users

    def is_spam(self, text):
        """
        Places a text in the spam queue for a few seconds, and returns whether
        the text is in the queue or not
        """
        
        # Get the text hash
        text_hash = hash(text)
        
        # Check if the text is in the spam queue
        if text_hash in self.spam:
            return True
        
        # Add the text to the spam queue
        self.spam.append(text_hash)
        
        # Remove the text from the spam queue after a few seconds
        delay_task(10, 'spam_%s' % text_hash, self.spam.remove, (text_hash,))
        return False

    def tell(self, users, message, prefix=True, tag=False, log=False):
        """
        Chat message that can be sent to any player or group of players.
        The text can also be color coded
        e.g: #red{prefix} | #green{tag} | #whiteHello World
        """

        # Setup the prefix
        if prefix:
            # If prefix is not a string, then use the settings prefix
            # otherwise use the given prefix
            if not isinstance(prefix, str):
                prefix = settings('chat_prefix')
            prefix = '#default%s #gray| ' % prefix if prefix else ''

        # If prefix is False, then don't use any prefix
        else: prefix = ''
        
        # Setup the tag to be used in the message
        tag = '#coral%s #gray| ' % (tag) if tag else ''

        # Merge the prefix, tag, and message into one text
        text = '#default' + prefix + tag + '#beige' + message

        # Check if the message is in the spam queue
        if self.is_spam(text) and settings('anti_spam_chat_messages'):
            return

        # Check if the message should be logged in the server console
        if log and ('#all' in users or '#human' in users):
            self.console(message, tag)
        
        # Send the message to the users
        usermsg.saytext2(self.sort_users(users), 0, format_text(text))

    def hud(self, users, *text):
        """
        A hudhint type message which appears in the bottom center of the player screen
        """

        usermsg.hudhint(
            self.sort_users(users),
            format_text('---< SAM >---\n \n' + '\n'.join(map(str, text)), True)
        )

    def center(self, users, text):
        """
        A type message which appears in the center of the player screen
        """

        usermsg.centermsg(self.sort_users(users), text)

    def side(self, users, *text):
        """
        A type message which appears on the side of the player screen
        """

        usermsg.keyhint(
            self.sort_users(users),
            format_text(
                '\n'.join(map(str, text)),
                remove_colors=True,
                remove_special=False
            )
        )

    def vgui_panel(self, users, panel_name, visible, data={}):
        """
        VGUI panel type message, to send VGUI panels to users
        """

        usermsg.showVGUIPanel(self.sort_users(users), panel_name, visible, data)

    def motd(self, users, window_title, url_or_filepath, message_type=2):
        """
        Message Of The Day type message, to send URL pages to
        users using the in-game MOTD window browser
        """
    
        usermsg.motd(
            self.sort_users(users),
            message_type,
            'SAM | %s' % window_title,
            url_or_filepath
        )

    def info(self, users, title, *lines):
        """
        Info type message, to send text to users using the in-game info window
        """

        with open(path.help_window_file, 'w') as f:
            f.write('\n'.join(lines))

        self.motd(
            users=self.sort_users(users),
            window_title=title,
            url_or_filepath=path.help_window_file.replace('\\', '/'),
            message_type=3
        )

    @staticmethod
    def console(text, tag=None):
        """
        Prints a message to the server console with SAM's prefix, a "tag" can be used
        to identify the system or addon from which the message is being sen 
        E.g. SAM | PLAYERS MANAGER | X was kicked from the server
        """

        print(
            format_text(
                '[%s][SAM] %s%s' % (get_time('%H:%M:%S'),
                tag.upper() + ' | ' if tag else '', text), True
            )
        )


msg = _MessageSystem()


class _AddonsMonitor:
    """
    Addons Monitor class
    """

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

    def __init__(self):

        # Init Addons dictionary instance
        self.addons = {}

        # Installed Addons verification
        self._verify_installed_addons()

        # Get Addons Monitor database
        database = databases.load('addons')

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

    def __call__(self, addon):
        
        return self.addons[addon] if addon in self.addons.keys() else None

    def _verify_installed_addons(self):
        """
        Verify if all installed Addons are valid
        """
    
        # Loop over all installed Addons
        installed = self.addons_dir_list()

        for addon in installed:
            metadata = path.addons + addon + '/%s.json' % addon
            if not os.path.isfile(metadata):
                debug(1, 
                      '[Addons Monitor] Failed to install/update %s addon.' \
                      ' (missing metadata.json file)' % addon.title())
                continue
            metadata = databases.load(metadata, bypass=True)
            if not metadata:
                debug(1, 
                      '[Addons Monitor] Failed to install/update %s addon.' \
                      ' (invalid metadata.json file)' % addon.title())
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
        """
        Save Addons Monitor database
        """

        database = {}
        for addon in self.addons.keys():
            database[addon] = self.addons[addon].__dict__.copy()
        databases.save('addons', database)

    @staticmethod
    def addons_dir_list():
        """
        List of Addons in the addons folder
        """

        return (i for i in os.listdir(path.addons) if os.path.isdir(path.addons + i))

    def is_running(self, addon):
        """
        Check if an Addon is running
        """

        if addon not in self.addons.keys():
            return False
        return self.addons[addon].state

    def import_addon(self, addon):
        """
        Import an Addon
        """

        if not self.is_running(addon):
            debug(1, 'Could not import %s, addon is not running or is missing' % addon)
            return None
        return import_module('addons/' + addon)


addons_monitor = _AddonsMonitor()


class _AdminsSystem:
    """
    Admins System

    This system is responsible for managing the server admins and groups.
    """

    def __init__(self):
        # Init admins and groups dictionaries
        self.admins = {}
        self.groups = {}
        # Set up the Permissions dictionaries
        self.addons_permissions = []
        self.admins_permissions = [
            'addons',
            'admins_manager',
            'players_manager',
            'kick_players',
            'rcon_command',
            'settings_manager'
        ]

    def __repr__(self):
        return str(type(self))

    def __str__(self):
        return self.__repr__()

    def __call__(self, arg=None):
        
        # Check if no argument was given
        if arg is None:
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
        return self.admins

    def is_admin(self, user):
        """
        Function to return whether a user is a valid Admin
        """

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
        """
        Checks whether an Admin has permission to perform an action.
        """
        
        # We return True if the permission is set to False, as a way to accommodate
        # the Players Manager commands which do not have a permission assigned
        if not permission:
            return True

        # Check if developer mode is level 3
        if plugin.developer_mode == 3:
            return True

        # Get the Admin class object
        admin = self.__call__(user)
        
        # Check if the admin is valid
        if not admin or not permission:
            return False
        
        # Get the admin group object
        group = self.get_admin_group(admin.steamid)

        # Check if the admin is a Super Admin
        if admin.super_admin:
            return 3 if permission == 'ban_level' else True

        # If permission is 'ban_level', return the Admin's ban level, or his group's
        if permission == 'ban_level':
            lvl = admin.ban_level
            return max(lvl, group.ban_level) if group else lvl

        # Check if the admin or his group has the permission assigned
        admin_perm = admin.permissions.get(permission, False) or\
                     admin.addons_permissions.get(permission, False)
        group_perm = False
        if group:
            group_perm = group.permissions.get(permission, False) or\
                         group.addons_permissions.get(permission, False)

        # Notify the Admin if they don't have permission
        if not (admin_perm or group_perm) and notify:
            msg.hud(user, 'You do not have permission to %s!' % title(permission))

        return admin_perm or group_perm

    def is_super_admin(self, user):
        """
        Function to check whether an Admin is a Super Admin
        """

        # Get the Admin class object
        admin = self.__call__(user)
    
        return admin.super_admin if admin else False

    def list(self, arg=None):
        """
        Get a specific list of admins or groups.
    
        - 'groups': Return a copy of the groups dictionary.
        - 'super_admins': Return a dictionary of super admins.
        - 'online': Return a dictionary of online admins.
        - (default): Return a copy of the admins dictionary.
        """

        if arg == 'groups':
            return self.groups.copy()
        elif arg == 'super_admins':
            return dict((x, y) for x, y in self.admins.copy().items() if y.super_admin)
        elif arg == 'online':
            return dict((x, y) for x, y in self.admins.copy().items() if get_userid(x))
        return self.admins.copy()

    def compare_immunity(self, admin1, admin2):
        """
        Compare the immunity levels between two Admins and
        determine if Admin1 has higher immunity than Admin2.
        """

        # If Developer mode is level 3, return True regardless
        if plugin.developer_mode == 3:
            return True

        # Admin1 is most likely a menu user, therefore, get his steamid
        admin1 = get_steamid(admin1)

        # Return True if Admin2 is not an actual Admin or is actually Admin1
        if not self.is_admin(admin2) or admin1 == admin2:
            return True

        # Get both Admins objects
        admin1 = self.admins[admin1]
        admin2 = self.admins[admin2]

        # Check if Admin2 is a Super Admin
        if admin2.super_admin:
            msg.hud(admin1, 'Action denied! %s is immune to you.' % admin2.name)
            return False

        # Check if Admin1 is a Super Admin
        if admin1.super_admin:
            return True

        # Function to get the immunity level of an Admin
        def get_immunity(admin):
            admin_imm = admin.immunity_level
            group_imm = self.groups.get(admin.group, 0).immunity_level
            return max(admin_imm, group_imm)

        # Compare the immunity levels between the two Admins
        result = get_immunity(admin1) > get_immunity(admin2)

        # Notify Admin1 if they don't have permission
        if not result:
            msg.hud(admin1, 'Action denied! %s is immune to you.' % admin2.name)

        return result


    def new_admin(self, steamid, super_admin=False):
        """
        Function to create a new Admin
        """

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
        """
        Function to delete an Admin
        """

        # Check if the Admin exists
        if steamid not in self.admins.keys():
            return

        # Delete the Admin
        del self.admins[steamid]
    
        # Save the database
        self.save_database()

    def new_group(self, group):
        """
        Function to create a new Admin Group
        """

        # Check if the group already exists
        if group in self.groups.keys():
            return
    
        # Create the group
        self.groups[group] = Group(group)
    
        # Save the database
        self.save_database()

    def delete_group(self, group):
        """
        Function to delete an Admin Group
        """

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
        """
        Function to get the members of an Admin Group
        """

        # Check if the group exists
        if group not in self.groups.keys():
            return []

        # Return the list of members
        return [admin.steamid for admin in self.admins.values() if admin.group == group]

    def get_admin_group(self, user):
        """
        Function to get the group of an Admin
        """

        # Check if user is an Admin
        if not self.is_admin(user):
            return False
        
        # Get the Admin object
        admin = self.__call__(user)

        # Get the Admin group key
        group = admin.group

        # Check if the Admin has a group assigned
        if not group:
            return False

        # Get the Admin Group object
        group = self.groups.get(group, False)
        
        # Check if the group exists
        if not group:
            admin.group = False
            return False

        # Return the group object
        return group

    def save_database(self):
        """
        Saves both Admins & Groups database at once
        """

        # Admins Database
        databases.save(
            'admins_database',
            dict((x, y.__dict__.copy()) for x, y in self.admins.items())
        )

        # We can skip Groups if none exists
        if not self.groups:
            return

        # Groups Database
        databases.save(
            'groups_database',
            dict((x, y.__dict__.copy()) for x, y in self.groups.items())
        )


    def register_addon_permission(self, permission):
        """
        Internal function for Addons to add their own permissions
        """

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


    def _toggle_permission(self, target, permission):
        """
        Toggle the state of an Admin/Group permission.
        """

        if permission in self.admins_permissions:
            # Toggle the state if the permission is already assigned
            target.permissions[permission] = not target.permissions[permission]
        elif permission in self.addons_permissions:
            # Toggle the state if the permission is already assigned
            target.addons_permissions[permission] = not target.addons_permissions[permission]
        else:
            # Remove the permission if it doesn't exist in any permissions list
            if permission in self.admins_permissions:
                self.admins_permissions.remove(permission)
            elif permission in self.addons_permissions:
                self.addons_permissions.remove(permission)


    def _initialize_database(self):
        """
        Initialize the Admins database by converting dictionaries to class objects.

        Notes:
        - Called only on load to initialize the database.
        - Converts the Admins and Groups dictionaries into Admin and Group class objects.
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
    """
    Admin Class object
    """

    def __init__(self, steamid, super_admin=False):
        player = get_userid(steamid)

        self.name = es.getplayername(player) if player else 'Unregistered'
        self.steamid = steamid
        self.admin_since = get_time('%d/%m/%Y')
        self.super_admin = super_admin
        self.ban_level = 0
        self.immunity_level = 0
        self.group = False
        self.permissions = dict((x, False) for x in admins.admins_permissions)
        self.addons_permissions = dict((x, False) for x in admins.addons_permissions)

    def toggle_permission(self, permission):
        """
        Channels this class through the AdminSystem's internal _toggle_permission
        function, which toggles admin/group's permission state
        """

        admins._toggle_permission(self, permission)


class Group(object):
    """
    Admin Group Class object
    """

    def __init__(self, name):
        self.id = name
        self.name = name
        self.ban_level = 0
        self.immunity_level = 0
        self.color = 'default'
        self.permissions = dict((x, False) for x in admins.admins_permissions)
        self.addons_permissions = dict((x, False) for x in admins.addons_permissions)

        # Attach the group color to the name
        self._attach_color()

    def toggle_permission(self, permission):
        """
        Channels this class through the AdminSystem's internal _toggle_permission
        function, which toggles admin/group's permission state
        """
        admins._toggle_permission(self, permission)

    def _attach_color(self):
        """
        Attaches the group color to the name
        """

        self.name = '#' + self.color + title(self.id) + '#default'


class _CommandsSystem:
    """
    A helper class for managing custom commands in SAM.
    """

    def chat(self, command, block):
        """
        Registers a chat command with the given command name and block of code.
        """

        self.delete(command)
        cmdlib.registerSayCommand('!' + command, block, 'SAM chat command')
        cmdlib.registerSayCommand('!sam_' + command, block, 'SAM chat command')

    def client(self, command, block):
        """
        Registers a client command with the given command name and block of code.
        """

        self.delete(command)
        cmdlib.registerClientCommand('sam_' + command, block, 'SAM client command')

    def server(self, command, block):
        """
        Registers a server command with the given command name and block of code.
        """

        self.delete(command)
        cmdlib.registerServerCommand('sam_' + command, block, 'SAM console command')

    @staticmethod
    def delete(command):
        """
        Unregisters a command with the given name.
        """

        cmdlib.unregisterSayCommand('!' + command)
        cmdlib.unregisterSayCommand('!sam_' + command)
        cmdlib.unregisterClientCommand('sam_' + command)
        cmdlib.unregisterServerCommand('sam_' + command)
    
    @staticmethod
    def no_permission(userid):
        """
        Notifies the user that they don't have permission to use the command
        """

        msg.hud(
            userid,
            'Commands System: You do not have permission to use this command!'
        )
        
    @staticmethod
    def is_disabled(userid):
        """
        Notifies the user that the command is disabled
        """
        
        msg.hud(userid, 'Commands System: This command is disabled!')



cmds = _CommandsSystem()


class _PlayersProfileSystem:
    """
    Systems responsible for gathering various types of information about
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
        """
        Return the Player info as a class object
        """
        target = None
        if isinstance(user, int):
            target = get_steamid(user)
        elif str(user).startswith('[U:') or str(user).startswith('STEAM_'):
            target = user
        return self.Player(self.data[target]) if target in self.data.keys() else None

    def list(self):
        return [self.Player(self.data[k]) for k in self.data.keys()]

    def update(self, userid):
        """
        Updates the player info into the database
        """
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


class _MenuSystem:
    """
    Menu System
    System to handle anything related to menus, whether is caching,
    forced user choices, or to process menu options.
    """
    
    class SubMenu:
        """
        Class to save last active menu and user choice as the new submenu
        info to be carried away in the menu callback
        """

        def __init__(self, a, b, c, d):
            self.menu_id = a
            self.object = b
            self.choice = c
            self.page = d
        
        def __repr__(self):
            """
            Returns the menu ID
            """
            
            return self.menu_id
        
        def send(self, userid):
            """
            Sends back the last active menu, and page, to the user
            """

            self.object.send(userid, self.page)
    
    def __init__(self):
        
        # Initialize the menus and users cache
        self.menus = {}
        self.users_active_menu = {}
        self.users_previous_menu = {}
        self.users_menu_history = {}
        
    def handle_choice(self, choice, user, force_close=False):
        """
        Handles the user's choice
        Used mostly to force a user to make certain choices
        """

        # Make sure to get a valid userid
        userid = get_userid(user)
        if not userid:
            msg.console('Invalid user ID (%s), could not handle user choice.' % userid,
                        'Menu System')
            return

        # If its not meant to force close the menu, then just process the choice
        if not force_close:
            self.process_user_choice(userid, choice)
            return
        
        # Otherwise, force the user to close the menu, and clear the user cache
        if self.get_active_menu(userid):
            del self.users_active_menu[userid]
            self.cancel_refresh(userid) 
        es.cexec(userid, 'slot10')
        
    def send_menu(self, userid, menu_id, page=1):
        """
        Sends the given menu to the user
        """

        if menu_id in self.menus.keys():
            self.menus[menu_id].send(userid, page)
        else:
            msg.console('Invalid Menu ID (%s), could not send menu to user.' % menu_id,
                        'Menu System')
    
    def exists(self, menu):
        """
        Checks whether the given menu exists
        """
        
        if isinstance(menu, str):
            return self.menus.get(menu, False)
        elif isinstance(menu, Menu) or isinstance(menu, self.SubMenu):
            return self.menus.get(menu.menu_id, False)
        return False
          
    def get_active_menu(self, userid):
        """
        Returns the user's active menu as a DynamicAttributes object
        """

        menu = self.users_active_menu.get(userid, False)
        return DynamicAttributes(menu) if menu else False

    def get_previous_menu(self, userid):
        """
        Returns the user's previous menu as a DynamicAttributes object
        """

        menu = self.users_previous_menu.get(userid, False)
        return DynamicAttributes(menu) if menu else False
    
    @staticmethod
    def cancel_refresh(target):
        """
        Cancels users menu refresh timer
        """

        # Check if the object is a valid filter
        if target in FILTERS or target == '#admins':
            for userid in userid_list(target):
                cancel_delay('sam_menu_refresh_%s' % userid) 
            return
        elif isinstance(target, tuple) or isinstance(target, list):
            for userid in target:
                cancel_delay('sam_menu_refresh_%s' % userid)
            return
        
        # Otherwise, make sure to get a valid userid
        userid = get_userid(target)
        if userid:
            cancel_delay('sam_menu_refresh_%s' % userid)
        
    def process_user_choice(self, userid, choice):
        """
        Processes the user menu choice by either executing a pre-defined function,
        sending the user to another page or closing the menu.
        """

        # Cancel the menu refresh
        self.cancel_refresh(userid)

        # Check if the user has an active menu and valid menu,
        # if not then the page has been closed before and we can end the process.
        active = self.get_active_menu(userid)
        if not active or not self.exists(active.menu_id):
            return
        
        # Save the active menu and page in the user's menu history
        if userid not in self.users_menu_history.keys():
            self.users_menu_history[userid] = {}
        self.users_menu_history[userid][active.menu_id] = active.page

        # Set the active menu now as the user's previous menu,
        # and remove it as the active menu
        self.users_previous_menu[userid] = active.__dict__.copy()
        del self.users_active_menu[userid]

        # Get the active menu class object
        menu = self.menus[active.menu_id]
    
        # If the user chose 0 (the 10th option), and the menu has a close option
        if choice == 10 and menu.close_option:

            # Get the the submenu, if there's any
            submenu = self.exists(menu.submenu)
            
            if submenu:
                # Get the user's menu history
                history = self.users_menu_history[userid]
                
                # If submenu is in the user's menu history, the send the user to the 
                # last page saved in history
                if submenu.menu_id in history.keys():
                    submenu.send(userid, history[submenu.menu_id])
                # Otherwise, send the user to the page saved in submenu object
                else:
                    self.menus[submenu.menu_id].send(userid, menu.submenu_page)
    
            return

        # If the choice is 8 and there's a previous page,
        # then send the user to the previous page
        elif choice == 8 and active.page > 1:
            menu.send(userid, active.page - 1)
            return

        # If the choice is 9, and theres a next page available,
        # send the user to the next page
        elif choice == 9 and active.page + 1 in menu.pages.keys():
            menu.send(userid, active.page + 1)
            return

        # Otherwise process the page options
        elif choice <= len(menu.get_page_options(active.page)):
            # Check if the menu hasnt a callback function, or the option is blocked
            if not menu.callback or choice in menu.blocked_options:
                # Notify the user if the option is blocked
                if choice in menu.blocked_options:
                    msg.hud(userid, 'This option is currently blocked')
                # Re-send the menu back to the user
                menu.send(userid, active.page)
                return

            # Otherwise call the menu callback function parsing the user's choice object,
            # and the active menu as the submenu
            menu.callback(userid,
                          menu.get_option_data(choice, active.page)['object'],
                          self.SubMenu(menu.menu_id, menu, choice, active.page))
            return
        # If anything fails, then re-send the menu back to the user
        else:
            menu.send(userid, active.page)  
            
menu_system = _MenuSystem()      


class Menu(object):
    """
    Class system based on EventScripts popuplib library to create paged menus
    using SourceEngine's Radio Popups as the user interface.
    """

    def __init__(self, menu_id, callback=None, submenu=None):
        self.menu_id = menu_id
        self.callback = callback
        self.submenu = False
        self.submenu_page = 1
        if isinstance(submenu, str):
            self.submenu = submenu
        elif isinstance(submenu, menu_system.SubMenu):
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
        """
        Adds/Changes the title of the menu
        """

        self.title_text = ' :: ' + text

    def description(self, *lines):
        """
        Adds/Changes the description of the menu

        Note: Multiple lines can be given as a list or tuple
        """

        self.description_text = '\n'.join(lines)

    def footer(self, *lines):
        """
        Adds/Changes the footer of the menu
            
        Note: Multiple lines can be given as a list or tuple
        """

        self.footer_text = self.separator_line + '\n' + '\n'.join(lines)

    def add_line(self, *lines):
        """
        Adds a new line to the menu

        Note: Multiple lines can be given as a list or tuple
        """

        self.pages[self._current_page()].extend([str(line) for line in lines])

    def add_option(self, obj, text, blocked=False):
        """
        Adds a new option to the menu
        """

        # Get the current page
        page = self._current_page()

        # Add the option to the current page
        self.pages[page].append(
            {
                'object': obj,
                'text': text,
                'blocked': blocked,
                'choice': len(self.pages[page]) + 1,
                'page': page
            }
        )

    def add_options(self, options_list):
        """
        Adds multiple options to the menu

        Note: Each option must be a tuple with the following format:
              (object, text, blocked=False)
        """

        for item in options_list:
            self.add_option(*item)

    def separator(self):
        """
        Adds a seperator line to the menu
        """

        self.add_line(self.separator_line)

    def next_page(self):
        """
        Adds a new page to the menu
        """

        self.pages[max(self.pages.keys()) + 1] = []

    def send(self, users, page=1):
        """
        It's called once the menu is fully setup and ready to be sent to the user.
        Builds the given page with the menu title, description, lines, options, etc.,
        and sends it to the user/users.
        """

        # Abort if users do not exist at all
        if not users:
            msg.console(
                'Invalid user/users list, could not send menu. (%s)' % self.menu_id,
                'Menu System'
            )
            return

        # If the given page is not valid, then set it to the first page
        if page not in self.pages.keys():
            page = 1

        # We build pages line by line, so we setup a list to store each line of the page
        # which is being constructed.
        display = []
    
        # First, we add the menu header, consisting of the plugin name + current version
        # and the current time, if enabled.
        # If the header is set to False, then will not be added.
        if bool(self.header_text):
            clock = ' ' * 30 + get_time('%H:%M') if settings('enable_menus_clock') else ''
            display.append('SAM v' + plugin.version + clock + '\n \n')

        # Second, we add the menu title, ideally consisting of the name of the
        # Module/Addon, or system from which menu is being sent from.
        if bool(self.title_text):
            pages_length = len(self.pages.keys())
            if self.pages_counter and pages_length > 1:
                counter = '(%s/%s)' % (page, pages_length)
                display.append('%s   %s' % (self.title_text, counter))
            else:
                display.append(self.title_text)
    
        # Third, we add the menu description, ideally to explain what the menu is about,
        # or instruct the user on what to do.
        if bool(self.description_text):
            display.extend((self.separator_line, self.description_text))
        display.append(self.separator_line)

        # Forth, we start adding the page's lines and options
        # Build a new list of blocked options
        self.blocked_options = []

        # Check if the number of max lines is between the valid values
        if not 1 <= self.max_lines <= 7:
            self.max_lines = 7
    
        # Iterate through the page's lines and options
        option = 0
        for index, line in enumerate(self.pages[page]):
            # If it's just a text line, we simply add the line
            if isinstance(line, str):
                display.append(line)
                continue
            # If it's an option, we add it as numbered option, unless its blocked
            option += 1
            blocked = '' if line['blocked'] else '->'
            display.append('%s%d. %s' % (blocked, option, line['text']))
    
        # Fith, we add the footer of the menu
        if self.footer_text:
            display.append(self.footer_text)

        # Sixth, we add the previous, next and close options if necessary
        if self.close_option:
            display.append(self.separator_line)
    
        # If there's more than one page in the menu, we add the previous page option
        if page > 1:
            display.append('->8. Previous Page')
        # Check if there is a next page after the given page
        if page < len(self.pages):
            display.append('->9. Next Page')
    
        if self.close_option:
            # The close option can either be a 'Close Menu' or 'Previous Menu' option
            # depending on whether the menu has a submenu or not
            text = '0. %s' % ('Previous Menu' if self.submenu else 'Close Menu')
            display.append(text)

        # If nothing was added to the page, we simply abort the process
        if not display:
            return
        # Otherwise, we join the page's lines and options into a single string
        display = '\n'.join(display)
        
        # At this point, the page is complete, and we can cache it
        menu_system.menus[self.menu_id] = self
        # Sort the users list
        users = (users,) if isinstance(users, int) else userid_list(users)
        # Cancel any refresh process for the users
        menu_system.cancel_refresh(users)

        # Send the page to each user
        for userid in users:
            # Cache the menu as the user's new active menu
            menu_system.users_active_menu[userid] = {'menu_id': self.menu_id,
                                                     'page': page}
            # Display the menu to the user in-game
            es.showMenu(
                self.timeout,
                userid,
                format_text(
                    display.encode('utf-8'),
                    remove_colors=True,
                    remove_special=True,
                    strip_text=False
                )
            )
            # If the menu has no timeout, we start the refresh process
            if not self.timeout:
                delay_task(1, 'refresh_%s_page' % userid, self._refresh_page, userid)

    def send_option(self, userid, option, page=None):
        """
        Sends the given option to the given user
        """

        option = self.get_option_data(option, page)
        self.send(userid, option['page'])
        menu_system.handle_choice(option['option_number'], userid)

    def get_option_data(self, obj, page=None):
        """
        Returns the option data of the given object

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

        # If no page was given, then look for the option in all the pages
        for page in self.pages.keys():
            option = look_in_page(obj, page)
            if option == obj:
                return option
        # If the option wasn't found, then return None
        return None

    def get_page_options(self, page=None):
        """
        Returns the list of all the page's options
        """

        # If a page was not given, then get the current page
        if not page:
            page = self._current_page()
        return [i for i in self.pages[page] if isinstance(i, dict)]

    @staticmethod
    def _refresh_page(user):
        """
        Refreshes the user's active menu by re-sending the page
        """
        
        # Make sure to get a valid userid
        userid = get_userid(user)
        
        # Get the user's active menu
        active_menu = menu_system.get_active_menu(userid)

        # If the user has an active menu, and the menu still exists,
        # then re-send the menu back to the user
        if active_menu and menu_system.exists(active_menu.menu_id):
            menu_system.send_menu(userid, active_menu.menu_id, active_menu.page)

    def _current_page(self):
        """
        Returns the last edited page
        """

        page = max(self.pages.keys())
        # Check if the number of the page options higher or equal to the max lines
        # if so then initiate the next page
        if self.max_lines and len(self.get_page_options(page)) >= self.max_lines:
            page += 1
            self.pages[page] = []
        return page


# Load/Unload Functions
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
    msg.tell('#all', 'Loaded', prefix='#redSAM', tag='#turquoise' + plugin.version)


def unload():

    # Close active menus from users
    for userid in menu_system.users_active_menu.keys():
        menu_system.handle_choice(10, userid, True)
        msg.hud(userid, 'Your page was closed because SAM is unloading.')

    # Clear cache and save data
    clear_cache_and_save_data()
    databases.save('players_data', players.data)

    # Delete core module commands
    cmds.delete('sam')
    cmds.delete('menu')
    cmds.delete('rcon')
    cmds.delete('admins')

    # Unload main modules
    msg.console('* Unloading Main Modules:')
    for module in MODULES:
        es.unload('sam/' + module)
        msg.console('* Unloaded %s Module' % title(module))

    msg.tell('#all', 'Unloaded', prefix='#redSAM', tag='#turquoise' + plugin.version)


# Home Page
def home_page(userid):
    """
    Send SAM's home page to the user
    """

    # Check if user is an Admin
    if not admins.is_admin(userid):
        msg.hud(userid, 'You are not allowed to use SAM!')

    menu = Menu('home_page', home_page_HANDLE)
    menu.title('Home Page')

    # Add main modules options
    for module in MODULES:
        if module == 'addons':
            menu.add_option(module, 'Addons Monitor')
            continue
        menu.add_option(module, title(module))

    # Add Addons options
    if HOME_PAGE_ADDONS:
        menu.separator()
        menu.add_line('  :: Addons')
        menu.separator()

        for basename in HOME_PAGE_ADDONS:
            # Get the Addon object
            addon = addons(basename)
            # Check if the Addon is enabled
            if addon and addon.state:
                menu.add_option(basename, addon.name)
                continue
            # Otherwise, remove the Addon from the list
            HOME_PAGE_ADDONS.remove(basename)

    menu.send(userid)


def home_page_HANDLE(userid, choice, submenu):
    
    # Check if the choice is a main module
    if choice in MODULES:
        import_module(choice).module_menu(userid)
        return
    # Otherwise, check if the choice is an Addon
    elif choice in HOME_PAGE_ADDONS:
        addons.import_addon(choice).addon_menu(userid)
        return
        
    # Send the user back to the home page
    home_page(userid)


# Command Functions
def sam_CMD(userid, args):
    """
    Command to open SAM's home page
    """
    
    # Check if the Admins database is empty
    if not admins.admins:
        # Proceed to first admin setup
        import_module('admins_manager').first_admin_setup(userid)
        return

    # Send the user to the Home Page
    home_page(userid)


def rcon_CMD(userid, args):
    """
    Command to execute RCON commands and server variables
    Note: Requires 'rcon_command' permission
    """

    # Check if the command is enabled and if the user has the permission to use it
    if not admins.is_allowed(userid, 'rcon_command'):
        cmds.no_permission(userid)
        return
    elif not settings('enable_!rcon_command'):
        cmds.is_disabled(userid)
        return

    # Check if any arguments were provided
    if not args:
        # If no arguments were given, send the syntax example to the user
        msg.tell(userid, '#specSyntax Example:')
        msg.tell(userid, '#salmon!rcon <command/variable> {arguments/value}')
        return

    # Extract the command/variable and arguments
    command = args.pop(0)
    arguments = ' '.join(args) if args else None

    # Check if the command is a valid variable
    if es.exists('variable', command):
        # If the command is sv_cheats,
        # only Super Admins can change it to prevent enabling cheats on the server
        if command == 'sv_cheats' and not admins.is_allowed(userid, 'super_admin'):
            msg.hud(userid, 'Only Super Admins can change sv_cheats command!')
            return

        # Check if arguments were given
        if not arguments:
            msg.tell(userid, 'No arguments given!')
            return

        # Set the server variable to the given arguments
        es.ServerVar(command).set(arguments)
        msg.tell(
            userid,
            '#specRCON: Set #salmon%s #specto #tomato%s' % (command, arguments)
        )
        return

    # Check if the command is a valid command
    elif es.exists('command', command):
        # Check if any arguments were given next to the command
        if arguments:
            # Execute the command with the given arguments
            es.server.insertcmd('%s %s' % (command, arguments))
        elif command.startswith(('bot_', 'es_')):
            # Execute the command without arguments if
            # it's related to bots or EventScripts settings
            es.server.insertcmd(command)
        msg.tell(userid, '#specRCON: Executed #salmon%s #tomato%s' % (command, arguments))
        return

    # Invalid command or variable
    msg.tell(userid, '#salmon\'%s\' #specis not a command or server variable.' % command)


def admins_CMD(userid, args):
    """
    Command to open a menu with a list of all the admins online
    """

    # Check if the command is enabled
    if not settings('enable_!admins_command'):
        cmds.is_disabled(userid)
        return

    # Get a list of all admins online with their Admin Class object
    online_admins = admins.list('online')

    # Check if there are any admins online
    if not online_admins:
        msg.hud(userid, 'There are no admins online')
        return

    # Start building the menu
    menu = Menu('admins_list')
    menu.header_text = False

    # Add a title to the menu showing the number of
    # admins online and the total number of admins
    menu.title('Admins Online (%s of %s)' % (len(online_admins), len(admins.list())))

    # Create a list with the name of all the Admins and tag them as Super Admin
    # if applicable, or tag them with the Admin group they are in if applicable
    admins_list = []
    super_admins_list = []

    for admin in online_admins.values():
        # Check if the admin is a Super Admin
        if admin.super_admin:
            super_admins_list.append(admin.name)
        # Otherwise, check if the admin is in a group
        elif admin.group:
                admins_list.append('%s (%s)' % (admin.name, admins(admin.group).name))
        # If nothing else, then just add the admin's name
        else:
            admins_list.append(admin.name)

    # Sort the lists alphabetically and add them to the menu
    menu.add_line('- Super Admins')
    menu.add_options(((x, x) for x in sorted(super_admins_list)))
    if len(super_admins_list) > 5:
        menu.next_page()
    else:
        menu.separator()
    menu.add_line('- Admins')
    menu.add_options(((x, x) for x in sorted(admins_list)))

    # Send the menu to the user
    menu.send(userid)


# Core Functions
def get_userid(user):
    """
    Returns the userid of the given user
    """

    # Use es.getuserid() for a faster result, and return it if valids
    userid = es.getuserid(user)
    if userid:
        return userid
    
    # Otherwise, loop through all the players
    for player in player_list('#all'):
        # Check if the user matches the player's steamid
        if player.steamid == user or \
            (isinstance(user, str) and user.lower() in player.name.lower()):
            return player.userid


def get_steamid(user):
    """
    Returns the steamid of the given user
    """

    return es.getplayersteamid(get_userid(user))

def get_player(user):
    """
    Returns the Player Class object of the given user
    """

    return playerlib.getPlayer(get_userid(user))

def player_list(*filters):
    """
    Returns a list of players (as their Player Object) from the server
    based on given filters.
    """

    all_players = playerlib.getPlayerList('#all')
    if not filters:
        return all_players
    if len(filters) == 1:
        target = filters[0]
        if target == '#admins':
            return [i for i in all_players if admins.is_admin(i.steamid)]
        return playerlib.getPlayerList(target if target in FILTERS else '#all')
    return [i for f in filters for i in playerlib.getPlayerList(f) if f in FILTERS]


def userid_list(*filters):
    """
    Returns a list of user IDs from the server based on given filters
    """

    all_userid = playerlib.getUseridList('#all')
    if not filters:
        return all_userid
    if len(filters) == 1:
        target = filters[0]
        if target == '#admins':
            return [i for i in all_userid if admins.is_admin(i)]
        return playerlib.getUseridList(target if target in FILTERS else '#all')
    return [i for f in filters for i in playerlib.getUseridList(f) if f in FILTERS]


def change_team(userid, team_id):
    """
    Moves the player to the given team
    """

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
    """
    Emits a sound to the given userid
    """

    es.emitsound('player', userid, sound, volume, attenuation)


def import_module(module):
    """
    Imports modules from the sam folder
    """

    return es.import_addon('sam/' + module)


def delay_task(seconds, name, function, args=()):
    """
    Delays a task for the given number of seconds
    """

    gamethread.delayedname(seconds, 'sam_' + name, function, args)


def cancel_delay(name):
    """
    Cancels a delayed task
    """

    gamethread.cancelDelayed('sam_' + name)


def get_time(frmt, from_stamp=None):
    """
    Gets the current time in the given format

    Examples:
    %d/%m/%Y, %H:%M:%S = 06/12/2018, 09:55:22
    %d %B, %Y          = 12 June, 2018
    """

    return datetime.fromtimestamp(from_stamp if from_stamp
                                  else timestamp()).strftime(frmt)


def random(obj):
    """
    Returns a random item from the given object
    """

    return random.choice(obj)


def timestamp():
    """
    Returns the current timestamp
    """

    return time.time()


def percent_of(part, whole):
    """
    Returns the percentage of the given part of the whole
    """

    return 100 * part / whole if part else 0


def title(text):
    """
    Returns the given text with the first letter of each word capitalized
    """

    return text.title().replace('_', ' ') if text else 'None'

def format_text(text, remove_colors=False, remove_special=True, strip_text=True):
    """
    Formats the given text for usage in different contexts,
    such as in-game chat or menus.

    remove_colors: If True, removes all color names from the text.
                   If False, replaces color names with RGB codes.
    remove_special: If True, removes all special characters from the text.
    strip_text: If True, strips any leading or trailing spaces from the text.
    """

    # Remove colors or replace with RGB code
    for color, code in msg.colors.items():
        text = text.replace('#' + color, '' if remove_colors else '\x07' + code)

    # Remove special characters
    if remove_special:
        text = re.sub(r'\\[nrt]', '', text)
    # Strip spaces at the start and end
    if strip_text:
        text = text.lstrip().rstrip()
    return text


def read_file(file_path, default=None, default_file=None):
    """
    Reads the given file and returns a list of lines
    """
    
    if not os.path.isfile(file_path) and default_file:
        write_file(default_file, default)
    
    lines = []
    with open(file_path, 'r') as f:
        for line in f:
            line = line.rstrip('\n')
            if line.strip() and not line.strip().startswith('//'):
                lines.append(line)
    
    return lines


def write_file(file_path, lines):
    """
    Writes the given lines to the given file
    """

    with open(file_path, 'w') as f:
        f.write('\n'.join(lines))


def decache_player(userid):
    """
    Decaches the player from the various systems
    """

    # Decache the player from any ongoing sounds
    if userid in cache.sounds:
        del cache.sounds[userid]

    # Decache the player from any active menus
    if userid in menu_system.users_active_menu:
        del menu_system.users_active_menu[userid]
    if userid in menu_system.users_previous_menu:
        del menu_system.users_previous_menu[userid]
    if userid in menu_system.users_menu_history:
        del menu_system.users_menu_history[userid]

    # Decache the player from any active chat filters
    for filter_id in chat_filter.filters:
        chat_filter.remove_user(userid, filter_id)

def clear_cache_and_save_data():
    """
    Clear all system's cache and saves all systems data
    """

    # Clear Menu System cache
    menu_system.menus.clear()
    menu_system.users_active_menu.clear()
    menu_system.users_previous_menu.clear()
    menu_system.users_menu_history.clear()
    
    # Clear temporary cache
    cache.temp.clear()

    # Terminate all chat filters
    chat_filter._delete_all_filters()

    # Make necessary database saves
    addons_monitor.save_database()
    admins.save_database()
    settings.save_database()

# Game Events
def server_shutdown(ev):
    """
    Called whenever the server is shutting down
    """

    # Safely unload SAM on shutdown to make sure all data is saved properly
    es.server.cmd('es_unload sam')


def es_map_start(ev):
    """
    Called whenever a map loads
    """

    clear_cache_and_save_data()


def es_client_command(ev):
    """
    Called whenever a user uses a console command
    
    Used to know when the user makes a menu choice
    """

    if ev['command'] == 'menuselect':
        menu_system.process_user_choice(int(ev['userid']), int(ev['commandstring']))


def player_activate(ev):
    """
    Called the player connects to the server and enters the game
    """

    # Update player info
    players.update(ev['userid'])


def player_disconnect(ev):
    """
    Called whenever a player disconnects from the server
    """

    userid = int(ev['userid'])
    steamid = ev['networkid']

    # Decache player from the various systems
    decache_player(userid)

    # Update player info with last seen
    if steamid in players.data.keys():
        players.data[steamid]['last_seen'] = get_time('%m/%d/%Y at %H:%M:%S')


# Class Declaration
players = _PlayersProfileSystem()
