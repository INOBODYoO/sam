import es
import psyco
psyco.full()

sam = es.import_addon('sam')
var = 'sam_bomb_countdown'

def unload(): cancel()

def bomb_planted(ev):
    bomb_timer(int(es.ServerVar('mp_c4timer')))

def bomb_defused(ev):
    cancel()
    sam.msg.center('#all', '## BOMB DEFUSED ##')

def bomb_exploded(ev):
    cancel()
    sam.msg.center('#all', '## BOMB EXPLODED ##')

def round_start(ev):
    cancel()

def bomb_timer(sec):
    if sec == 0:
        return
    sam.msg.side('#all', False, 'BOMB DETONATING IN %s!' % sec)
    sam.delay_task(1, var, bomb_timer, (sec - 1))

def cancel():
    sam.cancel_delay(var)