import es
import psyco
psyco.full()

sam = es.import_addon('sam')

def player_activate(ev):
    sid = ev['es_steamid']
    bm  = sam.import_addon('ban_manager')
    if sid == 'BOT':
        return
    elif bm and bm.is_banned(sid):
        sam.msg.console('%s attempted to connect to the server while banned!' % ev['es_username'])
        return
    sam.msg.tell('#human', '#spec%s #grayhas joined the server' % ev['es_username'], log=True)

def player_disconnect(ev):
    sid = ev['networkid']
    bm  = sam.import_addon('ban_manager')
    if sid == 'BOT' or (bm and bm.is_banned(sid)):
        return
    sam.msg.tell('#human', '#spec%s #grayhas left the server (#spec%s#gray)' %
                 (ev['es_username'], ev['reason']), log=True)