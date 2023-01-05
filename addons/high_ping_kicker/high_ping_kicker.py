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
        if ply.ping >= 80:
            sid = ply.steamid

            if sid not in warnings.keys():
                warnings[sid] = 0
            warnings[sid] += 1

            if warnings[sid] < 4:
                page = sam.Menu('high_ping_kicker')
                page.header_text = False
                page.title('High Ping Kicker')
                page.add_line('Warning: Your ping is too high!')
                page.add_line('This is your %s warning.' % msg[warnings[sid]])
                page.timeout = 10
                page.send(ply)
                continue
            else:
                ban_manager = sam.addons_monitor.import_addon('ban_manager')
                if ban_manager:
                    ban_manager.ban({'steamid': sid,
                                     'name': ply.name,
                                     'admin': 'SAM (High Ping Kicker)',
                                     'date': sam.get_time('%m/%d/%Y at %H:%M:%S'),
                                     'expiry_date': 300 + sam.timestamp(),
                                     'length_text': '5 Minutes',
                                     'reason': 'High Ping'})
                else:
                    ply.kick('You were kicked from the server! (Reason: High Ping)')


def unload():
    sam.cancel_delay('sam_hpk_loop')


loop()
