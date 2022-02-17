[this file is best read using regular expression syntax]

- Changelog:

This "Remastered" version is complete re-work of the old plugin, bringing new and improved systems,
to better fill the ultimate goal of SAM, an all-in-one tool, where server Admins/Operators can
do almost any kind of server administration/configuration in-game, avoiding to spend hours
dealing with server files, boring configuration, and unnecessary server restarts.

Since much as changed compared to the old plugin, this changelog will be mostly a
summary explaining what changed in the core module, the new systems, and each changes made to
existing Addons or functionalities.

[Unreleased]

[1.0.0] - (Remastered) - [2022]

[CORE MODULE]
(Responsible for most important systems and functions)

+ New Page System:
    * This new system is a replacement of the old "Menu System", entirely built-in, and no
      longer uses/requires EventScripts's "popuplib" library. Just like popuplib this system
      uses the game's "Radio Popups", treated as "Pages", and therefore the name "Page System".
    + Pages are divided in various sections:
        * Header: The top line of all pages, contaning info of the in-use version of the
          plugins and a local time clock.
        * Title: Usually to point out the the user's active page correspondent module or addon.
        * Description: Usually to describe the users active page purpose.
        * Footer: For informative messages, tips or useful indications of the user's active page
    + Support for toggle-able options, which in the old system was very difficult to achieve.
    + Improved user choice processing, to better redirect the user to the pages he is supose
      to go. Its also possible to force users choices which in some cases this is very handy.
      (e.g To force the user to close the active page when the plugin is unloaded.)

+ New Database System:
    + Now using SimpleJSON library to store data in JSON file format.
    - No longer uses the old data storage method, cPickle.
    * Fixed system saving empty data, leading to empty files.

[Other Changes]
+ Added timestamps to Console messages

[Settings Module]
(Responsible for storing and managing the core and all addons settings)

* A very user friendly system that allows any setting to be changed in realtime without the
  need to ever restart the server or reload the plugin for any changes to take effect
* Toggle-able options can be changed from the menu itself, for ease of use.
* Digit or String (text) type settings can only be changed in the settings.json file under the
  'required' folder, however take in mind once again, changes happen in realtime as soon
  as you save the file, no restarts or reloads are needed.
* When browsing settings in the menu, for each section/addon, theres a Settings Information
  option, which will open an MOTD window with the detailed description of each setting for the
  choosen section/addon, so users better understand what each setting does.

[Admins Manager Module]
(Built-in system to add or remove Admins and change their permissions either individually or
 by creating Admins Groups with sets of permissions and assign Admins to it)

+ Introducing Super Admins, functioning the same as SourceMods root Admins,
  having access and immunity to everything.
+ At least one Super Admin is required to operate SAM.
+ Fixed various Access & Immunity checks as Admins use the plugin's systems.
+ Re-designed Admins Profile page, for much easier change of admins groups,
  immunity level, ban levels and systems flags.
+ Re-worked First Admin Setup:
    * Just like the previous method, after installing and loading SAM, using !sam in the
      chat will prompt the user with the First Admin Setup page, asking the user if the user
      wants to add himself as Super Admin, the user will be required to type the exact server
      RCON password in the game chat to confirm if the user is a server owner/operator.
+ Added a counter to the module page displaying the number of Super Admins and the number
  of regular Admins currently online in the server.
+ Admins Profile will now also display the date of when the player was added as Admin.
+ Added a Group Members option when editing an Admin Group, to easily assign or remove
  multiple Admins to/from a Group.
+ Added a Group Color option when editing an Admin Group to choose a color to represent
  the selected group. This color is used to colorize the group name in the game chat,
  by default a random color will be assigned to the group when created
* Improved !admins command, re-designed the page, Super Admins will be listed first
  following with regular Admins, each identified with the respective Admin group if in any.
- Removed Update Check system.
- Removed Multi-Language System, now only English is supported.

[Players Manager Module]
(Responsible for handling player penalties that can be applied by admins)

+ An all new class based system with more than 10 available penalties and some custom built,
  "fun" like, functions to use on players, like: Fireworks, Drug Mode, and more.
+ Now Addons can also  take advantage of the new class system to apply penalties in certain
  situations. (e.g kicking AFK players, and much more)
* The Ban and Mute System have each been ported to their own standalone Addon.
- Unlike the old version, only a selection of penalties will feature chat commands
  (Some of the supported commands are !kick, !ban/!unban and !mute/unmute)

[Addons Monitor Module]
(Responsible for monitoring Addons, loading, unloading them or locking their state)

+ Improved toggle-able options visually, in a simplified manner.
+ Locked Addons can only be accessed by Super Admins, meaning that Admins with the
  Addons Monitor flag cannot accessed.
+ If an Addon has its own settings, after the first time the Addon is loaded up, the same
  Settings Help Window option will appear in the Addon profile page.

[Admins Chat Addon]

+ The filter now respects the "chat rules", to who the player is allowed to speak to
  depending on the player team, state, and also considering sv_alltalk variable.
+ Starting a message with @ in the team's chat, will make the Admin send an @ADMINS message which
  will only be displayed to all other Admins.
+ Starting a chat message with @ will make the Admin send a @SERVER message which will
  be displayed to all players in the server.
+ The 'say' command in the server console was also replaced and will act as a
  @SERVER message
+ Starting a message with @@ will display the message in the center of the screen to all players
+ Admins are allowed to use custom colors in messages in realtime
  (e.g #redHello #blueWorld)

[Damage Display Addon]

+ Will now display up to five lines, informing the damage given to and taken from players

[Ban Manager Addon]

+ Ban a Player option now lists 2 groups of players, Online players and Offline players,
  Offline players being players that have been in the server before but aren't currently active.
+ Ban lengths are now sorted and grouped by Ban Levels, and the Admin's ban level will be
  shown at the page footer.
+ Ban Profile page now lists the player name, SteamID, the date the ban was given,
  the ban expiration date + hour, the Admin that gave the ban and the ban reason.
+ Ban Logs are no longer stored in files, but rather in their own database.
+ Ban History option now sorts bans by year and month.
+ Ban logs are now shown in a MOTD type message.
+ 