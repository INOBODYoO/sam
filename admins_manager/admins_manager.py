import es
import psyco
psyco.full()

sam = es.import_addon('sam')

def load():
    for player in sam.player_list('#human'):
        if sam.admins.is_admin(player):
            sam.admins._update_admin(player)
    for group, flags in sam.admins.groups.items():
        for flag in sam.admins.flags:
            if flag not in flags.keys():
                flags[flag] = False

def module_page(uid):
    if not sam.admins.can(uid, 'admins_manager'):
        sam.home_page(uid)
        return
    page = sam.PageSetup('admins_manager', admins_manager_HANDLE, 'home_page')
    page.title('Admins Manager')
    page.option(1, 'Add New Admin')
    page.option(2, 'Remove Admin')
    page.option(3, 'Edit Admin Flags')
    page.separator()
    page.newline(':: Admins Groups')
    page.separator()
    page.option(4, 'Create New Group')
    page.option(5, 'Edit Group Flags')
    page.option(6, 'Remove Group')
    online = 0
    super_admins = 0
    for i in sam.userid_list():
        if sam.admins.can(i, 'super_admin', False):
            super_admins += 1
        elif sam.admins.is_admin(i):
            online += 1
    page.footer('Currently Online:',
                '* Super Admins: %s' % super_admins,
                '* Admins: %s' % online)
    page.send(uid)

def admins_manager_HANDLE(uid, choice, prev_page):
    if choice == 4:
        sam.msg.tell(uid, '#blueType the name of the group in the' +
                          ' chat or #red!cancel #blueto stop the operation.')
        sam.chat_filters.create('new_admin_group', _new_group_FILTER, True, uid)
        return
    elif choice in xrange(1,7):
        option = {1: ('Add Admin', 'Choose the new Admin:', add_admin),
                  2: ('Remove Admin', 'Choose the Admin to remove', remove_AdminOrGroup),
                  3: ('Edit Admin Flags', 'Choose the Admin to edit permission', edit_flags),
                  5: ('Edit Group Flags', 'Choose the Group to edit permission', edit_flags),
                  6: ('Remove Group', 'Choose the Group to remove', remove_AdminOrGroup)}[choice]
        page = sam.PageSetup('admins_groups_list', option[2], 'admins_manager')
        page.title(option[0])
        page.description(option[1])
        if choice == 1:
            users = [u for u in sam.player_list('#human') if not sam.admins.is_admin(u)]
            if not bool(users):
                sam.msg.hud(uid, 'There aren\'t any valid players in the server')
                prev_page.return_page(uid)
                return
            for u in users:
                page.option(u, u.name)
        elif choice in (2, 3):
            for k, v in sam.admins.items():
                page.option(k, v['name'] + ' [Super Admin]' if v['super_admin'] else v['name'])
        elif choice in (5, 6):
            if not bool(sam.admins('groups')):
                sam.msg.hud(uid, 'There aren\'t any groups available')
                prev_page.return_page(uid)
                return
            for k, v in sam.admins.items('groups'):
                page.option(k, sam.title(v['name']))
        page.send(uid)
        return
    prev_page.return_page(uid)

def add_admin(uid, user, prev_page=False, super_admin=False):
    user = sam.get_player(user)
    sam.admins.admins[user.steamid] = {'super_admin': super_admin,
                                       'name': user.name.encode('utf-8'),
                                       'group': None,
                                       'immunity_level': 0,
                                       'ban_level': 0,
                                       'since': sam.get_time('%m/%d/%Y')}
    for i in sam.admins.flags:
        sam.admins.admins[user.steamid][i] = False
    if prev_page: edit_flags(uid, user.steamid)

def remove_AdminOrGroup(uid, target, prev_page):
    module_page(uid)
    if target in sam.admins.list('groups'):
        sam.msg.hud(uid, '%s group has been removed' % sam.admins(target, 'name'))
        del sam.admins.groups[target]
        for admin in sam.admins.list():
            if sam.admins(admin)['group'] == target:
                sam.admins.admins[admin]['group'] = None
        return
    if sam.admins.is_admin(target):
        admin = sam.admins(target)
        if sam.getsid(uid) == target:
            sam.msg.hud(uid, 'You cannot remove yourself as Admin')
            prev_page.return_page(uid)
            return
        elif admin['super_admin'] and not sam.admins.can(uid, 'super_admin'):
            sam.msg.hud(uid, '%s is a Super Admin, and can\'t be removed' % admin['name'])
            prev_page.return_page(uid)
        else:
            sam.msg.hud(uid, '%s has been removed from Admins' % (admin['name']))
            del sam.admins.admins[target]
            target = sam.getuid(target)
            if target:
                sam.handle_choice(10, target, True)
                sam.msg.hud(target, 'You have been demoted from Admin',
                                    'Your active page has been closed for security reasons')
            module_page(uid)
            sam.handle_choice(2, uid)
    else:
        sam.msg.hud(uid, '%s is not a valid Admin or Group' % target)

def edit_flags(uid, target, prev_page=None, subpage=1):
    if not sam.admins.can(uid, 'admins_manager'):
        sam.home_page(uid)
        return
    data = sam.admins(target)
    def f(b):
        return 'Yes' if b else 'No'
    page = sam.PageSetup('edit_flags', edit_flags_HANDLER, 'admins_manager')
    page.title('Edit Flags')
    if sam.admins.is_admin(target):
        if not sam.admins(sam.getsid(uid), 'super_admin') and data['super_admin']:
            sam.msg.hud(uid, 'You are not allowed to edit Super Admins')
            return
        page.description('* NAME: ' + data['name'],
                         '* STEAMID: ' + target,
                         '* SINCE: ' + data['since'])
        page.option((target, 'super_admin'), 'Super Admin: %s' % f(data['super_admin']))
        page.option((target, 'admin_group'), 'Admin Group: ' + sam.title(data['group']))
    else:
        page.description('* GROUP NAME: ' + sam.title(data['name']))
        page.option((target, 'members'), 'Group Members (%s)' %
                    len([i for i in sam.admins.list() if sam.admins(i)['group'] == target]))
        page.option((target, 'group_color'), 'Group Color: ' + sam.title(data['color']))
    page.option((target, 'ban_level'), 'Ban Level: %s' % data['ban_level'])
    page.option((target, 'immunity_level'), 'Immunity Level: %s' % data['immunity_level'])
    if sam.admins.is_admin(target):
        page.maxlines = 5
        page.next_subpage()
        page.newline('Admin Flags:')
    for i in sorted(sam.admins.flags):
        page.option((target, i), '%s: %s' % (sam.title(i), f(data[i])))
    page.send(uid, subpage)

def edit_flags_HANDLER(uid, choice, prev_page):
    target, flag = choice
    data = sam.admins(target)
    if flag == 'admin_group':
        groups = sam.admins('groups')
        if bool(groups):
            page = sam.PageSetup('am_set_group', set_group_HANDLER, 'edit_flags')
            page.title('Edit Flags')
            page.description('- Choose a group group')
            if data['group']:
                page.option((target, 1), 'Remove Current Group')
            for g in groups.keys():
                page.option((target, g), sam.title(g))
            page.send(uid)
            return
        else:
            sam.msg.hud(uid, 'There aren\'t any Admin groups available')
    elif flag == 'members':
        page = sam.PageSetup('am_choose_members', set_group_members_HANDLER, 'edit_flags')
        page.title('%s Group Members' % sam.title(target))
        page.description('Choose an Admin to either assign',
                         'assign to or remove from this:')
        for i in sam.admins.list():
            a = sam.admins(i)
            page.option((target, i), '%s%s' %
                        (a['name'], ' [%s]' % sam.title(a['group']) if a['group'] else ''))
        page.send(uid)
        return
    elif flag == 'group_color':
        page = sam.PageSetup('am_choose_group_color', set_group_color_HANDLER, 'edit_flags')
        page.title('%s Group Color' % sam.title(target))
        page.description('Choose a color:')
        for color in sorted(sam.msg.chat_colors.keys()):
            page.option((target, color), sam.title(color))
        page.footer('This color will be used to colorize',
                    'the group name in the game chat')
        page.send(uid)
        return
    elif flag == 'immunity_level':
        page = sam.PageSetup('am_choose_immunity', set_immunity_HANDLER, 'edit_flags')
        page.title('Edit Flags')
        page.description('- Choose the immunity level')
        page.option((target, 0), 0)
        for i in xrange(1, 11):
            i *= 10
            page.option((target, i), i)
        page.send(uid)
        return
    elif flag == 'super_admin':
        sid = sam.getsid(uid)
        if not sam.admins(sid, 'super_admin'):
            sam.msg.hud(uid, 'You are not allowed to set/remove Super Admins')
        elif sid == target and len([k for k, v in sam.admins.items() if v['super_admin']]) < 2:
            sam.msg.hud(uid, 'Action denied, SAM requires at least one Super Admin to operate')
        else:
            data['super_admin'] = not data['super_admin']
    elif flag == 'ban_level':
        lvl = int(data['ban_level'])
        data['ban_level'] = lvl + 1 if lvl < 3 else 0
    elif flag in sam.admins.flags:
        data[flag] = not data[flag]
    edit_flags(uid, target, subpage=prev_page.subpage)

def set_group_color_HANDLER(uid, choice, prev_page):
    target, color = choice
    sam.admins.groups[target]['color'] = color
    sam.msg.hud(uid, '%s color is now %s' % (sam.title(target), color))
    edit_flags(uid, target)

def set_group_members_HANDLER(uid, choice, prev_page):
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
    edit_flags(uid, target)
    sam.handle_choice(1, uid)

def set_group_HANDLER(uid, choice, prev_page):
    target, group = choice
    sam.admins.admins[target]['group'] = None if group == 1 else group
    name = sam.admins(target)['name']
    sam.msg.hud(uid, '%s assigned to %s group' % (name, sam.title(target))
                if group else 'Removed %s from the group' % name)
    edit_flags(uid, target)

def set_immunity_HANDLER(uid, choice, prev_page):
    target, lvl = choice
    dat = sam.admins(target)
    dat['immunity_level'] = lvl
    sam.msg.hud(uid, 'Changed %s immunity level to %s' % (dat['name'], lvl))
    edit_flags(uid, target)

def _firstAdminSetup(uid):
    page = sam.PageSetup('first_admin_setup', first_admin_setup_HANDLE)
    page.title('First Admin Setup')
    page.newline('Hi ' + es.getplayername(uid),
                 ' ',
                 'SAM requires at least one Super Admin to be operate.',
                 'Do you want to setup yourself as Super Admin?')
    page.option(1, 'Yes, proceed')
    page.option(2, 'No')
    page.send(uid)

def first_admin_setup_HANDLE(uid, choice, prev_page):
    if choice == 1:
        del sam.cache.pages['first_admin_setup']
        sam.chat_filters.create('first_admin_setup', _first_admin_FILTER, True, uid)
        page = sam.PageSetup('rcon_verification')
        page.header_text = False
        page.title('First Admin Setup')
        page.newline('Good! Now SAM needs to verify you are',
                     'a server Owner/Operator, to do so:',
                     ' ',
                     '* Type in the chat the server RCON password',
                     '* To cancel this operation type !cancel')
        page.close_option = False
        page.send(uid)

# Chat Filters
def _first_admin_FILTER(uid, text, teamchat):
    sam.handle_choice(10, uid, True)
    if not sam.chat_filters.is_allowed(uid, 'first_admin_setup'):
        return (uid, text, teamchat)
    sam.chat_filters.remove('first_admin_setup', _first_admin_FILTER)
    del sam.cache.pages['rcon_verification']
    text = text.strip('"')
    if text == '!cancel':
        sam.msg.hud(uid, 'Operation Canceled!')
        return (0, 0, 0)
    elif text == str(es.ServerVar('rcon_password')):
        add_admin(uid, sam.get_player(uid), super_admin=True)
        sam.msg.side(uid, 'Great, RCON Password Confirmed!',
                          'You are now a Super-Admin, use !sam command to open the menu')
        sam.home_page(uid)
    else:
        sam.msg.hud(uid, 'RCON Password does not match, access denied!',
                         'Operation Canceled')
    return (0, 0, 0)

def _new_group_FILTER(uid, text, teamchat):
    if not sam.chat_filters.is_allowed(uid, 'new_admin_group'):
        return (uid, text, team)
    sam.chat_filters.remove_user(uid, 'new_admin_group')
    text = text.strip('"').lower()
    if text == '!cancel':
        sam.msg.hud(uid, 'Operation Canceled!')
        module_page(uid)
        return (0, 0, 0)
    else:
        key = text.lower().replace(' ', '_')
        if key not in sam.admins.list('groups'):
            sam.admins.groups[key] = {'name': key,
                                      'ban_level': 0,
                                      'immunity_level': 0,
                                      'color': sam.random(sam.msg.chat_colors.keys())}
            for i in sam.admins.flags:
                sam.admins.groups[key][i] = False
            edit_flags(uid, key)
        else:
            sam.msg.hud(uid, 'Action denied, %s group already exists!' % (text.title()))
            module_page(uid)
    return (0, 0, 0)

# Game Events
def player_activate(ev):
    u = int(ev['userid'])
    if sam.admins.is_admin(u):
        sam.admins._update_admin(u)