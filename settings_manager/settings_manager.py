import es
import psyco

psyco.full()

sam = es.import_addon('sam')

# Global Variables
GEN = 'General Settings'
ADD = 'Addons Settings'


def module_menu(userid):

    # Check if the user is allowed to use this module
    if not sam.admins.is_allowed(userid, 'settings_manager'):
        sam.home_page(userid)
        return

    menu = sam.Menu('settings_manager', settings_manager_HANDLE, 'home_page')
    menu.title('Settings Manager')
    
    # Add the general settings option
    menu.add_option(GEN, GEN)
    
    # Add added Addons as options
    addons_list = sam.settings(ADD)
    if addons_list:
        menu.separator()
        menu.add_line('Addons Settings:')
        for addon in addons_list.keys():
            menu.add_option(addon, sam.title(addon))
    menu.send(userid)


def settings_manager_HANDLE(userid, choice, submenu):

    titled = sam.title(choice)
    
    # Update the settings database before hand
    sam.settings.update_settings()

    menu = sam.Menu('settings_list', settings_list_HANDLE, submenu)
    menu.maxline = 5
    menu.title(titled)
    
    # Get the section settings
    settings = sam.settings(choice) if choice == GEN \
        else sam.settings.settings[ADD][choice]
    
    # Add each setting as an option
    for setting, data in settings.items():
        menu.add_option(
            (choice, data),
            '%s: %s' % (sam.title(setting),
                        'Enabled' if data['current_value'] else 'Disabled')
        ),

    # Add the help window option
    menu.separator()
    menu.add_option((choice, 'help'), titled + ' Help Window')

    # Send the menu
    menu.send(userid)


def settings_list_HANDLE(userid, choice, submenu):
    
    section, data = choice
    
    # If the user choose the help option, send the help window
    if data == 'help':
        sam.settings.help_window(userid, section)
        submenu.send(userid)
        return

    # Otherwise, toggle the setting value
    data['current_value'] = not data['current_value']

    # Save the database
    sam.settings.save_database()

    # Send the user back the page
    settings_manager_HANDLE(userid, section, 'settings_manager')
    sam.send_menu(userid, submenu.menu_id, submenu.page)
