from random import randint as rint

import es
import psyco
import usermsg

psyco.full()

sam = es.import_addon('sam')
effects = {}
setprop = es.setplayerprop
velocity = 'CCSPlayer.baseclass.localdata.m_vecBaseVelocity'
lifestate = 'CBasePlayer.m_lifeState'
teams = {'#all': '#yellowall players',
         '#ct': '#ctCounter-Terrorists',
         '#t': '#tTerrorists'}


class _PenaltiesClass:

    @staticmethod
    def kick(target, reason=None, notify=True):
        target.kick(reason)
        if notify:
            msg('#cyanAdmin #whitekicked #blue%s #whiteoff the server!' % target.name)

    @staticmethod
    def kill(target, notify=True):
        target.kill()
        msg('#cyanAdmin #whitekilled #red%s' % target.name, notify)

    @staticmethod
    def respawn(target):
        def f(*targets):
            for ply in targets:
                uid = int(ply)
                setprop(uid, 'CCSPlayer.m_iPlayerState', 0)
                setprop(uid, lifestate, 0)
                es.server.insertcmd('es_xspawnplayer %s' % uid)

        if target in teams.keys():
            f(*sam.player_list(target))
            msg('#cyanAdmin #whitehas respawned ' + teams[target])
        else:
            f(target)
            msg('#cyanAdmin #whiterespawned #green%s' % target.name)

    @staticmethod
    def strip_weapon(target):
        if target.weapon != 'weapon_knife':
            es.sexec(target, 'drop')
            msg('#cyanAdmin #whitestripped #red%s\'s #whiteweapon' % target.name)

    @staticmethod
    def set_firework(target):
        var = 'firework_%s' % target

        def push(target, amount):
            if is_alive(target):
                setprop(target, velocity, '0,0,%s' % amount)

        def explosion(target):
            if is_alive(target):
                x, y, z = target.location
                es.server.queuecmd('es_xeffect sparks %s,%s,%s 9999 10 0,0,0' % (x, y, z))
                target.kill()

        sam.emit_sound(target, 'weapons/physgun_off.wav')
        usermsg.shake(target, 85, 2)
        p = 35
        for n in (x * 0.1 for x in range(1, 12)):
            sam.delay_task(n, var, push, (target, p))
            p += 35
        sam.delay_task(1.4, var, sam.emit_sound, (target, 'weapons/c4/c4_beep1.wav'))
        sam.delay_task(1.5, var, sam.emit_sound, (target, 'weapons/c4/c4_beep1.wav'))
        sam.delay_task(1.7, var, explosion, target)
        sam.delay_task(1.7,
                       var,
                       sam.emit_sound,
                       (target, 'weapons/hegrenade/explode4.wav'))
        msg('#cyanAdmin #whiteset #red%s #whiteas a firework!' % target.name)

    @staticmethod
    def slap(target, damage=0):
        if is_alive(target):
            es.server.insertcmd('damage %s %s' % (target, damage))
            setprop(target, velocity,
                    es.createvectorstring(rint(-350, 350),
                                          rint(-350, 350),
                                          rint(200, 350)))
            sam.emit_sound(target, 'player/damage%s.wav' % rint(1, 3))
            msg('#cyanAdmin #white slapped #red%s #whitewith #green0 damage' %
                target.name)

    @staticmethod
    def blind(target):
        uid = int(target)
        effect = effects[uid]
        if effect.blind:
            sam.cancel_delay('blind_%s' % uid)
            text = '#cyanAdmin #whitehas removed blindness off #red%s' % target.name
        else:
            _blind_loop(uid)
            text = '#cyanAdmin #whitehas blinded #red%s' % target.name
        effect.blind = not effect.blind
        msg(text)

    @staticmethod
    def give_jetpack(target):
        effect = effects[int(target)]
        if effect.jetpack:
            target.jetpack(False)
            text = '#cyanAdmin #whiteremoved Jetpack from #blue%s' % target.name
        else:
            target.jetpack(True)
            text = '#cyanAdmin #whitegave #blue%s #whiteJetpack' % target.name
        effect.jetpack = not effect.jetpack
        msg(text)

    @staticmethod
    def give_godmode(target):
        effect = effects[int(target)]
        if effect.godmode:
            target.godmode(False)
            text = '#cyanAdmin #whitehas removed God Mode from #blue%s' % target.name
        else:
            target.godmode(True)
            text = '#cyanAdmin #whiteset #blue%s #whiteGod Mode' % target.name
        effect.godmode = not effect.godmode
        msg(text)

    @staticmethod
    def give_noclip(target):
        effect = effects[int(target)]
        if effect.noclip:
            target.noclip(False)
            text = '#cyanAdmin #whitehas removed No Clip from #blue%s' % target.name
        else:
            target.noclip(True)
            text = '#cyanAdmin #whitehas given #blue%s #whiteNo Clip' % target.name
        effect.noclip = not effect.noclip
        msg(text)

    @staticmethod
    def give_drugs(target):
        effect = effects[int(target)]
        if effect.ondrugs:
            sam.cancel_delay('drugs_%s' % target)
            text = '#cyanAdmin #whitehas removed drug effects from #blue%s' % target.name
        else:
            _drugs_loop(target)
            text = '#cyanAdmin #whitehas given #blue%s #whitedrugs' % target.name
        effect.ondrugs = not effect.ondrugs
        msg(text)

    @staticmethod
    def freeze(target):
        # Get the object from the effects dictionary
        obj = effects[target]

        # Toggle the state
        obj.frozen = not obj.frozen
        target.freeze(not obj.frozen)

        # Construct a message indicating the new state
        if obj.frozen:
            message = 'Admin has frozen %s' % obj.name
        else:
            message = 'Admin has unfrozen %s' % obj.name
        msg(message)

    @staticmethod
    def burn(target, admin=False):
        effect = effects[int(target)]
        target.burn()
        if not effect.onfire:
            effect.onfire = True
            msg('#cyanAdmin #whitehas set #red%s #whiteon fire' % target.name)
        elif admin:
            sam.msg.hud(admin, '%s is already on fire!' % target.name)

    @staticmethod
    def set_cash(target, amount, notify=True):
        def f(amount, *targets):
            for ply in targets:
                ply.cash = amount

        if target in teams.keys():
            f(amount, *sam.player_list(target))
            msg('#cyanAdmin #whiteset %s #greencash to $%s' %
                (teams[target], amount), notify)
        else:
            f(amount, target)
            msg('#cyanAdmin #whiteset #green%s #greencash to %s' %
                (target.name, amount), notify)

    @staticmethod
    def set_health(target, amount):
        def f(amount, *targets):
            for ply in targets:
                if is_alive(ply):
                    ply.health = amount
                else:
                    sam.msg.console('Could not change %s\'s health, player is dead.' %
                                    ply.name)

        if target in teams.keys():
            f(amount, *sam.player_list(target))
            msg('#cyanAdmin #whiteas set %s #whiteof health to %s' %
                (amount, teams[target]))
        else:
            f(amount, target)
            msg('#cyanAdmin #whiteas set #blue%s\'s #whitehealth to #blue%s' %
                (target.name, amount))


penalty = _PenaltiesClass()

penalties = {1: ('Kick', penalty.kick),
             2: ('Kill', penalty.kill),
             3: ('Slap', penalty.slap),
             4: ('Set Cash', penalty.set_cash),
             5: ('Set Health', penalty.set_health),
             6: ('Respawn', penalty.respawn),
             7: ('Strip Weapons', penalty.strip_weapon),
             8: ('Blind', penalty.blind),
             9: ('Freeze or Unfreeze', penalty.freeze),
             10: ('Give NoClip', penalty.give_noclip),
             11: ('Give Godmode', penalty.give_godmode),
             12: ('Give Jetpack Mode', penalty.give_jetpack),
             13: ('Give Drugs', penalty.give_drugs),
             14: ('Set As Firework', penalty.set_firework),
             15: ('Set On Fire', penalty.burn)}


class PlayerEffects:
    def __init__(self, uid):
        self.uid = uid
        self.blind = False
        self.onfire = False
        self.noclip = False
        self.frozen = False
        self.ondrugs = False
        self.godmode = False
        self.jetpack = False

    def remove_all(self):
        ply = sam.get_player(self.uid)
        if not ply:
            return
        if self.blind:
            penalty.blind(ply)
        if self.frozen:
            penalty.freeze(ply)
        if self.noclip:
            penalty.give_noclip(ply)
        if self.ondrugs:
            penalty.give_drugs(ply)
        if self.godmode:
            penalty.give_godmode(ply)
        if self.jetpack:
            penalty.give_jetpack(ply)
        if self.onfire:
            self.onfire = False


def load():
    for uid in es.getUseridList():
        cache_player(uid)
    sam.cmds.chat('kick', kick_CMD)


def unload():
    sam.cmds.delete('!kick')
    for uid in effects:
        effects[uid].remove_all()


def module_menu(uid):
    if not sam.admins.can(uid, 'players_manager'):
        sam.home_page(uid)
        return
    menu = sam.Menu('players_manager', players_manager_HANDLE, 'home_page')
    menu.title('Players Manager')
    for penalty in sorted(penalties.keys()):
        menu.add_option(penalty, penalties[penalty][0])
    menu.send(uid)


def players_manager_HANDLE(uid, pid, submenu):
    if pid == 1 and not sam.admins.can(uid, 'kick_players'):
        module_menu(uid)
        return
    penalty = penalties[pid]
    menu = sam.Menu('pm_choose_player', choose_player_HANDLE, submenu)
    menu.title('Players Manager')
    menu.description('Choose a player to: ' + penalty[0])
    if pid in (4, 5, 6):
        menu.add_option(('#all', pid), 'To all Players')
        menu.add_option(('#ct', pid), 'Counter-Terrorist Team')
        menu.add_option(('#t', pid), 'Terrorist Team')
        menu.separator()
    for ply in sam.player_list():
        menu.add_option((ply, pid), ply.name)
    menu.send(uid)


def choose_player_HANDLE(uid, choice, submenu):
    target, pid = choice
    penalty = penalties[pid]
    if pid not in (4, 5, 6) and not sam.admins.immunity_check(uid, target.steamid):
        submenu.send(uid)
        return
    if pid == 4:
        menu = sam.Menu('pm_cash_amount', cash_amount_HANDLE, submenu)
        menu.title('Players Manager')
        menu.description('Choose the amount of cash to give:')
        menu.add_option((target, 0), 'Remove Cash')
        for num in range(800, 16001, 800):
            menu.add_option((target, num), num)
        menu.send(uid)
        return
    elif pid == 5:
        menu = sam.Menu('pm_health_amount', health_amount_HANDLE, submenu)
        menu.title('Players Manager')
        menu.description('Choose the amount of health to give:')
        menu.add_option((target, 1), 1)
        for num in range(5, 101, 5):
            menu.add_option((target, num), num)
        menu.send(uid)
        return
    elif pid in (2, 6) or is_alive(target):
        penalty[1](target)
    else:
        sam.msg.hud(uid, 'Penalty not given, player must be alive.')
    submenu.send(uid)


def cash_amount_HANDLE(uid, choice, submenu=None):
    penalty.set_cash(choice[0], choice[1])
    submenu.send(uid)


def health_amount_HANDLE(uid, choice, submenu=None):
    penalty.set_health(choice[0], choice[1])
    submenu.send(uid)


def player_connect(ev):
    uid = int(ev['userid'])
    if uid not in effects:
        cache_player(uid)


def player_disconnect(ev):
    uid = int(ev['userid'])
    if uid in effects:
        del effects[uid]


def player_death(ev):
    uid = int(ev['userid'])
    if uid in effects:
        effects[uid].remove_all()
    else:
        cache_player(uid)


def kick_CMD(uid, args):
    if not sam.admins.can(uid, 'kick_players'):
        return
    if not args:
        sam.home_page(uid)
        sam.handle_choice(1, uid)
        sam.handle_choice(1, uid)
        return
    args = list(args)
    kicked = 0
    for arg in args:
        target = sam.getuid(arg)
        if es.exists('userid', target) and sam.admins.immunity_check(uid, target):
            penalty.kick(target)
            kicked += 1
            sam.msg.tell('Warning: %s of the target players were not found (%s)' % (len(args), ', '.join(args)))


def is_alive(target):
    return int(es.getplayerprop(target, lifestate)) in (512, 0)


def cache_player(uid):
    effects[uid] = PlayerEffects(uid)


def msg(text, notify=True):
    if notify:
        sam.msg.tell('#all', text)


def _blind_loop(uid):
    try:
        usermsg.fade(uid, 2, 1, 70, 0, 0, 0)
        sam.delay_task(.01, 'blind_%s' % uid, _blind_loop, uid)
    except AttributeError:
        return


def _drugs_loop(target):
    usermsg.shake(target, rint(20, 25), 1)
    usermsg.fade(target, 2, 1, 100, rint(0, 255), rint(0, 255), rint(0, 255), rint(100, 125))
    try:
        target.setColorint(rint(0, 255), rint(0, 255), rint(0, 255), rint(175, 255))
    except AttributeError:
        pass
    sam.delay_task(.1, 'drugs_%s' % target, _drugs_loop, target)
