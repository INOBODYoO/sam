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
    sam.cmds.chat('bots', addon_page)
    for k, v in sam.databases.load('bots_manager').items():
        exe('%s %s' % (k, v))

def unload():
    sam.cmds.delete('bots')
    sam.databases.save('bots_manager', dict((i, str(es.ServerVar(i))) for i in commands))
    exe('bot_quota 0')
    exe('bot_kick')

def addon_page(uid, args=None):
    if not sam.admins.can(uid, 'bots_manager'):
        sam.home_page(uid)
        return
    page = sam.PageSetup('bots_manager', bots_manager_HANDLE, 'home_page')
    page.title('Bots Manager')
    page.option(1, 'Add a Bot')
    page.option(2, 'Add a Bot to Counter-Terrorists')
    page.option(3, 'Add a Bot to Terrorists')
    page.option(4, 'Remove a Bot')
    page.option(5, 'Remove all Bots')
    page.separator()
    page.option(6, 'Bots Settings')
    page.send(uid)

def bots_manager_HANDLE(uid, choice, prev_page, subpage=1):
    if choice == 6:
        page = sam.PageSetup('bot_settings', bot_settings_HANDLE, 'bots_manager')
        page.title('Bots Settings')
        for cmd in commands:
            val = str(es.ServerVar(cmd))
            if cmd == 'bot_difficulty':
                val = {0: 'Easy', 1: 'Normal', 2: 'Hard', 3: 'Expert'}[int(val)]
            page.option(cmd, '%s: %s' % (sam.title(cmd.replace('bot_', '')), sam.title(val)))
        page.footer('Some of these commands are sv_cheats protected.')
        page.send(uid, subpage)
        return
    elif choice == 4:
        bots = sam.player_list('#bot')
        if bots:
            exe('bot_kick %s' % bots[0].name)
    else:
        exe({1: 'bot_add', 2: 'bot_add_ct', 3: 'bot_add_t', 5: 'bot_quota 0'}[choice])
    prev_page.return_page(uid)

def bot_settings_HANDLE(uid, choice, prev_page):
    var = es.ServerVar(choice)
    val = str(es.ServerVar(choice))
    if choice == 'bot_quota':
        page = sam.PageSetup('choose_bot_quota', choose_bot_quota_HANDLE, 'bot_settings')
        page.title('Bots Settings')
        for i in xrange(0, es.getmaxplayercount() + 1):
            page.option(i, i)
        page.send(uid)
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
    addon_page(uid)
    bots_manager_HANDLE(uid, 6, None, prev_page.subpage)

def choose_bot_quota_HANDLE(uid, choice, prev_page):
    es.ServerVar('bot_quota').set(choice)
    sam.home_page(uid)
    addon_page(uid)
    sam.handle_choice(6, uid)
    prev_page.return_page(uid)
