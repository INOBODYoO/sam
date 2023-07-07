import es
import psyco

psyco.full()

sam = es.import_addon('sam')
monitor = sam.addons_monitor


def load():
    
    # Load Addons
    sam.msg.console('* Loading Addons:')
    for addon in monitor.addons.values():
        if addon.state:
            sam.msg.console('   - Loaded %s' % addon.name)
            es.load('sam/addons/' + addon.basename)


def unload():
    
    # Unload Addons
    sam.msg.console('* Unloading Addons:')
    for addon in monitor.addons.values():
        if addon.state:
            es.unload('sam/addons/' + addon.basename)
            sam.msg.console('   - Unloaded %s' % addon.name)
            
    # Save the database
    monitor.save_database()


def module_menu(userid):
    
    # Check if the user is allowed to use this module
    if not sam.admins.is_allowed(userid, 'addons_monitor'):
        sam.home_menu(userid)
        return

    menu = sam.Menu('addons_monitor', addons_monitor_HANDLE, 'home_page')
    menu.title('Addons Monitor')
    menu.description('Select an Addon to open its monitor:')

    # Add each addon as an option, with its state and lock state
    for addon in sorted(monitor.addons.values(), key=lambda x: x.name):
        state = '[running]' if addon.state else ''
        locked = '[locked]' if addon.locked else ''
        menu.add_option(addon.basename, addon.name + ' ' + state + locked)

    menu.footer('Locked Addons can be accessed only by Super Admins')
    menu.send(userid)


def addons_monitor_HANDLE(userid, choice, submenu):
    
    menu = sam.Menu('monitor', monitor_HANDLE, submenu)
    menu.title('Addons Monitor')
    
    # Get the addon object
    addon = sam.addons_monitor(choice)
    
    # Add the addon's information as a description
    menu.description(' - NAME: ' + addon.name,
                     ' - VERSION: %s' % addon.version,
                     ' - DESCRIPTION:\n' +
                     '\n'.join(addon.description) if addon.description else '')
    
    # Add the option to toggle the Addon state
    menu.add_line('Toggle Addon State:')
    menu.add_option((choice, 'state'),
                    '[enabled] |  disabled' if addon.state else 'enabled  | [disabled]')

    # Add the option to toggle the Addon lock state, if the user is a super admin
    if sam.admins.is_super_admin(userid):
        menu.add_line('Toggle Lock State:')
        menu.add_option(
            (choice, 'locked'),
            '[locked] |  unlocked' if addon.locked else 'locked  | [unlocked]'
        )
    
    # Add the option to view the Addon's settings
    settings = sam.settings
    if choice in settings.settings[settings.modules]:
        menu.separator()
        menu.add_option((choice, 'settings'), 'Settings Help Window')
        
    # Send the menu
    menu.send(userid)


def monitor_HANDLE(userid, choice, submenu):
    
    addon, key = choice

    # If key is settigns, send the Addon's settings help window
    if key == 'settings':
        sam.settings.help_window(userid, addon)
        submenu.send(userid)
        return

    # Get the addon object
    addon = sam.addons_monitor.addons[addon]
    
    # Load/Unload the addon if the key is the Addon's state
    if key == 'state':
        if addon.state:
            es.unload('sam/addons/' + addon.basename)
            if addon.basename in sam.HOME_PAGE_ADDONS:
                sam.HOME_PAGE_ADDONS.remove(addon)
            sam.msg.console('Unloaded ' + addon.name, 'Addons Monitor')
        else:
            es.load('sam/addons/' + addon.basename)
            sam.msg.console('Loaded ' + addon.name, 'Addons Monitor')
            
    # Toggle the key value
    addon.__dict__[key] = not addon.__dict__[key]
    
    # Return the user to the Addon monitor, rebuilding the menu
    sam.home_page(userid)
    module_menu(userid)
    addons_monitor_HANDLE(userid, addon.basename, 'addons_monitor')
