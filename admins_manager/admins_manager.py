#!/usr/bin/python
# -*- coding: utf-8 -*-

import es
import psyco
psyco.full()

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

    # If the admin chooses to create a new group (choice 4), we need to register
    # a chat filter to capture the name of the new group. Since this doesn't immediately
    # lead to another menu, we return after setting up the chat filter.
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

    # Initialize the next menu with the appropriate title,
    # description and callback function.
    menu = sam.Menu('am_admins_or_groups_list', option[2], 'admins_manager')
    menu.title(option[0])
    menu.description(option[1])

    # Construct a list of non-admin players using Profile System
    if choice == 1:
        def condition(player):
            return sam.admins.is_admin(player.steamid)
        menu.construct_players_profile_list()

    # If the user chose to remove an admin or edit an admin's profile (choices 2 and 3),
    # we need to list the current admins.
    elif choice in (2, 3):
        admins = [
            (
                admin.steamid,
                admin.name + ' [Super Admin]' if admin.super_admin else admin.name
            )
            for admin in sam.admins.list()
        ]
        menu.add_options(admins)

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

    # Save the database in case something was previously changed and not saved
    sam.admins.save_database()

    # Check if the player is allowed to access the module
    if not sam.admins.is_allowed(userid, 'admins_manager'):
        sam.home_page(userid)
        return

    # Get the Admin/Group object
    target_id = choice
    is_target_admin = sam.admins.is_admin(target_id)
    target = sam.admins.get_admin(target_id) if is_target_admin else \
            sam.admins.get_group(target_id)
    
    # Check if the player is trying to edit a Super Admin profile
    if is_target_admin and not sam.admins.is_super_admin(userid) and target.super_admin:
        sam.msg.hud(userid, 'You cannot edit a Super Admin profile')
        submenu.send(userid)
        return

    # Initialize the menu
    menu = sam.Menu('am_profile_editor', profile_editor_HANDLE, 'admins_manager')
    menu.max_lines = 5 if is_target_admin else 6
    menu.title('%s Profile Editor' % ('Admins' if is_target_admin else 'Groups'))

    # Add options to the menu based on whether the target is an admin or a group
    if is_target_admin:
        menu.description('* NAME: ' + target.name,
                         '* STEAMID: ' + target.steamid,
                         '* SINCE: ' + target.admin_since)
        menu.add_options([
            ((target_id, 'super_admin'), 'Super Admin: ' + yes_or_no(target.super_admin)),
            ((target_id, 'admin_group'), 'Admin Group: ' + sam.title(target.group))
        ])
    else:
        menu.description('* GROUP NAME: ' + target.name)
        menu.add_options([
            ((target_id, 'members'),
             'Group Members: (%s)' % len(sam.admins.get_group_members(target_id))),
            ((target_id, 'rename'), 'Rename Group'),
            ((target_id, 'color'), 'Group Color: ' + sam.title(target.color))
        ])

    # Add common options
    menu.add_options([
        ((target_id, 'ban_level'), 'Ban Level: %s' % target.ban_level),
        ((target_id, 'immunity'), 'Immunity Level: %s' % target.immunity_level),
        ((target_id, 'addons'), 'Addons Permissions')
    ])

    # At last, list all the Admin permissions on a new page
    menu.next_page()
    menu.add_line('Permissions:')

    # Finally, list all the permissions
    menu.add_options([
        ((target_id, permission),
        '%s: %s' % (sam.title(permission), yes_or_no(target.permissions[permission])))
        for permission in sorted(target.permissions)
    ])

    # Send the menu to the player
    menu.send(userid)

def profile_editor_HANDLE(userid, choice, submenu):
    """
    Handles the profile editor menu choice
    """

    # Unpack the choice into target_id and option
    target_id, option = choice

    # Check if the target_id is an admin
    is_target_admin = sam.admins.is_admin(target_id)
    
    # Get the target object
    target = sam.admins.get_admin(target_id) if is_target_admin \
            else sam.admins.get_group(target_id)

    # If the Admin/Group does not exist, call invalid_admin_group and return
    if not target: 
        invalid_admin_group(userid, is_target_admin)
        return

    # Define a dictionary to store menu setup, title, and description for each option
    option_menu_setup = {
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
            '%s Profile Editor' % ('Admins' if is_target_admin else 'Groups'),
            'Choose Immunity Level:'
        ),
        'addons': (
            ('am_change_addons', addons_permissions_HANDLE, 'am_profile_editor'),
            'Addons Permissions',
            'Select the permissions:'
        ),
    }.get(option)

    # If the option isnt in the dictionary, send it to the non menu handler
    if not option_menu_setup:
        profile_editor_non_menu_HANDLE(userid, (target, target_id, option), submenu)
        return

    # Otherwise, initialize the menu with the appropriate title and description
    menu = sam.Menu(*option_menu_setup[0])
    menu.title(option_menu_setup[1])
    menu.description(option_menu_setup[2])

    # If the option is to change the admin group
    if option == 'admin_group':

        # Get the list of groups
        groups = sam.admins.list('groups')

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
            group = sam.title(group)
            group = group + ' (current)' if group == target.group else group
            menu.add_option((target_id, group), group)

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
        for color in sorted(sam.msg.colors.keys()):
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
    elif option in target.permissions.keys():
        target.toggle_permission(option)

    # Make sure the Admin is allowed to manage Admins
    if sam.admins.is_allowed(userid, 'admins_manager'):
        # Send the user back to the profile editor menu
        profile_editor(userid, target_id, submenu.object.submenu)
        sam.menu_system.send_menu(userid, submenu.menu_id, submenu.page)
    else:
        sam.home_page(userid)


def change_admin_group_HANDLE(userid, choice, submenu):

    # Get the Admin object
    steamid, group = choice
    admin = sam.admins.get_admin(steamid)

    # Check if the admin still exists
    if not admin:
        invalid_admin_group(userid, True)
        return

    # If the choice is 'remove', remove the admin from his current group
    if group == 'remove':
        sam.msg.hud('#admins',
                    '%s removed from %s group' % (admin.name, sam.title(admin.group)))
        admin.group = False

    # Else if the player is trying to add the admin to the group
    else:
        sam.msg.hud('#admins', '%s added to %s group' % (admin.name, sam.title(group)))
        admin.group = group

    # Send the user directly to the profile editor
    profile_editor(userid, steamid, 'admins_manager')


def edit_group_members_HANDLE(userid, choice, submenu):
    """
    Handles the edit group members menu choice
    """

    # Get the admin object
    target, admin = choice

    admin = sam.admins.get_admin(admin)

    # Check if the admin still exists
    if not admin:
        invalid_admin_group(userid, True)

    # If the admin is already in the group, remove him
    elif admin.group == target:
        sam.msg.hud('#admins', admin.name + ' removed from %s group' % admin.group)
        admin.group = False

    # Otherwise, add him to the group
    else:
        admin.group = target
        sam.msg.hud('#admins', admin.name + ' added to %s group' % admin.group)

    # Send the user back to the Group Members menu
    profile_editor(userid, target, 'admins_manager')
    profile_editor_HANDLE(userid, (target, 'members'), 'am_profile_editor')
    sam.menu_system.send_menu(userid, submenu.menu_id, submenu.page)


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
    profile_editor(userid, target, 'admins_manager')


def change_immunity_level_HANDLE(userid, choice, submenu):
    """
    Handles the change immunity level menu choice
    """

    # Get the target target
    target_id, choice = choice
    is_target_admin = sam.admins.is_admin(target_id)
    target = sam.admins.get_admin(target_id) if is_target_admin \
            else sam.admins.get_group(target_id)

    # Check if either the Admin or the Group still exists
    if not target:
        invalid_admin_group(userid, is_target_admin)
        return

    # Set the immunity level
    target.immunity_level = choice
    sam.msg.hud('#admins', target.name + '%s immunity level set to %s' %
                ('\'s' if is_target_admin else ' group', choice))

    # Send the user back to the Profile Editor menu
    profile_editor(userid, target_id, 'admins_manager')


def addons_permissions_HANDLE(userid, choice, submenu):
    """
    Handles the Addons permissions menu choice
    """

    # Get the target object
    target_id, choice = choice
    is_target_admin = sam.admins.is_admin(target_id)
    target = sam.admins.get_admin(target_id) if is_target_admin \
            else sam.admins.get_group(target_id)

    # Check if either the Admin or the Group still exists
    if not target:
        invalid_admin_group(userid, is_target_admin)
        return

    # Toggle the permission
    target.toggle_permission(choice)

    # We need to build the menu again since changes were made to the Admin/Group target
    profile_editor_HANDLE(userid, (target_id, 'addons'), 'am_profile_editor')
    sam.menu_system.send_menu(userid, submenu.menu_id, submenu.page)


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
        'Hello %s' % es.getplayername(userid),
        ' ',
        'SAM requires at least one Super Admin to function.',
        'If you\'re a server owner/operator,',
        'proceed to set yourself as Admin.',
        ' '
    )
    menu.add_option(1, 'Yes, Proceed')
    menu.add_option(2, 'No, I\'m not the server owner/operator')
    # Send the menu
    menu.send(userid)


def first_admin_setup_HANDLE(userid, choice, submenu):
    """
    Handles the First Admin Setup menu choice
    """

    if choice in (1, 2):
        del sam.menu_system.menus['first_admin_setup']
    # If the user chooses to proceed, then start the RCON verification process
    if choice == 1:
        # Register a chat filter to get the name of the new group
        f = sam.chat_filter.register('rcon_verification')
        f.function = rcon_verification_FILTER
        f.users.append(userid)
        f.cancel_option = True
        f.instructions_page(
            'SAM needs a server owner/operator verification.',
            'Type the server\'s exact RCON password in chat.'
        )


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
            'You\'re now a Super Admin. Type !sam for the menu.',
            'Suggested: bind <key> sam_menu'
        )

    # Otherwise, notify the user that the RCON password is incorrect
    else:
        sam.msg.hud(userid, 'RCON Password incorrect! Operation canceled!')

    return 0, 0, 0


def admin_group_creation_FILTER(userid, text, teamchat):
    """
    Handles the Admin Group Creation chat filter
    """

    # Remove the user from the chat filter
    sam.chat_filter.remove_user(userid, 'admin_group_creation')

    # Send the user to the Module Page in case the operation is canceled
    module_menu(userid)

    # Check if the user canceled the operation
    text = sam.format_text(text).lower()

    # Check if the text is valid for a group name
    if can_name_group(userid, text):
        sam.admins.new_group(text)
        sam.msg.hud('#admins', 'Group %s created!' % text)
        profile_editor(userid, text, 'admins_manager')

    return 0, 0, 0


def rename_admin_group_FILTER(userid, text, teamchat):
    """
    Handles the Admin Group Rename chat filter
    """

    # Delete the chat filter
    sam.chat_filter.remove_user(userid, 'rename_admin_group')

    # Send the user to the Module Page in case the operation is canceled
    module_menu(userid)
    new_group_id = sam.format_text(text).lower()

    # Check if the text is valid for a group name
    if userid in sam.cache.temp and can_name_group(userid, text):
        old_group_id = sam.cache.temp[userid]
        old_group_name = sam.admins.get_group(old_group_id).name
        sam.msg.hud('#admins', 'Renamed %s group to %s created!' % (old_group_name, text))
        sam.admins.groups[new_group_id] = sam.admins.groups.pop(old_group_id)
        sam.admins.groups[new_group_id].id = new_group_id
        sam.admins.groups[new_group_id]._attach_color()
        profile_editor(userid, new_group_id, 'admins_manager')
        del sam.cache.temp[userid]

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
    
def can_name_group(userid, text):
    """
    Makes sure the given text is illegible to be used as a group name,
    either to create a new group or to rename an existing one.
    """
    
    val = False
    opr = 'Operation canceled!'
    
    # Check if the name has more than 12 characters
    if len(text) > 12:
        sam.msg.hud(userid, 'The name must be less than 12 characters!', opr)

    # Check if the name already exists
    elif text in sam.admins.groups:
        sam.msg.hud(userid, 'This group already exists!', opr)

    # Otherwise, the group can be named
    else: 
        val = True
        
    return val
