import es
import psyco

psyco.full()

sam = es.import_addon('sam')

settings = sam.settings
general = settings.general
modules = settings.modules


def module_menu(userid):

    # Check if the user is allowed to use this module
    if not sam.admins.is_allowed(userid, 'settings_manager'):
        sam.home_page(userid)
        return

    menu = sam.Menu('settings_manager', settings_manager_HANDLE, 'home_page')
    menu.title('Settings Manager')
    
    # Add the General Settins option
    menu.add_option(general, general)
    
    # Get the registered modules list
    modules_list = settings(modules).keys()
    
    # If there are any registered modules
    if modules_list:
        menu.separator()
        menu.add_line(modules)

        # Add each registered module as an option
        for module in sorted(modules_list):
            menu.add_option(module, sam.title(module))
            
    menu.send(userid)


def settings_manager_HANDLE(userid, choice, submenu):

    titled = sam.title(choice)

    menu = sam.Menu('settings_list', settings_list_HANDLE, submenu)
    menu.maxline = 5
    menu.title(titled)
    
    # Get the section settings
    section = settings(choice) if choice == general else settings(modules)[choice]
    titled = sam.title(choice)

    # Lambda function to convert boolean values to strings
    f = lambda value: 'Enabled' if value else 'Disabled'
    
    boolean_count = 0

    # Add each setting as an option
    for setting, value in section.items():
        if isinstance(value['current_value'], bool):
            boolean_count += 1
            menu.add_option(
                (choice, value), sam.title(setting) + ': ' + f(value['current_value'])
            )

    # Add a note if there are toggle-able settings
    if not boolean_count:
        menu.add_line(
            'There are no toggle-able settings',
            'available for this Module/Addon.',
            ' ',
            'Please check the help window for',
            'more information.'
            ' ',
        )

    # Add the help window option
    menu.separator()
    menu.add_option((choice, 'help'), titled + ' Help Window')

    # Send the menu
    menu.send(userid)


def settings_list_HANDLE(userid, choice, submenu):
    
    # Get the choice data
    section, value = choice
    
    # If the user choose the help option, send the help window
    if value == 'help':
        sam.settings.help_window(userid, section)
        submenu.send(userid)
        return
    
    # Otherwise, toggle the setting value
    value['current_value'] = not value['current_value']

    # Save the database
    sam.settings.save_database(update=False)

    # Send the user back the page
    settings_manager_HANDLE(userid, section, 'settings_manager')
    sam.menu_system.send_menu(userid, submenu.menu_id, submenu.page)
