#!/usr/bin/python
# -*- coding: utf-8 -*-
import es
import psyco
psyco.full()

sam = es.import_addon('sam')
msg = {1: 'first', 2: 'second', 3: 'third and final'}
warnings = {}


def loop():
    sam.delay_task(30, 'sam_hpk_loop', loop, ())

    for ply in sam.player_list():
        if ply.ping >= 0:
            sid = ply.steamid

            if sid not in warnings.keys():
                warnings[sid] = 0
            warnings[sid] += 1

            if warnings[sid] < 4:
                p = sam.PageSetup('high_ping_kicker')
                p.header_text = False
                p.title('High Ping Kicker')
                p.newline('Warning: Your ping is too high!')
                p.newline('This is your %s warning.' % msg[warnings[sid]])
                p.timeout(10)
                p.send(ply)
                continue
            else:
                ban_manager = sam.import_addon('ban_manager')
                if ban_manager:
                    ban_manager.ban({
                        'steamid': sid,
                        'name': ply.name,
                        'admin': 'SAM (High Ping Kicker)',
                        'date': sam.get_time('%m/%d/%Y at %H:%M:%S'),
                        'expiry_date': 300 + sam.timestamp(),
                        'length_text': '5 Minutes',
                        'reason': 'High Ping',
                        })
                else:

                    ply.kick('You were kicked from the server! (Reason: High Ping)'
                             )


def unload():
    sam.cancel_delay('sam_hpk_loop')


loop()