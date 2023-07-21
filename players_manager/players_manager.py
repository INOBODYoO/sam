# Python Imports
from random import randint as rint
import psyco
psyco.full()

# Eventscripts Imports
import es
import usermsg

# Global Variables
sam = es.import_addon('sam')
effects = {}
setprop = es.setplayerprop
lifestate = 'CBasePlayer.m_lifeState'

# Module Classes
class _PenaltiesClass:


    @staticmethod
    def kick(target, reason='You were kicked from the server!', notify=True):

        target.kick(reason)
        msg('%s has been #salmonkicked #beigefrom the server!' % get_name(target), notify)
        msg('#gray[Reason: #silver%s#gray]' % reason, notify)


    @staticmethod
    def kill(target, notify=True):

        if is_alive(target):
            target.kill()
            msg('%s #beigehas been #salmonkilled' % get_name(target), notify)


    @staticmethod
    def respawn(target, notify=True):

        def respawn_player(player):
            userid = int(player)
            setprop(userid, 'CCSPlayer.m_iPlayerState', 0)
            setprop(userid, lifestate, 0)
            es.server.insertcmd('es_xspawnplayer %d' % userid)

        # If target is one of the teams, then loop though all players and respawn them
        if target in sam.FILTERS:
            for player in sam.player_list(target):
                respawn_player(player)
        # Otherwise, respawn the target player
        else:
            respawn_player(target)
        
        msg('%s #beigehas/have been #greenrespawned' % get_name(target), notify)


    @staticmethod
    def strip_weapon(target, notify=True):
        
        # Check if target is alive and is holding anything but the knife
        if is_alive(target) and target.weapon != 'weapon_knife':
            es.sexec(target, 'drop')
            msg('%s\'s #beigeweapon have been #greenstripped' % get_name(target), notify)


    @staticmethod
    def set_firework(target, notify=True):
        
        # Check if the target is alive
        if not is_alive(target):
            return
        
        # Give the target an id for the firework effect
        var = 'firework_%s' % target

        def explosion(target, notify=True):
            """
            Helper function to make an explosion animation
            on the target player with some spark effects
            """
            
            vector = es.createvectorstring(target.location)
            es.server.queuecmd('es_xeffect sparks %s 9999 10 0,0,0' % vector)
            play(target, 'weapons/hegrenade/explode4.wav')
            target.kill()

        # Emit a sound on the target player, as a lift off sound,
        # and shake the player screen as it was turbulence
        play(target, 'weapons/physgun_off.wav')
        usermsg.shake(target, 85, 2)

        # Create a gradual pushing effect, to push the player up in the air
        push_ammount = 35
        for miliseconds in (x * 0.1 for x in range(1, 12)):
            sam.delay_task(miliseconds, var, push, (target, 0, 0, push_ammount))
            push_ammount += 35

        # Create a beeping sound just before the explosion
        sound = (target, 'weapons/c4/c4_beep1.wav')
        sam.delay_task(1.4, var, play, sound)
        sam.delay_task(1.5, var, play, sound)
        
        # Create the explosion effect
        sam.delay_task(1.7, var, explosion, target)

        msg('%s #beigeis now a #salmonfirework' % get_name(target), notify)


    @staticmethod
    def slap(target, damage=0, notify=True):
        
        # Check if the target is alive
        if not is_alive(target):
            return
        
        # Damage the player with the specified amount
        es.server.insertcmd('damage %s %s' % (target, damage))
       
        # Create a pushing montion to the player to random directions
        push(target, rint(-300, 300), rint(-300, 300), rint(300, 300))
        
        # Emit a sound on the player location
        play(target, 'player/damage%s.wav' % rint(1, 3))
        
        # Notify the players of the action
        msg(
            '%s has been #salmonslapped #beigewith #salmon%s #beigedamage' \
            % (get_name(target), damage),
            notify
        )



    @staticmethod
    def blind(target, notify=True):
        
        # Check if the target is alive
        if not is_alive(target):
            return
        
        userid = target.userid
        
        # Get the target effects object
        effect = effects[userid]

        # If the target is already blind, then cancel the loop
        if effect.blind:
            sam.cancel_delay('blind_%s' % userid)
            text = '%s is no longer #salmonblind' % get_name(target)
        # Otherwise, start the loop
        else:
            blind_effect_loop(userid)
            text = '%s is now #salmonblind' % get_name(target)
            
        # Toggle the blindness effect
        effect.blind = not effect.blind
        
        msg(text, notify)


    @staticmethod
    def give_jetpack(target, notify=True):
        
        # Check if the target is alive
        if not is_alive(target):
            return

        # Get the target effects object
        effect = effects[int(target)]

        # If the target is already on jetpack mode, then cancel the loop
        if effect.jetpack:
            target.jetpack(False)
            text = '%s is no longer on #greenJetpack Mode' % get_name(target)
        # Otherwise, 
        else:
            target.jetpack(True)
            text = '%s is now on #greenJetpack Mode' % get_name(target)
            
        # Toggle the jetpack effect
        effect.jetpack = not effect.jetpack
        
        msg(text, notify)


    @staticmethod
    def give_godmode(target, notify=True):
        
        # Check if the target is alive
        if not is_alive(target):
            return
        
        # Get the target effects object
        effect = effects[int(target)]

        # If the target is already on god mode, toggle it off
        if effect.godmode:
            target.godmode(False)
            text = '%s is no longer on #greenGod Mode' % get_name(target)
        # Otherwise, toggle it on
        else:
            target.godmode(True)
            text = '%s is now on #greenGod Mode' % get_name(target)
        
        # Toggle the god mode
        effect.godmode = not effect.godmode
        
        msg(text, notify)


    @staticmethod
    def give_noclip(target, notify=True):
        
        # Check if the target is alive
        if not is_alive(target):
            return
        
        # Get the target effects object
        effect = effects[int(target)]
        
        # If the target is already on noclip, toggle it off
        if effect.noclip:
            target.noclip(False)
            text = '%s is no longer on #greenNo Clip Mode' % get_name(target)
        # Otherwise, toggle it on
        else:
            target.noclip(True)
            text = ' %s is now on #greenNo Clip Mode' % get_name(target)

        # Toggle the noclip mode
        effect.noclip = not effect.noclip

        msg(text, notify)


    @staticmethod
    def give_drugs(target, notify=True):
        
        # Check if the target is alive
        if not is_alive(target):
            return
        
        # Get the target effects object
        effect = effects[int(target)]
        
        # If the target is already on drugs, stop the target loop
        if effect.ondrugs:
            sam.cancel_delay('drugs_%s' % target)
            text = '%s is now on #greenDrugs' % get_name(target)
        # Otherwise, start the target loop
        else:
            drugs_effect_loop(target)
            text = '%s is no longer on #greenDrugs' % get_name(target)
        
        # Toggle the drugs effect
        effect.ondrugs = not effect.ondrugs
        
        msg(text, notify)


    @staticmethod
    def freeze(target, notify=True):
        
        # Check if the target is alive
        if not is_alive(target):
            return

        # Get the object from the effect dictionary
        effect = effects[int(target)]

        # Construct a message indicating the new state
        if target.freeze:
            text = '%s is no longer #greenfrozen' % get_name(target)
        else:
            text = '%s is now #greenfrozen' % get_name(target)

        # Toggle the freeze effect and freeze/unfreeze the player
        target.freeze = not target.freeze
        effect.frozen = target.freeze
        
        msg(text, notify)


    @staticmethod
    def burn(target, notify=True):
        
        # Check if the target is alive
        if not is_alive(target):
            return

        # Get the target effects object
        effect = effects[int(target)]
        
        if is_alive(target) and not effect.onfire:
            target.burn()
            effect.onfire = True
            msg('%s is now on #salmonfire' % get_name(target))


    @staticmethod
    def set_cash(target, amount, notify=True):

        # If target is one of the teams
        if target in sam.FILTERS:
            for player in sam.player_list(target):
                player.cash = amount
        # Otherwise, set the target player cash
        else:
            target.cash = amount
            
        msg('%s cash set to #green%s$' % (get_name(target), amount), notify)


    @staticmethod
    def set_health(target, amount, notify=True):    

        # Whether to send the message or not
        send = False
        
        # If target is one of the teams
        if target in sam.FILTERS:
            for player in sam.player_list(target):
                if is_alive(player):
                    player.health = amount
            send = True
        # Otherwise, set the target player health
        elif is_alive(target):
            target.health = amount
            send = True
        
        if send:  
            msg(
                '%s health set to #green%s HP' % (get_name(target), amount),
                notify
            )


penalty = _PenaltiesClass()

class PlayerEffects:
    """
    Class to hold all the effects of a player and their states
    """
    
    def __init__(self, userid):
        self.userid = userid
        self.blind = False
        self.onfire = False
        self.noclip = False
        self.frozen = False
        self.ondrugs = False
        self.godmode = False
        self.jetpack = False

    def remove_all(self):
        """
        Removes all effects from the target player
        """
        
        player = sam.get_player(self.userid)
        if not player:
            return
        if self.blind:
            penalty.blind(player)
        if self.frozen:
            penalty.freeze(player)
        if self.noclip:
            penalty.give_noclip(player)
        if self.ondrugs:
            penalty.give_drugs(player)
        if self.godmode:
            penalty.give_godmode(player)
        if self.jetpack:
            penalty.give_jetpack(player)
        if self.onfire:
            self.onfire = False

# Commands Handlers
def kick_CMD(userid, args):
    commands_filter(userid, args, 1)


def kill_CMD(userid, args):
    commands_filter(userid, args, 2)


def slap_CMD(userid, args):
    commands_filter(userid, args, 3)


def respawn_CMD(userid, args):
    commands_filter(userid, args, 4)


def strip_CMD(userid, args):
    commands_filter(userid, args, 5)


def freeze_CMD(userid, args):
    commands_filter(userid, args, 6)


def noclip_CMD(userid, args):
    commands_filter(userid, args, 7)


def godmode_CMD(userid, args):
    commands_filter(userid, args, 8)


def jetpack_CMD(userid, args):
    commands_filter(userid, args, 9)


def blind_CMD(userid, args):
    commands_filter(userid, args, 10)


def drugs_CMD(userid, args):
    commands_filter(userid, args, 11)


def setcash_CMD(userid, args):
    commands_filter(userid, args, 12)


def sethealth_CMD(userid, args):
    commands_filter(userid, args, 13)


def firework_CMD(userid, args):
    commands_filter(userid, args, 14)


def burn_CMD(userid, args):
    commands_filter(userid, args, 15)


penalties = {
    1: {
        'name': 'Kick',
        'function': penalty.kick,
        'command': 'kick',
        'handle': kick_CMD,
        'permission': 'kick_players',
        'description': 'Kicks the player from the server'
    },
    2: {
        'name': 'Kill',
        'function': penalty.kill,
        'command': 'kill',
        'handle': kill_CMD,
        'permission': False,
        'description': 'Instantly eliminates the player'
    },
    3: {
        'name': 'Slap',
        'function': penalty.slap,
        'command': 'slap',
        'handle': slap_CMD,
        'permission': False,
        'description': 'Slaps the player, causing minor damage'
    },
    4: {
        'name': 'Respawn',
        'function': penalty.respawn,
        'command': 'respawn',
        'handle': respawn_CMD,
        'permission': False,
        'description': 'Brings the player back to life'
    },
    5: {
        'name': 'Strip Weapon',
        'function': penalty.strip_weapon,
        'command': 'strip',
        'handle': strip_CMD,
        'permission': False,
        'description': 'Removes the player\'s weapons'
    },
    6: {
        'name': 'Freeze / Unfreeze',
        'function': penalty.freeze,
        'command': 'freeze',
        'handle': freeze_CMD,
        'permission': False,
        'description': 'Freezes or unfreezes the player'
    },
    7: {
        'name': 'Set NoClip Mode',
        'function': penalty.give_noclip,
        'command': 'noclip',
        'handle': noclip_CMD,
        'permission': False,
        'description': 'Grants or revokes NoClip mode for the player'
    },
    8: {
        'name': 'Set God Mode',
        'function': penalty.give_godmode,
        'command': 'godmode',
        'handle': godmode_CMD,
        'permission': False,
        'description': 'Enables or disables God Mode for the player'
    },
    9: {
        'name': 'Set Jetpack Mode',
        'function': penalty.give_jetpack,
        'command': 'jetpack',
        'handle': jetpack_CMD,
        'permission': False,
        'description': 'Grants or removes a jetpack for the player'
    },
    10: {
        'name': 'Set Blind Mode',
        'function': penalty.blind,
        'command': 'blind',
        'handle': blind_CMD,
        'permission': False,
        'description': 'Applies a visual impairment effect to the player'
    },
    11: {
        'name': 'Set Drugs Effect',
        'function': penalty.give_drugs,
        'command': 'drugs',
        'handle': drugs_CMD,
        'permission': False,
        'description': 'Applies a drugs effect to the player'
    },
    12: {
        'name': 'Set Cash',
        'function': penalty.set_cash,
        'command': 'setcash',
        'handle': setcash_CMD,
        'permission': False,
        'description': 'Sets the amount of cash for the player'
    },
    13: {
        'name': 'Set Health',
        'function': penalty.set_health,
        'command': 'sethp',
        'handle': sethealth_CMD,
        'permission': False,
        'description': 'Sets the health amount for the player'
    },
    14: {
        'name': 'Set As Firework',
        'function': penalty.set_firework,
        'command': 'firework',
        'handle': firework_CMD,
        'permission': False,
        'description': 'Transforms the player into a firework'
    },
    15: {
        'name': 'Set On Fire',
        'function': penalty.burn,
        'command': 'burn',
        'handle': burn_CMD,
        'permission': False,
        'description': 'Sets the player on fire'
    }
}


# Load & Unload
def load():

    # Create a configuration file for the module to enable/disable penalties commands
    config = {}
    for penalty in penalties.values():
        config['enable_!%s_command' % penalty['command']] = {
            'description': (
                'Enable the !%s command' % penalty['name'],   
                penalty['description'] 
            ),
            'current_value': True
        }
    sam.settings.module_config('players_manager', config)

    # Cache all players on load
    for userid in sam.userid_list():
        cache_player(userid)
    
    # Register all penalties commands
    for penalty in penalties.values():
        sam.cmds.chat(penalty['command'], penalty['handle'])


def unload():
    
    # Unregister all penalties commands
    for penalty in penalties.values():
        sam.cmds.delete(penalty['command'])
    
    # Remove all effects to all players
    for userid in effects:
        effects[userid].remove_all()


# Menu Functions and Handlers
def module_menu(userid, page=1):
    
    # Check if the player is allowed to use the module
    if not sam.admins.is_allowed(userid, 'players_manager'):
        sam.home_page(userid)
        return
    
    menu = sam.Menu('players_manager', players_manager_HANDLE, 'home_page')
    menu.title('Players Manager')

    for penalty in sorted(penalties.keys()):
        menu.add_option(penalty, penalties[penalty]['name'])

    menu.send(userid, page=page)


def players_manager_HANDLE(userid, choice, submenu):
    
    penalty = penalties[choice]

    # In case the penalty choosen requires a permission, check if the player has it
    if not sam.admins.is_allowed(userid, penalty['permission']):
        module_menu(userid)
        return

    menu = sam.Menu('pm_choose_player', players_list_HANDLE, submenu)
    menu.title('Players Manager')
    menu.description('Choose a player to: ' + penalty['name'])
    menu.max_lines = 6

    # For pernalties that can be applied to to multiple players
    if penalty in (4, 12, 13):
        menu.add_option(('#all', choice), 'To all Players')
        menu.add_option(('#ct', choice), 'Counter-Terrorist Team')
        menu.add_option(('#t', choice), 'Terrorist Team')
        menu.separator()

    # Add each player as an option
    for ply in sam.player_list():
        menu.add_option((ply, choice), ply.name)
        
    menu.footer(
        'Tip: You can also use chat commands',
        ' ',
        '!%s {player_name}' % penalty['command']
    )

    menu.send(userid)


def players_list_HANDLE(userid, choice, submenu):

    # Return the admin to the previous menu
    if not isinstance(submenu, str):
        submenu.send(userid)

    # Get the choice objects
    target, penalty_id = choice

    # Get the penalty dictionary
    penalty = penalties[penalty_id]

    # If the chosen penalty "harms" the player, and the admin has lower
    # immunity than the target player, return the admin to the previous menu
    if penalty_id not in (4, 12, 13) and \
        not sam.admins.compare_immunity(userid, target.steamid):
        return

    # If the penalty is either Set Cash or Set Health,
    # open the submenu for specifying the amount
    if penalty_id in (12, 13):
        menu = sam.Menu(
            'pm_%s_amount' % penalty['command'],
            set_cash_HANDLE if penalty_id == 12 else set_health_HANDLE,
            submenu
        )
        menu.title('Players Manager')

        # Set Cash Values
        if penalty_id == 12:
            menu.description('Choose the cash ammount:')
            menu.add_option((target, 0), 'Remove Cash')
            for num in range(800, 16001, 800):
                menu.add_option((target, num), num)

        # Set Health Values
        elif penalty_id == 13:
            menu.description('Choose the health ammount:')
            menu.add_option((target, 1), 1)
            for num in range(5, 101, 5):
                menu.add_option((target, num), num)

        menu.send(userid)
        return

    # Apply the penalty to the target player
    penalty['function'](target)


def set_cash_HANDLE(userid, choice, submenu):

    # Modify the target player cash
    penalty.set_cash(*choice)
    
    # Return the admin to the previous menu, but rebuild the menu first
    players_list_HANDLE(userid, (choice[0], 12), submenu.object.submenu)
    sam.menu_system.send_menu(userid, submenu.menu_id, submenu.page)


def set_health_HANDLE(userid, choice, submenu):

    # Modify the target player health
    penalty.set_health(*choice)
    
    # Return the admin to the previous menu, but rebuild the menu first
    players_list_HANDLE(userid, (choice[0], 12), submenu.object.submenu)
    sam.menu_system.send_menu(userid, submenu.menu_id, submenu.page)

def commands_filter(userid, args, penalty_id):
    """
    Filters the usage of the penalty commands by making the necessary checks
    before executing the penalty function
    """

    # Get the penalty dictionary
    penalty = penalties[penalty_id]

    # Check the command is enabled, else check if the player has permission
    # to use the module and the penalty command
    if not sam.settings('players_manager').get('enable_!%s_command' % penalty['command']):
        sam.cmds.is_disabled(userid)
        return
    elif not sam.admins.is_allowed(userid, 'players_manager') or \
        not sam.admins.is_allowed(userid, penalty['permission']):
        sam.cmds.no_permission(userid)
        return

    # If no arguments were given, open the penalty option in the menu
    if not args:
        module_menu(userid, page=(penalty_id - 1) // 7 + 1)
        players_manager_HANDLE(userid, penalty_id, 'players_manager')
        return

    # Sort the target
    target = args.pop(0) if args else False

    # Check whether the penalty does not accept multiple targets
    if penalty_id not in (4, 12, 13) and target in sam.FILTERS:
        sam.msg.hud(userid, 'This command does not accept multiple targets')
        return

    # Get the target player or player filter
    if isinstance(target, str) and target not in sam.FILTERS:
        target = sam.get_player(target)

    # Check if the target is not valid or is not a valid player filter
    if not target and target not in sam.FILTERS:
        sam.msg.hud(
            userid,
            'Target is not a valid player or player filter.',
            'Valid Player Filters: %s' % ', '.join(sam.FILTERS)
        )
        return

    # Set the arguments for the penalty function
    arguments = [target]

    # Handle penalties that require additional arguments
    if penalty_id in (3, 4, 12, 13) and args and args[0].isdigit():
        arguments.append(int(args[0]))
    elif penalty_id == 1 and args:
        arguments.append(' '.join(args))

    # Execute the penalty function
    penalty['function'](*arguments)


# Helper Functions
def is_alive(target):
    """
    Returns whether the target player is alive or not
    """
    
    return int(es.getplayerprop(target, lifestate)) in (512, 0)


def cache_player(userid):
    """
    Caches the player in the effects dictionary
    """
    
    effects[userid] = PlayerEffects(userid)

def play(target, sound):
    """
    Helper function to emit a sound on the target player
    """ 
    
    sam.emit_sound(target, sound)

def get_name(target):
    """
    Returns the formatted name of the target player with their team color
    """

    # If target is a player:
    if target not in sam.FILTERS:
        team_color = ''
        if target.team == 1:
            team_color = '#spec'
        elif target.team == 2:
            team_color = '#terro'
        elif target.team == 3:
            team_color = '#ct'
        return '%s%s#beige' % (team_color, target.name)

    # If target is one of the teams
    teams = {
        '#spec': '#specSpectators',
        '#t': '#terroTerrorists',
        '#ct': '#ctCounter Terrorists'
    }

    if target in teams:
        return '%s players#beige' % teams[target]

    # Otherwise if target is another player filter
    elif target in sam.FILTERS:
        return '#orange%s players#beige' % target.strip('#').title()
    
    # If nothing else return as Unknown
    return '#orangeUnknown#beige'

    
def push(target, x, y, z):
    """
    Pushes the target player with the specified amount
    """
    
    if is_alive(target):
        setprop(
            target,
            'CCSPlayer.baseclass.localdata.m_vecBaseVelocity',
            es.createvectorstring(x, y, z)
        )

def msg(text, notify=True):
    """
    Helper function to send a message to all players
    """
    
    if notify:
        sam.msg.tell('#all', '#beige' + text)


def blind_effect_loop(userid):
    """
    A loop to maintain the blindness effect on the target player
    """
    
    try:
        usermsg.fade(userid, 2, 1, 70, 0, 0, 0)
        sam.delay_task(.01, 'blind_%s' % userid, blind_effect_loop, userid)
    except AttributeError:
        return


def drugs_effect_loop(target):
    """
    A loop to maintain the drugs effect on the target player
    """
    
    usermsg.shake(target, rint(20, 25), 1)
    usermsg.fade(
        target, 2, 1, 100, rint(0, 255), rint(0, 255), rint(0, 255), rint(100, 125)
    )
    try:
        target.setColorint(rint(0, 255), rint(0, 255), rint(0, 255), rint(175, 255))
    except AttributeError:
        pass
    sam.delay_task(.1, 'drugs_%s' % target, drugs_effect_loop, target)
    
# Game Events
def player_connect(ev):
    
    # Cache the player on connect
    userid = int(ev['userid'])
    if userid not in effects:
        cache_player(userid)


def player_disconnect(ev):
    
    # Decache the player on disconnect
    userid = int(ev['userid'])
    if userid in effects:
        del effects[userid]


def player_death(ev):
    
    # Remove all effects on death
    userid = int(ev['userid'])
    if userid in effects:
        effects[userid].remove_all()
    else:
        cache_player(userid)
