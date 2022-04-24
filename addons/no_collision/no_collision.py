import es
import psyco
psyco.full()

prop = 'CCSPlayer.baseclass.baseclass.baseclass.baseclass.baseclass.baseclass.m_CollisionGroup'
func = es.setplayerprop

def load():
    for uid in es.getUseridList():
        func(uid, prop, 2)

def unload():
    for uid in es.getUseridList():
        func(uid, prop, 0)

def player_spawn(ev):
    func(int(ev['userid']), prop, 2)