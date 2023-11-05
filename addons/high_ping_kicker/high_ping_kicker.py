#!/usr/bin/python
# -*- coding: utf-8 -*-

import es
import psyco

psyco.full()

sam = es.import_addon('sam')

# Global variables
WARNINGS = {}

# Addon Config
sam.settings.module_config(
    'high_ping_kicker',
    {
        'minimum_ping_limit': {
            'description': (
                'The minimum ping before the player starts being warned',
            ),
            'current_value': 120
        },
        'maximum_warnings': {
            'description': (
                'The maximum number of warnings before the player is kicked',
            ),
            'current_value': 3
        },
        'ban_length': {
            'description': (
                'The length of the ban, in minutes',
            ),
            'current_value': 5
        },
        'warning_interval': {
            'description': (
                'The interval, in seconds, between warnings sent to players',
            ),
            'current_value': 60
        }
    }
)

def high_ping_kicker_loop():

    # Settings
    settings = sam.settings('high_ping_kicker')

    # Loop the function
    sam.delay_task(
        settings.warning_interval, 'sam_high_ping_kicker_loop', high_ping_kicker_loop, ()
    )

    # Loop through all human players
    for player in sam.player_list('#human'):

        # If the player's ping is greater than 80
        if player.ping >= settings.minimum_ping_limit:

            # Get the player's steamid
            steamid = player.steamid

            # If the player has not been warned yet, set their warning to 0
            if steamid not in WARNINGS.keys():
                WARNINGS[steamid] = 0

            # Add one to the player's warning
            WARNINGS[steamid] += 1

            # Send a warning page to the player
            if WARNINGS[steamid] < settings.maximum_warnings + 1:
                menu = sam.Menu('high_ping_kicker')
                menu.header_text = False
                menu.title('High Ping Kicker')
                menu.add_line('Warning: Your ping is too high!')

                # Get the warning message, according to the number of warnings
                warning_msg = get_warning_msg(WARNINGS[steamid])
                if WARNINGS[steamid] == settings.maximum_warnings:
                    warning_msg = warning_msg + ' and final'

                menu.add_line('This is your %s warning!' % warning_msg)

                menu.timeout = 10
                menu.send(player)
                continue

            elif sam.addons_monitor.is_running('ban_manager'):
                
                ban_length = settings.ban_length

                # Import the ban_manager addon
                ban_manager = sam.addons_monitor.import_addon('ban_manager')
                ban_manager.ban(
                    {
                        'steamid': steamid,
                        'name': player.name,
                        'admin': 'SAM (High Ping Kicker Addon)',
                        'date': sam.get_time('%m/%d/%Y at %H:%M:%S'),
                        'expiry_date': ban_length * 60 + sam.timestamp(),
                        'length_text': '%s Minutes' % ban_length,
                        'reason': 'High Ping (After %s Warnings)' % settings.maximum_warnings
                    }
                )
            else:
                # If the ban_manager addon is not running, kick the player
                player.kick('You were kicked from the server! (Reason: High Ping)')

            # Reset the player's warning
            del WARNINGS[steamid]

# Unload
def unload():

    # Cancel the loop
    sam.cancel_delay('sam_high_ping_kicker_loop')

# Functions
def get_warning_msg(num):
    if num == 1:
        return 'first'
    elif num == 2:
        return 'second'
    elif num == 3:
        return 'third'
    else:
        return '%dth' % num

# Game Events
def es_map_start(event_var):

    # Reset the warnings
    WARNINGS.clear()


# Start the loop
high_ping_kicker_loop()
