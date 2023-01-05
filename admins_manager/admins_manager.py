import es
import psyco

psyco.full()

sam = es.import_addon('sam')


def load():
    for player in sam.player_list('#human'):
        if sam.admins.is_admin(player):
            sam.admins.update_admin(player)
    for group, flags in sam.admins.groups.items():
        for flag in sam.admins.flags:
            if flag not in flags.keys():
                flags[flag] = False


def module_menu(uid):
    if not sam.admins.can(uid, 'admins_manager'):
        sam.home_page(uid)
        return
    menu = sam.Menu('admins_manager', admins_manager_HANDLE, 'home_page')
    menu.title('Admins Manager')
    menu.add_option(1, 'Add New Admin')
    menu.add_option(2, 'Remove An Admin')
    menu.add_option(3, 'Edit Admins Profiles')
    menu.separator()
    menu.add_line(':: Admins Groups')
    menu.separator()
    menu.add_option(4, 'Create a Group')
    menu.add_option(5, 'Delete a Group')
    menu.add_option(6, 'Edit Groups Profiles')
    online = 0
    super_admins = 0
    for i in sam.userid_list():
        if sam.admins.can(i, 'super_admin', False):
            super_admins += 1
        elif sam.admins.is_admin(i):
            online += 1
    menu.footer('Currently Online:',
                '- Super Admins: %s' % super_admins,
                '- Admins: %s' % online)
    menu.send(uid)


def admins_manager_HANDLE(uid, choice, submenu):
    if choice == 4:
        sam.msg.tell(uid, '#blueType the name of the group in the ' +
                     'chat or #red!cancel #blueto stop the operation.')
        sam.chat_filters.create('new_admin_group', _new_group_FILTER, True, uid)
        return
    elif choice in xrange(1, 7):
        option = {1: ('Add New Admin', 'Choose The New Admin:', add_admin),
                  2: ('Remove An Admin', 'Choose An Admin:', remove_AdminOrGroup),
                  3: ('Admins Profiles', 'Choose The Admin:', profile_editor),
                  5: ('Delete a Group', 'Choose The Group To Be Deleted:', remove_AdminOrGroup),
                  6: ('Groups Profiles', 'Choose A Group:', profile_editor)}[choice]
        menu = sam.Menu('admins_groups_list', option[2], submenu)
        menu.title(option[0])
        menu.description(option[1])
        if choice == 1:
            users = [u for u in sam.player_list('#human') if not sam.admins.is_admin(u)]
            if not bool(users):
                sam.msg.hud(uid, 'There aren\'t any valid players in the server')
                submenu.send(uid)
                return
            for u in users:
                menu.add_option(u, u.name)
        elif choice in (2, 3):
            for k, v in sam.admins.items():
                name = v['name'] + ' [Super Admin]' if v['super_admin'] else v['name']
                menu.add_option(k, name)
        elif choice in (5, 6):
            if not bool(sam.admins('groups')):
                sam.msg.hud(uid, 'There aren\'t any groups available')
                submenu.send(uid)
                return
            for k, v in sam.admins.items('groups'):
                menu.add_option(k, sam.title(v['name']))
        menu.send(uid)
        return
    submenu.send(uid)


def add_admin(uid, user, submenu=False, super_admin=False):
    user = sam.get_player(user)
    sam.admins.admins[user.steamid] = {'super_admin': super_admin,
                                       'name': user.name.encode('utf-8'),
                                       'group': None,
                                       'immunity_level': 0,
                                       'ban_level': 0,
                                       'since': sam.get_time('%m/%d/%Y')}
    for i in sam.admins.flags:
        sam.admins.admins[user.steamid][i] = False
    if submenu:
        profile_editor(uid, user.steamid)


def remove_AdminOrGroup(uid, target, submenu):
    module_menu(uid)
    if target in sam.admins.list('groups'):
        sam.msg.hud(uid, '%s group has been deleted' % sam.admins(target, 'name'))
        del sam.admins.groups[target]
        for admin in sam.admins.list():
            if sam.admins(admin)['group'] == target:
                sam.admins.admins[admin]['group'] = None
        return
    if sam.admins.is_admin(target):
        admin = sam.admins(target)
        if sam.getsid(uid) == target:
            sam.msg.hud(uid, 'You cannot remove yourself as Admin')
            submenu.send(uid)
            return
        elif admin['super_admin'] and not sam.admins.can(uid, 'super_admin'):
            sam.msg.hud(uid, '%s is a Super Admin, and can\'t be removed' % admin['name'])
            submenu.send(uid)
        else:
            sam.msg.hud(uid, '%s has been removed from Admins' % (admin['name']))
            del sam.admins.admins[target]
            target = sam.getuid(target)
            if target:
                sam.handle_choice(10, target, True)
                sam.msg.hud(target,
                            'Your Admin permissions have been removed!',
                            'Any active pages have been closed for security reasons.')
            module_menu(uid)
            sam.handle_choice(2, uid)
    else:
        sam.msg.hud(uid, '%s is not a valid Admin or Group' % target)


def profile_editor(uid, target, submenu, page=1):
    if not sam.admins.can(uid, 'admins_manager'):
        sam.home_page(uid)
        return
    data = sam.admins(target)

    def f(b):
        return 'Yes' if b else 'No'

    menu = sam.Menu('profile_editor', profile_editor_HANDLER, submenu)
    menu.title('Edit Flags')
    if sam.admins.is_admin(target):
        if not sam.admins(sam.getsid(uid), 'super_admin') and data['super_admin']:
            sam.msg.hud(uid, 'You are not allowed manage Super Admins')
            return
        menu.description('* NAME: ' + data['name'],
                         '* STEAMID: ' + target,
                         '* SINCE: ' + data['since'])
        menu.add_option((target, 'super_admin'), 'Super Admin: %s' % f(data['super_admin']))
        menu.add_option((target, 'admin_group'), 'Admin Group: ' + sam.title(data['group']))
    else:
        menu.description('* GROUP NAME: ' + sam.title(data['name']))
        menu.add_option((target, 'members'), 'Group Members (%s)' %
                        len([i for i in sam.admins.list() if sam.admins(i)['group'] == target]))
        menu.add_option((target, 'group_color'), 'Group Color: ' + sam.title(data['color']))
    menu.add_option((target, 'ban_level'), 'Ban Level: %s' % data['ban_level'])
    menu.add_option((target, 'immunity_level'), 'Immunity Level: %s' % data['immunity_level'])
    if sam.admins.is_admin(target):
        menu.maxlines = 5
        menu.next_page()
        menu.add_line('Permissions:')
    for i in sorted(sam.admins.flags):
        menu.add_option((target, i), '%s: %s' % (sam.title(i), f(data[i])))
    menu.send(uid, page)


def profile_editor_HANDLER(uid, choice, submenu):
    target, flag = choice
    data = sam.admins(target)
    if flag == 'admin_group':
        groups = sam.admins('groups')
        if bool(groups):
            menu = sam.Menu('am_set_group', set_group_HANDLER, submenu)
            menu.title('Edit Admins Profiles')
            menu.description('Choose A Group:')
            if data['group']:
                menu.add_option((target, 1), 'Remove From Current Group')
            for g in groups.keys():
                menu.add_option((target, g), sam.title(g))
            menu.send(uid)
            return
        else:
            sam.msg.hud(uid, 'There aren\'t any Admin groups available')
    elif flag == 'members':
        menu = sam.Menu('am_choose_members', set_group_members_HANDLER, submenu)
        menu.title('%s Group Members' % sam.title(target))
        menu.description('Choose an Admin to either assign',
                         'assign to or remove from this:')
        for i in sam.admins.list():
            a = sam.admins(i)
            menu.add_option((target, i), '%s%s' % \
                            (a['name'],
                             ' [%s]' % sam.title(a['group']) if a['group'] else ''))
        menu.send(uid)
        return
    elif flag == 'group_color':
        menu = sam.Menu('am_choose_group_color', set_group_color_HANDLER, submenu)
        menu.title('%s Group Color' % sam.title(target))
        menu.description('Choose A Color:')
        for color in sorted(sam.msg.colors.keys()):
            menu.add_option((target, color), sam.title(color))
        menu.footer('This color will be used to colorize',
                    'the group name in the game chat')
        menu.send(uid)
        return
    elif flag == 'immunity_level':
        menu = sam.Menu('am_choose_immunity', set_immunity_HANDLER, submenu)
        menu.title('Edit Flags')
        menu.description('- Choose the immunity level')
        menu.add_option((target, 0), 0)
        for i in xrange(1, 11):
            i *= 10
            menu.add_option((target, i), i)
        menu.send(uid)
        return
    elif flag == 'super_admin':
        sid = sam.getsid(uid)
        if not sam.admins(sid, 'super_admin'):
            sam.msg.hud(uid, 'You are not allowed to set/remove Super Admins')
        elif sid == target and len([k for k, v in sam.admins.items()
                                    if v['super_admin']]) < 2:
            sam.msg.hud(uid,
                        'Action denied, SAM requires at least one Super Admin to operate')
        else:
            data['super_admin'] = not data['super_admin']
    elif flag == 'ban_level':
        lvl = int(data['ban_level'])
        data['ban_level'] = lvl + 1 if lvl < 3 else 0
    elif flag in sam.admins.flags:
        data[flag] = not data[flag]
    profile_editor(uid, target, submenu.object.submenu, submenu.page)


def set_group_color_HANDLER(uid, choice, submenu):
    target, color = choice
    sam.admins.groups[target]['color'] = color
    sam.msg.hud(uid, '%s color is now %s' % (sam.title(target), color))
    profile_editor(uid, target, 'admins_manager')


def set_group_members_HANDLER(uid, choice, submenu):
    target, admin = choice
    if not sam.admins.can(uid, 'super_admin') and sam.admins.can(admin, 'super_admin'):
        sam.msg.hud(uid, 'You can\'t change Super Admins groups')
    elif sam.admins(admin)['group'] != target:
        sam.admins.admins[admin]['group'] = target
        sam.msg.hud(uid, '%s assigned to %s group' % (sam.admins(admin)['name'], sam.title(target)))
    else:
        sam.admins.admins[admin]['group'] = None
        sam.msg.hud(uid, '%s removed from %s group' %
                    (sam.admins(admin)['name'], sam.title(target)))
    profile_editor(uid, target, 'admins_manager')


def set_group_HANDLER(uid, choice, submenu):
    target, group = choice
    sam.admins.admins[target]['group'] = None if group == 1 else group
    name = sam.admins(target)['name']
    sam.msg.hud(uid, '%s assigned to %s group' %
                     (name,
                      sam.title(target)) if group else 'Removed %s from the group' % name)
    profile_editor(uid, target, 'admins_manager')


def set_immunity_HANDLER(uid, choice, submenu):
    target, lvl = choice
    dat = sam.admins(target)
    dat['immunity_level'] = lvl
    sam.msg.hud(uid, 'Changed %s immunity level to %s' % (dat['name'], lvl))
    profile_editor(uid, target, 'admins_manager')


def first_admin_setup(uid):
    menu = sam.Menu('first_admin_setup', first_admin_setup_HANDLE)
    menu.title('First Admin Setup')
    menu.add_line('Hi ' + es.getplayername(uid),
                 ' ',
                 'SAM requires at least one Super Admin to be operate.',
                 'Do you want to setup yourself as Super Admin?')
    menu.add_option(1, 'Yes, proceed')
    menu.add_option(2, 'No')
    menu.send(uid)


def first_admin_setup_HANDLE(uid, choice, submenu):
    if choice == 1:
        del sam.cache.pages['first_admin_setup']
        sam.chat_filters.create('first_admin_setup', _first_admin_FILTER, True, uid)
        menu = sam.Menu('rcon_verification')
        menu.header_text = False
        menu.title('First Admin Setup')
        menu.add_line('Good! Now SAM needs to verify you are',
                     'a server Owner/Operator, to do so:',
                     ' ',
                     '* Type in the chat the server RCON password',
                     '* To cancel this operation type !cancel')
        menu.close_option = False
        menu.send(uid)


# Chat Filters
def _first_admin_FILTER(uid, text, teamchat):
    sam.handle_choice(10, uid, True)
    if not sam.chat_filters.is_allowed(uid, 'first_admin_setup'):
        return uid, text, teamchat
    sam.chat_filters.remove('first_admin_setup', _first_admin_FILTER)
    del sam.cache.pages['rcon_verification']
    text = text.strip('"')
    if text == '!cancel':
        sam.msg.hud(uid, 'Operation Canceled!')
        return 0, 0, 0
    elif text == str(es.ServerVar('rcon_password')):
        add_admin(uid, sam.get_player(uid), super_admin=True)
        sam.msg.side(uid, 'Great, RCON Password Confirmed!',
                     'You are now a Super-Admin, use !sam command to open the menu')
        sam.home_page(uid)
    else:
        sam.msg.hud(uid, 'RCON Password does not match, access denied!',
                         'Operation Canceled')
    return 0, 0, 0


def _new_group_FILTER(uid, text, teamchat):
    if not sam.chat_filters.is_allowed(uid, 'new_admin_group'):
        return uid, text, team
    sam.chat_filters.remove_user(uid, 'new_admin_group')
    text = text.strip('"').lower()
    if text == '!cancel':
        sam.msg.hud(uid, 'Operation Canceled!')
        module_menu(uid)
        return 0, 0, 0
    else:
        key = text.lower().replace(' ', '_')
        if key not in sam.admins.list('groups'):
            sam.admins.groups[key] = {'name': key,
                                      'ban_level': 0,
                                      'immunity_level': 0,
                                      'color': sam.random(sam.msg.colors.keys())}
            for i in sam.admins.flags:
                sam.admins.groups[key][i] = False
            profile_editor(uid, key, 'admins_manager')
        else:
            sam.msg.hud(uid, 'Action denied, %s group already exists!' % (text.title()))
            module_menu(uid)
    return 0, 0, 0


# Game Events
def player_activate(ev):
    u = int(ev['userid'])
    if sam.admins.is_admin(u):
        sam.admins.update_admin(u)
