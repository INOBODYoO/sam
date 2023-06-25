import es
import psyco

psyco.full()

sam = es.import_addon('sam')


def module_menu(userid):
    """ Displays the main menu of the module """

    # Check if the player is allowed to access the module
    if not sam.admins.is_allowed(userid, 'admins_manager'):
        sam.home_page(userid)
        return

    # Initialize the menu
    menu = sam.Menu('admins_manager', admins_manager_HANDLE, 'home_page')
    menu.title('Admins Manager')
    menu.add_option(1, 'Add New Admin')
    menu.add_option(2, 'Remove An Admin')
    menu.add_option(3, 'Admins Profile Editor')
    menu.separator()
    menu.add_line(':: Admins Groups')
    menu.separator()
    menu.add_option(4, 'Create a Group')
    menu.add_option(5, 'Delete a Group')
    menu.add_option(6, 'Groups Profile Editor')
    # Get the number of online admins
    admins = sam.admins.list()
    super_admins = sam.admins.list('super_admins')
    for admin in super_admins:
        del admins[admin]
    menu.footer('Currently Online:',
                '- Super Admins: %s' % len(super_admins.keys()) if super_admins else '',
                '- Admins: %s' % len(admins) if admins else '')
    # Send the menu
    menu.send(userid)


def admins_manager_HANDLE(userid, choice, submenu):
    """ Handles the main menu of the module """

    # First check for option number 4, to create a new Admin Group
    # We check for option 4 first, because it's not required sending a menu to the user.
    # Instead, we can directly execute the required code and skip the rest of the code.
    if choice == 4:
        # Register a chat filter to get the name of the new group
        f = sam.chat_filter.register('admin_group_creation')
        f.function = admin_group_creation_FILTER
        f.users.append(userid)
        f.cancel_option = module_menu
        f.cancel_args = ('userid',)
        f.instructions_page('Type in the chat name of the new group',
                            ' ',
                            '* The name can only have up to 12 characters')
        return
    # Dictionary mapping choice to option tuple
    option = {
        1: ('Add New Admin', 'Choose the new Admin:', add_admin),
        2: ('Remove An Admin', 'Choose the Admin to remove:', remove_admin_or_group),
        3: ('Admins Profile Editor', 'Choose an Admin:', profile_editor),
        5: ('Delete a Group', 'Choose the Group to delete:', remove_admin_or_group),
        6: ('Groups Profile Editor', 'Choose a Group:', profile_editor)
    }.get(choice)
    # Check for an invalid option
    if option is None:
        submenu.send(userid)
        return
    # Initialize the menu
    menu = sam.Menu('am_admins_or_groups_list', option[2], 'admins_manager')
    menu.title(option[0])
    menu.description(option[1])
    # Start the process of adding a new Admin
    if choice == 1:
        # Get the list of non-admins players
        players = [i for i in sam.player_list() if not sam.admins.is_admin(i)]
        # Check if there are any players to be added as admins
        if not players:
            sam.msg.hud(userid, 'There are no valid players to be added as admins')
            submenu.send(userid)
            return
        # Add the players to the menu
        menu.add_options([(player, player.name) for player in players])
    # For both option 2 and 3, we need the list of admins
    elif choice in (2, 3):
        admins = sam.admins.list().values()
        menu.add_options([
            (admin.steamid,
             '%s [Super Admin]' % admin.name if admin.super_admin else admin.name)
            for admin in admins
        ])
    # For both option 5 and 6, we need the list of groups
    elif choice in (5, 6):
        groups = sam.admins.list('groups')
        # Check if there are any groups available
        if not len(groups):
            sam.msg.hud(userid, 'There are no groups available')
            submenu.send(userid)
            return
        menu.add_options([(group, groups[group].name) for group in groups])
    # Send the menu to the player
    menu.send(userid)


def add_admin(userid, user, submenu=False, super_admin=False):
    """ Adds a new admin to the Admins list """

    # Get the steamid of the player
    steamid = sam.get_steamid(user)
    # Check if the player is already an admin
    if sam.admins.is_admin(steamid):
        sam.msg.hud(userid, 'This player is already an admin')
        submenu.send(user)
        return
    # Initialize the new Admin object
    sam.admins.new_admin(steamid, super_admin)
    sam.msg.hud('#admins', '%s is now an Admin!' % user.name)
    # Send the player to the Profile Editor of the new Admin
    profile_editor(userid, steamid, 'admins_manager')


def remove_admin_or_group(userid, object, submenu):
    """ Removes an admin from the Admins list or deletes a group """

    # Send the user back to the module's menu either way
    module_menu(userid)
    # If the object is a group, delete it
    if object in sam.admins.list('groups'):
        sam.msg.hud(userid, '%s group deleted!' % sam.admins(object).name)
        sam.admins.delete_group(object)
        return
    # Else check if the object is an admin
    elif sam.admins.is_admin(object):
        # Get the admin object
        admin = sam.admins(object)
        # Check if the user is trying to remove himself
        if admin.steamid == sam.get_steamid(userid):
            sam.msg.hud(userid, 'You cannot remove yourself from the admins list')
            submenu.send(userid)
            return
        # If the admin to be removed is a super admin and the player trying to remove
        # them is not a super admin, then we should not allow the removal at all
        elif admin.super_admin and not sam.admins.is_super_admin(userid):
            sam.msg.hud(userid, 'You cannot remove a Super Admins')
            submenu.send(userid)
            return
        sam.msg.hud('#admins', 'Admin %s deleted from the admins list!' % admin.name)
        # Check if user is active
        player = sam.get_userid(admin.steamid)
        if player:
            # Notify the player that he has been removed
            sam.msg.hud(admin.steamid,
                        'You have been removed from the admins list!',
                        'Your active menu has been closed as a safety measure.')
            # Close the Admin active menu if it's open
            sam.handle_choice(None, player, force_close=True)
        # Delete the admin
        sam.admins.delete_admin(object)


def profile_editor(userid, object, submenu):
    """ Edits the profile of an admin or a group """

    # Save the database in case something was previously changed and not saved
    sam.admins.save_database()
    # Check if the player is allowed to access the module
    if not sam.admins.is_allowed(userid, 'admins_manager'):
        sam.home_page(userid)
        return
    is_admin = sam.admins.is_admin(object)
    target = sam.admins(object)
    # Check if the player is trying to edit a Super Admin profile
    if is_admin and not sam.admins.is_super_admin(userid) and target.super_admin:
        sam.msg.hud(userid, 'You cannot edit a Super Admin profile')
        submenu.send(userid)
        return
    # Initialize the menu
    menu = sam.Menu('am_profile_editor', profile_editor_HANDLE, 'admins_manager')
    menu.max_lines = 5 if is_admin else 6
    menu.title('%s Profile Editor' % 'Admins' if is_admin else 'Groups')
    # If target is an Admin:
    if is_admin:
        menu.description('* NAME: ' + target.name,
                         '* STEAMID: ' + target.steamid,
                         '* SINCE: ' + target.admin_since)
        menu.add_options([
            ((object, 'super_admin'), 'Super Admin: ' + yes_or_no(target.super_admin)),
            ((object, 'admin_group'), 'Admin Group: ' + sam.title(target.group))
        ])
    # If target is a Group:
    else:
        
        print(target)
        
        menu.description('* GROUP NAME: ' + target.name)
        menu.add_options([
            ((object, 'members'),
             'Group Members: (%s)' % len(sam.admins.get_group_members(object))),
            ((object, 'rename'), 'Rename Group'),
            ((object, 'color'), 'Group Color: ' + sam.title(target.color))
        ])
    menu.add_options([
        ((object, 'ban_level'), 'Ban Level: %s' % target.ban_level),
        ((object, 'immunity'), 'Immunity Level: %s' % target.immunity_level),
        ((object, 'addons'), 'Addons Permissions')
    ])
    # At last, list all the Admin permissions on a new page
    menu.next_page()
    menu.add_line('Permissions:')
    # Finally, list all the permissions
    menu.add_options([
        ((object, permission),
         '%s: %s' % (sam.title(permission), yes_or_no(target.permissions[permission])))
        for permission in sorted(target.permissions)
    ])
    # Send the menu to the player
    menu.send(userid)


def profile_editor_HANDLE(userid, choice, submenu):
    """ Handles the profile editor menu choice """

    object, key = choice
    is_admin = sam.admins.is_admin(object)
    target = sam.admins(object)
    # Check if Admin/Group still exists
    if not target:
        invalid_admin_group(userid, is_admin)
        return
    # In case the chosen key requires a menu to be displayed, we use a dictionary
    # to store the menu_id, handler, submenu, title and description.
    options = {
        'admin_group': (
            ('am_change_admin_group', change_admin_group_HANDLE, 'am_profile_editor'),
            'Change Admin Group',
            'Select the Admin Group:'
        ),
        'members': (
            ('am_edit_group_members', edit_group_members_HANDLE, 'am_profile_editor'),
            'Groups Profile Editor',
            'Edit Group Members:'
        ),
        'color': (
            ('am_change_group_color', change_group_color_HANDLE, 'am_profile_editor'),
            'Groups Profile Editor',
            'Select the Group Color:'
        ),
        'immunity': (
            ('am_change_immunity_level', change_immunity_level_HANDLE, 'am_profile_editor'),
            '%s Profile Editor' % ('Admins' if is_admin else 'Groups'),
            'Choose Immunity Level:'
        ),
        'addons': (
            ('am_change_addons', addons_permissions_HANDLE, 'am_profile_editor'),
            'Addons Permissions',
            'Select the permissions:'
        ),
    }
    if key not in options:
        if key == 'super_admin':
            # Check if the user is allowed to manage Super Admins
            if not sam.admins.is_super_admin(userid):
                sam.msg.hud(userid, 'Only Super Admins can manage other Super Admins')

            elif len(sam.admins.list('super_admins')) == 1 \
                    and sam.get_steamid(userid) == target.steamid:
                sam.msg.hud(userid,
                            'Unable to perform this action!',
                            'SAM requires one Super Admin to function properly')
            else:
                target.super_admin = not target.super_admin
        elif key == 'rename':
            sam.cache.temp[userid] = object
            f = sam.chat_filter.register('rename_admin_group')
            f.function = rename_admin_group_FILTER
            f.users.append(userid)
            f.cancel_option = module_menu
            f.cancel_args = ('userid',)
            f.instructions_page('Type in the chat name of the group',
                                ' ',
                                '* The name can only have up to 12 characters')
            return
        elif key == 'ban_level':
            target.ban_level = (target.ban_level + 1) % 4
        elif key in target.permissions.keys():
            target.toggle_permission(key)
        # Send the user back to the profile editor menu
        profile_editor(userid, object, submenu.object.submenu)
        sam.send_menu(userid, submenu.menu_id, submenu.page)
        return
    menu_setup, title, description = options[key]
    # Initialize the menu
    menu = sam.Menu(*menu_setup)
    menu.title(title)
    menu.description(description)
    if key == 'admin_group':
        groups = sam.admins.list('groups')
        # Check if there are any groups available
        if not groups:
            sam.msg.hud(userid, 'There are no groups available at the moment')
            submenu.send(userid)
            return
        # Add an option to remove the admin from his current group
        if target.group:
            menu.add_option((object, 'remove'), 'Remove from current group')
        # Add the groups as options
        for group in groups:
            menu.add_option((object, group),
                            sam.title(group) + ' (current)'
                            if group == target.group else sam.title(group))
    elif key == 'members':
        for admin in sam.admins.list().values():
            # Compile the text for each option
            text = '%s %s' % ('[ X ]' if admin.group == object else '[ - ]', admin.name)
            if admin.group and admin.group != object:
                text += ' (%s)' % sam.title(admin.group)
            menu.add_option((object, admin.steamid), text)
        menu.footer('- Selecting an Admin will add him to the group',
                    '- Selected Admins will be removed from the group')
    elif key == 'color':
        for color in sorted(sam.msg.colors.keys()):
            menu.add_option((object, color), sam.title(color))
    elif key == 'immunity':
        for level in range(0, 101):
            menu.add_option((object, level), level)
        menu.footer('Current Level: %s' % target.immunity_level)
    elif key == 'addons':
        for perm, val in target.addons_permissions.items():
            menu.add_option((object, perm), sam.title(perm) + ': ' + yes_or_no(val))
    # Send the menu
    menu.send(userid)


def change_admin_group_HANDLE(userid, choice, submenu):
    """ Handles the change admin group menu choice """

    # Get the admin object
    object, group = choice
    admin = sam.admins(object)
    # Check if the admin still exists
    if not admin:
        invalid_admin_group(userid, True)
        return
    # If the choice is 'remove', remove the admin from his current group
    if group == 'remove':
        sam.msg.hud('#admins', '%s removed from %s group' % (admin.name,
                                                             sam.title(admin.group)))
        admin.group = False
    # Else if the player is trying to add the admin to the group
    else:
        sam.msg.hud('#admins', '%s added to %s group' % (admin.name, sam.title(group)))
        admin.group = group
    # Send the user directly to the profile editor
    profile_editor(userid, object, 'admins_manager')


def edit_group_members_HANDLE(userid, choice, submenu):
    """ Handles the edit group members menu choice """

    # Get the admin object
    object, admin = choice
    admin = sam.admins(admin)
    # Check if the admin still exists
    if not admin:
        invalid_admin_group(userid, True)
    # If the admin is already in the group, remove him
    elif admin.group == object:
        sam.msg.hud('#admins', admin.name + ' removed from %s group' % admin.group)
        admin.group = False
    # Otherwise, add him to the group
    else:
        admin.group = object
        sam.msg.hud('#admins', admin.name + ' added to %s group' % admin.group)

    # Send the user back to the Group Members menu
    profile_editor_HANDLE(userid, (object, 'members'), 'am_profile_editor')
    sam.send_menu(userid, submenu.menu_id, submenu.page)


def change_group_color_HANDLE(userid, choice, submenu):
    """ Handles the change group color menu choice """

    object, color = choice
    group = sam.admins(object)
    # Set the color
    group.color = color
    group._attach_color()
    # Send the user back to the Profile Editor menu
    profile_editor(userid, object, 'admins_manager')


def change_immunity_level_HANDLE(userid, choice, submenu):
    """ Handles the change immunity level menu choice """

    # Get the target object
    object, choice = choice
    is_admin = sam.admins.is_admin(object)
    target = sam.admins(object)
    # Check if either the Admin or the Group still exists
    if not target:
        invalid_admin_group(userid, is_admin)
        return
    # Set the immunity level
    target.immunity_level = choice
    sam.msg.hud('#admins', target.name + '%s immunity level set to %s' %
                ('\'s' if is_admin else ' group', choice))
    # Send the user back to the Profile Editor menu
    profile_editor(userid, object, 'admins_manager')


def addons_permissions_HANDLE(userid, choice, submenu):
    """ Handles the Addons permissions menu choice """

    object, choice = choice
    target = sam.admins(object)
    # Check if either the Admin or the Group still exists
    if not target:
        invalid_admin_group(userid, sam.admins.is_admin(target))
        return
    # Toggle the permission
    target.toggle_permission(choice)
    # We need to build the menu again since changes were made to the Admin/Group object
    profile_editor_HANDLE(userid, (object, 'addons'), 'am_profile_editor')
    sam.send_menu(userid, submenu.menu_id, submenu.page)


# First Admin Setup
def first_admin_setup(userid):
    """ Displays the First Admin Setup menu """

    # Initialize the menu
    menu = sam.Menu('first_admin_setup', first_admin_setup_HANDLE)
    menu.header = False
    menu.title('First Admin Setup')
    menu.add_line('Hello %s' % es.getplayername(userid),
                  ' ',
                  'SAM requires one Admin to be set up before it can be used.',
                  'If you are the server owner/operator and want to',
                  'set yourself up as Admin, choose to proceed.',
                  ' ')
    menu.add_option(1, 'Yes, Proceed')
    menu.add_option(2, 'No, I\'m not the server owner/operator')
    # Send the menu
    menu.send(userid)


def first_admin_setup_HANDLE(userid, choice, submenu):
    """ Handles the First Admin Setup menu choice """

    if choice in (1, 2):
        del sam.cache.menus['first_admin_setup']
    # If the user chooses to proceed, then start the RCON verification process
    if choice == 1:
        # Register a chat filter to get the name of the new group
        f = sam.chat_filter.register('rcon_verification')
        f.function = rcon_verification_FILTER
        f.users.append(userid)
        f.cancel_option = True
        f.instructions_page('In order to proceed, SAM needs to verify that you are',
                            'the server owner/operator.',
                            'Please type the server RCON password in the chat.')


# Chat Filters
def rcon_verification_FILTER(userid, text, teamchat):
    """ Handles the RCON verification chat filter """
    # Check if the user entered the correct RCON password
    if text == es.ServerVar('rcon_password'):
        # Create the Admin object
        sam.admins.new_admin(sam.get_steamid(userid), super_admin=True)
        # Send the user to the Home Page
        sam.home_page(userid)
        sam.msg.hud(userid,
                    'RCON Password confirmed!',
                    'You are now a Super Admin, type !sam in chat to access the menu.',
                    'It is also recommended to make a key bind: bind <key> sam_menu')
    # Otherwise, notify the user that the RCON password is incorrect
    else:
        sam.msg.hud(userid, 'RCON Password incorrect! Operation cancelled!')
    return 0, 0, 0


def admin_group_creation_FILTER(userid, text, teamchat):
    """ Handles the Admin Group Creation chat filter """

    # Remove the user from the chat filter
    sam.chat_filter.remove_user(userid, 'admin_group_creation')
    # Send the user to the Module Page in case the operation is canceled
    module_menu(userid)
    # Check if the user canceled the operation
    text = sam.compile_text(text).lower()
    if text == '!cancel':
        sam.msg.hud(userid, 'Operation cancelled!')
        return 0, 0, 0
    # Check if the name has more than 12 characters
    if len(text) > 12:
        sam.msg.hud(userid, 'The name must be less than 12 characters!',
                    'Operation cancelled!')
    elif text in sam.admins.groups.keys():
        sam.msg.hud(userid, 'This group already exists!',
                    'Operation cancelled!')
    else:
        sam.admins.new_group(text)
        sam.msg.hud('#admins', 'Group %s created!' % text)
        profile_editor(userid, text, 'admins_manager')
    return 0, 0, 0


def rename_admin_group_FILTER(userid, text, teamchat):
    """ Handles the Admin Group Rename chat filter """

    # Delete the chat filter
    sam.chat_filter.remove_user(userid, 'rename_admin_group')
    # Send the user to the Module Page in case the operation is canceled
    module_menu(userid)
    text = sam.compile_text(text).lower()
    # Check if the name has more than 12 characters
    if len(text) > 12:
        sam.msg.hud(userid, 'The name must be less than 12 characters!',
                    'Operation cancelled!')
    elif text in sam.admins.groups.keys():
        sam.msg.hud(userid, 'This group already exists!', 'Operation cancelled!')
    elif userid in sam.cache.temp.keys():
        key = sam.cache.temp[userid]
        sam.msg.hud('#admins',
                    'Renamed %s group to %s created!' % (sam.admins(key).name, text))
        sam.admins.groups[text] = sam.admins.groups.pop(key)
        sam.admins.groups[text].id = text
        sam.admins.groups[text]._attach_color()
        profile_editor(userid, text, 'admins_manager')
        del sam.cache.temp[userid]
    return 0, 0, 0


# Functions
def yes_or_no(boolean):
    """ Returns Yes or No based on the boolean value """
    return 'Yes' if boolean else 'No'


def invalid_admin_group(userid, is_admin):
    """ Displays an error message when the admin or group doesn't exist anymore """
    sam.msg.hud(userid,
                'This ' + 'admin' if is_admin else 'group' + ' does not exist anymore')
    module_menu(userid)
