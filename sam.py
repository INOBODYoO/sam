#!/usr/bin/python
# -*- coding: utf-8 -*-

# Standard library imports
from __future__ import with_statement
from datetime import datetime

import os
import random
import re
import time

# EventScripts specific imports
import es
import cmdlib
import gamethread
import playerlib
import usermsg

# Plugin Info & Global Variables
plugin = es.AddonInfo()
plugin.name = 'S.A.M (Server Administration Menu) [Remastered]'
plugin.version = '0.2.0'
plugin.basename = 'sam'
plugin.author = 'NOBODY'
plugin.description = 'All-in-one tool featuring various modules for server management.'
plugin.url = 'https://github.com/INOBODYoO/sam'
plugin.developer_mode = 1


# Developer Mode Levels:
# 0 = All systems will run normally without any debug messages
#     and or debug like behaviors
# 1 = Python Exceptions, Systems errors, and other debug like messages
# 2 = Pages Setup Debug (Prints all page setups to console)
# 2.1 = Menus cache report (Prints all menus cache to console,
#       may impact plugin/server performance)
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
PLAYER_FILTERS = set(('#all', '#human', '#ct', '#t', '#alive', '#dead', '#spec', '#bot'))

print('[%s][SAM] * Initializing Core Module' % datetime.now().strftime('%H:%M:%S'))

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
    Class to dynamically assign attributes from a dictionary.
    """

    def __init__(self, dictionary, lookup_key=None):
        """
        Initializes the class with dynamic attributes from a dictionary.
        """
        if not isinstance(dictionary, dict):
            raise TypeError("Object must be a dictionary")

        # If a lookup_key is not provided, then update the class with the dictionary
        if not lookup_key:
            self.__dict__.update(dictionary)
            return


        converted = {}
        for key, value in dictionary.items():
            if isinstance(value, dict) and lookup_key in value:
                converted[key] = value[lookup_key]
            else:
                converted[key] = value

        self.__dict__.update(converted)


    def get(self, key, default=None):
        """
        Returns the value for key if key is in the dictionary, else default.
        """

        return self.__dict__.get(key, default)


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

    def load(self, database, bypass=False):
        """
        Loads a JSON database file
        """
        
        import simplejson

        if not bypass:
            database = path.databases + database + '.json'
        if os.path.isfile(database):
            with open(database, 'r') as f:
                return simplejson.load(f, object_hook=self.ascii_decoder)
        return {}

    @staticmethod
    def save(database, data, bypass=False):
        """
        Saves a JSON database file
        """
        
        if not bypass:
            database = path.databases + database + '.json'
        if not data:
            if os.path.isfile(database):
                os.remove(database)
            return
        try:
            import simplejson

            with open(database, 'w') as f:
                simplejson.dump(data, f, indent=4, sort_keys=True)
        except:
            debug(1, 'Error saving data to file %s' % database.split('\\')[:-1])


    def ascii_decoder(self, pairs):
        """
        Decodes Unicode keys to ASCII
        """

        if isinstance(pairs, list):
            return [(self.ascii_decoder(key), value) for key, value in pairs]
        elif isinstance(pairs, tuple):
            return tuple((self.ascii_decoder(key), value) for key, value in pairs)
        elif isinstance(pairs, dict):
            return dict((self.ascii_decoder(key), value) for key, value in pairs.items())
        elif isinstance(pairs, unicode):
            return str(pairs)
        else:
            return pairs

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
                    'The maximum allowed value is 50.',
                ],
                'current_value': 35,
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
        elif arg in self.settings:
            return self.settings[arg]

        # If the argument is one of the general settings, return the setting value
        elif arg in self.settings[self.general]:
            return self.settings[self.general][arg]['current_value']

        # If the argument is one of the addons, return the addon settings
        elif self.settings[self.modules]:
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
        for addon in database[m]:
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
        if module in self.settings[self.modules]:
            config = self.settings[self.modules][module]
            
            # Remove old settings
            for key in config:
                if key not in settings:
                    del config[key]
            
            # Update settings by adding new settings and updating descriptions
            for key, val in settings.items():
                if key not in config:
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
        settings descriptions and current values
        """

        # Get the given section's settings, or return if the section is invalid
        if section == self.general:
            settings = self.settings[self.general]
        elif section in self.settings[self.modules]:
            settings = self.settings[self.modules][section]
        else:
            msg.hud(
                userid,
                'Invalid settings section name: %s' % section,
                nametag='Settings System'
            )
            return

        titled = title(section)
        separator = '-' * 34

        # Add the settings help window disclaimer
        lines = [
            '// This window displays the descriptions and current values of each setting',
            '// and cannot be used to modify them. To modify these settings, use the menu',
            '// or manually update the settings file located at:\n ',
            path.settings,
            '',
            '// Settings For: %s Module/Addon' % section.upper(),
            ''
        ]

        # For each setting add its title, description, and current value
        for setting, data in settings.items():
            lines.extend(
                [
                    separator,
                    '[%s]' % setting.upper(),
                    separator,
                    'CURRENT VALUE: %s' % data['current_value'],
                    'DESCRIPTION:',
                    '\n'.join(data['description']),
                    ' '
                ]
            )

        # Display the help window
        msg.info(userid, titled, *lines)
        
    def _default_settings(self):
        """
        Returns the default general settings
        """
        
        return {
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
                    'The maximum allowed value is 50.',
                ],
                'current_value': 35,
            }
        }


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

        if filter_id in self.filters:
            f = self.filters[filter_id]
            if userid not in self._get_users(f.users):
                return
            f.users.remove(userid)
            if not f.users and f.delete_on_empty:
                self.delete(filter_id)
            user = menu_system.users.get(userid, False)
            if user and user['active_menu'] == filter_id:
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
                msg.hud(userid, 'Operation canceled!', nametag='Chat Filter System')
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
            elif u in PLAYER_FILTERS or u == '#admins':
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

        if menu_system.get_menu(filter_id):
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
            'coral': 'FF7F50', 't': 'FF3D3D', 'ct': '9BCDFF',
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
        elif isinstance(users, int) or users in PLAYER_FILTERS:
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

    def tell(self, users, message, prefix=True, nametag=False, log=False):
        """
        Chat message that can be sent to any player or group of players.
        The text can also be color coded
        e.g: #red{prefix} | #green{nametag} | #whiteHello World
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
        
        # Setup the nametag to be used in the message
        nametag = '#coral%s #gray| ' % (nametag) if nametag else ''

        # Merge the prefix, nametag, and message into one text
        text = '#default' + prefix + nametag + '#beige' + message

        # Check if the message is in the spam queue
        if self.is_spam(text) and settings('anti_spam_chat_messages'):
            return

        # Check if the message should be logged in the server console
        if log and ('#all' in users or '#human' in users):
            self.console(message, nametag)
        
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
    def console(text, nametag=None):
        """
        Prints a message to the server console with SAM's prefix, a "nametag" can be used
        to identify the system or addon from which the message is being sen 
        E.g. SAM | PLAYERS MANAGER | X was kicked from the server
        """

        print(
            format_text(
                '[%s][SAM] %s%s' % (get_time('%H:%M:%S'),
                nametag.upper() + ' | ' if nametag else '', text), True
            )
        )


class _AddonsMonitor:
    """
    Addons Monitor class
    """

    class Addon(str):
        def __init__(self, addon_basename):
            self.basename = addon_basename
            self.name = 'unregistered_addon'
            self.version = '0.0'
            self.description = []
            self.state = False
            self.locked = False
            self.home_page_option = False

        def __repr__(self):
            return "<Addon(name=%s, version=%s)>" % (self.name, self.version)

        def __str__(self):
            return self.__repr__()


    def __init__(self):
        
        # Initialize Addons dictionary and home page options list
        self.addons = {}
        self.home_page_options = []

        # Update installed Addons
        self._update_installed_addons(load_addons=False)

        # Load the Addons database
        database = databases.load('addons')

        # Update installed each Addon Class object with the database values
        for addon, data in database.items():
            # Ignore Addon if it's not installed
            if addon not in self.addons:
                continue

            for key, val in data.items():
                if isinstance(val, bool) and not key == 'home_page_option':
                    setattr(self.addons[addon], key, val)
    

    def get_addon(self, addon):
        """
        Returns an Addons Class object
        """

        return self.addons.get(addon)

    def addons_list(self):
        """
        Returns a list of all Addons as their class objects
        """

        return self.addons.values()

    def save_database(self):
        """
        Save Addons Monitor database
        """
            
        # Save the file, creating a dictionary where each addon holds a copy
        # of its class object dictionary
        databases.save(
            'addons',
            dict((addon, data.__dict__.copy()) for addon, data in self.addons.items())
        )

    @staticmethod
    def is_loaded(addon_basename):
        """
        Check if an Addon is loaded
        """

        return is_script_loaded('sam/addons/%s/%s' % (addon_basename, addon_basename))

    def import_addon(self, addon):
        """
        Import an Addon
        """

        if self.is_loaded(addon):
            return import_module('addons/' + addon)
    

    def _load_addon(self, addon_basename):
        """
        Load an Addon, regardless of its state
        """

        # Get the addon object
        addon = self.get_addon(addon_basename)

        # Check if the Addon is valid and if it's not loaded
        if addon and not self.is_loaded(addon.basename):
            
            # Load the Addon script
            es.load('sam/addons/' + addon.basename)
            
            # If the addon has a home page option, add it to the list
            if addon.home_page_option and addon.basename not in self.home_page_options:
                self.home_page_options.append(addon.basename)
                
            msg.console('   - Loaded %s' % addon.name)

    def _unload_addon(self, addon_basename):
        """
        Unloads an Addon, regardless of its state
        """

        # Get the addon object
        addon = self.get_addon(addon_basename)
        
        # Check if the Addon is valid and if it's loaded
        if addon and self.is_loaded(addon.basename):
            
            # Unload the Addon script
            es.unload('sam/addons/' + addon.basename)
            
            # If the addon has a home page option, remove it from the list
            if addon.home_page_option and addon.basename in self.home_page_options:
                self.home_page_options.remove(addon.basename)

            msg.console('   - Unloaded %s' % addon.name)

    def _enable_addon(self, addon_basename):
        """
        Enables an Addon, by changing its state and loading the script if not loaded
        """
        
        # Get the addon object
        addon = self.get_addon(addon_basename)
        
        if addon:
            # Change the addon state
            addon.state = True
            # Load the addon script
            self._load_addon(addon_basename)

    def _disable_addon(self, addon_basename):
        """
        Disables an Addon, by changing its state and unloading the script if loaded
        """
        
        # Get the addon object
        addon = self.get_addon(addon_basename)
        
        if addon:
            # Change the addon state
            addon.state = False
            # Unload the addon script
            self._unload_addon(addon_basename)
        
        
    def _update_installed_addons(self, load_addons=True):
        """
        Checks whether addons to be installed.
        Creates their Addon Class object, and loads the addon if necessary
        """
        
        # Get the list of installed Addons
        installed = self._get_installed_addons()
        
        for addon in installed:
            
            # Load the addon metadata
            metadata = databases.load('%s%s\\%s.json' % (path.addons, addon, addon), True)
            
            # Check if the metadata file is valid
            if not metadata:
                self._log('Missing or invalid metadata file for %s addon' % title(addon))
                return
            
            # If not existent, create the its Addon Class object and update its values
            # with the values from the metadata file as its defaults
            if addon not in self.addons:
                self.addons[addon] = self.Addon(addon)
                self.addons[addon].__dict__.update(metadata.copy())
            
            # Load the Addon if needed
            if load_addons and self.addons[addon].state:
                self._load_addon(addon)
      
    @staticmethod
    def _get_installed_addons():
        """
        Returns a list of all installed Addons in the sam/addons folder
        """

        return [i for i in os.listdir(path.addons) if os.path.isdir(path.addons + i)]
             
    @staticmethod   
    def _log(message):
        """
        Logs a system message
        """
        
        msg.console(message, 'Addons Monitor')


class _AdminsSystem:
    """
    Admins System

    This system is responsible for managing the server admins and groups.
    """

    def __init__(self):

        # Init admins and groups dictionaries
        self.admins = {}
        self.groups = {}

        # Default Admins permissions
        self.admins_permissions = [
            'addons_monitor',
            'admins_manager',
            'players_manager',
            'kick_players',
            'rcon_command',
            'settings_manager'
        ]

        # A list for addons to register their own permissions
        self.addons_permissions = []

    def __repr__(self):
        return str(type(self))

    def __str__(self):
        return self.__repr__()

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
        return user in self.admins

    def is_allowed(self, user, permission, notify=True):
        """
        Checks whether an Admin has permission to perform an action.
        """
        
        # Return True if no permission is required or in developer mode level 3
        if not permission or plugin.developer_mode == 3:
            return True

        admin = self.get_admin(user)
        if not admin:
            return False

        # Handle Super Admin case
        if admin.super_admin:
            return 3 if permission == 'ban_level' else True

        group = self.get_admin_group(admin.steamid)
        if permission == 'ban_level':
            return max(admin.ban_level, getattr(group, 'ban_level', admin.ban_level))

        # Consolidate permission checks for admin and group
        has_permission = any([
            admin.permissions.get(permission, False),
            admin.addons_permissions.get(permission, False),
            getattr(group, 'permissions', {}).get(permission, False),
            getattr(group, 'addons_permissions', {}).get(permission, False)
        ])

        # Notify if permission is lacking
        if not has_permission and notify:
            msg.hud(user, 'You do not have permission to %s!' % title(permission))

        return has_permission

    def is_super_admin(self, user):
        """
        Function to check whether an Admin is a Super Admin
        """

        # Get the Admin class object
        admin = self.get_admin(user)
    
        return admin.super_admin if admin else False

    def list(self, arg=None):
        """
        Get a specific list of admins or groups.

        - 'groups': Returns the groups dictionary.
        - 'super_admins': Return a list of super admins.
        - 'online': Return a list of online admins.
        - (default): Return a list of all admins.
        """
        
        if arg == 'groups':
            return self.groups.copy()

        # Copy the admins once, and use it for filtering based on the argument
        admins = list(self.admins.values())

        if arg == 'super_admins':
            return [admin for admin in admins if admin.super_admin]
        elif arg == 'online':
            return [admin for admin in admins if get_userid(admin.steamid)]

        return admins

    def compare_immunity(self, admin1, admin2):
        """
        Compare the immunity levels between two Admins and
        determine if Admin1 has higher immunity than Admin2.
        """

        # If Developer mode is level 3, return True regardless
        if plugin.developer_mode == 3:
            return True

        # Admin1 is most likely a menu user, therefore, get his steamid
        admin1_steamid = get_steamid(admin1)

        # Return True if Admin2 is not an actual Admin or is actually Admin1
        if not self.is_admin(admin2) or admin1_steamid == get_steamid(admin2):
            return True

        # Get both Admins objects
        admin1_obj = self.admins[admin1_steamid]
        admin2_obj = self.admins.get(get_steamid(admin2))

        # If admin2_obj is None, it means admin2 was not found in admins
        if admin2_obj is None:
            return True

        # Check if Admin2 is a Super Admin
        if admin2_obj.super_admin:
            msg.hud(admin1_obj, 'Action denied! %s is immune to you.' % admin2_obj.name)
            return False

        # Check if Admin1 is a Super Admin
        if admin1_obj.super_admin:
            return True

        # Function to get the immunity level of an Admin
        def get_immunity(admin):
            admin_imm = admin.immunity_level
            group_imm = self.groups.get(admin.group, 0).immunity_level
            return max(admin_imm, group_imm)

        # Compare the immunity levels between the two Admins
        result = get_immunity(admin1_obj) > get_immunity(admin2_obj)

        # Notify Admin1 if they don't have permission
        if not result:
            msg.hud(admin1_obj, 'Action denied! %s is immune to you.' % admin2_obj.name)
        return result

    def new_admin(self, player, super_admin=False):
        """
        Function to create a new Admin
        """

        # Create the Admin
        self.admins[player.steamid] = Admin(player, super_admin)

        # Save the database
        self.save_database()

        # Notify the Admin
        userid = get_userid(player.steamid)
        if userid:
            msg.hud(userid,
                    'You are now an Admin!',
                    'You may now start using !sam, to open the menu')

    def delete_admin(self, steamid):
        """
        Function to delete an Admin
        """

        # Check if the Admin exists
        if steamid not in self.admins:
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
        if group in self.groups:
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
        if group not in self.groups:
            return False

        # Delete the group
        del self.groups[group]

        # Set the group of all Admins in this group to None (or a specific default value)
        for admin in self.admins.values():
            if admin.group == group:
                admin.group = None

        # Save the database
        self.save_database()

    def get_group_members(self, group):
        """
        Retrieves the SteamIDs of members belonging to a specified Admin Group.
        """

        # Directly return the list of members belonging to the group
        return [admin.steamid for admin in self.admins.values() if admin.group == group]

    def get_admin_group(self, steamid):
        """
        Retrieves the group of an Admin by their SteamID.
        """

        # Attempt to retrieve the Admin object
        admin = self.get_admin(steamid)

        # Return the Admin's group object if the Admin exists
        return self.get_group(admin.group) if admin else None
    
    
    def get_admin(self, steamid):
        """
        Retrieves an Admin object by its SteamID. Converts numeric IDs to SteamID format,
        ensures SteamID is in uppercase, and returns None if the SteamID is invalid.
        """

        if isinstance(steamid, int):
            steamid = get_steamid(steamid)
        elif not is_valid_steamid(steamid):
            return None

        return self.admins.get(steamid.upper())
    
    def get_group(self, group_id):
        """
        Function to get an Admin Group object by its ID
        """

        return self.groups.get(group_id, False)


    def save_database(self):
        """
        Saves both Admins & Groups database at once
        """

        # Admins Database
        databases.save(
            'admins_database',
            dict((x, y.__dict__.copy()) for x, y in self.admins.items())
        )

        # Skip saving Groups Database if no groups exist
        if self.groups:
            databases.save(
                'groups_database',
                dict((x, y.__dict__.copy()) for x, y in self.groups.items())
            )


    def register_addon_permission(self, permission):
        """
        Registers a new permission for addons,
        ensuring it's added to the list of addon permissions and initializing this
        permission with a default value of False for all existing admins and groups.
        """

        # Check if the permission is already registered
        if permission not in self.addons_permissions:
            self.addons_permissions.append(permission)

        # Assign the permission to all Admins and Groups
        for admin in self.admins.values():
            admin.addons_permissions.setdefault(permission, False)

        for group in self.groups.values():
            group.addons_permissions.setdefault(permission, False)


    def _toggle_permission(self, target, permission):
        """
        Optimized toggle of an Admin/Group permission
        """

        # Toggle in target.permissions if permission exists in admins_permissions
        if permission in self.admins_permissions:
            current_state = target.permissions.get(permission, False)
            target.permissions[permission] = not current_state
        # Toggle in target.addons_permissions if permission exists in addons_permissions
        elif permission in self.addons_permissions:
            current_state = target.addons_permissions.get(permission, False)
            target.addons_permissions[permission] = not current_state
        # Remove the permission if it doesn't exist in either but is in target.permissions
        elif permission in target.permissions:
            del target.permissions[permission]


    def _initialize_database(self):
        """
        Initialize the Admins and Groups databases by converting dictionaries to class objects
        and ensuring permissions are up-to-date.
        """

        def update_permissions(target_permissions, current_permissions):
            """
            Update permissions to reflect the current state of permissions.
            """
    
            for permission in self.admins_permissions:
                target_permissions.setdefault(permission, False)
            for permission in list(target_permissions):
                if permission not in current_permissions:
                    del target_permissions[permission]

        # Load the admins and groups databases
        admins_db = databases.load('admins_database')
        groups_db = databases.load('groups_database')

        # Return early if both databases are empty
        if not admins_db and not groups_db:
            return

        # Convert the Admins database
        if admins_db:
            for steamid, data in admins_db.items():
                admin = Admin(profile_system.get_player(steamid))
                admin.__dict__.update(data)
                self.admins[steamid] = admin
                update_permissions(admin.permissions, self.admins_permissions)

        # Convert the Groups database
        if groups_db:
            for name, data in groups_db.items():
                group = Group(name)
                group.__dict__.update(data)
                self.groups[name] = group
                update_permissions(group.permissions, self.admins_permissions)

admins = _AdminsSystem()

class Admin(object):
    """
    Admin Class object
    """

    def __init__(self, player, super_admin=False):

        self.name = player.name
        self.steamid = player.steamid
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


class _MenuSystem:
    """
    Menu System to handle anything related to menus, whether it's caching,
    forced user choices, or processing menu options.
    """
    
    class SubMenu:
        """
        Class to save last active menu and user choice as the new submenu
        info to be carried away in the menu callback.
        """
        def __init__(self, a, b, c, d):
            self.menu_id = a
            self.object = b
            self.choice = c
            self.page = d
        
        def __repr__(self):
            """
            Returns the menu ID.
            """
            return self.menu_id
        
        def send(self, userid, rebuild=False, rebuild_arguments=None):
            """
            Sends back the last active menu, and page, to the user.
            """
            self.object.send(userid, self.page, rebuild, rebuild_arguments)
    
    def __init__(self):
        self.menus = {}
        self.users = {}
        
    def handle_choice(self, choice, user, force_close=False):
        """
        Handles the user's choice.
        Used mostly to force a user to make certain choices.
        """
        userid = get_userid(user)
        if not userid:
            self._log('Invalid user ID (%s), could not handle user choice.' % userid)
            return

        if not force_close:
            self._process_user_choice(userid, choice)
            return

        if userid in self.users:
            del self.users[userid]
            self._cancel_refresh(userid)
        es.cexec(userid, 'slot10')

        
    def send_menu(self, userid, menu_id, page=1, rebuild=False, rebuild_arguments=None):
        """
        Sends the given menu to the user.
        """

        menu = self.menus.get(menu_id)
        if menu:
            menu.send(userid, page, rebuild, rebuild_arguments)
            return
        self._log('Invalid Menu ID (%s), could not send menu to user.' % menu_id)

    
    def get_menu(self, menu):
        """
        Checks whether the given menu exists.
        """
        if isinstance(menu, str):
            return self.menus.get(menu, False)
        elif isinstance(menu, (Menu, self.SubMenu)):
            return self.menus.get(menu.menu_id, False)
        return False

    def _process_user_choice(self, userid, choice):
        """
        Processes the user menu choice by either executing a pre-defined function,
        sending the user to another page, or closing the menu.
        """

        # Cancel the user's page refresh timer
        self._cancel_refresh(userid)
        
        # Get the user cache
        user = self.users.get(userid, False)
        
        # Abort if the user is not valid or the menu does not exist
        if not user or not self.get_menu(user['active_menu']):
            return

        # Process the user cache changes;
        # - Remove the menu as the active menu
        # - Set this menu and page as the previous menu and page 
        # - Save the menu in the user history, with the page as its value
        active_menu = user['active_menu']
        user['active_menu'] = None
        user['previous_menu'] = active_menu
        user['previous_page'] = user['active_page']
        user['history'][active_menu] = user['active_page']
        
        # Get the menu object
        menu = self.menus[active_menu]

        # If the user chose to go to the next page
        if choice == 8 and user['active_page'] > 1:
            menu.send(userid, user['active_page'] - 1)
        # If the user chose to go to the previous page
        elif choice == 9 and user['active_page'] + 1 in menu.pages:
            menu.send(userid, user['active_page'] + 1)
        # If the user chose to close the menu or go back to the previous menu
        elif choice == 10 and menu.close_option:  
            self._handle_close_option(menu, user, userid)
        # If the user chose anything between 1 and 7
        elif choice <= len(menu.get_page_options(user['active_page'])):
            self._handle_valid_choice(menu, user, choice, userid)
        else:
            menu.send(userid, user['active_page'])
            
    def _handle_close_option(self, menu, user, userid):
        """
        Handle the close option (choice 10).
        """

        submenu = self.get_menu(menu.submenu)
        if submenu:
            if submenu.menu_id == 'home_page':
                submenu.send(userid, rebuild=True, rebuild_arguments=(userid,))
            elif submenu.menu_id in user['history']:
                submenu.send(userid, user['history'][submenu.menu_id])
            else:
                self.menus[submenu.menu_id].send(userid, menu.submenu_page)
        else:
            del self.users[userid]

    def _handle_valid_choice(self, menu, user, choice, userid):
        """
        Handle a valid user choice (choices between 1 and 7).
        """

        # Check if the option is blocked
        if choice in menu.blocked_options:
            if menu.locked_option_message:
                msg.hud(userid, menu.locked_option_message)
            menu.send(userid, user['active_page'])
            return

        # Check if there isn't a callback defined
        if not menu.callback:
            menu.send(userid, user['active_page'])
            return

        # Call the menu callback
        menu.callback(
            userid,
            menu.get_option_info(choice, user['active_page'])['object'],
            self.SubMenu(menu.menu_id, menu, choice, user['active_page'])
        )
    
    def _refresh_menu(self, user):
        """
        Refreshes the user's active menu by re-sending the page,
        or rebuilding it if necessary.
        """

        userid = get_userid(user)
        user = self.users.get(userid, False)
        menu = self.menus.get(user['active_menu'], False) if user else False

        if menu:
            menu.send(userid, user['active_page'], rebuild=menu.rebuild_on_refresh)

    @staticmethod
    def _cancel_refresh(userid):
        """
        Cancel the user menu refresh
        """

        userid = get_userid(userid)
        if userid:
            cancel_delay('menu_refresh_%s' % userid)
            
    @staticmethod
    def _log(message):
        """
        Logs a system message
        """
        
        msg.console(message, 'Menu System')


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
        self.timeout = 0
        self.display = None
        self.blocked_options = []
        self.build_function = None
        self.build_arguments_list = []
        self.rebuild_on_refresh = False
        self.locked_option_message = 'This option is currently blocked!'
        length = int(settings('menus_separator_line_length'))
        self.separator_line = '-' * length if length <= 50 else 30

    def title(self, text):
        """
        Adds/Changes the title of the menu.
        """
        self.title_text = '\n :: ' + text

    def description(self, *lines):
        """
        Adds/Changes the description of the menu.
        Note: Multiple lines can be given as a list or tuple.
        """
        self.description_text = '\n'.join(lines)

    def footer(self, *lines):
        """
        Adds/Changes the footer of the menu.
        Note: Multiple lines can be given as a list or tuple.
        """
        self.footer_text = self.separator_line + '\n' + '\n'.join(lines)

    def add_line(self, *lines):
        """
        Adds a new line to the menu.
        Note: Multiple lines can be given as a list or tuple.
        """
        self.pages[self._current_page()].extend([str(line) for line in lines])

    def add_option(self, obj, text, blocked=False):
        """
        Adds a new option to the menu.
        """
        page = self._current_page()
        self.pages[page].append({
            'object': obj,
            'text': text,
            'blocked': blocked,
            'choice': len(self.pages[page]) + 1,
            'page': page
        })

    def add_options(self, options_list):
        """
        Adds multiple options to the menu.
        Note: Each option must be a tuple with the following format:
              (object, text, blocked=False)
        """

        for index, item in enumerate(options_list):
            if isinstance(item, (list, tuple)):
                self.add_option(*item)
            else:
                self.add_option(index, item)
                

    def get_option_info(self, obj, page=None):
        """
        Returns the option data of the given object.
        """
        def find_option_in_page(_obj, _page):
            """
            Searches for the option in the specified page.
            """
            options = self.get_page_options(_page)
            if isinstance(_obj, int):
                try:
                    return options[_obj - 1]
                except IndexError:
                    return None

            for option in options:
                if option['object'] == _obj:
                    return option
            return None

        if page:
            return find_option_in_page(obj, page)

        for pg in self.pages:
            option = find_option_in_page(obj, pg)
            if option:
                return option
        return None

    def get_page_options(self, page=None):
        """
        Returns the list of all the page's options.
        """
        if not page:
            page = self._current_page()
        return [_page for _page in self.pages[page] if isinstance(_page, dict)]

    def separator(self):
        """
        Adds a separator line to the menu.
        """
        self.add_line(self.separator_line)

    def next_page(self):
        """
        Adds a new page to the menu.
        """
        self.pages[max(self.pages) + 1] = []

    def construct_players_profile_list(self, status=None,
                                       handle_key=None, condition_function=None):
        """
        Constructs a list of player profiles and adds them to the menu.
        """
        def add_players_to_menu(players):
            has_players = False
            for player in sorted(players, key=lambda p: p.name):
                if condition_function and not condition_function(player):
                    continue
                option = (handle_key, player) if handle_key else player
                self.add_option(option, player.name)
                has_players = True
            if not has_players:
                self.add_line('* No players available', ' ')

        def process_status_group(status_group):
            self.add_line('[%s Players]' % status_group.title())
            players = profile_system.list_players(status_group)
            add_players_to_menu(players)
            
        if status in ('online', 'offline'):
            players = profile_system.list_players(status)
            add_players_to_menu(players)
        else:
            process_status_group('online')
            self.next_page()
            process_status_group('offline')


    def send_option(self, userid, option, page=None):
        """
        Sends the given option to the given user.
        """

        option = self.get_option_info(option, page)
        self.send(userid, option['page'])
        menu_system.handle_choice(option['option_number'], userid)


    def send(self, target, page=1, rebuild=False, rebuild_arguments=None):
        """
        Sends the menu to the user/users.
        """
        
        # Check if there's a valid target
        if not target:
            return  # Exit if no target is specified

        # Validate the menu page, default to page 1 if specified page is not valid
        page = page if page in self.pages else 1

        # Rebuild the menu if necessary,
        # based on the 'rebuild' flag and if a build function is provided
        if rebuild and self.build_function:
            self._rebuild_menu(rebuild_arguments)
        else:
            # Otherwise, build the page display
            self._build_page_display(page)
        
            # If the display is not valid then abort the operation
            if not self.display:
                return

        # Determine the target type and send the menu accordingly
        if isinstance(target, (tuple, list, set)):
            # If the target is a collection of users, iterate and send the menu to each
            for userid in target:
                self._process_sending_page_to_user(userid, page)
        elif target in PLAYER_FILTERS:
            # If the target matches a predefined player filter,
            # resolve to user IDs and send
            for userid in userid_list(target):
                self._process_sending_page_to_user(userid, page)
        else:
            # If the target is a single user, directly send the menu to them
            self._process_sending_page_to_user(target, page)

    def _rebuild_menu(self, rebuild_arguments=None):
        """
        Rebuilds the menu by calling its build function with either
        new arguments or the original ones.
        """

        # Choose the appropriate arguments for rebuilding the menu
        arguments = rebuild_arguments if rebuild_arguments else self.build_arguments_list

        # Call the build function with the selected arguments
        self.build_function(*arguments)

        # Update the current menu instance with attributes from the newly rebuilt menu
        # This ensures the current menu reflects any changes made during the rebuild
        updated_menu = menu_system.menus[self.menu_id]
        self.__dict__.update(updated_menu.__dict__.copy())


    def _process_sending_page_to_user(self, userid, page):
        """
        Processes sending the page to each user individually.
        """

        # Validate and get the actual userid
        userid = get_userid(userid)
        if not userid:
            return  # Exit if userid is not valid
        
        # Cancel any existing page refresh timer for the user
        menu_system._cancel_refresh(userid)

        # Initialize or retrieve the user's menu cache
        user_cache = menu_system.users.setdefault(userid, {
            'active_menu': None,
            'active_page': 1,
            'previous_menu': None,
            'previous_page': 1,
            'history': {},
        })

        # Update the user's active menu and page information
        user_cache.update({'active_menu': self.menu_id, 'active_page': page})
        
        # Prepare and display the menu page to the user
        formatted_display = format_text(
            self.display.encode('utf-8'),
            remove_colors=True,
            remove_special=True,
            strip_text=False
        )
        es.showMenu(self.timeout, userid, formatted_display)

        # Schedule a menu refresh if the menu has no timeout
        if not self.timeout:
            delay_task(1, 'menu_refresh_%s' % userid, menu_system._refresh_menu, userid)


    def _build_page_display(self, page=1):
        """
        Builds the given page display, including headers, titles, descriptions, options,
        and footers, while also handling pagination and special options like 'Previous Page',
        'Next Page', and 'Close Menu'.
        """
        
        # Initialize the display list
        display = []

        # Page Header
        if self.header_text:
            header_line = 'SAM v%s' % plugin.version
            clock = ''
            if settings('enable_menus_clock'):
                clock = get_time('%H:%M')
                space = max(len(self.separator_line) - len(header_line) - len(clock), 0)
                clock = '%s%s' % (' ' * space, clock)
            display.append('%s%s\n \n' % (header_line, clock))

        # Page Title
        if self.title_text:
            title = self.title_text
            if self.pages_counter and len(self.pages) > 1:
                title += '   (%d/%d)' % (page, len(self.pages))
            display.append(title)
            display.append(self.separator_line)

        # Page Description
        if self.description_text:
            display.extend([self.description_text, self.separator_line])

        # Page Lines and Options
        self.blocked_options = []
        option = 0
        for line in self.pages[page]:
            if isinstance(line, str):
                display.append(line)
            else:
                option += 1
                blocked = '' if line['blocked'] else '->'
                if line['blocked']:
                    self.blocked_options.append(option)
                display.append('%s%d. %s' % (blocked, option, line['text']))

        # Page Footer
        if self.footer_text:
            display.append(self.footer_text)
        if self.close_option:
            display.append(self.separator_line)

        # Navigation Options
        if page > 1:
            display.append('->8. Previous Page')
        if page < len(self.pages):
            display.append('->9. Next Page')
        if self.close_option:
            close_text = 'Previous Menu' if self.submenu else 'Close Menu'
            display.append('0. %s' % close_text)

        # Finalize Display
        if display:
            self.display = '\n'.join(display)
            menu_system.menus[self.menu_id] = self

    def _current_page(self):
        """
        Returns the current page being edited. If the current page is full, it initializes
        and returns the next page.
        """
        # Find the highest numbered page
        page = max(self.pages)
        
        # Check if the current page is full
        if len(self.get_page_options(page)) >= self.max_lines:
            # Move to the next page
            page += 1
            # Initialize the next page if it doesn't exist
            self.pages.setdefault(page, [])
        
        return page


class _ProfileSystem:
    """
    System to gather various useful information about the players who play on the server
    """

    class PlayerProfile:

        def __init__(self):

            self.name = 'unregistered'
            self.steamid = 'unregistered'
            self.seen_since = get_time('%d/%m/%Y')
            self.last_seen = get_time('%d/%m/%Y - %H:%M')
            self.last_seen_timestamp = time.time()
            self.kick_history = []
            self.ban_history = []
            self.mute_history = []
            self.reports = []

        def is_online(self):
            """
            Checks whether the player is online or not
            """

            return self.steamid in [player.steamid for player in player_list('#all')]

    def __init__(self):

        # Initialize the players database
        self.database = databases.load('players_profile_database')

        # Convert each player data into a PlayerProfile object
        for steamid, data in self.database.items():
            profile = self.PlayerProfile()
            profile.__dict__.update(data.copy())
            self.database[steamid] = profile

        # Clear inactive players
        self.clear_inactive_players()

        # Update online players
        for userid in userid_list():
            self.update_player(userid)

    def is_registered(self, steamid):
        """
        Checks whether the given user is registered in the database
        """
        
        # Make sure to get a valid steamid
        if isinstance(steamid, int):
            steamid = get_steamid(steamid)

        return steamid in self.database
    
    def register_player(self, userid):
        """
        Registers the given user in the database

        Notes:
        - This function is called automatically when a user joins the server.
        - Registering a player should only happen when the player is online, therefore
          the user's userid is required.
        """

        if self.is_registered(userid):
            return

        # Create a new PlayerProfile object
        profile = self.PlayerProfile()
        profile.name = es.getplayername(userid)
        profile.steamid = get_steamid(userid)

        # Add the new PlayerProfile object to the database
        self.database[profile.steamid] = profile

    def update_player(self, userid):
        """
        Updates the given player basic info, like name and last seen date
        """

        player = get_player(userid)

        # Make sure the player is registered
        if not self.is_registered(player.steamid):
            self.register_player(userid)

        # Update the basic info
        info = self.database.get(player.steamid, False)
        info.name = player.name
        info.last_seen = get_time('%d/%m/%Y')
        info.last_seen_timestamp = time.time()

    def get_player(self, steamid):
        """
        Returns the given user's PlayerProfile object as DynamicAttributes
        """

        if isinstance(steamid, int):
            steamid = get_steamid(steamid)

        player = self.database.get(steamid, False)

        # Check if the player is registered
        if not player:
            return False

        return player
    
    def list_players(self, status=None):
        """
        Returns a list of registered players, if status is 'online' than only players
        that are only, if 'offline' then only players that are offline.
        """

        # If a status is given, return a list of online or offline players
        if status in ('online', 'offline'):
            
            # Get a list of steamids of all online players
            online = [player.steamid for player in player_list('#human')]

            # Return a list of online players
            if status == 'online':
                return [self.get_player(steamid) for steamid in online]
            
            # Return a list of offline players
            return [player for player in self.database.values()
                    if player.steamid not in online]

        # Otherwise, return a list of all players
        return self.database.values()

    def save_database(self):
        """
        Saves the players database
        """

        # Create a new dictionary to store the database converting the PlayerProfile
        # objects into dictionaries
        database = {}
        for steamid, profile in self.database.items():
            database[steamid] = profile.__dict__.copy()

        databases.save('players_profile_database', database)

    def clear_inactive_players(self):
        """
        Clears the database from inactive players who haven't been seen for three months
        """

        # Get the current time
        now = time.time()

        # Iterate through the database
        for steamid, profile in self.database.items():
            # If the player has not been seen for three months, then delete it
            if now - profile.last_seen_timestamp >= 7776000:
                del self.database[steamid]


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
        if module == 'addons':
            module += '_monitor'
        msg.console(' - Loaded %s Module' % title(module))

    # Make plugin version public
    es.setinfo('sam_version', plugin.version)
    es.makepublic('sam_version')
    msg.tell('#all', 'Loaded', prefix='#redSAM', nametag='#turquoise' + plugin.version)


def unload():

    # Close active menus from users
    for userid in menu_system.users.keys():
        menu_system.handle_choice(10, userid, True)
        msg.hud(userid, 'Your page was closed because SAM is unloading.')

    # Clear cache and save data
    clear_cache_and_save_data()

    # Delete core module commands
    cmds.delete('sam')
    cmds.delete('menu')
    cmds.delete('rcon')
    cmds.delete('admins')

    # Unload main modules
    msg.console('* Unloading Main Modules:')
    for module in MODULES:
        es.unload('sam/' + module)
        msg.console(' - Unloaded %s Module' % title(module))
    msg.console('* Unloaded Core Module')

    msg.tell('#all', 'Unloaded', prefix='#redSAM', nametag='#turquoise' + plugin.version)


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
    menu.build_function = home_page

    # Add main modules options
    for module in MODULES:
        if module == 'addons':
            menu.add_option(module, 'Addons Monitor')
            continue
        menu.add_option(module, title(module))

    # Get the list of Addons with a home page option
    home_page_addons = addons_monitor.home_page_options

    # Add Addons options
    if home_page_addons:
        menu.separator()
        menu.add_line('  :: Addons')
        menu.separator()

        for addon in home_page_addons:
            # Get the Addon object
            addon = addons_monitor.get_addon(addon)
            # Check if the Addon is enabled
            if addon and addon.state:
                menu.add_option(addon.basename, addon.name)
                continue
            # Otherwise, remove the Addon from the list
            home_page_addons.remove(addon.basename)

    menu.send(userid)


def home_page_HANDLE(userid, choice, submenu):
    
    # Check if the choice is a main module
    if choice in MODULES:
        import_module(choice).module_menu(userid)
        return
    # Otherwise, check if the choice is an Addon
    elif choice in addons_monitor.home_page_options:
        addons_monitor.import_addon(choice).addon_menu(userid)
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

    def tell(message):
        msg.tell(userid, message)

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
        tell('#specSyntax Example:')
        tell('#salmon!rcon <command/variable> {arguments/value}')
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
            tell('No arguments given!')
            return

        # Set the server variable to the given arguments
        es.ServerVar(command).set(arguments)
        tell('#specRCON: Set #salmon%s #specto #tomato%s' % (command, arguments))
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
        tell('#specRCON: Executed #salmon%s #tomato%s' % (command, arguments or ''))
        return

    # Invalid command or variable
    tell('#salmon\'%s\' #specis not a command or server variable.' % command)


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
    menu.title('Admins Online (%s/%s)' % (len(online_admins), len(admins.list())))

    # Initialize lists for Super Admins and regular Admins
    super_admins_list, regular_admins_list = [], []

    # Loop through each online admin and add them to the appropriate list
    for admin in online_admins:
        admin_name = admin.name
        if admin.super_admin:
            super_admins_list.append('[SA] ' + admin_name)
        elif admin.group:
            group_name = admins.get_group(admin.group).name
            regular_admins_list.append('%s (%s)' % (admin_name, group_name))
        else:
            regular_admins_list.append(admin_name)

    # Sort the lists alphabetically
    super_admins_list.sort()
    regular_admins_list.sort()

    # Add Super Admins to the menu
    if super_admins_list:
        menu.add_options(super_admins_list)

    # Add regular Admins to the menu
    if regular_admins_list:
        menu.add_options(regular_admins_list)

    # Send the menu to the user
    menu.footer('[SA] = Super Admin')
    menu.send(userid)


# Core Functions
def get_userid(target):
    """
    Returns the userid of the given target
    """

    # Use es.getuserid() for a faster result, and return it if valid
    userid = es.getuserid(target)
    if userid:
        return userid

    # If the target is not a string, then its just an invalid userid
    if not isinstance(target, str):
        return None

    is_steamid_valid = is_valid_steamid(target)
    target_string = target.lower()

    for player in player_list('#all'):

        # Check if target is a valid SteamID
        if is_steamid_valid and player.steamid == target:
            return player.userid
        
        # Otherwise check if target is a valid name
        elif player.name == target or target_string in player.name.lower():
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

def _player_list(list_type, filters):
    """
    Returns a list of players of a specified type
    """
    
    # If no filters are given, return all players
    if not filters:
        return list_type('#all')

    # Create a set to store the filtered players
    filtered_players = set()

    # Loop through each given filter
    for filter_name in filters:
        # If the filter is #admins, return a list of all admins
        if filter_name == '#admins':
            filtered_players.update(i for i in list_type('#human') if admins.is_admin(i))
        # If the filter is a valid player filter, add them to the list
        elif filter_name in PLAYER_FILTERS:
            filtered_players.update(list_type(filter_name))

    return list(filtered_players)
    

def player_list(*filters):
    """
    Returns a list of players (as their Player Object) from the server
    based on given filters.
    """
    
    return _player_list(playerlib.getPlayerList, filters)

def userid_list(*filters):
    """
    Returns a list of user IDs from the server based on given filters.
    If no filters are provided, returns all user IDs.
    """
    return _player_list(playerlib.getUseridList, filters)


def is_valid_steamid(string):
    """
    This function checks if a given string is a valid SteamID or SteamID3.
    """

    # SteamID format: STEAM_X:Y:Z
    steamid_pattern = r"^STEAM_[0-5]:[01]:\d+$"

    # SteamID3 format: [U:1:Z]
    steamid3_pattern = r"^\[U:1:\d+\]$"

    return bool(re.match(steamid_pattern, string) or re.match(steamid3_pattern, string))


def change_team(userid, new_team):
    """
    Moves the player to the given team
    """

    new_team = {'spec': 1, 'terro': 2, 'ct': 3}.get(new_team, new_team)

    es.changeteam(userid, 1)
    if new_team == 2:
        es.changeteam(userid, 2)
        es.setplayerprop(userid, 'CCSPlayer.m_iClass', random.randint(1, 4))
        msg.vgui_panel(userid, 'class_ter', False, {})
    elif new_team == 3:
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

def get_loaded_scripts():
    """
    Returns a tuple of EventScipts loaded scripts
    """
    
    return tuple(i.__name__.replace('.', '/') for i in es.addons.getAddonList())

def is_script_loaded(script_path):
    """
    Checks whether the given script is loaded
    
    Note: This is an alternative to using es.exists('script', script_path),
          as es.exists() is not working.
    """
    
    return script_path in get_loaded_scripts()

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


def timestamp():
    """
    Returns the current timestamp
    """

    return time.time()

def get_time(format_string, time_stamp=None):
    """
    Gets the current time or a specific time in the given format.

    Examples:
    %d/%m/%Y, %H:%M:%S -> 06/12/2018, 09:55:22
    %d %B, %Y          -> 12 June, 2018
    """
    
    
    if time_stamp is None:
        time_stamp = timestamp()
    return datetime.fromtimestamp(time_stamp).strftime(format_string)


def percent_of(part, whole):
    """
    Returns the percentage of part in whole
    """

    return 100 * part / whole if whole else 0


def title(text):
    """
    Replaces underscores with spaces and capitalizes the first letter of each word
    """

    return text.replace('_', ' ').title() if text else 'None'

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


def write_file(file_path, lines):
    """
    Writes the given lines to the given file
    """
    with open(file_path, 'w') as f:
        f.write('\n'.join(lines))


def read_file(file_path, default_content=None, default_file=None):
    """
    Reads the given file and returns a list of lines
    """
    if not os.path.isfile(file_path) and default_file:
        write_file(default_file, default_content or [])
    
    with open(file_path, 'r') as f:
        return [line.rstrip('\n') for line in f
                if line.strip() and not line.strip().startswith('//')]


def decache_player(userid):
    """
    Decaches the player from the various systems
    """

    # Decache the player from any ongoing sounds
    if userid in cache.sounds:
        del cache.sounds[userid]

    # Decache the player from any active menus
    if userid in menu_system.users:
        menu_system._cancel_refresh(userid)
        del menu_system.users[userid]

    # Decache the player from any active chat filters
    for filter_id in chat_filter.filters:
        chat_filter.remove_user(userid, filter_id)

def clear_cache_and_save_data():
    """
    Clear all system's cache and saves all systems data
    """

    # Terminate all chat filters
    chat_filter._delete_all_filters()

    # Clear Menu System cache
    menu_system.menus.clear()
    menu_system.users.clear()
    
    # Clear temporary cache
    cache.temp.clear()

    # Make necessary database saves
    addons_monitor.save_database()
    admins.save_database()
    settings.save_database()
    profile_system.save_database()

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

    # Check for newly installed Addons
    addons_monitor._update_installed_addons()

    # Clear cache and save data for all systems
    clear_cache_and_save_data()


def es_client_command(ev):
    """
    Called whenever a user uses a console command
    
    Used to know when the user makes a menu choice
    """

    if ev['command'] == 'menuselect':
        menu_system._process_user_choice(int(ev['userid']), int(ev['commandstring']))


def player_activate(ev):
    """
    Called the player connects to the server and enters the game
    """

    userid = int(ev['userid'])

    # Update the player's profile
    profile_system.update_player(userid)


def player_disconnect(ev):
    """
    Called whenever a player disconnects from the server
    """

    userid = int(ev['userid'])
    steamid = ev['networkid']

    # Update the player's profile
    player = profile_system.get_player(steamid)
    player.last_seen = get_time('%d/%m/%Y - %H:%M')
    player.last_seen_timestamp = time.time()
    player.name = ev['name']

    # Decache player from the various systems
    decache_player(userid)

def player_changename(ev):
    """
    Called whenever a player changes their name
    """

    userid = int(ev['userid'])

    # Update the player's profile
    profile_system.update_player(userid)

# Declare classes
msg = _MessageSystem()
menu_system = _MenuSystem()
profile_system = _ProfileSystem()
addons_monitor = _AddonsMonitor()