_CHANGELOG_
===========
**This document serves as a changelog for the ongoing development of the project. Updates and changes will be documented with their respective release dates.**

[05-06-2023 Update Notes]
=========================

## Admins System and Module Changes:

#### Added

- Added `is_super_admin()` method to check if an admin is a super admin.
- Added `get_group_members()` method to retrieve the members of a group.
- Added `save_database()` method to save the database.
- Added `new_admin()` method to create a new admin.
- Added `delete_admin()` method to remove an admin.
- Added `new_group()` method to create a new group.
- Added `delete_group()` method to delete a group.
- Added `register_addon_permission()` method for addons to register their own permissions.
- Added Addons Permissions option in the Profile Editor for both Admins and Groups to toggle registered permissions.
- Added Rename Group option, allowing group renaming using a chat filter.

#### Changed

- Renamed some of the system's class methods to provide more descriptive names reflecting their purposes.
- Improved the efficiency and accuracy of the `compare_immunity()` and `is_allowed()` methods for permission and immunity checks.
- Re-wrote the `list()` method, which now returns a copy of the Admins dictionary data by default.
  - Additional arguments can be used with `list()` method:
    - `'super_admin'`: to retrieve only Super Admins.
    - `'groups'`: to retrieve only groups.
    - `'online'`: to retrieve only online admins.
    - With these changes, `items()` method has been removed
- Enhanced the Admins Online counter on the module main page, displaying the number of Super Admins and regular Admins.
- Removing an Admin will now close their active menus and notify them if they are online.
- Improved the editing process of a Group's member list. Members of the group being edited are marked with an 'X', admins without a group are not marked, and admins in other groups are labeled with their respective group name.
- Adapted the First Admin Setup to work with the new Chat Filter System, also improved the whole process.

## Chat Filter System Changes:

#### Added

- Added `instructions_page(*instructions)`, which creates a menu with the provided instructions. The menu will remain open as long as the filter is active, or the user cancels the operation.
- Added a better cancel option to the ChatFilter class, which the user can always type !cancel in the chat, or if open, choose the cancel option from the instructions menu.
  - Its also possible to attach a function to the cancel option, which will be executed when the user cancels the operation.

#### Changed

- SAM no longer creates a new chat filter, using es.addons.registerSayFilter, for each filter. Instead, it creates a single filter (the Main Filter) to handle all registered filter Keys.
  - The Main Filter is only active when there are registered filter Keys, and is disabled when there are no registered filter Keys. This is done to reduce the number of filters created by ES stored in memory.
  - The Main Filter goes through all active filter Keys, and executes their respective functions on their valid users.

## Main Modules & Add-ons Changes:

#### Added

- **[Core Module]:** Added docstrings and comments to all functions and classes, and included numerous code comments.
- **[Database System]:** Introduced a default file extension variable.

#### Changed

- **[Core Module]:** Renamed some functions to provide more descriptive names reflecting their purposes.
- **[Core Module]:** Converted _compile() method from Message System to compile_text() now as a Core function, allowing other modules to use it.
  - Added strip_text argument, to choose whether to strip whitespace from the text or not.
  - Also made some code improvements.
- **[Core Module]:** Improved get_userid() function, which was not working properly in some cases.
- **[Menu System]:** Added add_options() to add multiple options from a list of tuples
- **[Menu System]:** Improvements made to get_option_data() function, which was not working properly in some cases.
- **[Admins Chat]:** Adapted the Addon to work with the new Chat Filter System.
- **[Admins Chat]:** Fixed misleading chat logic when the user was dead or alive
- **[Admins Chat]:** Minor code improvements.
- **[Message System]:** Sending messages to multiple lists of users will no longer iterate using playerlib and rather using lists of userid's.

#### Fixed

- **[Core Module]:** Fixed send_menu() function not working as intended.
- **[Core Module]:** Fixed not being checking if the users are Admins before sending the Home Page
- **[Message System]:** Fixed an occasion if the user was part of more than one list, the message would be sent duplicated.
- **[Player Manager]:** Fixed Freeze & Unfreeze function not working.

#### Removed

- None