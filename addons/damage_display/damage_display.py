import es
import psyco
psyco.full()

sam = es.import_addon('sam')
sep = '-' * 20
dat = {}

# Load Block
def load():
    for user in sam.userid_list('#all'): _add(user)

# Game Events
def player_hurt(ev):
    dmg = ev['dmg_health']
    for user in (ev['userid'], ev['attacker']):
        user = int(user)
        if user in dat.keys():
            dat[user].append('-%s from %s' % (dmg, ev['es_attackername'])
                             if user == int(ev['userid']) else
                             '-%s to %s' % (dmg, ev['es_username']))
            if len(dat[user]) == 6:
                del dat[user][0]
            sam.msg.side(user, False, '\n'.join(sorted(dat[user], reverse=True)))

def player_activate(ev): _add(int(ev['userid']))

def player_disconnect(ev): _clear(int(ev['userid']))

def player_death(ev): _clear(int(ev['userid']))

def round_end(ev):
    for user in dat.keys(): _clear(user)

# Functions
def _add(user):
    if user not in dat.keys(): dat[user] = []

def _clear(user):
    if user in dat.keys(): del dat[user][:]