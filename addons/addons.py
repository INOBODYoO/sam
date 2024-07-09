import es
import psyco

psyco.full()

sam = es.import_addon('sam')
monitor = sam.addons_monitor

def load():

    sam.msg.console('  * Loading Addons:')
    
    # Load Addons
    for addon in monitor.addons_list():
        if addon.state and not monitor.is_loaded(addon.basename):
            monitor._load_addon(addon.basename)


def unload():
    
    sam.msg.console('  * Unloading Addons:')

    # Unload Addons
    for addon in monitor.addons_list():
        if addon.state and monitor.is_loaded(addon.basename):
            monitor._unload_addon(addon.basename)


def module_menu(userid):
    
    # Check if the user is allowed to use this module
    if not sam.admins.is_allowed(userid, 'addons_monitor'):
        sam.home_page(userid)
        return
    
    # Update installed addons
    monitor._update_installed_addons()
    addons_list = monitor.addons_list()
    
    # Check if there are any Addons installed
    if not addons_list:
        sam.msg.hud(userid, 'There are no Addons installed!')
        sam.home_page(userid)
        return

    # Initialize the menu
    menu = sam.Menu('addons_monitor', addons_monitor_HANDLE, 'home_page')
    menu.max_lines = 5
    menu.build_function = module_menu
    menu.title('Addons Monitor')
    menu.description('Select an Addon:')

    # Add each addon, displaying its state and lock state
    for addon in sorted(addons_list, key=lambda x: x.name):
        state = '[loaded]' if addon.state else ''
        locked = '[locked]' if addon.locked else ''
        menu.add_option(
            addon.basename,
            '%s %s%s' % (addon.name, state, locked),
            addon.locked and not sam.admins.is_super_admin(userid)
        )
    
    menu.locked_option_message = 'Only super admins can manage locked addons!'
    menu.send(userid)


def addons_monitor_HANDLE(userid, choice, submenu):
    
    menu = sam.Menu('monitor', monitor_HANDLE, submenu)
    menu.title('Addons Monitor')
    menu.build_function = addons_monitor_HANDLE
    menu.build_arguments_list = (userid, choice, submenu)
    
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

    # If the user is a super admin, add the option to toggle the Addon lock state
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
        menu.add_option((addon, 'settings'), 'View Addon Settings')
        
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
            monitor._disable_addon(addon.basename)
        else:
            monitor._enable_addon(addon.basename)

    elif key == 'locked':
        monitor.addons[addon.basename].locked = not monitor.addons[addon.basename].locked

    # Save the database
    monitor.save_database()
        
    # Since values have been changed, we also must rebuild the Addons List page
    # to display the updated values
    sam.menu_system.send_menu(
        userid,
        menu_id='addons_monitor',
        page=submenu.object.submenu_page,
        rebuild=True,
        rebuild_arguments=(userid,)
    )
    
    # We can now send the rebuilt Monitor page back to the user 
    submenu.send(userid, rebuild=True)
    