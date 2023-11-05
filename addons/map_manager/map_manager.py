import es
import psyco

psyco.full()

sam = es.import_addon('sam')

# Global Variables
NEXTLEVEL = 'none'


def addon_page(uid):
    if not sam.admins.is_allowed(uid, 'map_manager'):
        sam.home_page(uid)
        return
    p = sam.Menu('map_manager', map_manager_HANDLE, 'home_page')
    p.settitle('Map Changer')
    if nextlevel != 'none':
        p.description('Pending Map Change: %s' % nextlevel)
    p.add_option(1, 'Change Map Now')
    p.add_option(2, 'Change At End Of Round')
    p.add_option(3, 'Reload Current Map')
    if nextlevel:
        p.line(sam.pages_line)
        p.add_option(4, 'Cancel Pending Change (%s)' % nextlevel)
    p.send(uid)
