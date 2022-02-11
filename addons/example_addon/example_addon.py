import es
import psyco
psyco.full()

# [Mandatory] Import SAM script for access to all core systems and functions
sam = es.import_addon('sam')
# By appending the Addon's basename to HOME_PAGE_ADDONS we're telling SAM to list this addon
# in the home page options, when chosen, addon_page function from said Addon will be called
sam.HOME_PAGE_ADDONS.append('example_addon')


def addon_page(uid):
    ''' This is where the Addon's main page should be built and sent from '''

    page = sam.PageSetup('example_addon', example_addon_HANDLE, 'home_page')
    # Give the page a title, usually the name of the module/addon the user is in.
    page.title('Example Addon')
    # Description of the page (supports multiple lines)
    page.description('This page showcases various features SAM provides',
                     'Choose an option:')
    # Start giving the page some options
    page.option('colors', 'Chat Colors Showcase')
    page.option('hud', 'Hudhint Example')
    page.option('motd', 'MOTD Link Example (google.com)')
    # Blocked option remain there, but can't be chosen
    page.option(None, 'Blocked Option Example', True)
    # Call makes the page to go to the next subpage
    page.next_subpage()
    # Its possible to add one, or multiple lines between options
    page.newline('This is just to show',
                 'you can add multiple',
                 'lines in between options')
    # Adds a separator line
    page.separator()
    # Lines can be used as small descriptions of the options that follows them
    page.newline('Choose a number:')
    for num in (1, 2, 3):
        page.option(num, num)
    page.footer('{Page Footer}')
    page.send(uid)

def example_addon_HANDLE(uid, choice, prev_page):
    ''' In this example the user will be sent back the same
        page and subpage he was in, regardless of his choice. '''

    # prev_page keeps the previous page information, this way you not only know what page the user
    # used, but can also be modified, or like in this case, return the user to the exact same page.
    # Note: The page isn't rebuilt, this means if the page had info that can change in real-time,
    #       the page will be sent exactly as it was. An example to rebuild the page was to just
    #       call the previous page function, say in this case:
#   addon_page(uid)
    prev_page.return_page(uid)

    # Will showcase all the available chat colors in one single chat message
    if choice == 'colors':
        colors = ['#%s%s' % (color, color) for color in sam.msg.chat_colors.keys()]
        colors = [colors[i:i + 6] for i in xrange(0, len(colors), 6)]
        sam.msg.tell('#all', 'Chat Colors Showcase:')
        for chunck in colors:
            sam.msg.tell('#all', '#white, '.join(chunck), log=False)
    # Example of a center hud message
    elif choice == 'hud':
        sam.msg.hud(uid, 'This is what a Hud message looks like.')
    # Example of webpage sent in a MOTD type message
    elif choice == 'motd':
        sam.msg.motd(uid, 'MOTD Example (google.com)', 'https://www.google.com/')
    elif isinstance(choice, int):
        sam.msg.hud(uid, 'You have chosen the number: %s' % choice)