import es
import psyco

psyco.full()

sam = es.import_addon('sam')

# Global Variables
GENERAL = 'General Settings'
ADDONS = 'Addons Settings'


def module_menu(uid):
    if not sam.admins.can(uid, 'settings_manager'):
        sam.home_page(uid)
        return
    menu = sam.Menu('settings_manager', settings_manager_HANDLE, 'home_page')
    menu.title('Settings')
    menu.add_option(GENERAL, GENERAL)
    addons_list = sam.settings(ADDONS)
    if addons_list:
        menu.separator()
        menu.add_line('Addons Settings:')
        for k in addons_list.keys():
            menu.add_option(k, sam.title(k))
    menu.send(uid)


def settings_manager_HANDLE(uid, choice, prev_page):
    menu = sam.Menu('settings_list', settings_list_HANDLE, prev_page)
    menu.maxline = 5
    data = sam.settings._load()

    def f(choice):
        if choice == GENERAL:
            menu.title(GENERAL)
            return data[GENERAL].items()
        menu.title(sam.title(choice) + ' Settings')
        return data[ADDONS][choice].items()

    for k, v in f(choice):
        if not isinstance(v, bool):
            continue
        menu.add_line(sam.title(k))
        menu.add_option((choice, data, k, v),
                        '[enabled] |  disabled' if v else 'enabled  | [disabled]')
    menu.separator()
    menu.add_option((choice, 'help'), 'Settings Help Window')
    menu.send(uid)


def settings_list_HANDLE(uid, choice, prev_page):
    if choice[1] == 'help':
        sam.settings.info_window(uid, choice[0])
        prev_page.send_previous_menu(uid)
        return
    section, data, variable, value = choice
    if section == GENERAL:
        data[GENERAL][variable] = not value
    else:
        data[ADDONS][section][variable] = not value
    sam.settings._save(data)
    sam.home_page(uid)
    sam.handle_choice(4, uid)
    settings_manager_HANDLE(uid, section, 'settings_manager')
