# S.A.M (Server Administration Menu)

## What is SAM?

S.A.M (Server Administration Menu) is a powerful, all-in-one tool designed to simplify server administration for Counter-Strike servers. It's a plugin written in Python 2.7 using EventScripts, providing a user-friendly menu-driven interface for managing various aspects of the server, including players, addons, admins, and settings. SAM strives to make server management as seamless as possible, aiming to avoid the need for manual file changes or server restarts for most features.

## Key Features

* **Modular Design:** SAM is built with a modular structure, allowing for easy expansion and customization. Each module focuses on a specific aspect of server management.
* **Menu System:** SAM utilizes a robust built-in menu system based on EventScripts' popuplib library, providing a visually appealing and intuitive interface for admins.
* **Chat Commands:** SAM introduces a set of chat commands (e.g., `!sam`, `!rcon`, `!admins`) that allow admins to interact with the plugin directly from the game.
* **Database System:** SAM uses JSON databases to store settings, admin data, player profiles, and addon information, ensuring persistence across server restarts.

## Relevant Systems

* **Menu System:** The menu system is the core of SAM's user interface. It allows admins and playersto navigate through various options and perform actions using a simple and intuitive menu structure, all in-game and in real-time.
* **Database System:** The database system is responsible for storing and retrieving data, ensuring that settings, admin information, player profiles, and addon data are persistent across server restarts.
* **Admins System:** The Admins System controls access to different features, addons and settings, ensuring that only authorized admins can perform specific actions. It also manages server admins and admin groups, providing functions for adding, removing, editing, and managing permissions.
* **Chat Filter System:** The chat filter system allows for the filtering of chat messages based on various criteria, preventing spam and controlling communication, as well as way of retrieving text input from players.
* **Message System:** The message system provides a comprehensive set of functions for sending different types of messages to players and the server console, including chat messages, HUD hints, center messages, side messages, VGUI panels, MOTD messages, and info messages.

## Main Modules

### 1. Players Manager

* **Purpose:** Provides tools for managing players, including kicking, killing, slapping, freezing, and applying various effects.
* **Key Features:**
    * **Player Penalties:** Allows admins to apply various penalties to players, such as kicking, killing, slapping, freezing, and more. Also some of these penalties custom made.
    * **Player Effects:** Enables admins to apply effects to players, such as blindness, fire, noclip, god mode, and jetpack.
    * **Player Cash and Health:** Allows admins to modify player cash and health amounts.

### 2. Addons Monitor

* **Purpose:** Allows admins to manage installed SAM addons, enabling/disabling, locking/unlocking, and viewing addon settings.
* **Key Features:**
    * **Addon Management:** Provides a central location for managing installed SAM addons, enabling or disabling them as needed. (These changes are applied in real-time, without requiring a server restart.)
    * **Addon Locking:** Allows super admins to lock addons, preventing other admins from modifying their settings.
    * **Addon Settings:** Enables admins to view and modify addon settings, customizing their behavior.

### 3. Admins Manager

* **Purpose:** Enables admins to manage other admins and admin groups, adding, removing, editing, and assigning permissions.
* **Key Features:**
    * **Super Admins:** Super Admins are immune to everythin and have full access to all features, addons and settings, regardless of their permissions.
    * **Admin Management:** Allows admins to add, remove, and edit other admins, including assigning permissions and setting their super admin status. (These changes are applied in real-time, without requiring a server restart.)
    * **Admin Group Management:** Enables admins to create, delete, and manage admin groups, assigning permissions and setting group-specific settings.
    * **Permission Management:** Provides a detailed system for managing permissions, allowing admins to control access to specific features and settings.
### 4. Settings Manager

* **Purpose:** Provides a user interface for viewing and modifying plugin settings, including general options and module-specific configurations.
* **Key Features:**
    * **General Settings:** Allows admins to configure general plugin settings, such as chat prefix, anti-spam settings, and menu options. (These changes are applied in real-time, without requiring a server restart.)
    * **Module Settings:** Enables admins to view and modify settings for individual modules and addons, customizing their behavior.
    * **Help Window:** Provides a help window for each section, displaying descriptions and current values of settings.

## Conclusion

SAM is a powerful and versatile plugin that significantly enhances server administration for Counter-Strike. Its modular design, user-friendly interface, and comprehensive features make it an invaluable tool for any server owner or administrator. SAM's real-time functionality ensures that changes made through the plugin take effect immediately, streamlining the server management process.
