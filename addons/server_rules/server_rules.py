import os
import es
import psyco

psyco.full()

sam = es.import_addon('sam')
rules_file = sam.path.core + '/required/server_rules.txt'
default_file = [
    "// SAM - Server Rules",
    "//",
    "// This file contains the server rules to be displayed on the !rules page:",
    "//",
    "// - To add or remove a rule, simply add or remove a line.",
    "// - Changes made to this file are read in real-time and do\
        not require reloading the plugin.",
    " ",
    "Do not disrespect other players or administrators.",
    "Do not excessively spam the chat.",
    "Do not abuse the voice chat by making loud noises or playing music/sounds.",
    "Do not exploit any known game or map bugs.",
    "Cheating is strictly forbidden."
]

sam.settings.addon_config('server_rules', {
    'display_on_player_activate': {
        'description': [
            'Specifies if to send rules on player connect.'
        ],
        'current_value': False
    },
    'footer_message': {
        'description': [
            'Message at the bottom of the rules page.',
            'Set to False to disable the footer.'
        ],
        'current_value': [
            'Disrespecting rules may result in kick or ban.'
        ]
    }
})


def load():

    # Create file if not existent
    if not os.path.exists(rules_file):
        sam.write_file(rules_file, default_file)

    # Create addon command
    sam.cmds.chat('rules', addon_menu)


def unload():

    # Delete the command
    sam.cmds.delete('rules')


# Addon Page
def addon_menu(userid, args=None):
    
    menu = sam.Menu('server_rules')
    menu.header_text = False
    menu.title('Server Rules')
    
    # Read the rules file, and add each rule as an enumerated option
    menu.add_options(enumerate(sam.read_file(rules_file, rules)))

    # Add the footer message
    footer = sam.settings('server_rules').footer_message.get('current_value')
    if footer:
        menu.footer(*footer)

    # Send the menu
    menu.send(userid)


# Game Events
def player_activate(ev):
    
    # Display the rules on player connect
    if sam.settings('server_rules').display_on_player_activate:
        addon_menu(ev['userid'])
