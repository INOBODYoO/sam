import es
import psyco
psyco.full()

prop = 'CCSPlayer.baseclass.baseclass.baseclass.baseclass.baseclass.baseclass.m_CollisionGroup'

def player_spawn(ev):
    es.setplayerprop(int(ev['userid']), prop, 2)