import es
import psyco
psyco.full()

sam   = es.import_addon('sam')
file  = sam.path.core + '/required/server_rules.txt'
rules = ['// SAM - Server Rules',
         '// ',
         '// Each line below represents a server rule to be displayed in the !rules page:',
         '// - To add/remove a rule, simply add/remove a line',
         '// - When done editing the file simply save it,',
         '//   its not necessary to reload the plugin, the file is read in real-time.\n',
         'Do not disrespect other players or Admins',
         'Do not spam the chat',
         'Do not abuse of the voice chat (i.e: loud noises, playing music/sounds)',
         'Do not abuse of a known game/map bug',
         'Cheating is forbidden']

sam.settings.addon_config('server_rules', {
    'display_on_player_activate': {
        'desc': ['Sends the rules page as soon as the player connects the server'],
        'default': False
    },
    'footer_message': {
        'desc': ['Message to display in the bottom of the page',
                 'Setting to false will disable the footer entirely.'],
        'default': ['Disrespecting these rules may lead to',
                    'a kick or even ban from the server.']
    }
})

def load():

    # Create file if not existent
    sam.write_file(file, rules)

    # Create addon command
    sam.cmds.chat('rules', addon_page)

def unload():

    sam.cmds.delete('rules')

# Addon Page
def addon_page(uid, args=None):
    page = sam.PageSetup('server_rules', server_rules_HANDLE)
    page.header_text = False
    page.title('Server Rules')
    page.options(sam.read_file(file, rules))
    footer = sam.settings('server_rules').footer_message
    try:
        if footer: page.footer(*footer)
    except: pass
    page.send(uid)

def server_rules_HANDLE(uid, choice, prev_page):
    prev_page.return_page(uid)

# Game Events
def player_activate(ev):
    if sam.settings('server_rules').display_on_player_activate:
        addon_page(ev['userid'])