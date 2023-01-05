import es
import psyco

psyco.full()

# Global Variables
sam = es.import_addon('sam')


def load():
    # Initiate Addons
    sam.msg.console('* Loading Addons:')
    for addon, data in sam.addons_monitor.addons.items():
        if data.state:
            sam.msg.console('   - Loaded %s' % data.name)
            es.load('sam/addons/' + data.basename)


def unload():
    # Unload Addons & save Addons Monitor database
    sam.msg.console('* Unloading Addons:')
    for addon, data in sam.addons_monitor.addons.items():
        if data.state:
            es.unload('sam/addons/' + data.basename)
            sam.msg.console('   - Unloaded %s' % data.name)
    sam.addons_monitor.save_database()


def module_menu(uid, send=True):
    if not sam.admins.can(uid, 'addons_monitor'):
        sam.home_page(uid)
        return
    page = sam.Menu('addons_monitor', addons_monitor_HANDLE, 'home_page')
    page.title('Addons Monitor')
    for name in sorted(sam.addons_monitor.addons.keys()):
        addon = sam.addons_monitor(name)
        text = addon.name + ' '
        if addon.state:
            text = text + '[running]'
        page.add_option(name, text, addon.locked and not sam.admins.can(uid, 'super_admin'))
    page.footer('Locked Addons can only be',
                'accessed by Super Admins')
    if send:
        page.send(uid)


def addons_monitor_HANDLE(uid, choice, prev_page):
    addon = sam.addons_monitor(choice)
    page = sam.Menu('monitor', monitor_HANDLE, prev_page)
    page.title('Addons Monitor')
    page.description(' - NAME: ' + addon.name,
                     ' - VERSION: %s' % addon.version,
                     ' - DESCRIPTION:\n' +
                     '\n'.join(addon.description) if addon.description else '')
    page.add_line('Toggle Addon State:')
    page.add_option((choice, 'state', prev_page),
                '[enabled] |  disabled' if addon.state else 'enabled  | [disabled]')
    if sam.admins.can(uid, 'super_admin'):
        page.add_line('Toggle Lock State:')
        page.add_option((choice, 'locked', prev_page),
                    '[locked] |  unlocked' if addon.locked else 'locked   | [unlocked]')
    if choice in sam.settings.default['Addons Settings']:
        page.separator()
        page.add_option((choice, 'settings_help', prev_page), 'Settings Help Window')
    page.send(uid)


def monitor_HANDLE(uid, choice, prev_page):
    addon, key, previous = choice
    if key == 'settings_help':
        sam.settings.info_window(uid, addon)
    else:
        if key == 'state':
            if sam.addons_monitor(addon).state:
                es.unload('sam/addons/' + addon)
                if addon in sam.HOME_PAGE_ADDONS:
                    sam.HOME_PAGE_ADDONS.remove(addon)
            else:
                es.load('sam/addons/' + addon)
        sam.addons_monitor.addons[addon].__dict__[key] = \
            not sam.addons_monitor.addons[addon].__dict__[key]
    sam.home_page(uid)
    sam.handle_choice(3, uid)
    addons_monitor_HANDLE(uid, addon, previous)
