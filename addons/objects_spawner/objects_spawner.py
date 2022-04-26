import es
import vecmath
import psyco
psyco.full()

sam = es.import_addon('sam')
sam.HOME_PAGE_ADDONS.append('objects_spawner')

# Global Variables
OBJECTS = sam.databases.load(sam.path.addons + '/objects_spawner/objects.json', True)
SPAWNED = dict((int(k), v) for k, v in sam.databases.load('spawned_objects').items())
CACHE   = {'move_speed': {}, 'ui': []}
LINE    = '-' * 45
COLORS  = {'Red': '255,0,0',
           'Green': '0,255,0',
           'Blue': '0,0,255',
           'Black': '0,0,0',
           'Brown': '150,100,0',
           'Dark Red': '125,0,0',
           'Gray': '175,175,175',
           'Green': '0,125,0',
           'Light Green': '0,255,0',
           'Orange': '255,150,0',
           'Pink': '255,0,255',
           'Purple': '175,0,175',
           'Red': '255,0,0',
           'Turkey': '0,255,255',
           'Yellow': '255,255,0'}

m_vecOrigin = 'CBaseEntity.m_vecOrigin'

def load():
    # Create chat command
    sam.cmds.chat('!props', addon_page)

    # Start View Object UI update loop
    view_object_ui_loop()

def unload():
    # Delete chat command
    sam.cmds.delete('!props')

    # Stop View Object UI update loop
    sam.cancel_delay('view_object_ui_loop')
    for uid in CACHE['ui']: toggle_ui(uid)

    # Save spawned objects database
    sam.databases.save('spawned_objects', SPAWNED)

# View Object UI
def toggle_ui(uid):
    if uid not in CACHE['ui']:
        CACHE['ui'].append(uid)
    else:
        CACHE['ui'].remove(uid)
        sam.msg.side(uid, ' ')

def view_object_ui_loop():
    for uid in CACHE['ui']:
        if not es.exists('userid', uid):
            CACHE['ui'].remove(uid)
            continue
        view_object_ui(uid)
    sam.delay_task(0.25, 'view_object_ui_loop', view_object_ui_loop, ())

def view_object_ui(uid):
    # Get view object index, return if its not valid
    index = view_object(uid)
    targetname = es.entitygetvalue(index, 'targetname')
    if index is None or not targetname.startswith('sam'):
        sam.msg.side(uid, LINE, 'NOT LOOKING AT A VALID OBJECT', LINE)
        return
    # Get object info, return if its not valid
    obj = SPAWNED[index] if index in SPAWNED.keys() else None
    if not obj:
        return
    # Send UI message to players
    x, y, z = es.getindexprop(index, m_vecOrigin).split(',')
    dis = distance(uid, index)
    sam.msg.side(uid,
                 LINE,
                 'OBJECT NAME: ' + obj['name'],
                 'OBJECT ID: ' + obj['id'],
                 'POSITION: %.2f, %.2f, %.2f' % (float(x), float(y), float(z)),
                 'DISTANCE: %.2f units | %.2f meters' % (dis, dis * 0.01905),
                 LINE)

# Addon Funtions
def addon_page(uid, args=None):
    p = sam.PageSetup('objects_spawner', objects_spawner_HANDLE, 'home_page')
    p.title('Objects Spawner')
    for num, option in enumerate(('Spawn Objects',
                                  'Delete Object [Aim To Delete]',
                                  'Remove All Objects',
                                  'Move Objects',
                                  'Rotate Objects',
                                  'Change Objects Color')):
        p.option(num + 1, option)
    p.separator()
    p.option(7, 'View Object UI [%s]' %
            ('Enabled' if uid in CACHE['ui'] else 'Disabled'))
    p.send(uid)

def objects_spawner_HANDLE(uid, choice, prev_page):
    if choice == 1:
        p = sam.PageSetup('categorys_list',
                          categorys_list_HANDLE,
                          'objects_spawner')
        p.title('Objects Spawner')
        p.maxlines = 8
        p.description('Choose a category of objects:')
        for category in sorted(OBJECTS.keys()):
            p.option(category,  sam.title(category))
        p.send(uid)
        return
    elif choice == 2:
        delete_object(uid)
    elif choice == 3:
        delete_all(uid)
    elif choice == 4:
        if uid not in CACHE['move_speed'].keys():
            CACHE['move_speed'][uid] = 8
        p = sam.PageSetup('move_objects', move_objects_HANDLE, 'objects_spawner')
        p.title('Move Objects')
        p.option(1, 'Move Speed: %s units' % CACHE['move_speed'][uid])
        p.separator()
        p.option('+x', 'FORWARD [+X]')
        p.option('-x', 'BACK [-X]')
        p.option('+y', 'LEFT [+Y]')
        p.option('-y', 'RIGHT [-Y]')
        p.option('+z', 'UP [+Z]')
        p.option('-z', 'DOWN [-Z]')
        p.footer('* Aim at an object to move it',
                 '* Move Speed represents how far the',
                 '  object will move in game units')
        p.send(uid)
        return
    elif choice == 5:
        p = sam.PageSetup('rotate_object', rotate_object_HANDLE, 'objects_spawner')
        p.title('Rotate Objects')
        p.option(2, 'ROLL [+X]')
        p.option(5, 'ROLL [-X]')
        p.option(0, 'PITCH [+Y]')
        p.option(3, 'PITCH [-Y]')
        p.option(1, 'YAW [+Z]')
        p.option(4, 'YAW [-Z]')
        p.footer('* Aim at an object to rotate it')
        p.send(uid)
        return
    elif choice == 6:
        p = sam.PageSetup('color_objects', color_objects_HANDLE, 'objects_spawner')
        p.title('Objects Spawner')
        p.description('Choose a color:')
        p.option('Default', 'Default Color')
        for i in sorted(COLORS.keys()):
            p.option(i, i)
        p.footer('* Aim at an object to change its color')
        p.send(uid)
        return
    elif choice == 7:
        toggle_ui(uid)
    addon_page(uid)

# Spawn Objects Blocks
def categorys_list_HANDLE(uid, category, prev_page):
    p = sam.PageSetup(category + '_objects', category_objects_HANDLE, 'categorys_list')
    p.title('Objects Spawner')
    p.description('Choose an object:')
    for num, obj in enumerate(sorted(OBJECTS[category].keys())):
        if num == 0 or num % 6 == 0:
            p.option((category, 'delete_%s' % num), '(QUICK DELETE) [Aim To Delete]')
        p.option((category, obj), sam.title(obj))
    sam.msg.hud(uid, 'Objects Spawner | Objects will spawn exactly where you are aiming at')
    p.send(uid)

def category_objects_HANDLE(uid, choice, prev_page):
    # Return the page to the user
    prev_page.return_page(uid)
    # If the choice is a Quick Delete option, delete the object
    if choice[1].startswith('delete'):
        delete_object(uid)
        return
    cat, obj = choice
    inf = OBJECTS[cat][obj]
    # Pre-cache the model and spawn the object
    es.precachemodel(inf['model'])
    es.server.cmd('es_xprop_%s_create %i %s' % (inf['type'], uid, inf['model']))
    # Cache object meta-data
    index = int(es.ServerVar('eventscripts_lastgive'))
    SPAWNED[index] = {'name': sam.title(obj),
                      'id': 'sam_%s_%s' % (inf['type'], sam.timestamp()),
                      'type': inf['type']}
    # Change object targetname for easy tracking
    es.entitysetvalue(index, 'targetname', SPAWNED[index]['id'])

# Move Object Block
def move_objects_HANDLE(uid, choice, prev_page):
    # Change the user move speed
    speed = CACHE['move_speed'][uid]
    if choice == 1:
        if speed == 1:
            speed = 8
        else:
            speed = speed + speed if speed < 128 else 1
        CACHE['move_speed'][uid] = speed
        # Return page rebuilt to the user
        addon_page(uid)
        sam.handle_choice(4, uid)
        return
    # Any other, return the same page to the user
    prev_page.return_page(uid)
    # Get view object
    index = view_object(uid)
    if not index:
        return
    offset, cord = tuple(choice)
    i = dict(zip(('x', 'y', 'z'), es.getindexprop(index, m_vecOrigin).split(',')))
    if offset == '+':
        i[cord] = float(i[cord]) + speed
    else:
        i[cord] = float(i[cord]) - speed
    es.entitysetvalue(index, 'origin', '%s %s %s' % (i['x'], i['y'], i['z']))

# Rotate Objects Block
def rotate_object_HANDLE(uid, cord, prev_page):
    prev_page.return_page(uid)
    index = view_object(uid)
    if not index:
        return
    angles = es.entitygetvalue(index, 'angles').split()
    if cord in (0, 1, 2):
        angles[cord] = str(float(angles[cord]) + 10)
    elif cord in (3, 4, 5):
        angles[cord-3] = str(float(angles[cord-3]) - 10)
    es.entitysetvalue(index, 'angles', ' '.join(angles))

# Change Objects Color
def color_objects_HANDLE(uid, choice, prev_page):
    prev_page.return_page(uid)
    index = view_object(uid)
    if not index:
        return
    m_nRenderMode = 'CBaseEntity.m_nRenderMode'
    m_nRenderFX   = 'CBaseEntity.m_nRenderFX'
    r, g, b = COLORS[choice].split(',') if choice in COLORS.keys() else (255, 255, 255)
    color = int(r) + (int(g) << 8) + (int(b) << 16) + (int(255) << 24)
    if color >= 2**31: color -= 2**32
    es.setindexprop(index, m_nRenderMode, es.getindexprop(index, m_nRenderMode) | 1)
    es.setindexprop(index, m_nRenderFX, es.getindexprop(index, m_nRenderFX) | 256)
    es.setindexprop(index, 'CBaseEntity.m_clrRender', color)

# Delete Object Blocks
def delete_object(uid=None, index=None):
    # If an object index is not given, look for an object the player is aiming at
    if index is None:
        index = view_object(uid)
        # Check whether the player is aiming at a valid object
        if index is None:
            sam.msg.hud(uid, 'You are not aiming at a valid object.')
            return
    # Check if object is cached, and de-cache it
    if index in SPAWNED.keys():
        del SPAWNED[index]
    # Remove the object entity
    es.server.cmd('ent_remove_all ' + es.entitygetvalue(index, 'targetname'))

def delete_all(uid):
    # Clear spawned cache
    SPAWNED.clear()
    # Gather all the valid objects entities
    valid = (i for i in es.createentitylist().keys()\
             if es.entitygetvalue(i, 'targetname').startswith('sam'))
    # Remove all objects if any were found
    if valid:
        for idx in valid:
            delete_object(uid, idx)
    else: sam.msg.hud(uid, 'There are no any objects spawned by SAM')

def view_object(uid):
    view = '%s_view_object' % sam.getsid(uid)
    entities = es.createentitylist().keys()
    entities_names = dict((i, es.entitygetvalue(i, 'targetname')) for i in entities)
    es.entsetname(uid, view)
    for entity in entities:
        entity = int(entity)
        if es.entitygetvalue(entity, 'targetname') != view:
            continue
        ent_name = entities_names[entity]
        ent_clas = es.entitygetvalue(entity, 'classname')
        if ent_name == view:
            ent_name = 'sam_%s_%s' % (ent_clas, sam.timestamp())
        es.entitysetvalue(entity, 'targetname', ent_name)
        return entity if ent_clas.startswith('prop')\
                      and distance(uid, entity) < 700\
                      else None
    return None

def distance(uid, idx):
    return vecmath.distance(vecmath.vector(es.getplayerlocation(uid)),
                            vecmath.vector(es.getindexprop(idx, m_vecOrigin).split(',')))

# Game Events
def break_prop(ev):
    # De-cache prop if it breaks
    index = int(ev['entindex'])
    if index in SPAWNED.keys():
        del SPAWNED[index]



        
