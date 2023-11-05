import es
import psyco

psyco.full()

sam = es.import_addon('sam')
monitor = sam.addons_monitor

def load():
    
    # Load Addons
    sam.msg.console('  * Loading Addons:')

    for addon in monitor.get_addons():
        # Check if the addon is enabled
        if addon.state:
            # Load the addon
            monitor.load_addon(addon.basename)


def unload():
    
    # Unload Addons
    sam.msg.console('  * Unloading Addons:')

    for addon in monitor.get_addons():
        # Check if the addon is enabled
        if addon.state:
            # Unload the addon
            monitor.unload_addon(addon.basename)


def module_menu(userid):
    
    # Check if the user is allowed to use this module
    if not sam.admins.is_allowed(userid, 'addons_monitor'):
        sam.home_page(userid)
        return
    
    # Verify for new installed addons
    monitor.verify_for_new_addons()

    menu = sam.Menu('addons_monitor', addons_monitor_HANDLE, 'home_page')
    menu.max_lines = 5
    menu.title('Addons Monitor')
    menu.description('Select an Addon:')

    # Add each addon as an option, with its state and lock state
    for addon in sorted(monitor.get_addons(), key=lambda x: x.name):
        state = '[running]' if addon.state else ''
        locked = '[locked]' if addon.locked else ''
        menu.add_option(addon.basename, addon.name + ' ' + state + locked)

    menu.footer('Locked Addons can only be',
                'accessed by Super Admins')
    menu.send(userid)


def addons_monitor_HANDLE(userid, choice, submenu):
    
    menu = sam.Menu('monitor', monitor_HANDLE, submenu)
    menu.title('Addons Monitor')
    
    # Get the addon object
    addon = monitor.get_addon(choice)
    
    # Add the addon's information as a description
    menu.description(
        ' - NAME: ' + addon.name,
        ' - VERSION: %s' % addon.version,
        ' - DESCRIPTION:\n' +
        '\n'.join(addon.description) if addon.description else ''
    )

    # Add the option to toggle the Addon state
    menu.add_line('Toggle Addon State:')
    menu.add_option(
        (addon, 'state'),
        '[enabled] |  disabled' if addon.state else 'enabled  | [disabled]'
    )

    # Add the option to toggle the Addon lock state, if the user is a super admin
    if sam.admins.is_super_admin(userid):
        menu.add_line('Toggle Lock State:')
        menu.add_option(
            (addon, 'locked'),
            '[locked] |  unlocked' if addon.locked else 'locked  | [unlocked]'
        )
    
    # Add the option to view the Addon's settings
    settings = sam.settings
    if addon.basename in settings.settings[settings.modules]:
        menu.separator()
        menu.add_option((addon, 'settings'), 'Settings Help Window')
        
    # Send the menu
    menu.send(userid)


def monitor_HANDLE(userid, choice, submenu):
    
    addon, key = choice

    # If key is settigns, send the Addon's settings help window
    if key == 'settings':
        sam.settings.help_window(userid, addon.basename)
        submenu.send(userid)
        return
    
    # Load/Unload the addon if the key is the Addon's state
    if key == 'state':
        if addon.state:
            monitor.unload_addon(addon.basename)
        else:
            monitor.load_addon(addon.basename)

        # Save the database
        monitor.save_database()
    
    # Return the user to the Addon monitor, rebuilding the menu
    sam.home_page(userid)
    addons_monitor_HANDLE(userid, addon.basename, 'addons_monitor')