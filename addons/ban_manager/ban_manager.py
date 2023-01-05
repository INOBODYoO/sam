from __future__ import with_statement

import es
import psyco

psyco.full()

sam = es.import_addon('sam')

# Global Variables
data = sam.databases.load('ban_players_data')
logs = sam.databases.load('ban_logs')
reasons_file = sam.path.core + '/required/ban_reasons.txt'
reasons = [
    '// SAM - Ban Reasons File',
    '// ',
    '// Right down the reasons you want to be available for Admins to choose from',
    '// when banning a player. To do so:',
    '// - To add/remove a reason, simply add/remove a line',
    '// - When done editing the file simply save it, this file is read in',
    '//   real-time, you don\'t need to restart the server or reload the plugin.\n',
    'Disrespected/insulted players',
    'Disrespected/insulted Admins/Moderators',
    'Used wall-hack cheating',
    'Used Aim-bot cheating',
    'Abuse of Voice Chat (Loud noises, play music, etc)',
    'Intentional chat Spam',
    'Intentional abuse of a known game/map bug']
lengths = {1: (('5 Minutes', 300),
               ('30 Minutes', 1800),
               ('1 Hour', 3600),
               ('3 Hours', 10800),
               ('12 Hours', 43200),
               ('1 Day', 86400)),
           2: (('3 Days', 259200),
               ('1 Week', 604800),
               ('1 Month', 2629746),
               ('3 Months', 7889238),
               ('6 Months', 15778476),
               ('1 Year', 31556952))}


def load():
    # Create reasons file
    sam.write_file(reasons_file, reasons)

    # Add Home Page add_option
    sam.HOME_PAGE_ADDONS.append('ban_manager')


def unload():
    # Save databases
    _save_data()


def addon_menu(uid, args=None):
    if not sam.admins.can(uid, 'ban_level'):
        sam.msg.hud(uid, 'You don\'t have permission to use Ban Manager')
        sam.home_page(uid)
        return
    menu = sam.Menu('ban_manager', ban_manager_HANDLE, 'home_page')
    menu.title('Ban Manager')
    menu.add_option(1, 'Ban a Player')
    menu.add_option(2, 'Banned Players (%s)' % len(data.keys()))
    menu.add_option(3, 'Ban History')
    menu.send(uid)


def ban_manager_HANDLE(uid, choice, submenu):
    def r(uid, text):
        sam.msg.hud(uid, text)
        addon_menu(uid)

    if choice == 1:
        menu = sam.Menu('bm_player_list', player_list_HANDLE, submenu)
        menu.title('Ban Manager')
        menu.description('Choose a player to ban:')
        active = []
        inactive = []
        for user in sam.players.list():
            # Skip players who match these checks:
            # - player is Super Admin
            # - player is currently banned
            # - player is the user of the page
            # - player is also an Admin with higher immunity level
            if sam.admins.can(user.steamid, 'super_admin') \
                    or is_banned(user.steamid) \
                    or not sam.admins.immunity_check(uid, user.steamid) \
                    or user.steamid == sam.getsid(uid):
                continue
            if sam.getuid(user.steamid):
                active.append(user)
            else:
                inactive.append(user)
        menu.add_line('[Online Players]')
        if active:
            for u in sorted(active, key=lambda u: u.name):
                menu.add_option(u, u.name)
        else:
            menu.add_line('- No Valid Players Found', ' ')
        menu.add_line('[Offline Players]')
        if inactive:
            for u in sorted(inactive, key=lambda u: u.name):
                menu.add_option(u, u.name)
        else:
            menu.add_line('- No Valid Players Found', ' ')
        menu.send(uid)
        return
    elif choice == 2:
        if not data.keys():
            r(uid, 'Currently, there aren\'t any players banned.')
            return
        menu = sam.Menu('banned_list', ban_profile, submenu)
        menu.title('Ban Manager')
        menu.description('Choose a player:')
        for k, v in data.items():
            menu.add_option(v, v['name'])
        menu.send(uid)
        return
    elif choice == 3:
        if not logs.keys():
            r(uid, 'There aren\'t any bans registered yet')
            return
        menu = sam.Menu('ban_history_year', ban_history_year_HANDLE, submenu)
        menu.title('Ban Manager')
        menu.description('Choose a year:')
        for i in sorted(logs.keys()):
            menu.add_option(i, i)
        menu.send(uid)


def ban_profile(uid, info, submenu=False):
    sid = info['steamid']
    menu = sam.Menu('ban_profile', ban_profile_HANDLE, submenu)
    menu.title('Ban Profile')
    menu.add_line('NAME: ' + info['name'],
                  'STEAMID: ' + sid,
                  'BAN DATE: ' + info['date'],
                  'EXPIRES: %s' % (sam.get_time('%m/%d/%Y at %H:%M:%S',
                                                info['expiry_date'])
                                   if info['expiry_date'] != 'permanent'
                                   else info['length_text']),
                  'ADMIN: ' + info['admin'],
                  'REASON:\n - ' + info['reason'])
    can = sam.admins.can(uid, 'ban_level')
    menu.separator()
    menu.add_option(info, 'Unban Player', can != 3)
    if can != 3:
        menu.footer('Only Admins with Ban Level 3 may Unban')
    menu.send(uid)


def ban_profile_HANDLE(uid, choice, submenu):
    if not isinstance(choice, dict):
        submenu.send(uid)
        return
    unban(choice['steamid'])
    sam.msg.hud('#admins',
                '%s ban removed by %s' % (choice['name'], es.getplayername(uid)))
    addon_menu(uid)


def player_list_HANDLE(uid, choice, submenu):
    menu = sam.Menu('bm_ban_length', ban_length_HANDLE, submenu)
    menu.title('Ban Manager')
    menu.description('Choose ban length:')
    lvl = sam.admins.can(uid, 'ban_level')
    if lvl == 3:
        menu.add_option([choice, 'Permanent', 0.0], 'Permanent')
    for num in lengths.keys():
        if lvl >= num:
            menu.add_line('[Ban Level %s]' % num)
            for text, secs in lengths[num]:
                menu.add_option([choice, text, secs], text)
    menu.footer('You have access up to Ban Level %s' % lvl)
    menu.send(uid)


def ban_length_HANDLE(uid, choice, submenu):
    menu = sam.Menu('bm_ban_reason', ban_reason_HANDLE, submenu)
    menu.title('Ban Manager')
    menu.description('Choose ban reason:')
    for line in sam.read_file(reasons_file, reasons):
        menu.add_option((choice, line), line)
    menu.send(uid)


def ban_reason_HANDLE(uid, choice, submenu):
    user, length_text, length = choice[0]
    length = 'permanent' if length == 0 else length + sam.timestamp()
    info = {'steamid': user.steamid,
            'name': user.name,
            'admin': es.getplayername(uid),
            'date': sam.get_time('%m/%d/%Y at %H:%M:%S'),
            'expiry_date': length,
            'length_text': length_text,
            'reason': choice[1]}
    ban(info)
    addon_menu(uid)
    ban_profile(uid, info)


def ban(info):
    sid = info['steamid']
    # Remove player from ban list if banned
    if sid in data.keys():
        del data[sid]
    # Register player ban to the addon's database, and save
    data[sid] = info.copy()
    _save_data()
    # Log ban to database
    year = sam.get_time('%Y')
    month = sam.get_time('%B')
    if year not in logs.keys():
        logs[year] = {}
    if month not in logs[year].keys():
        logs[year][month] = []
    logs[year][month].append(info)
    # Kick player if he is active
    kick(sid)
    # Register ban to the player's ban history
    sam.players.data[sid]['ban_history'].append({'length': info['length_text'],
                                                 'date': info['date'],
                                                 'admin': info['admin'],
                                                 'reason': info['reason']})


def unban(sid):
    if sid in data.keys():
        del data[sid]
    _save_data()


def kick(sid, notify=True):
    ply = sam.get_player(sid)
    dat = data[sid] if sid in data.keys() else False
    if not dat or not ply:
        return
    if dat['length_text'] == 'Permanent':
        kick_t = 'You are permanently banned from the server!'
        chat_t = '#red%s #whitehas been #orangepermanently banned #whitefrom the server!'\
                 % dat['name']
    else:
        kick_t = 'You are banned for %s from the server. (Reason: %s)' %\
                 (dat['length_text'], dat['reason'])
        chat_t = '#red%s #whitehas been #orangebanned for %s #whitefrom the server! (Reason: %s)'\
                 % (dat['name'], dat['length_text'], dat['reason'])
    ply.kick(kick_t)
    if notify:
        sam.msg.tell('#human', chat_t)


# BAN LOGS
def ban_history_year_HANDLE(uid, choice, submenu):
    if not logs[choice].keys():
        sam.msg.hud(uid, 'There aren\'t any bans registered in %s' % choice)
        del logs[choice]
        addon_menu(uid)
        return
    menu = sam.Menu('ban_history_month', ban_history_month_HANDLE, submenu)
    menu.title('Ban Manager')
    menu.description('Choose a month:')
    for i in ('January', 'February', 'March', 'April', 'May', 'June',
              'July', 'August', 'September', 'October', 'November', 'December'):
        if i in logs[choice].keys():
            menu.add_option((choice, i), i)
    menu.send(uid)


def ban_history_month_HANDLE(uid, choice, submenu):
    year, month = choice
    submenu.send(uid)
    lines = ['// SAM (Server Administration Menu)',
             '//',
             '// Logs are sorted in chronological order.',
             ' ']
    for k in logs[year][month]:
        lines.extend(('Player: ' + k['name'],
                      'Ban Admin: ' + k['admin'],
                      'Ban Date: ' + k['date'],
                      'Ban Length: ' + k['length_text'],
                      'Expiration Date: %s' %
                      (sam.get_time('%m/%d/%Y at %H:%M:%S',
                       k['expiry_date']) if k['expiry_date'] != 'permanent' else k['length_text']),
                      'Ban Reason: ' + k['reason']))
        lines.append('-' * 80)
    sam.msg.info(uid, 'Ban History from %s of %s' % (month, year), *lines)


# Addon Functions
def is_banned(sid):
    if sid not in data.keys():
        return False
    exp = data[sid]['expiry_date']
    if exp == 'permanent' or sam.timestamp() < exp:
        return True
    unban(sid)
    return False


def banned_list():
    return [v for k, v in data.items() if is_banned(k)]


def _convert(date):
    return datetime.strptime(date, '%Y-%m-%d %H:%M:%S.%f')


def _save_data():
    sam.databases.save('ban_players_data', data)
    sam.databases.save('ban_logs', logs)


# Game Events
def player_activate(ev):
    sid = sam.getsid(int(ev['userid']))
    if is_banned(sid):
        kick(sid, False)
