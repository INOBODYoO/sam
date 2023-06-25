import es
import psyco

psyco.full()

sam = es.import_addon('sam')

def player_activate(ev):
    sid = ev['es_steamid']
    ban_manager = sam.addons_monitor.import_addon('ban_manager')
    if sid == 'BOT':
        return
    elif ban_manager and ban_manager.is_banned(sid):
        sam.msg.console('%s attempted to connect to the server while banned!' % ev['es_username'])
        return
    sam.msg.tell('#human', '#spec%s #grayhas joined the server' % ev['es_username'], log=True)


def player_disconnect(ev):
    sid = ev['networkid']
    ban_manager = sam.addons_monitor.import_addon('ban_manager')
    if sid == 'BOT' or (ban_manager and ban_manager.is_banned(sid)):
        return
    sam.msg.tell('#human', '#spec%s #grayhas left the server (#spec%s#gray)' %
                 (ev['es_username'], ev['reason']), log=True)
