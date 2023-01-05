import random
import usermsg


def player_hurt(ev):
    # get the player who was hurt
    victim = int(ev['userid'])

    # get the player who inflicted the damage
    attacker = int(ev['attacker'])

    # get the amount of damage taken
    damage = int(ev['dmg_health'])

    # message to display
    attacker_message = '+%s' % damage
    hurt_message = '-%s' % damage

    # position of the message on the screen
    x = random.uniform(0.4, 0.6)
    y = random.uniform(0.8, 0.9)

    # send messages to both players, one showing the damage taken, and the other given
    usermsg.hudmsg(attacker, attacker_message, 0, x, y, r1=0, g1=255, b1=0, holdtime=1.8)
    usermsg.hudmsg(victim, hurt_message, 1, x, y, r1=255, g1=0, b1=0, holdtime=1.8)
