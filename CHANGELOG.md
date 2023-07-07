# CHANGELOG

This document serves as a changelog for the project's continuous development. 
It aims to document updates and changes along with their corresponding release dates.


# 07-07-2023 Update Notes:

#### Added

**[Main Modules]** Added module tags to chat messages.

#### Changed

- **[Core Module]** Moved all Menu System related functions to the new Menu System class.
- **[Core Module]** Improvements made to classes and functions documentation.
- **[Core Module]** Optimizations and QOL improvements to `!rcon` Command function.
- **[Core Module]** Optimizations and improvements to `!admins` Command function.
- **[Menu System]** Major code improvements, optimizations and polishing.
- **[Menu System]** Improvements to the Menu display build-up process.
- **[Menu System]** Improvements to the `proccess_user_choice` function.
- **[Settings System]** Further optimizations to the Settings System class and module.
- **[Settings System]** `update_settings` now only updates the values of the settings that have been changed.
- **[Settings System]** Changed `addon_config` function to `module_config`, as this can be utilized by any module or addon to create its own configuration file.
- **[Admins System]** Optimized Database saving process.
- **[Admins System]** Improvements to the `get_admin_group` function.
- **[Message System]** Improved the Message Spam system.
- **[Message System]** Improved the `tell` function.
- **[Commands System]** Optimizations to the whole Commands System class.

#### Fixed

- **[Core Module]** Fixed Chat Prefix showing a False instead of being completely removed.
- **[Core Module]** Fixed disabled commands not notifying the user that the command is disabled.
- **[Settings System]** Fixed database resetting on load.
- **[Settings System]** Fixed when calling for Modules settings, returning the setting dictiorary instead of the setting value.
- **[Settings System]** Fixed non toggleable settings being listed when using the menu.
- **[Admins System]** Fixed when checking if an Admin has a certain permission, not considering the Admin's group permissions, if in any.
- **[Admins System]** Fixed when canceling the operation of renaming a group name sending the user to the module page instead of the group profile editor.
- **[Menu System]** Fixed occasion where the Next Page option would not show up.
- **[Admins Chat]** Fixed Terrorists Team wrong color name.
- **[Admins Chat]** Fixed Group tags not displaying at all.

#### Removed

- **[Menu System]** Removed all the debug messages from the display build process.

# 25-06-2023 Update Notes]

#### Added

- **[Core Module]:** Added user_active_menu() which returns the active menu of the user if any, else returns None.
- **[Core Module]:** Added get_admin_group() to quickly get the admin group class object.
- **[Settings System]:** Added comments and documentation to the systems functions.
- **[Addons Monitor]:** Added comments and documentation to the systems functions.

#### Changed

- **[Addons Monitor]:** Various optimizations, improvements and code polishing done to the system.
- **[Settings System]:** Improved database update effeciency.
- **[Settings System]:** Database will now only be compared and updated with the default settings on load, instead of every time the file is loaded.
- **[Settings System]:** Tweaked settings descriptions to be more clear.
- **[Core Module]:** Optimized compile_text() function efficiency.
- **[Core Module]:** Optimized write_file() and read_file() functions efficiency.
- **[Core Module]:** Optimized get_userid() function efficiency.
- **[Core Module]:** Optimized userid_list() and player_list() functions efficiency.
- **[Core Module]:** Renamed compile_text() function to format_text().
- **[Message System]:** Color codes now use a more flat color scheme.
- **[Message System]:** Expanded the colors available for chat messages.
- **[Message System]:** Optimized sorting of users before sending messages.
- **[Chat Filter System]:** Various optimizations and improvements to the system.
- **[Server Rules]:** Various optimizations, improvements.
- **[Bots Manager]:** Small menu handling improvements.

#### Fixed

- **[Core Module]:** Fixed issue with when removing color names from text would return a blank string.
- **[Settings System]:** Fixed the module not working at all, was left outdated upon some of the major changes to the core system in previous updates.
- **[Settings System]:** Fixed Help Windows not working at all.
- **[Server Rules]:** Fixed the page still using the old add_multiple_options() function which was removed in a previous update.
- **[Server Rules]:** Fixed the default rules file being written on each load, the addon will now check if the file exists before writing it.

#### Removed

- None
