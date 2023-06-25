_CHANGELOG_
===========
**This document serves as a changelog for the ongoing development of the project. Updates and changes will be documented with their respective release dates.**

[25-06-2023 Update Notes]
=========================

## Main Modules & Addons Changes:

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