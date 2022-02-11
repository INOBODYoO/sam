# SAM (Server Administration Menu)
#### For [Counter-Strike: Source](https://store.steampowered.com/app/240/CounterStrike_Source/), powered by [EventScripts by Mattie](http://mattie.net/cs/)

### Introduction:

An all-in-one tool featuring various useful functionalities for any CS:Source server, with the ultimate goal
of provide all the features below without the need of server files handling, server restarts or plugin reloads,
making the majority of alterations and interactions possible within the in-game menu.
SAM also provides various Addons to use in the server, with the ability to turn them on and off at anytime.
Addons like Ban Management, Trickz Menu, Admins Chat, among various other useful addons for any kind of server,
whether is destined to be a surf server, a competitive server, or any other mod, giving the server owners/operators
the ability to fully customize the server with their needs.

### Features:

**Players Management:**

- Kick, Slay, Give Health, Give Money among others useful functions
- Various "fun" like functions, such as: Jetpack, Fireworks, Drug Mode, among others

**Admins Management:**

- Super Admins, for server owners/operators with access anything over everyone in the server
- Ability to Add & Remove admins
- Admins Profiles, to view and alter Admins permissions, immunity & and ban level, and other useful info
- Admin Groups:
    - Add or Remove Admin groups, give specific permissions, and assign admins to groups,
      instead of changing admins permissions individually
      
**Addons Monitor:**

A system to manage Addons, enable or disable them at any time without any restarts or reloads.

- Enable / Disable addons at any time
- Super Admins can block Addons state, therefore other Admins cannot change said Addon state set by a Super Admin
- Individual Settings for each Addon incorporated in SAM's Settings System

**Settings System:**

A very easy to use system, allowing Admins with the right permission to change almost any setting within the in-game menu:

- General Settings, SAM's core settings
- Addons Settings
- Change almost any setting from the menu (Exceptions to settings that require text or specific numbers)
- Any changes made through in-game menu or to setting files happen in realtime, no restarts or reloads required

**Built-In Page System:**

For those familiar with EventScripts popuplib will know how buggy and unreliable populib can be. This system
is a major improvement on popuplib, with better page & cache handling, blockale options, list like options
and line customization.

## How to install:
1. Install Counter-Strike: Source
2. Install EventScripts v2.1.1 Beta (Patched for current game's version)
3. Install the latest SAM version
4. Optional But Recommended:

    1. Create a autoexec.cfg file in your server's cfg folder
    2. type es_load sam, and save the file
    
Installation is complete, to access the menu type !sam in the game chat.
I also recommend making a bind for easy access, i.e:
bind . sam_menu
or
bind . "say !sam" 
