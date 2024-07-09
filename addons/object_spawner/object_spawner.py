from math import sqrt
import es
import psyco

psyco.full()

sam = es.import_addon('sam')

# Global Variables
OBJECTS = sam.databases.load(sam.path.addons + '/object_spawner/objects.json', True)
SPAWNED = {}
LASTGIVE = es.ServerVar('eventscripts_lastgive')
VECTOR_ORIGIN = 'CBaseEntity.m_vecOrigin'
OBJECT_COUNTER = 0
UI_SEPARATOR = '-' * 50
UI_USERS = sam.databases.load('object_spawner_ui.json')
UI_LOOP = False
COLORS = {
    'Blue': '0,0,255',
    'Black': '0,0,0',
    'Brown': '150,100,0',
    'Dark Red': '125,0,0',
    'Gray': '175,175,175',
    'Light Green': '0,255,0',
    'Orange': '255,150,0',
    'Pink': '255,0,255',
    'Purple': '175,0,175',
    'Red': '255,0,0',
    'Turkey': '0,255,255',
    'Yellow': '255,255,0'
}

# Load
def load():

    # Register the addon's Admin permission
    sam.admins.register_addon_permission('object_spawner_menu')

    # Register the addon chat command
    sam.cmds.chat('!props', addon_menu)

# Unload
def unload():

    # Unregister the addon chat command
    sam.cmds.delete('!props')

    # Stop View Object UI update loop
    if UI_USERS:
        sam.cancel_delay('op_object_ui_loop')
        for userid in UI_USERS:
            toggle_ui(userid, False)

    # Save the the UI users dictionary
    save_ui_data()


def addon_menu(userid, opened_from_command=False):

    # Check if the user has permission to use the addon
    if sam.admins.is_allowed(userid, 'object_spawner_menu'):
        if not opened_from_command:
            sam.home_page(userid)

    menu = sam.Menu('object_spawner', object_spawner_HANDLE, 'home_page')
    menu.title('Object Spawner')
    menu.add_option(1, 'Spawn Objects')
    menu.add_option(2, 'Delete Object [Aim To Delete]')
    menu.add_option(3, 'Remove All Objects')
    menu.separator()
    menu.add_option(4, 'Move Object')
    menu.add_option(5, 'Rotate Object')
    menu.add_option(6, 'Color Object')
    menu.separator()
    menu.add_option(7,
        'Object UI: %s' % ('Enabled' if userid in UI_USERS else 'Disabled')
    )
    menu.send(userid)

def object_spawner_HANDLE(userid, choice, submenu):

    submenu.send(userid)

    # Option to spawn objects
    if choice == 1:
        menu = sam.Menu('op_categorys_list', categorys_list_HANDLE, 'object_spawner')
        menu.title('Objects Spawner')
        menu.description('Choose a category:')

        # Get the objects dictionary
        for category in sorted(OBJECTS):
            menu.add_option(category, sam.title(category))

        menu.send(userid)
        return
    
    # Option to delete objects
    elif choice == 2:
        # Get the index of the object the user is looking at
        index = get_view_object(userid)
        if index:
            delete_object(index, userid)
            addon_menu(userid)
        return
    
    # Option to delete all objects
    elif choice == 3:
        # Check if there are any objects to be deleted
        if SPAWNED:
            delete_all_objects(userid)
            addon_menu(userid)
        else:
            sam.msg.hud(userid, 'No valid objects found', 'Object Spawner')
        return

    # Option to toggle the user's Object UI
    elif choice == 7:
        toggle_ui(userid)
        addon_menu(userid)
    
# Spawn Objects Process
def categorys_list_HANDLE(userid, category, submenu):

    menu = sam.Menu('op_%s_object_list' % category, object_list_HANDLE, submenu)
    menu.title('Objects Spawner')
    menu.description('Choose a category:')

    for num, obj in enumerate(sorted(OBJECTS[category])):
        num += 1
        # Add a quick delete option as the first option in every page
        if num == 1 or num % 6 == 1:
            menu.add_option((category, num, 'delete_%s' % num), '{ QUICK DELETE }')
            menu.separator()
        menu.add_option((category, obj), sam.title(obj))

    menu.send(userid)

def object_list_HANDLE(userid, choice, submenu):

    if len(choice) > 2 and choice[2].startswith('delete_'):
        # Get the index of the object the user is looking at
        index = get_view_object(userid)
        if index:
            delete_object(index, userid)
        # Return to the previous menu
        submenu.send(userid)
        return

    # Spawn the object
    spawn_object(userid, choice[0], choice[1])
    # Return to the previous menu
    submenu.send(userid)

def spawn_object(userid, category, object_key):
    """
    Spawns an object
    """

    # Check if the category and object exist
    if not OBJECTS.get(category) or not OBJECTS[category].get(object_key):
        sam.msg.console('Unable to spawn object, category or object does not exist',
                        'Object Spawner')
        return

    # Retrieve the information of the specified object
    object_info = OBJECTS[category][object_key]

    # Create a unique id for the object
    # Unique combination: sam_{object_name}_{timestamp}_{object_counter}
    global OBJECT_COUNTER
    object_id = 'sam_%s_%s_%s' % (object_key, int(sam.timestamp()), OBJECT_COUNTER)
    OBJECT_COUNTER += 1

    # Pre-cache the model of the object before spawning it
    es.precachemodel(object_info['model'])

    # Create the object entity
    es.server.cmd(
        'es_xprop_%s_create %s %s' % (object_info['type'], userid, object_info['model'])
    )

    # Get the index of the object and set its targetname to the unique id
    index = int(LASTGIVE)
    es.entitysetvalue(index, 'targetname', object_id)

    # Save the object information in the spawned objects dictionary
    SPAWNED[index] = {
        'index': index,
        'object': sam.title(object_key),
        'object_id': object_id,        
        'position': es.getindexprop(index, VECTOR_ORIGIN),
        'type': object_info['type'],
        'model': object_info['model'],
    }

def delete_object(index, userid=None):
    """
    Deletes an object
    """

    print(UI_SEPARATOR)
    for i in es.createentitylist():
        print(i, es.entitygetvalue(i, 'targetname'))
    print(UI_SEPARATOR)

    # Check if the object exists
    if not index and userid:
        sam.msg.hud(userid,
                    'Unable to delete object %s, object does not exist' % index,
                    'Object Spawner')

    
    # Check if the object is in the spawned objects dictionary
    if index in SPAWNED:
        es.server.cmd('ent_remove_all %s' % index)

        # If the object was deleted by a player, notify them
        if userid:
            sam.msg.hud(userid,
                        'Object %s deleted' % SPAWNED[index]['object'],
                        'Object Spawner')        
            
        # Delete the object from the spawned objects dictionary
        del SPAWNED[index]

    # In case SAM has been reload, check if the object was created by SAM, if so delete it
    else:
        targetname = es.entitygetvalue(index, 'targetname')
        if targetname.startswith('sam_'):
            es.server.cmd('ent_remove_all %s' % index)
        elif targetname == '':
            es.server.cmd('ent_remove_all %s' % index)

def delete_all_objects(userid=None):
    """
    Deletes all spawned objects
    """

    # Loop through all the spawned objects
    for index in SPAWNED:
        # Delete the object
        delete_object(index)

    # Make sure the spawned objects dictionary is empty
    SPAWNED.clear()

def get_view_object(userid):
    """
    Gets the view object of a user
    """

    # Create a unique name to identify the view object
    view = '%s_view_object' % sam.get_steamid(userid)

    # Retrieve all the entities in the map
    entities = es.createentitylist()

    # Create a dictionary of all the entities and their original names
    entities_names = dict(
        (int(ent), es.entitygetvalue(ent, 'targetname')) for ent in entities
    )

    # es.entsetname() changes the name of the entity the player is looking at,
    # therefore we give it the unique name we created earlier to keep track of it
    es.entsetname(userid, view)

    # Loop through all the entities in the map
    for entity_index in entities:
        # If not the entity we are looking for, continue
        if es.entitygetvalue(entity_index, 'targetname') != view:
            continue
        # Get the entity original name and rename it back to its original name
        entity_name = entities_names[entity_index]
        es.entitysetvalue(entity_index, 'targetname', entity_name)

        # If the entity was not created by SAM then ignore it
        if not entity_name.startswith('sam_'):
            return None
        # Get the entity position
        ent_position = es.getindexprop(entity_index, VECTOR_ORIGIN)
        # Finally check if the entity is within the maximum units of the player
        if get_distance(ent_position, es.getplayerlocation(userid)) < 500:
            return entity_index

    # If the entity was not found, return None
    return None

def get_distance(vector1, vector2):
    """
    Gets the distance between two vectors in meters
    """

    # Check if the vectors are strings or tuples
    if isinstance(vector1, str):
        vector1 = tuple(float(i) for i in vector1.split(','))

    if isinstance(vector2, str):
        vector2 = tuple(float(i) for i in vector2.split(','))

    # Calculate the distance using the Euclidean distance formula
    return sqrt(sum((v1 - v2)**2 for v1, v2 in zip(vector1, vector2)))

def toggle_ui(userid, force=None):
    '''
    Toggle the UI for a user, if force is a boolean,
    it will force the UI to be enabled or disabled
    '''

    global UI_LOOP

    # Check if the user has the UI enabled, or if its forced to be disabled
    if userid in UI_USERS or force is False:
        # Delete the user from the UI users dictionary
        del UI_USERS[userid]
        sam.msg.side(userid, '') # Clear the user UI
        sam.msg.hud(userid, 'Object UI Disabled', 'Object Spawner')

        # Check if there aren't any users with the UI enabled
        if not UI_USERS:
            UI_LOOP = False
            sam.cancel_delay('op_object_ui_loop')
            sam.msg.console('Object UI Loop disabled', 'Object Spawner')

    # Check if the user has the UI disabled, or if its forced to be enabled
    elif userid not in UI_USERS or force is True:
        # Add the user to the UI users dictionary
        UI_USERS[userid] = {'move_speed': 5, 'rotate_speed': 5}
        sam.msg.hud(userid, 'Object UI Enabled', 'Object Spawner')

        # Check if the UI loop is not running
        if not UI_LOOP:
            UI_LOOP = True
            object_ui_loop()
            sam.msg.console('Object UI Loop enabled', 'Object Spawner')


def object_ui_loop():
    '''
    Loops through all the users with the UI enabled
    '''

    for userid in UI_USERS:
        if sam.get_userid(userid):
            object_ui(userid)
    sam.delay_task(0.25, 'op_object_ui_loop', object_ui_loop, ())

def object_ui(userid):
    '''
    Updates the UI for a user
    '''
        
    # Get the index and targetname of the object the user is looking at
    index = get_view_object(userid)
    targetname = es.entitygetvalue(index, 'targetname')
    
    if index in SPAWNED:
        
        # Get the object information
        object_info = SPAWNED.get(index)

        # Setup the UI text
        object_id = object_info['object_id']
        name = object_info['object']
        distance = get_distance(object_info['position'],
                                es.getplayerlocation(userid)) * 0.0254

    elif targetname.startswith('sam_'):

        # Setup the UI text
        object_id = targetname
        name = 'Unknown'
        distance = get_distance(es.getindexprop(index, VECTOR_ORIGIN),
                                es.getplayerlocation(userid)) * 0.0254
        
    else:
        sam.msg.side(userid,
            UI_SEPARATOR,
            'Not Looking At A Valid Object',
            UI_SEPARATOR,
        )
        return

    # Display the UI text
    sam.msg.side(userid,
        UI_SEPARATOR,
        'Object ID: %s' % object_id,
        'Object Name: %s' % name,
        'Distance: %.2f meters' % distance,
        UI_SEPARATOR,
    )

def save_ui_data():
    """
    Saves the objects database
    """

    sam.databases.save('object_spawner_ui.json', UI_USERS)

# Game Events
def es_map_start(ev):
    """
    Called when a map starts
    """

    # Clear the spawned objects dictionary
    SPAWNED.clear()

    # Save the the UI users dictionary
    save_ui_data()

def round_start(ev):
    """
    Called when a round starts
    """

    # Clear the spawned objects dictionary
    SPAWNED.clear()

def break_prop(ev):
    """
    Called when a prop is broken
    """

    # Get the index of the broken prop
    index = int(ev['entindex'])

    # Check if the prop is in the spawned objects dictionary
    if index in SPAWNED:
        # Remove the object from the spawned objects dictionary
        delete_object(index)

def break_breakable(ev):
    """
    Called when a breakable is broken
    """

    # Get the index of the broken breakable
    index = int(ev['entindex'])

    # Check if the breakable is in the spawned objects dictionary
    if index in SPAWNED:
        # Remove the object from the spawned objects dictionary
        delete_object(index)