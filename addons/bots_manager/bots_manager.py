import es
import psyco

psyco.full()

sam = es.import_addon('sam')
sam.HOME_PAGE_ADDONS.append('bots_manager')
exe = es.ForceServerCommand
commands = ('bot_quota',
            'bot_quota_mode',
            'bot_difficulty',
            'bot_chatter',
            'bot_defer_to_human',
            'bot_join_after_player',
            'bot_randombuy',
            'bot_auto_follow',
            'bot_stop',
            'bot_auto_vocate',
            'bot_walk',
            'bot_flipout',
            'bot_dont_shoot',
            'bot_zombie',
            'bot_allow_grenades',
            'bot_allow_machine_guns',
            'bot_allow_snipers',
            'bot_allow_pistols',
            'bot_allow_rifles',
            'bot_allow_rogues',
            'bot_allow_sub_machine_guns')
modes = {'bot_quota_mode': ['normal', 'fill', 'match'],
         'bot_chatter': ['off', 'radio', 'minimal', 'normal']}


def load():
    sam.cmds.chat('bots', addon_menu)
    for k, v in sam.databases.load('bots_manager').items():
        exe('%s %s' % (k, v))


def unload():
    sam.cmds.delete('bots')
    sam.databases.save('bots_manager', dict((i, str(es.ServerVar(i))) for i in commands))
    exe('bot_quota 0')
    exe('bot_kick')


def addon_menu(uid, args=None):
    if not sam.admins.is_allowed(uid, 'bots_manager'):
        sam.home_page(uid)
        return
    menu = sam.Menu('bots_manager', bots_manager_HANDLE, 'home_page')
    menu.title('Bots Manager')
    menu.add_option(1, 'Add a Bot')
    menu.add_option(2, 'Add a Bot to Counter-Terrorists')
    menu.add_option(3, 'Add a Bot to Terrorists')
    menu.add_option(4, 'Remove a Bot')
    menu.add_option(5, 'Remove all Bots')
    menu.separator()
    menu.add_option(6, 'Bots Settings')
    menu.send(uid)


def bots_manager_HANDLE(uid, choice, submenu, page=1):
    if choice == 6:
        menu = sam.Menu('bot_settings', bot_settings_HANDLE, submenu)
        menu.title('Bots Settings')
        for cmd in commands:
            val = str(es.ServerVar(cmd))
            if cmd == 'bot_difficulty':
                val = {0: 'Easy', 1: 'Normal', 2: 'Hard', 3: 'Expert'}[int(val)]
            menu.add_option(cmd, '%s: %s' % (sam.title(cmd.replace('bot_', '')),
                                             sam.title(val)))
        menu.footer('Some of these commands are sv_cheats protected.')
        menu.send(uid, page)
        return
    elif choice == 4:
        bots = sam.player_list('#bot')
        if bots:
            exe('bot_kick %s' % bots[0].name)
    else:
        exe({1: 'bot_add', 2: 'bot_add_ct', 3: 'bot_add_t', 5: 'bot_quota 0'}[choice])
    submenu.send(uid)


def bot_settings_HANDLE(uid, choice, submenu):
    var = es.ServerVar(choice)
    val = str(es.ServerVar(choice))
    if choice == 'bot_quota':
        menu = sam.Menu('choose_bot_quota', choose_bot_quota_HANDLE, submenu)
        menu.title('Bots Settings')
        for i in range(0, es.getmaxplayercount() + 1):
            menu.add_option(i, i)
        menu.send(uid)
        return
    elif choice == 'bot_difficulty':
        val = int(val) + 1 if int(val) < 3 else 0
    elif choice in ('bot_quota_mode', 'bot_chatter'):
        mod = modes[choice]
        idx = mod.index(val)
        val = mod[idx + 1 if idx < len(mod) - 1 else 0]
    else:
        val = 1 if int(val) == 0 else 0
    var.set(val)
    sam.home_page(uid)
    addon_menu(uid)
    bots_manager_HANDLE(uid, 6, submenu.object.submenu, submenu.page)


def choose_bot_quota_HANDLE(uid, choice, submenu):
    es.ServerVar('bot_quota').set(choice)
    sam.home_page(uid)
    addon_menu(uid)
    sam.handle_choice(6, uid)
    submenu.send(uid)
