# CHANGELOG

This document serves as a changelog for the project's continuous development. 
It aims to document updates and changes along with their corresponding release dates.

# Update Notes - 09-07-2024

### **Core Module**
- Added `get_loaded_scripts()` to   retrieve all scripts loaded by Eventscripts, replacing `es.exist    ('script', script_path)` whichis   not functioning correctly.
- Introduced `is_script_loaded()`   to check if a specific script is   currently loaded.
- Optimized functions such as   `player_list()`, `userid_list()`,  `write_file()`, `read_file()`, and    `get_time()` for betterperformance and efficiency.
- Updated `change_team()` to also   accept team nametags. (`spec`, `terro`, or `ct`).
- Fixed `!admins` command not working, and improved the command functionality.

### **Database System**:
- Implemented `ascii_decoder()` to convert database keys from byte strings to unicode strings, ensuring compatibility with Python 2.7.
- Fixed the system saving empty files when no data is present in the database.

### **Menu System**
- Added functionality to rebuild menus before re-sending them to users:
    - This allows to update values from menus with valus can change while the player has a menu open.
    - `.build_function` can be used to assign the original function that builds the menu, and `.build_arguments_list` to assign the original arguments list.
- Introduced `locked_option_message` for displaying messages when attempting to access locked options.
- Improved the user data cache system for better efficiency and performance.
- Renamed and moved `_refresh_menu()` to the `Menu System` class, to be called within the system itself, instead of calling it from every menu instance.
- Fixed issues with blocked options not working correctly.
- Fixed major issue with `_cancel_refresh()`, not canceling the correct delayed task name, and causing a chain of instances of the same menu being called every time the menu was refreshed, resulting in a server crash.
- Optimized `get_option_info()` and `construct_players_profile_list()` functions.
- Simplified the `send()` function to support the new 'rebuild' functionality.
- Enabled sending menus to multiple users at once using player filters.
- Conducted various other code optimizations and polishing.

### **Admins System**
- Streamlined the process for renaming Admin Groups.
- Improved the `First Admin Setup` process instructions for better clarity of each step.
- Fixed an issue where the `Add Admin` option was listing Admins instead of Non-Admin players.
- Fixed an error occuring while converting Admins data from the database into the Admins Class object during load.
- Fixed an issue where upon toggling a permission in the Admin `Profile Editor` page, would not return the user to the correct page.
- Fixed the removal process for non-existent permissions.

### **Addons Monitor**
- Reworked `_update_installed_addons()`:
    - Re-named the function, previously named `_verify_installed_addons()`.
    - Greatly improved the process of porting/updating addons metadata files data.
    - Now also loads addons that can be loaded if the their state is `True`.
- Added `_enable_addon()` and `_disable_addon()` methods for managing addon states speratly.
    - These methods change the state of the addon and also loads/unloads the addon accordingly.
- Added `_load_addon()` and `_unload_addon()` methods for managing addon loading and unloading.
    - These methods only load/unload the addon, but do not change the state of the addon.
- Introduced `.is_loaded()` method to check if an addon is loaded, replacing the `is_running()` method.
- Renamed `get_addons()` to `addons_list()` for clarity.
- Optimized `.save_database()` to improve efficiency.
- Fixed the Addon Lock State toggle option not working correctly.
- Fixed non Super Admins being able to access locked addons.
- Removed the footer from the `Addons List` page, as it was replaced by the new locked option custom message functionality from the Menu System.
- Removed the `Objects Spawner` addon due to a game engine bug.
- Temporarily removed the Example Addon for rework due to system changes.

### **Bots Manager Addon**
- Fixed issue with Home Page Option, resulting the addon not being available in the Home Page.

### **Admins Chat Addon**
- Fixed messages not being processed when `allow_custom_chat_colors` is disabled.

# Update Notes - 05-11-2023

## Profile System Re-Work
- Converted player data into the new `PlayerProfile` class object after loading the database.
- Added `save_database()` to save the database from the class.
- Added `get_player()` to get a player's profile object.
- Added `clear_inactive_players()` to clear players from the database that have been inactive for more than three months from the server.
- Major code improvements and polishing to fit the new code style.

## Addons Monitor
- Added `load_addon()` and `unload_addon()` functions to the systems class to make the system more modular.
- Added `get_addon()` function to get an `AddonClass` object.
- The system now checks for newly added addons right upon an Admin uses the Addons Monitor option, and upon a map change.
- Reduced `Addons List` menu max lines to 5, to prevent the menu from being too long and missing characters.
- The process for registering Home Page Options for addons has been streamlined. Previously, addons needed to individually register their Home Page Option upon load. Now, a `home_page_option` key has been introduced in the addon's metadata file. This allows the system to automatically register the Home Page Option, eliminating the need for manual registration.
- Replaced `list()` function with `get_addons()`, which returns a the list of addons in their class object.
- Fixed module menu missing its submenu, which is the Home Page

## Ban Manager
- Added player listing using the new Profile System, this means that its now possible to ban offline players that are registered to the Profile System.
- Added the Admin `Ban Level` to the footer of the page when choosing the `Ban Length`.
- Added a notification message exclusive to admins for when a ban has expired.
- Added a notification message exclusive to admins for when a player has been unbanned by another Admin.
- Removed `Help Windows` method of displaying ban logs, as these windows are limited to how much text they can display.
- The `Ban History` option has been updated to use the classic use of menus to view ban logs. The process now involves several steps:
    - **Year Selection**: The first step is to select the year of the ban logs you want to view.
    - **Month Selection**: After selecting the year, you'll be prompted to choose the month of the ban logs.
    - **Player Selection**: Once you've selected the year and month, you'll be presented with a list of players who have been banned during the chosen month.
    - **Ban Log Selection**: After selecting a player, you'll see a list of ban logs for that player during the chosen month. You can select a ban log from this list to view detailed information about the ban.
- Improved the `server message notification` for when a player is banned.
- Improvements made the default Reasons file content
- Major improvements, optimizations and polishing to the Addon's code.

## High Ping Kicker
- Added various settings to the addon:
    - minimum_ping_limit: The minimum ping before the player starts being warned.
    - maximum_warnings: The maximum number of warnings before the player is kicked.
    - ban_length: The length of the ban, in minutes.
    - warning_interval: The interval, in seconds, between warnings sent to players.
- Fixed the system checking all players instead of checking only human players.
- Fixed the player's individual warnings not being reset upon being banned/kicked.
- Major improvements, optimizations and polishing to the Addon's code.

## Core & Main Modules & Addons

### Aditions
- **[Menu System]** Added a new function `construct_players_profile_list()`. This function is used to construct a list of registered players profile objects from the new `Profile System`. By default contructs the list of players in two groups, first the `[Online Players]`, and second all `[Offline Players]`, the `status` parameter can be used to specify which group to return `('online' or 'offline')`. Also a `condition_function` parameter can be used to specify a function to filter the players list, so only the players that pass the condition are listed.

### Changes
- **[Admins System]** Removed the `__call__` function entirely from the `AdminsSystem` class, and added both `get_admin()` and `get_group()` to get the object class of each respectively.
- **[Admins System]** Re-worked the `list()` function:
    - When returning a list of admins, the function no longer returns a copy of the admins dictionary, but instead a copy of the values of the dictionary.
    - Except for the `groups` argument, which still returns a copy of the groups dictionary.
- **[Admins Manager]** `Add an Admin` option now uses the new `Profile System` to list the players. This also means that its now possible to add offline players that are registered to the Profile System as Admins.
- **[Admins Manager]** Fixed the option to rename a Group, when editing a group profile.
- **[Admins Manager]** Various optimizations, improvements and code polishing done to the module.
- **[Admins Manager]** Minor improvements to the First Admin Setup process.
- **[Settings System]** Added a note to inform users when editing a setting for a module or addon that does not have any toggle-able settings available. This helps to prevent confusion and ensures that users are aware of the limitations of the settings system.
- **[Settings System]** Improved the header information for the Help Window to provide more clarity on the purpose of the window. The new header text emphasizes that the window is for displaying settings descriptions and current values only, and cannot be used to modify the settings directly. This helps to prevent accidental changes to the settings and ensures that users understand the limitations of the help window.
- **[Menu System]** Various improvements and optimizations to the `send()` function, which is responsible for building-up menus and sending them to users
- **[Menu System]** Reduced the default separator length from 40 to 30, to prevent the menu from being too long and missing characters, and the max allowed length is now 50 characters.

### Fixes
- **[Admins System]** Fixed on `_initialize_database()` not updating both Admins and Groups permissions correctly, if a new permission was added, or an existing one was removed.
- **[Admins System]** Fixed `Profile Editor` page not updating correctly upon using the `Edit Group Members` option
- **[Admins System]** Fixed `Addons Permissions` option in the `Profile Editor` page displaying an empty list if there are no addons permissions available.
- **[Admins System]** Fixed an issue in the `Remove Admin` option, the names of regular admins to appear blank.
- **[Core Module]** Fixed `get_userid()` function not accepting SteamID3 as a valid argument, therefore returning NoneType.
- **[Admins Chat]** Fixed various tags, names and colors misplacements in the chat messages. (such as Admin group nametag, teams names, misplaced colors, and a few more)
- **[Server Rules]** Fixed the addon not working at all, was left outdated upon some of the major changes to the Settings System in previous updates, also updated the default rules file and settings to improve clarity.

### Removals

- None


# 15-10-2023 Update Notes:

#### Aditions

- None

#### Changes

- **[Addons Monitor]** Moved the module code to the `addons.py` file in the addons folder.
- **[Addons Monitor]** Addons metadata file were renamed to the addon's base folder name.

#### Fixes

- **[GitHub]** Fixed addons metadata files not being included in the repository.

#### Removals

- **[Addons Monitor]** Removed addons_monitor folder.

# 21-07-2023 Update Notes:

#### Aditions

- **[Players Manager]** Added command triggers for all penalties/effects.
- **[Players Manager]** Added a configuration file for the module, to simply enable/disable the commands for each penalties/effects.
- **[Core Module]** Added `get()` function to DynamicAttributes class, as an alternative to return the value of an attribute using a string

#### Changes

- **[Players Manager]** Optimized the Set Firework animation function.
- **[Players Manager]** Re-ordered the various penalties/effects options.
- **[Players Manager]** Improved notifications for all penalties/effects by shortening the messages and making them more clear.
- **[Players Manager]** Implemented an enhanced color palette for messages to ensure greater clarity. Now, when a message is displayed, the target player's name will be highlighted in their respective team color. Additionally, groups of players will be highlighted in yellow for better visibility. To emphasize harmful penalties or effects, they will be displayed in a reddish color, while un-harmful penalties or effects will be presented in a greenish color.

#### Fixes

- **[Menu System]** Fixed issue where users were being redirected to the first page of the menu when choosing to go back to the previous page. Instead, the system now ensures that users are taken to the last page of the menu they were on.

#### Removals

- **[Main Modules]** Removed module tags to chat messages. As they make messages long and cluttered.

# 07-07-2023 Update Notes:

#### Aditions

**[Main Modules]** Added module tags to chat messages.

#### Changes

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

#### Fixes

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

#### Removals

- **[Menu System]** Removed all the debug messages from the display build process.

# 25-06-2023 Update Notes]

#### Aditions

- **[Core Module]:** Added user_active_menu() which returns the active menu of the user if any, else returns None.
- **[Core Module]:** Added get_admin_group() to quickly get the admin group class object.
- **[Settings System]:** Added comments and documentation to the systems functions.
- **[Addons Monitor]:** Added comments and documentation to the systems functions.

#### Changes

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

#### Fixes

- **[Core Module]:** Fixed issue with when removing color names from text would return a blank string.
- **[Settings System]:** Fixed the module not working at all, was left outdated upon some of the major changes to the core system in previous updates.
- **[Settings System]:** Fixed Help Windows not working at all.
- **[Server Rules]:** Fixed the page still using the old add_multiple_options() function which was removed in a previous update.
- **[Server Rules]:** Fixed the default rules file being written on each load, the addon will now check if the file exists before writing it.

#### Removals

- None
