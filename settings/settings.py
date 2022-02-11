import es
import psyco
psyco.full()

sam = es.import_addon('sam')

# Global Variables
gen = 'General Settings'
add = 'Addons Settings'

def module_page(uid):
    if not sam.admins.can(uid, 'change_settings'):
        sam.home_page(uid)
        return

    page = sam.PageSetup('settings_page', settings_page_HANDLE, 'home_page')
    page.title('Settings')
    page.option(gen, gen)
    page.separator()
    page.newline('Addons Settings:')
    for k in sam.settings.default['Addons Settings'].keys():
        page.option(k, sam.title(k))
    page.send(uid)

def settings_page_HANDLE(uid, choice, prev_page):
    page = sam.PageSetup('settings_list', settings_list_HANDLE, 'settings_page')
    page.maxline = 5
    data = sam.settings._load()
    def f(choice):
        if choice == gen:
            page.title(gen)
            return data[gen].items()
        page.title(sam.title(choice) + ' Settings')
        return data[add][choice].items()

    for k, v in f(choice):
        if not isinstance(v, bool):
            continue
        page.newline(sam.title(k))
        page.option((choice, data, k, v), state(v))
    page.separator()
    page.option((choice, 'help'), 'Settings Help Window')
    page.send(uid)

def settings_list_HANDLE(uid, choice, prev_page):
    if choice[1] == 'help':
        sam.settings.info_window(uid, choice[0])
        prev_page.return_page(uid)
        return
    section, data, cmd, val = choice
    if section == gen:
        data[gen][cmd] = not val
    else:
        data[add][section][cmd] = not val
    sam.settings._save(data)
    sam.home_page(uid)
    sam.handle_choice(4, uid)
    settings_page_HANDLE(uid, section, None)

def state(val, short=False):
    return '[enabled] |  disabled' if val else 'enabled  | [disabled]'