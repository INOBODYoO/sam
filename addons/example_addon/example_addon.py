import es
import psyco
psyco.full()

# [Mandatory] Import SAM script for access to all core systems and functions
sam = es.import_addon('sam')
# By appending the Addon's basename to HOME_PAGE_ADDONS we're telling SAM to list this addon
# in the home options, when chosen, addon_menu function from said Addon will be called
sam.HOME_PAGE_ADDONS.append('example_addon')


def addon_menu(uid):
    ''' This is where the Addon's main menu should be built and sent from '''

    menu = sam.Menu('example_addon', example_addon_HANDLE, 'home_page')
    # Give the menu a title, usually the name of the module/addon the user is in.
    menu.title('Example Addon')
    # Description of the menu (supports multiple lines)
    menu.description('This menu showcases various features SAM provides',
                     'Choose an option:')
    # Start giving the menu =some options
    menu.add_option('colors', 'Chat Colors Showcase')
    menu.add_option('hud', 'Hudhint Example')
    menu.add_option('motd', 'MOTD Link Example (google.com)')
    # Blocked add_option remain there, but can't be chosen
    menu.add_option(None, 'Blocked Option Example', True)
    # Call makes the menu =to go to the next page
    menu.next_page()
    # Its possible to add one, or multiple lines between options
    menu.add_line('This is just to show',
                  'you can add multiple',
                  'lines in between options')
    # Adds a separator line
    menu.separator()
    # Lines can be used as small descriptions of the options that follows them
    menu.add_line('Choose a number:')
    for num in (1, 2, 3):
        menu.add_option(num, num)
    menu.footer('{Footer}')
    menu.send(uid)

def example_addon_HANDLE(uid, choice, submenu):
    ''' In this example the user will be sent back the same
        menu =and menu =he was in, regardless of his choice. '''

    # submenu keeps the previous menu information, this way you not only know what menu the user
    # used, but can also be modified, or like in this case, return the user to the exact same menu.
    # Note: The menu isn't rebuilt, this means if the menu had info that can change in real-time,
    #       the menu will be sent exactly as it was. An example to rebuild the menu was to just
    #       call the previous menu function, say in this case:
#   addon_menu(userid)
    submenu.send(uid)

    # Will showcase all the available chat colors in one single chat message
    if choice == 'colors':
        colors = ['#%s%s' % (color, color) for color in sam.msg.colors.keys()]
        colors = [colors[i:i + 6] for i in xrange(0, len(colors), 6)]
        sam.msg.tell('#all', 'Chat Colors Showcase:')
        for chunck in colors:
            sam.msg.tell('#all', '#white, '.join(chunck), log=False)
    # Example of a center hud message
    elif choice == 'hud':
        sam.msg.hud(uid, 'This is what a Hud message looks like.')
    # Example of web menu sent in a MOTD type message
    elif choice == 'motd':
        sam.msg.motd(uid, 'MOTD Example (google.com)', 'https://www.google.com/')
    elif isinstance(choice, int):
        sam.msg.hud(uid, 'You have chosen the number: %s' % choice)