#!/usr/bin/python
# -*- coding: utf-8 -*-

import es

sam = es.import_addon('sam')

def module_menu(userid):
    """
    Displays the main menu of the module
    """

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

    # Get the list of 
    admins = []
    super_admins = []

    # Construct two lists of admins, one for super admins and one for regular admins
    for admin in sam.admins.list():
        if admin.super_admin:
            super_admins.append(admin)
        else:
            admins.append(admin)

    menu.footer('Currently Online:',
                '- Super Admins: %s' % len(super_admins) if super_admins else '',
                '- Admins: %s' % len(admins) if admins else '')

    # Send the menu
    menu.send(userid)

def admins_manager_HANDLE(userid, choice, submenu):
    """
    This function handles the main menu of the admin management module.
    """

    if choice == 4:
        f = sam.chat_filter.register('admin_group_creation')
        f.function = admin_group_creation_FILTER
        f.users.append(userid)
        f.cancel_option = module_menu
        f.cancel_args = ('userid',)
        f.instructions_page('Type in the chat name of the new group',
                            ' ',
                            '* The name can only have up to 12 characters')
        return

    # Get the option tuple from the dictionary
    option = {
        1: ('Add New Admin', 'Choose the new Admin:', add_admin),
        2: ('Remove An Admin', 'Choose the Admin to remove:', remove_admin_or_group),
        3: ('Admins Profile Editor', 'Choose an Admin:', profile_editor),
        5: ('Delete a Group', 'Choose the Group to delete:', remove_admin_or_group),
        6: ('Groups Profile Editor', 'Choose a Group:', profile_editor)
    }.get(choice)

    # Initialize the next menu
    menu = sam.Menu('am_admins/groups_list', option[2], 'admins_manager')
    menu.title(option[0])
    menu.description(option[1])

    # Construct a list of non-admin players using Profile System
    if choice == 1:
        def condition(player):
            return not sam.admins.is_admin(player.steamid)
        menu.construct_players_profile_list(condition_function=condition)

    # If the user chose to remove an admin or edit an admin's profile (choices 2 and 3),
    # we need to list the current admins.
    elif choice in (2, 3):
        menu.add_options(
            [
                (
                    admin.steamid,
                    admin.name + ' [Super Admin]' if admin.super_admin else admin.name
                )
                for admin in sam.admins.list()
            ]
        )

    # If the user chose to delete a group or edit a group's profile (choices 5 and 6),
    # we need to list the current groups.
    elif choice in (5, 6):
        groups = sam.admins.list('groups')
        # If there are no groups, display a message and resend the current menu.
        if not len(groups):
            sam.msg.hud(userid, 'There are no groups available')
            submenu.send(userid)
            return
        menu.add_options([(group, groups[group].name) for group in groups])

    # Send the next menu to the player
    menu.send(userid)


def add_admin(userid, player, submenu=False, super_admin=False):
    """
    Adds a new admin to the Admins list
    """

    # Check if the player is already an admin
    if sam.admins.is_admin(player.steamid):
        sam.msg.hud(userid, 'This player is already an admin')
        submenu.send(userid)
        return

    # Initialize the new Admin object
    sam.admins.new_admin(player, super_admin)
    sam.msg.hud('#admins', '%s is now an Admin!' % player.name)

    # Send the player to the Profile Editor of the new Admin
    profile_editor(userid, player.steamid, 'admins_manager')


def remove_admin_or_group(userid, target, submenu):
    """
    This function removes an admin from the Admins list or deletes a group.
    """

    # Regardless of the outcome, we send the user back to the module's menu.
    module_menu(userid)

    # If the target is a group, we delete it.
    if target in sam.admins.list('groups'):
        sam.msg.hud(userid, '%s group deleted!' % sam.admins.get_group(target).name)
        sam.admins.delete_group(target)
        return

    # If target is not an admin, inform the user.
    if not sam.admins.is_admin(target):
        invalid_admin_group(userid, True)
        return

    # Get the admin object
    admin = sam.admins.get_admin(target)

    # In case the Admin is trying to remove himself 
    if admin.steamid == sam.get_steamid(userid):
        sam.msg.hud(userid, 'You cannot remove yourself from the admins list')
        submenu.send(userid)
        return

    # If the admin is not a super admin, and is trying to remove a super admin
    elif admin.super_admin and not sam.admins.is_super_admin(userid):
        sam.msg.hud(userid, 'You cannot remove Super Admins')
        submenu.send(userid)
        return

    # Notify the admins that the admin was removed
    sam.msg.hud('#admins', '%s removed from the admins list!' % admin.name)

    # If the admin is online, we need to close his menu and notify him that he was removed
    player = sam.get_userid(admin.steamid)
    if player:
        sam.msg.hud(admin.steamid,
                    'You have been removed from the admins list!',
                    'Your active menu has been closed as a safety measure.')
        sam.menu_system.handle_choice(None, player, force_close=True)

    # Finally, remove the admin from the Admins list
    sam.admins.delete_admin(target)


def profile_editor(userid, choice, submenu):
    """
    Edits the profile of an admin or a group
    """

    # Assign sam.admins to a variable to reduce redundancy
    admins = sam.admins
    admins.save_database()

    # Check if the user has permission to manage admins
    if not admins.is_allowed(userid, 'admins_manager'):
        sam.home_page(userid)
        return

    # Get the target admin or group based on the choice
    target_id = choice
    is_admin = admins.is_admin(target_id)
    target = admins.get_admin(target_id) if is_admin else admins.get_group(target_id)

    # Check if the player is trying to edit a Super Admin profile
    if is_admin and not admins.is_super_admin(userid) and target.super_admin:
        sam.msg.hud(userid, 'You cannot edit a Super Admin profile')
        submenu.send(userid)
        return

    # Initialize the menu
    menu = sam.Menu('am_profile_editor', profile_editor_HANDLE, 'admins_manager')
    menu.max_lines = 5 if is_admin else 6
    menu.build_function = profile_editor
    menu.build_arguments_list = [userid, target_id, submenu]
    menu.title('%s Profile Editor' % ('Admins' if is_admin else 'Groups'))

    # Add options to the menu based on whether the target is an admin or a group
    if is_admin:
        menu.description('* NAME: ' + target.name,
                        '* STEAMID: ' + target.steamid,
                        '* SINCE: ' + target.admin_since)
        options = [
            ('super_admin', 'Super Admin: ' + yes_or_no(target.super_admin)),
            ('admin_group', 'Admin Group: ' + sam.title(target.group))
        ]
    else:
        menu.description('* GROUP NAME: ' + target.name)
        options = [
            ('members', 'Group Members: (%s)' % len(admins.get_group_members(target_id))),
            ('rename', 'Rename Group'),
            ('color', 'Group Color: ' + sam.title(target.color))
        ]

    # Add common options
    options += [
        ('ban_level', 'Ban Level: %s' % target.ban_level),
        ('immunity', 'Immunity Level: %s' % target.immunity_level),
        ('addons', 'Addons Permissions')
    ]

    # Add options to the menu
    menu.add_options([((target_id, option[0]), option[1]) for option in options])

    # At last, list all the Admin permissions on a new page
    menu.next_page()
    menu.add_line('Permissions:')
    menu.add_options(
        [((target_id, permission),
        '%s: %s' % (sam.title(permission), yes_or_no(target.permissions[permission])))
        for permission in sorted(target.permissions)]
    )

    menu.send(userid)

def profile_editor_HANDLE(userid, choice, submenu):
    """
    Handles the profile editor menu choice
    """

    # Unpack the choice into target_id and option
    target_id, option = choice

    # Check if the target_id is an admin
    is_admin = sam.admins.is_admin(target_id)
    
    # Get the target object
    target = sam.admins.get_admin(target_id) if is_admin \
            else sam.admins.get_group(target_id)

    # If the Admin/Group does not exist, call invalid_admin_group and return
    if not target: 
        invalid_admin_group(userid, is_admin)
        return

    # Define a dictionary to store menu setup, title, and description for each option
    option_menu_setup = {
        'admin_group': (
            ('am_change_admin_group', change_admin_group_HANDLE),
            'Change Admin Group',
            'Select the Admin Group:'
        ),
        'members': (
            ('am_edit_group_members', edit_group_members_HANDLE),
            'Groups Profile Editor',
            'Edit Group Members:'
        ),
        'color': (
            ('am_change_group_color', change_group_color_HANDLE),
            'Groups Profile Editor',
            'Select the Group Color:'
        ),
        'immunity': (
            ('am_change_immunity_level', change_immunity_level_HANDLE),
            '%s Profile Editor' % ('Admins' if is_admin else 'Groups'),
            'Choose Immunity Level:'
        ),
        'addons': (
            ('am_change_addons', addons_permissions_HANDLE),
            'Addons Permissions',
            'Select And Toggle Permissions:'
        ),
    }.get(option)

    # If the option is not in the menu setup, it means it does't require a follow up menu
    # and must be sent to a different handler to process what to do with the option
    if not option_menu_setup:
        profile_editor_non_menu_HANDLE(userid, (target, target_id, option), submenu)
        return

    # Otherwise, initialize the menu with the appropriate title and description
    menu = sam.Menu(submenu='am_profile_editor', *option_menu_setup[0])
    menu.build_function = profile_editor_HANDLE
    menu.build_arguments_list = (userid, choice, submenu)
    menu.title(option_menu_setup[1])
    menu.description(option_menu_setup[2])

    # If the option is to change the admin group
    if option == 'admin_group':
        groups = sam.admins.list('groups') # Get the list of Admin groups

        # If there are no groups, display a message and return
        if not groups:
            sam.msg.hud(userid, 'There are no groups available at the moment')
            submenu.send(userid)
            return

        # If the Admin is already in a group, add an option to remove him from the group
        if target.group:
            menu.add_option((target_id, 'remove'), 'Remove from current group')
            menu.separator()
    
        # Add each group as an option
        for group in groups:
            name = sam.title(group)
            menu.add_option(
                (target_id, group),
                name + ' (current)' if group == target.group else name
            )

    # If the option is to edit the Group members
    elif option == 'members':

        for admin in sam.admins.list():
            # Compile the text for each option
            text = '%s %s' % (
                '[ X ]' if admin.group == target_id else '[ - ]', admin.name
            )
            if admin.group and admin.group != target_id:
                text += ' (%s)' % sam.title(admin.group)
            menu.add_option((target_id, admin.steamid), text)

        menu.footer('- Selecting an Admin will add him to the group',
                    '- Selected Admins will be removed from the group')

    # If the option is 'color', add options to change the group color
    elif option == 'color':
        for color in sorted(sam.msg.colors):
            menu.add_option((target_id, color), sam.title(color))
    
    # If the option is 'immunity', add options to change the immunity level
    elif option == 'immunity':
        for level in range(0, 101):
            menu.add_option((target_id, level), level)
        menu.footer('Current Level: %s' % target.immunity_level)
        
    # If the option is 'addons', add options to change the addons permissions
    elif option == 'addons':
        permissions = sorted(target.addons_permissions.items())
        if not permissions:
            sam.msg.hud(userid, 'There are no Addons Permissions available at the moment')
            submenu.send(userid)
            return
        for permission, val in permissions:
            menu.add_option((target_id, permission),
                            sam.title(permission) + ': ' + yes_or_no(val))

    # Send the menu to the user
    menu.send(userid)

def profile_editor_non_menu_HANDLE(userid, choice, submenu):
    ''' Handles Profile Editor options that do not require a new menu '''

    # Unpack the choice into target_id, is_admin and option
    target, target_id, option = choice
    
    # Check if the user is trying to edit a Super Admin profile
    if option == 'super_admin':
        # Check if the user is allowed to manage Super Admins
        if not sam.admins.is_super_admin(userid):
            sam.msg.hud(userid, 'Only Super Admins can manage other Super Admins')
        # Check if the user is trying to remove himself

        elif len(sam.admins.list('super_admins')) == 1 \
                and sam.get_steamid(userid) == target.steamid:
            sam.msg.hud(userid,
                        'Unable to perform this action!',
                        'SAM requires one Super Admin to function properly')
        else:
            # Otherwise its safe to toggle the Super Admin status
            target.super_admin = not target.super_admin

    # Check if the user is trying to rename a group
    elif option == 'rename':
        # Register a chat filter to get the name of the new group
        sam.cache.temp[userid] = target_id
        f = sam.chat_filter.register('rename_admin_group')
        f.function = rename_admin_group_FILTER
        f.users.append(userid)
        f.cancel_option = profile_editor
        f.cancel_args = ('userid', target_id, submenu.object.submenu)
        f.instructions_page('Type in the chat name of the group',
                            ' ',
                            '* The name can only have up to 12 characters')
        return

    # Check if the user is trying to change the ban level
    elif option == 'ban_level':
        target.ban_level = (target.ban_level + 1) % 4
    
    # Check if the user is trying to change the addons permissions
    elif option in target.permissions:
        target.toggle_permission(option)
        profile_editor(userid, target_id, 'admins_manager')
        sam.menu_system.send_menu(userid, 'am_profile_editor', submenu.page)
        return
    
    # Save changes to the database
    sam.admins.save_database()

    # Make sure the Admin is allowed to manage Admins
    if sam.admins.is_allowed(userid, 'admins_manager'):
        submenu.send(userid,
                     rebuild=True,
                     rebuild_arguments=(userid, target_id, 'admins_manager'))
    else:
        sam.home_page(userid)


def change_admin_group_HANDLE(userid, choice, submenu):
    """
    Handles the change admin group menu choice
    """

    # Unpack the choice tuple for clarity
    steamid, group_action = choice
    admin = sam.admins.get_admin(steamid)

    # Check if the admin still exists
    if not admin:
        invalid_admin_group(userid, True)
        return

    # Determine the action and update the admin's group accordingly
    if group_action == 'remove':
        message = '%s removed from %s group' % (admin.name, sam.title(admin.group))
        admin.group = False
    else:
        message = '%s added to %s group' % (admin.name, sam.title(group_action))
        admin.group = group_action

    # Display the action message
    sam.msg.hud('#admins', message)

    # Redirect to the profile editor
    submenu.send(userid, rebuild=True)


def edit_group_members_HANDLE(userid, choice, submenu):
    """
    Handles adding or removing an admin from a group.
    """

    # Unpack the choice tuple
    target_group, admin_id = choice

    # Retrieve the admin object
    admin = sam.admins.get_admin(admin_id)

    # Verify the admin exists
    if not admin:
        invalid_admin_group(userid, True)
        return

    # Determine action based on current group membership
    if admin.group == target_group:
        # Remove admin from the group
        admin.group = False
        action_message = 'removed from'
    else:
        # Add admin to the group
        admin.group = target_group
        action_message = 'added to'

    # Display action message
    sam.msg.hud('#admins', '%s %s %s group' %
                (admin.name, action_message, admin.group if admin.group else 'no'))

    # Update the menu for the user
    submenu.send(userid, rebuild=True)


def change_group_color_HANDLE(userid, choice, submenu):
    """
    Handles the change group color menu choice
    """

    # Get the group object
    target, color = choice
    group = sam.admins.get_group(target)  
    
    # Set the color
    group.color = color
    group._attach_color()

    # Send the user back to the Profile Editor menu
    submenu.send(userid, rebuild=True)


def change_immunity_level_HANDLE(userid, choice, submenu):
    """
    Handles the change immunity level menu choice
    """

    # Unpack the choice tuple
    target_id, new_immunity_level = choice
    is_admin = sam.admins.is_admin(target_id)
    target = sam.admins.get_admin(target_id) if is_admin else sam.admins.get_group(target_id)

    # Check if the target exists
    if not target:
        invalid_admin_group(userid, is_admin)
        return

    # Update the immunity level
    target.immunity_level = new_immunity_level
    entity_type = 'Admin' if is_admin else 'Group'
    sam.msg.hud('#admins', "%s's %s immunity level set to %s" % 
                (target.name, entity_type, new_immunity_level))

    # Redirect to the Profile Editor menu
    submenu.send(userid, rebuild=True)


def addons_permissions_HANDLE(userid, choice, submenu):
    """
    Handles the Addons permissions menu choice
    """

    # Get the target object
    target_id, choice = choice
    is_admin = sam.admins.is_admin(target_id)
    target = sam.admins.get_admin(target_id) if is_admin else sam.admins.get_group(target_id)

    # Check if either the Admin or the Group still exists
    if not target:
        invalid_admin_group(userid, is_admin)
        return

    # Toggle the permission
    target.toggle_permission(choice)
    
    # Save changes to the database
    sam.admins.save_database()
    
    # Rebuild the page and send it back to the user
    submenu.send(userid, rebuild=True)

# First Admin Setup
def first_admin_setup(userid):
    """
    Displays the First Admin Setup menu
    """

    # Initialize the menu
    menu = sam.Menu('first_admin_setup', first_admin_setup_HANDLE)
    menu.header = False
    menu.title('First Admin Setup')
    menu.add_line(
        'Welcome, %s!' % es.getplayername(userid),
        ' ',
        'SAM needs at least one Super Admin to manage the server effectively.',
        'As the server owner or a trusted operator, you should now assign the first Super Admin.',
        'This action grants full access to all admin features.',
        ' ',
        'Are you ready to become the first Super Admin?'
    )
    menu.add_option(1, 'Yes, assign me as Super Admin')
    menu.add_option(2, 'No, cancel the setup')

    menu.send(userid)


def first_admin_setup_HANDLE(userid, choice, submenu):
    """
    Handles the First Admin Setup menu choice
    """

    # Remove the menu from the system regardless of the choice
    del sam.menu_system.menus['first_admin_setup']

    if choice == 1:
        # Proceed with RCON verification process
        f = sam.chat_filter.register('rcon_verification')
        f.function = rcon_verification_FILTER
        f.users.append(userid)
        f.cancel_option = True
        f.instructions_page(
            'Verification Required: Server Owner/Operator',
            'Please type the exact RCON password in the chat to verify.'
        )
    elif choice == 2:
        # Display operation canceled message
        sam.msg.hud(userid, 'Operation canceled!')


# Chat Filters
def rcon_verification_FILTER(userid, text, teamchat):
    """
    Handles the RCON verification chat filter
    """

    # Check if the user entered the correct RCON password
    if text == es.ServerVar('rcon_password'):
        # Create the Admin object
        sam.admins.new_admin(sam.profile_system.get_player(sam.get_steamid(userid)),
                             super_admin=True)
        # Send the user to the Home Page
        sam.home_page(userid)
        sam.msg.hud(
            userid,
            'RCON confirmed!',
            'Congratulations! You are now a Super Admin. Type !sam to access the admin menu.'
        )

    # Otherwise, notify the user that the RCON password is incorrect
    else:
        sam.msg.hud(userid, 'RCON Password incorrect! Operation canceled!')

    return 0, 0, 0


def admin_group_creation_FILTER(userid, text, teamchat):
    """
    Handles the Admin Group Creation chat filter.
    """

    # Remove the user from the chat filter and send them to the Module Page
    sam.chat_filter.remove_user(userid, 'admin_group_creation')
    module_menu(userid)

    # Format the input text for group name
    formatted_text = sam.format_text(text).lower()

    # Create the group if the name is valid
    if is_valid_group_name(userid, formatted_text):
        sam.admins.new_group(formatted_text)
        sam.msg.hud('#admins', 'Group %s created!' % formatted_text)
        profile_editor(userid, formatted_text, 'admins_manager')

    return 0, 0, 0


def rename_admin_group_FILTER(userid, text, teamchat):
    """
    Handles the Admin Group Rename chat filter
    """

    # Delete the chat filter and send the user to the Module Page
    sam.chat_filter.remove_user(userid, 'rename_admin_group')
    module_menu(userid)

    # Format and validate the new group name
    new_group_id = sam.format_text(text).lower()
    if userid not in sam.cache.temp or not is_valid_group_name(userid, text):
        return 0, 0, 0  # Early exit if the group name is not valid

    # Retrieve old group data
    old_group_id = sam.cache.temp[userid]
    old_group_name = sam.admins.get_group(old_group_id).name

    # Rename the group
    group = sam.admins.groups.setdefault(new_group_id, sam.admins.groups.pop(old_group_id))
    group.id = new_group_id  # Update the group ID
    group._attach_color()  # Re-attach the group color

    # Notify the Admins of the change
    sam.msg.hud('#admins', 'Renamed %s group to %s!' % (old_group_name, text))

    # Cleanup and redirect the user
    del sam.cache.temp[userid]
    profile_editor(userid, new_group_id, 'admins_manager')

    return 0, 0, 0


# Functions
def yes_or_no(boolean):
    """
    Returns Yes or No based on the boolean value
    """

    return 'Yes' if boolean else 'No'


def invalid_admin_group(userid, is_admin):
    """
    Displays an error message when the admin or group doesn't exist anymore
    """

    sam.msg.hud(
        userid,
        'This %s does not exist anymore' % ('admin' if is_admin else 'group')
    )
    
    module_menu(userid)
    
def is_valid_group_name(userid, text):
    """
    Checks whether the given text is a valid name for an Admin Group
    """
    
    # Check if the name has more than 12 characters
    if len(text) > 12:
        message = 'The name must be less than 12 characters!'
    # Check if the name already exists
    elif text in sam.admins.groups:
        message = 'This group already exists!'
    # Otherwise, the group name is valid
    else: 
        return True

    sam.msg.hud(userid, message, 'Operation canceled!')
    return False
