import es
import psyco

psyco.full()

sam = es.import_addon('sam')
exe = es.ForceServerCommand
commands = (
    'bot_quota',
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
    'bot_allow_sub_machine_guns'
)
modes = {
    'bot_quota_mode': ('normal', 'fill', 'match'),
    'bot_chatter': ('off', 'radio', 'minimal', 'normal')
}


def load():
    
    # Register the bots manager chat command
    sam.cmds.chat('bots', bots_CMD)
    
    # Load the bots manager database
    for k, v in sam.databases.load('bots_manager').items():
        exe('%s %s' % (k, v))


def unload():
    
    #  Unregister the bots manager chat command
    sam.cmds.delete('bots')
    
    # Save the bots manager database
    sam.databases.save('bots_manager', dict((i, str(es.ServerVar(i))) for i in commands))
    
    # Remove all bots
    exe('bot_quota 0')
    exe('bot_kick')


def addon_menu(userid, submenu='home_page'):
    if not sam.admins.is_allowed(userid, 'bots_manager'):
        sam.home_page(userid)
        return

    menu = sam.Menu('bots_manager', bots_manager_HANDLE, submenu)
    menu.title('Bots Manager')
    menu.add_option(1, 'Add a Bot')
    menu.add_option(2, 'Add a Bot to Counter-Terrorists')
    menu.add_option(3, 'Add a Bot to Terrorists')
    menu.add_option(4, 'Remove a Bot')
    menu.add_option(5, 'Remove all Bots')
    menu.separator()
    menu.add_option(6, 'Bots Settings')
    menu.send(userid)


def bots_manager_HANDLE(userid, choice, submenu, page=1):
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
        menu.send(userid, page)
        return
    elif choice == 4:
        bots = sam.player_list('#bot')
        if bots:
            exe('bot_kick %s' % bots[0].name)
    else:
        exe({1: 'bot_add', 2: 'bot_add_ct', 3: 'bot_add_t', 5: 'bot_quota 0'}[choice])
    submenu.send(userid)


def bot_settings_HANDLE(userid, choice, submenu):
    var = es.ServerVar(choice)
    val = str(es.ServerVar(choice))
    if choice == 'bot_quota':
        menu = sam.Menu('choose_bot_quota', choose_bot_quota_HANDLE, submenu)
        menu.title('Bots Settings')
        for i in range(0, es.getmaxplayercount() + 1):
            menu.add_option(i, i)
        menu.send(userid)
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
    bots_manager_HANDLE(userid, 6, submenu.object.submenu, submenu.page)


def choose_bot_quota_HANDLE(userid, choice, submenu):
    es.ServerVar('bot_quota').set(choice)
    bots_manager_HANDLE(userid, 6, 'bots_manager')
    
# Commands Functions
def bots_CMD(userid, args):
    addon_menu(userid, submenu=False)
