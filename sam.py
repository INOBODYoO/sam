from __future__ import with_statement
from datetime import datetime
import simplejson as json
import random as rdm
import time
import os
import es
import cmdlib
import usermsg
import playerlib
import gamethread
import psyco
psyco.full()

# Script Info
plugin = es.AddonInfo()
plugin.name           = 'S.A.M (Server Administration Menu) [Remastered]'
plugin.version        = '1.0-Alpha'
plugin.basename       = 'sam'
plugin.author         = 'NOBODY'
plugin.description    = 'All-In-One players, addons & server administration tool'
plugin.url            = 'https://github.com/INOBODYoO/sam'
plugin.developer_mode = 1

""" Developer Modes Levels:
    1 = Python Exceptions / eventscripts_debug set to 0
    2 = Pages Setup Debug
    3 = GodMode (Anyone can access anything in the menu even if not a Super or Regular Admin)
    4 = Prints all settings updates to console """
def debug(lvl, *msg):
    if lvl == plugin.developer_mode:
        for line in msg:
            print('[SAM][DEBUG] %s' % line)
# Turn off ES debug completely (if SAM debug is)
es.server.cmd('eventscripts_debug %s' % '0' if bool(plugin.developer_mode) else '-1')

# Global Variables
MODULES = ('players_manager', 'admins_manager', 'addons_monitor', 'settings')
FILTERS = ('#all', '#human', '#ct', '#t', '#alive', '#dead', '#spec', '#bot')
HOME_PAGE_ADDONS = []

# Core Module Systems
print('[SAM]   - Initializing Core Systems')

class _Cache:
    def __init__(self):
        self.pages = {}
        self.pages_users = {}
        self.sounds = {}
cache = _Cache()

class _Path:
    def __init__(self):
        self.core = es.getAddonPath('sam')
        self.sounds = 'cstrike/sound/sam_sounds'
        self.addons = self.core + '/addons/'
        self.settings = self.core + '/required/settings.json'
        self.databases = self.core + '/required/databases/'
        self.info_window_file = self.core + '/required/info_window (ignore this file).txt'
path = _Path()

class _database_system:
    # Create directories
    if not os.path.exists(path.databases):
        os.makedirs(path.databases)
    if not os.path.exists(path.databases + 'addons/'):
        os.makedirs(path.databases + 'addons/')

    def load(self, file, bypass=False):
        if not bypass:
            file = path.databases + file + '.json'
        if os.path.isfile(file):
            with open(file, 'r') as f:
                return json.load(f)
        return {}

    def save(self, file, data, bypass=False):
        if not bypass:
            file = path.databases + file + '.json'
        if not bool(data) and os.path.isfile(file):
            os.remove(file)
            return
        try:
            with open(file, 'w') as f:
                json.dump(data, f, indent=4, sort_keys=True)
        except AttributeError:
            return
databases = _database_system()

class _settings_system:

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
                    'desc': ['Enables !rcon command. (Requires "Rcon Command" permission)',
                             'Allow Admins to execute almost any kind of server',
                             'commands/variables through the game chat'],
                    'default': True,
                },
                'enable_!admins_command': {
                    'desc': ['Opens a page with a list of all Admins currently online'],
                    'default': True,
                },
                'enable_pages_clock': {
                    'desc': ['Displays a clock in the top righ corner of all pages.',
                             '(Local time, which is the time from where the server is hosted)'],
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
        return str(self.config)

    def __str__(self):
        return self.__repr__()

    def __call__(self, arg):
        data = self._load()
        class config_class(object):
            def __init__(self, obj):
                self.__dict__.update(obj.copy())
            def __getattr__(self, attr):
                return self.__dict__[attr]
        if arg in data[self.gen].keys():
            return data[self.gen][arg]
        elif arg in data[self.add].keys():
            return config_class(data[self.add][arg])
        return config_class(data[self.gen])

    def _load(self):
        data = databases.load(path.settings, True)
        if not data:
            data['Addons Settings'] = {}
            data[self.gen] = dict([(k, v['default']) for k, v in self.default[self.gen].items()])
        dft = self.default[self.gen]
        cfg = data[self.gen]
        if cfg == dft:
            return data
        for cmd in dft.keys():
            if cmd not in cfg.keys():
                cfg[cmd] = dft[cmd]['default']
        return data

    def _save(self, data):
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
        obj  = None
        if key == self.gen:
            data = data[self.gen].copy()
            obj = self.default[key].copy()
        elif key in self.default[self.add].keys():
            data = data[self.add][key].copy()
            obj = self.default[self.add][key].copy()
        else:
            msg.hud(uid, 'Error: could not retrieve these settings information.')
            return
        lines = ['This window is for informational purposes only and content cant be changed.',
                 'To modify these settings and more you need to access the Settings file under:',
                 'cstrike/addons/eventscripts/sam/required/settings.json\n',
                 'Toggle-able options can be changed from the menu itself, other settings of',
                 'digit or string (text) type values, can only be changed from the settings file',
                 'mentioned above, however changes from the file happen in real-time, meaning',
                 'that server-restarts or SAM reloads ARE NOT REQUIRED for changes to take effect',
                 '\n%s' % (90 * '-')]
        for k, v in obj.items():
            lines.extend(('[ %s ]' % title(k),
                          '- Description:\n%s' % '\n'.join(v['desc']),
                          '- Default Value: %s' % v['default'],
                          '- Current Value: %s\n' % data[k]))
        msg.info(uid, key if key == self.gen else title(key) + ' | Settings Help Page', *lines)

settings = _settings_system()

class _ChatFilters:

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
        try: es.addons.unregisterSayFilter(block)
        except ValueError: pass

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

    def _remove_all(self):
        for k, v in self.filters.items():
            try: es.addons.unregisterSayFilter(v.block)
            except ValueError: pass
        self.filters.clear()
chat_filters = _ChatFilters()

class _messages_system:
    """ System responsible for plugin's messaging types """

    def __init__(self):
        self.spam_queue = []
        self.chat_colors = {'blue': '71ACDF',
                            'green': '5cb85c',
                            'cyan': '5bc0de',
                            'orange': 'f0ad4e',
                            'red': 'EF625D',
                            'black': '292b2c',
                            'white': 'FFFFFF',
                            'pink':'ffc0cb',
                            'gray': 'a9a9a9',
                            'purple': '931CE2',
                            'yellow': 'ffff00',
                            'cyan': '00ffff',
                            't':'ff3d3d',
                            'ct': '9bcdff',
                            'spec':'cdcdcd',
                            'default':'ffb300'}

    def _compile(self, text, remove=False, special=True):
        """ Compiles the given text making 3 essential changes:
            - Replaces color tags (e.g #blue) with color codes for colorful chat messages
            - Removes special characters like Newline (e.g \\n) from the text
            - Strips white spaces from the text

            * If the remove argument is true then removes the color tags
            instead of replacing them, this is so if the text is sent to console
            or hudhints the text appears clean without the tags.

            * If the special argument is False then special characters wont be removed"""
        if remove:
            for color in self.chat_colors.keys():
                text = text.replace('#' + color, '')
        else:
            for color, code in self.chat_colors.items():
                text = text.replace('#' + color, '\x07' + code)
        if special:
            for i in ('\\n','\\r','\\t'):
                text = text.replace(i, '')
        return text.strip()

    def _sort_users(self, users):
        if isinstance(users, int) or users in FILTERS:
            return users
        elif users == '#admins':
            return player_list('#admins')
        new = []
        for i in users:
            if i == '#admins':
                for i in player_list('#admins'):
                    if int(i) not in new:
                        new.append(int(i))
            elif i in FILTERS:
                for u in playerlib.getUseridList(i):
                    if int(u) not in new:
                        new.append(int(u))
            elif es.exists('userid', int(i)) and int(i) not in new:
                new.append(int(i))
        return new

    def _in_queue(self, text):
        text_hash = hash(text)
        if text_hash in self.spam_queue:
            return True
        self.spam_queue.append(text_hash)
        delay_task(10, 'message_spam_queue_%s' % text_hash, self.spam_queue.remove, (text_hash))
        return False

    def tell(self, users, text, prefix=True, tag=False, log=False, queue=True):
        """ Chat message that can be sent to any player or group of players
            The text can be color coded

            e.g: #red{prefix} | #green{tag} | #whiteHello World """

        prefix = '#default%s #gray| ' % settings('chat_prefix') if prefix else '#default'
        tag    = '#green%s #gray| ' % tag if tag else ''
        text2   = '%s%s#white%s' % (prefix, tag, text)
        if self._in_queue(text):
            return
        if log and ('#all' in users or '#human' in users):
            self.console(text, tag)
        usermsg.saytext2(self._sort_users(users), 0, """%s""" % self._compile(text2))

    def hud(self, users, *text):
        """ A hudhint type message which appears in the bottom center of the player screen """
        usermsg.hudhint(self._sort_users(users),
                        self._compile('| SAM |\n' + '\n'.join(map(str, text)), True))

    def center(self, users, text):
        usermsg.centermsg(self._sort_users(users), text)

    def side(self, users, tag=True, *text):
        text = '[ SAM ]\n' if tag else '' + '\n'.join(map(str, text))
        usermsg.keyhint(self._sort_users(users), self._compile(text, remove=True, special=False))

    def VGUIPanel(self, users, panel_name, visible, data={}):
        usermsg.showVGUIPanel(self._sort_users(users), panel_name, visible, data)

    def motd(self, users, title, path, t=2):
        """ Message Of The Day type message, to send URL pages to
            users using the in-game MOTD window browser """
        usermsg.motd(self._sort_users(users), t, 'SAM | %s' % title, path)

    def info(self, users, title, *lines):
        with open(path.info_window_file, 'w') as f:
            f.write('\n'.join(lines))
        self.motd(self._sort_users(users), title, path.info_window_file.replace('\\', '/'), 3)

    def console(self, text, tag=None):
        """ Prints a message to the server console with SAM's prefix, a "tag" can be used
            to identify the system or addon from which the message is being sent

            e.g SAM | PLAYERS MANAGER | X was kicked from the server. """
        print(self._compile('[%s][SAM] %s%s' %
                            (get_time('%H:%M:%S'),tag.upper() + ' | ' if tag else '', text), True))
msg = _messages_system()

class _admins_system:

    def __init__(self):
        self.admins = databases.load('admins_data')
        self.groups = databases.load('admins_groups')
        self.flags = ['addons_monitor',
                      'admins_manager',
                      'players_manager',
                      'teams_manager',
                      'kick_players',
                      'mute_players',
                      'maps_manager',
                      'bots_manager',
                      'rcon_command',
                      'admins_chat',
                      'settings',
                      'ban_manager']

        # Update admin groups with new flags if any new flag exists
        for k, v in self.groups.items():
            keys = v.keys()
            for i in self.flags:
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
            i = admin[flag] or (group[flag] if group else False)
            if not i:
                msg.hud(uid, 'You don\'t have permission to use %s' % title(flag))
            return i
        elif flag == 'ban_level':
            return max(admin['ban_level'], group['ban_level'] if group else 0)

    def immunity_check(self, uid, admin2):
        if plugin.developer_mode == 3:
            return True
        sid = getsid(uid)
        if not self.is_admin(admin2) or sid == admin2:
            return True
        admin1 = self.admins[sid]
        admin2 = self.admins[admin2]
        if admin2['super_admin']:
            msg.hud(uid, 'Action denied! %s is a Super Admin.' % admin2['name'])
            return False
        elif admin1['super_admin']:
            return True
        admin1_g = self.groups[admin1['group']]['immunity_level'] if admin1['group'] else 0
        admin2_g = self.groups[admin2['group']]['immunity_level'] if admin2['group'] else 0
        check = max(admin1['immunity_level'], admin1_g) > max(admin2['immunity_level'], admin2_g)
        if not check:
            msg.hud(uid, 'Action denied! %s has higher immunity level than you' % admin2['name'])
        return check

    def _update_admin(self, admin):
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
            if i not in self.flags and i not in ('name', 'since', 'immunity_level', 'super_admin',
                                                 'ban_level', 'group'):
                del data[i]
admins = _admins_system()

class _commands_system:

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

    def delete(self, command):
        if es.exists('saycommand', '!' + command):
            cmdlib.unregisterSayCommand('!' + command)
            cmdlib.unregisterSayCommand('!sam_' + command)
        command = 'sam_' + command
        if es.exists('clientcommand', command):
            cmdlib.unregisterClientCommand(command)
        if es.exists('variable', command) or es.exists('command', command):
            cmdlib.unregisterServerCommand(command)
cmds = _commands_system()

class _players_info_system:
    """ Internal Player information system """

    class Player(object):
        def __init__(self, data):
            for key in data.keys():
                setattr(self, key, data[key])

    def __init__(self):
        # Load database
        self.data = databases.load('players_data')

        # Update active players
        for uid in userid_list('#human'):
            self._update(uid)

    def __call__(self, user):
        """ Return the Player info as class object """
        target = None
        if isinstance(user, int):
            target = getsid(user)
        elif str(user).startswith('[U:') or str(user).startswith('STEAM_'):
            target = user
        return self.Player(self.data[target]) if target in self.data.keys() else None

    def list(self):
        return [self.Player(self.data[k]) for k in self.data.keys()]

    def _update(self, uid):
        """ Updates the player info into the database """
        ply = get_player(uid)
        if ply.steamid == 'BOT': return
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
        else: self.data[ply.steamid] = i.copy()
        databases.save('players_data', self.data)

class PageSetup(object):

    def __init__(self, pageid, callback=None, previous_page=None):
        self.pageid = pageid
        self.callback = callback
        self.previous_page = previous_page
        self.previous_subpage = 1
        self.title_text = False
        self.header_text = True
        self.footer_text = False
        self.description_text = False
        self.close_option = True
        self.subpage_counter = True
        self.subpages = {1: []}
        self.maxlines = 7
        self.all_valid = False
        self.timeout = 0
        self.blocked_options = []
        sep = int(settings('pages_separator_line_length'))
        self.separator_line = '-' * sep if sep <= 40 else 40

    def title(self, text):
        self.title_text = ' :: ' + text

    def description(self, *lines):
        self.description_text = '\n'.join(lines)

    def footer(self, *lines):
        self.footer_text = self.separator_line + '\n' + '\n'.join(lines)

    def newline(self, *text):
        self.subpages[self._current_subpage()].extend([i for i in text])

    def separator(self):
        self.newline(self.separator_line)

    def option(self, obj, text, blocked=False):
        subpage = self._current_subpage()
        self.subpages[subpage].append({'object': obj,
                                       'text': text,
                                       'blocked': blocked,
                                       'choice': len(self.subpages[subpage]) + 1})

    def next_subpage(self):
        self.subpages[max(self.subpages.keys()) + 1] = []

    def send(self, users, subpage=1):
        debug(2, '[Initializing Page Setup Process]')
        debug(2, '- Page ID: %s' % self.pageid)
        display = []
        debug(2, '- Page Features:')
        debug(2, '   * Header: %s' % str(bool(self.header_text)))
        if bool(self.header_text):
            display.append('SAM v%s %s\n \n' %
            (plugin.version, ' ' * 30 + get_time('%H:%M') if settings('enable_pages_clock') else ''))
        debug(2, '   * Title: %s' % str(bool(self.title_text)))
        if bool(self.title_text):
            total_subpages = len(self.subpages.keys())
            if total_subpages > 1:
                display.append('%s   (%s/%s)' % (self.title_text, subpage, total_subpages)
                                if self.subpage_counter else self.title_text)
            else: display.append(self.title_text)
        debug(2, '   * Description: %s' % str(bool(self.description_text)))
        if self.description_text:
            display.extend((self.separator_line, self.description_text))
        display.append(self.separator_line)
        debug(2, '   * Settting up Lines & Options')
        option = 0
        self.blocked_options = []
        if self.maxlines > 7:
            self.maxlines = 7
        for line in self.subpages[subpage]:
            if self.maxlines and option == self.maxlines:
                break
            if not isinstance(line, dict):
                display.append(str(line))
                if self.all_valid:
                    option += 1
                continue
            option += 1
            if line['blocked']:
                self.blocked_options.append(option)
            display.append('%s%s. %s' % ('' if line['blocked'] else '->', option, line['text']))
        debug(2, '   * Blocked Options: %s' % len(self.blocked_options))
        debug(2, '   * Footer: %s' % str(bool(self.footer_text)))
        if self.footer_text:
            display.append(self.footer_text)
        if self.close_option:
            display.append(self.separator_line)
        if subpage > 1:
            debug(2, '- Previous Page: %s' % self.previous_page)
            display.append('->8. Previous Subpage')
        if subpage + 1 in self.subpages.keys():
            debug(2, '- Next Page Option Set')
            display.append('->9. Next Subpage')
        debug(2, '- Close Option: %s' % str(self.close_option))
        if self.close_option:
            text = '0. %s' % ('Previous Page' if self.previous_page else 'Close Page')
            display.append(text)
        if not display:
            debug(2, '[Aborting Page Setup Process: Empty Page]')
            return
        display = '\n'.join(display)
        debug(2, '>> Page display build process complete!')
        cache.pages[self.pageid] = self
        debug(2, '>> Page caching complete!')
        users = (users, ) if isinstance(users, int) else userid_list(users)
        if not users:
            debug(2, '[Aborting Page Setup Process: No Valid Users Found]')
            return
        debug(2, '>> Sending Page To Users:')
        for user in users:
            uid = int(user)
            debug(2, '   -------------------------')
            debug(2, '   userid - steamid')
            debug(2, '   -------------------------')
            debug(2, '   %s      - %s' % (user, getsid(user)))
            debug(2, '   -------------------------')
            _cancel_page_refresh(uid)
            cache.pages_users[uid] = {'active': self.pageid, 'subpage': subpage}
            es.showMenu(self.timeout, uid, display.encode('utf-8'))
            if self.timeout == 0:
                delay_task(1, 'refresh_%s_page' % uid, self._refresh_page, uid)
        debug(2, '[Page Setup Process Complete]')

    def send_option(self, uid, option):
        option = self.get_option(option)
        self.send(uid, option['subpage'])
        handle_choice(option['choice'], int(uid))

    def get_option(self, option, subpage=None):
        if not subpage:
            for pg in self.subpages.keys():
                for option in self.page_options(pg):
                    if option['object'] == option:
                        subpage = pg
        options = self.page_options(subpage)
        if isinstance(option, int):
            return options[option - 1]
        for option in options:
            if option['object'] == option:
                option['subpage'] = subpage
                return option

    def page_options(self, subpage=None):
        if not subpage:
            subpage = self._current_subpage()
        return [i for i in self.subpages[subpage] if isinstance(i, dict)]

    def _refresh_page(self, user):
        if user not in cache.pages_users.keys():
            return
        page = cache.pages_users[int(user)]
        if page['active'] in cache.pages.keys():
            cache.pages[page['active']].send(user, page['subpage'])

    def _current_subpage(self):
        subpage = max(self.subpages.keys())
        if self.maxlines and len(self.page_options(subpage)) == self.maxlines:
            subpage += 1
            self.subpages[subpage] = []
        return subpage

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
    for user in cache.pages_users.keys():
        handle_choice(10, user, True)
        msg.hud(user, 'Your page was closed since SAM is unloading.')

    # Terminate all chat filters
    chat_filters._remove_all()

    # Clear cache
    cache.pages.clear()
    cache.pages_users.clear()

    # Delete core module commands
    cmds.delete('sam')
    cmds.delete('menu')
    cmds.delete('rcon')
    cmds.delete('admins')

    # Cancel delays
    cancel_delay('settings_watch')

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
    page = PageSetup('home_page', home_page_HANDLE)
    page.title('Home Page')
    for module in MODULES:
        page.option(module, title(module))
    if HOME_PAGE_ADDONS:
        page.separator()
        page.newline(' :: Addons')
        page.separator()
        addons = import_module('addons_monitor').addons
        for addon in HOME_PAGE_ADDONS:
            if addon in addons.keys() and addons[addon]['state']:
                page.option(addon, addons[addon]['name'])
            else:
                HOME_PAGE_ADDONS.remove(addon)
                home_page(uid)
                return
    page.send(uid)

def home_page_HANDLE(uid, choice, prev_page):
    if choice in MODULES:
        import_module(choice).module_page(uid)
        return
    elif choice in HOME_PAGE_ADDONS:
        import_addon(choice).addon_page(uid)

# Command Functions
def sam_CMD(uid, args):
    if not bool(admins.admins):
        import_module('admins_manager')._firstAdminSetup(uid)
        return
    if admins.is_admin(uid):
        home_page(uid)
    else: msg.hud(uid, 'You don\'t have permission to use this')

def rcon_CMD(uid, args):
    if not admins.can(uid, 'rcon_command') or not settings('enable_!rcon_command'):
        return
    if not args:
        msg.tell(uid, '#blueSyntax example:\n#orange!rcon <command/variable> {arguments/value}')
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
    else: msg.tell(uid, '#green\'%s\' #orangeis not a command or server variable.' % (cmd))

def admins_CMD(uid, args):
    if not settings('enable_!admins_command'):
        return
    lis1 = [admins(i.steamid) for i in player_list('#human') if admins.is_admin(i)]
    if not lis1:
        msg.tell(uid, '#redThere are no #cyanAdmins #redonline')
        return
    page = PageSetup('admins_list')
    page.header_text = False
    page.title('Admins Online (%s of %s)' % (len(lis1), len(admins.list())))
    lis2 = []
    for i in lis1:
        text = i['name']
        if i['super_admin']:
            page.option(i, text + ' [Super Admin]')
        else:
            lis2.append('%s [%s]' % (title(i['group']), text) if i['group'] else text)
    for i in sorted(lis2):
        page.option(i, i)
    page.send(uid)

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
    try: return playerlib.getPlayer(getuid(user))
    except: return None

def player_list(*filters):
    if not filters:
        return playerlib.getPlayerList('#human')
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

def change_team(uid, newteam):
    es.changeteam(uid, 1)
    if newteam == 2:
        es.changeteam(uid, 2)
        es.setplayerprop(uid, 'CCSPlayer.m_iClass', random.randint(1, 4))
        msg.VGUIPanel(uid, 'class_ter', False, {})
    elif newteam == 3:
        es.changeteam(uid, 3)
        es.setplayerprop(uid, 'CCSPlayer.m_iClass', random.randint(5, 8))
        msg.VGUIPanel(uid, 'class_ct', False, {})

def emit_sound(target, sound, volume=1, attenuation=0.5):
    es.emitsound('player', target, sound, volume, attenuation)

def play_sound(users, sound, volume=1.0):
    pass

def stop_sound(uid):
    pass

def import_module(module):
    return es.import_addon('sam/' + module)

def import_addon(addon):
    addons = import_module('addons_monitor').addons
    if addon in addons.keys() and addons[addon]['state']:
        return import_module('addons/' + addon)
    console('Error: Failed to import "%s" addon' % addon)
    return None

def delay_task(time, name, function, args=()):
    gamethread.delayedname(time, 'sam_' + name, function, args)

def cancel_delay(name):
    gamethread.cancelDelayed('sam_' + name)

def get_time(frmt, from_stamp=None):
    """ Examples:
        %d/%m/%Y, %H:%M:%S = 06/12/2018, 09:55:22
        %d %B, %Y          = 12 June, 2018
    """
    return datetime.fromtimestamp(from_stamp if from_stamp else timestamp()).strftime(frmt)

def random(obj):
    return rdm.choice(obj)

def timestamp():
    return time.time()

def percentof(part, whole):
    return 100 * part / whole if part else 0

def title(text):
    return text.title().replace('_', ' ') if text else 'None'

# Page Functions
def handle_choice(choice, user, force_close=False):
    if not force_close:
        _process_user_choice(user, choice)
        return
    es.cexec(user, 'slot10')
    if user in cache.pages_users.keys():
        del cache.pages_users[user]
        _cancel_page_refresh(user)

def _cancel_page_refresh(tar):
    if tar in FILTERS:
        for uid in userid_list(tar):
            cancel_delay('refresh_%s_page' % uid)
    else: cancel_delay('refresh_%s_page' % int(tar))

def _process_user_choice(uid, choice):
    _cancel_page_refresh(uid)
    if uid not in cache.pages_users.keys():
        return
    user = cache.pages_users[uid]
    active_page = user['active']
    active_subpage = user['subpage']
    del cache.pages_users[uid]
    if active_page not in cache.pages.keys():
        return
    page = cache.pages[active_page]
    if choice == 10 and page.close_option:
        if page.previous_page and page.previous_page in cache.pages.keys():
            cache.pages[page.previous_page].send(uid, page.previous_subpage)
        return
    elif choice <= len(page.page_options(active_subpage)):
        if choice in page.blocked_options or not page.callback:
            if choice in page.blocked_options:
                msg.hud(uid, 'This option is currently blocked')
            page.send(uid, active_subpage)
            return
        class PageInfo:
            def __init__(self, a, b, c, d):
                self.pageid  = a
                self.object  = b
                self.choice  = c
                self.subpage = d
            def return_page(self, uid):
                self.object.send(uid, self.subpage)
        page.callback(uid, page.get_option(choice, active_subpage)['object'],
                      PageInfo(page.pageid, page, choice, active_subpage))
    elif choice == 8 and active_subpage > 1:
        page.send(uid, active_subpage - 1)
    elif choice == 9 and active_subpage + 1 in page.subpages.keys():
        page.send(uid, active_subpage + 1)
    else:
        page.send(uid, active_subpage)

# Game Events
def es_map_start(ev):
    # Clear Page System Cache
    cache.pages.clear()
    cache.pages_users.clear()

    # Remove all unnecessary chat filters
    for name in chat_filters.filters.keys():
        _filter = chat_filters.filters[name]
        _filter.users.clear()
        chat_filters.remove(name, _filter.block)

def es_client_command(ev):
    # Called when player chooses a page option
    if ev['command'] == 'menuselect':
        _process_user_choice(int(ev['userid']), int(ev['commandstring']))

def player_activate(ev):
    uid = ev['userid']
    # Update player info
    players._update(uid)

def player_disconnect(ev):
    # Decache player from the various systems
    uid = int(ev['userid'])
    sid = ev['networkid']
    if uid in cache.sounds.keys():
        del cache.sounds[uid]
    if uid in cache.pages_users.keys():
        del cache.pages_users[uid]
    for name in chat_filters.filters.keys():
        _filter = chat_filters.filters[name]
        if uid in _filter.users:
            chat_filters.remove_user(uid, name)
    # Update player last seen time
    if sid in players.data.keys():
        players.data[sid]['last_seen'] = get_time('%m/%d/%Y at %H:%M:%S')

# Class Declaration
players = _players_info_system()