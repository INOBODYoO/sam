# Introduction

S.A.M stands for Server Administration Menu, began to be my very first Python project and
my starting point in programming, was mostly used privately to serve my own needs, but
later on a public version was released. Being very new to programming, and of course to Python
SAM wasn't really built the best way possible, but the best way I could , many mistakes
were made throughout its many iterations, making it really unstable and unreliable,
nevertheless I was always proud of my work since I was pretty much self-taught through the
process of learning skills and applying them.

The goal always stood the same, as an "All-In-One independent server modding & administration tool".
SAM is based on Mani-Admin Menu for its unique Player Administration tools and its built-in
Admins system, and on SourceMod for its unique and extensive and flexible list of plugins
for any kind of server, the idea being that SAM would take the best features of both into
one single plugin.

Note: While not entirely true, since SAM requires EventScripts framework and
      simplejson (shipped together by default) to work, SAM ultimately avoids being
      dependent of other Addons or libraries but these two being the biggest exceptions.

SAM's second ultimate goal was to be the most user friendly and independent plugin ever.
- User-Friendly: 

SAM's remastered version is a complete re-work of an older version of SAM, mostly used in
private, even though EventScripts is unmaintained and outdated and CS:S itself is no longer
the game it used to be, this version is just to be on the record as one of the biggest
scriptigng projects ever done by me, and my starting point in programming.

#### Remastered Version Note:
Since so much has changed from the previous versions of the plugin, this changelog will mostly
containing explanations of SAM's top features, addons, and core systems.

# [1.0.0] - (Remastered) - [2021 / 2023]

## [CORE MODULE] - sam.py
(Responsible for handling main modules, systems and functions for the whole script to work)

# Page System:
> What are pages?
> 
> Source games have these "radio popups", a good example is team radios where players
> use quick sound communications to teammates to send instructions or call out reports in game.
> SAM uses these popups to create what I call pages, and therefore create menus
> with options, all kinds of useful information and functionalities, all this in-game of course. 
> 
> Previously SAM used a EventScripts popuplib's library to create pages, which the library
> itself was a buggy mess, and limited SAM too much in what SAM could and needed to do.
> The new Pages System is now built-in into SAM and no longer requiring ES popuplib,
> this being the biggest change to the plugin and substantially improving SAM's capabilities.

- ES Popuplib library is no longer used.
+ Pages new features:
  * Header: Top line of every page displaying SAM's installed version and a local clock.
  * Title: Mostly to easily identify to what module, system or addon the current page belongs to.
  * Description: Usually to describe the content of the page.
  * Lines: Simply lines of text, however the biggest change is that now lines can be placed
           in between options, where in the old version wasnt possible.
  * Options: Listed options are enumerated optiosn the player can choose using numbers from 0 to 9
             (0 represents the number 10 in popups, used mostly as the Close Options and/or Previous Page)
  * Blocked Options: Options can be block, unabling the user to choose them.
                     (i.e: When an Addon State was locked by a Super Admin, a regular admin can still
                      see the Addon listed, however can not change its state because the add_option is blocked)
  * Seperators: Seperator lines.
  * Footer: Usually for informational notes.
+ Added support for toggle-able options, which was previously harder to achieve.
+ Its now possible to force users choices.
(Mostly usefull to force the user to close the page, or redirect a certain page to the user)
+ Improved user choice processing, pages now keep a dictionary containing the page object,
  page ID, and previous page information.

# Database System:
> Previously I had this rule where SAM should be independable at all costs, and sort of is, 
> however EventScripts lacks a good data storage system.
> 
> To work this out I broke my own rule by making SAM dependable of SimpleJSON, to use
> JSON file format as one of the best data storage solutions, however even this might
> be changed to sqlite-dict.
+ Now using SimpleJSON library to store data in JSON file format.
- No longer uses Pickle for data storage
* Fixed system saving empty data, leading to empty files.

# Message System
(Represents all message type functions available)
> All message types are:
> - Tell: Chat message. These can be color coded by using tags such as: #red, #blue, #green, and many others
> - Hud: A hudhint message, appears in bottom center of the screen.
> - Side: Hint type message, appears in the right center of the screen.
> - Center: Center type message, appears in the center of the screen.
> - VGUIPanel / Motd: Theres various funtionalities with this one, but it's mostly used as MOTD type
>					  message, to send web links to the user, of text documents.
> - Info: As decribed above, takes advantage of VGUIPanel to send text documents.
>		  SAM mostly uses this so players can view log files, ranking systems and settings files in game.
>		  (However they are for view only, cannot be edited)
> - Console: Console messages, system messages, logging and debugging.

+ Added Info type message.
+ Added timestamps to Console messages.
+ Added a Anti Spam system, to avoid multiple repeated messages from SAM to spam the chat.
+ Changed system to a class type.
+ Improved Compiler function to replace color tags, remove special characters and white spaces

# Settings Module
(New module responsible for all general and addon settings)

- Now possible to change any toggle-able settings in the menu.
- Other settings types must be changed in the respective file with the required/settings folder
- All changes made either in game or through the file happen in real-time,
  restarts or reloads are not required.
- In all Settings pages, on the bottom of the page theres a Help add_option, when chosen
  a Info type message will be sent with the setting file of the respective module/addon,
  where the user can learn all settings and their descriptions of that module/addon.

# Admins Manager Module
(Responsible for managing and editing admins & admins groups)
> One of SAM biggest features is its built-in Admins system.
> One can Add & Remove Admins, changes their permissions, or create admins groups with
> specific permissions and assign Admins to them to make things easy. All this in-game.

+ If SAM does not find a Admins Database or no Admins added to it, and one opens !sam,
  SAM will promt the user if one wants to become Super Admin, however to take effect
  the user will be required to type the exact RCON password in the game chat for validation.
  Upon validation the user will become Super Admins.
  This also means that SAM can only work properly with at least one Super Admin.
+ Added Super Admins, the same as SourceMod's root Admins, with access & immunity to
  anything and everything.
+ Re-designed Admins Profile page, now featuring:
	- Admin Name, SteamID and Since Date
	- Add/Remove Admins as Super Admin
	- Admin Group, if none, its possible to easily remove the or even add the admin to a group
	- Change Ban Level
	- Change Immunity Level
	- Change all other modules/addons permissions
+ In the footer of the module page theres now a counter of the current online Admins & Super Admins
+ Added a Group Members add_option when editing an Admin Group, to easily assign or remove
  multiple Admins to/from a Group.
+ Added a Group Color add_option when editing an Admin Group to choose a color to represent
  the selected group. This color is used to colorize the group name in the game chat,
  by default a random color will be assigned to the group when created
* Improved !admins command, Super Admins will be listed first following with regular Admins,
  each identified with the respective Admin group if in any.

# Players Manager Module
(Responsible for handling player penalties that can be applied by admins)

+ An all new class based system with more than 10 available penalties and some custom built,
  "fun" like functions to use on players, like: Fireworks, Drug Mode, and more.
+ Now Addons can also  take advantage of the new class system to apply penalties in certain
  situations. (i.g kicking AFK players)
* The Ban and Mute System have each been ported to their own standalone Addon.
- Unlike the old version, only a selection of penalties will feature chat commands

# Addons Monitor Module
(Responsible for monitoring, loading, unloading Addons)

+ Improved toggle-able options visually, in a simplified manner.
+ Locked Addons can only be accessed by Super Admins, meaning that Admins with the
  Addons Monitor flag cannot accessed.
+ If an Addon has its own settings, after the first time the Addon is loaded up, the same
  Settings Help Window add_option will appear in the Addon profile page.

# Addons Section:
(Not all Addons will be mentioned below, but only the ones who received major changes)

[Admins Chat]

+ Admins default chat colour is now in white.
+ Admins can use @ before any in-game message for special funtions such as:
	- Starting team message with one @ will send the message in private to all other Admins.
	- Starting an all-chat with @ will send a @SERVER message, anyone in the server can see it.
	- Starting an all-chat with @@ will send a center message, anyone in the server can see it.
+ Admins can use color codes in their own messages.
+ The 'say' command in the server console was replaced and will act as @SERVER message.

[Ban Manager Addon]

+ Ban add_option now lists 2 groups of players, Online players and Offline players, Offline players
  being players that have been in the server before but aren't currently active.
  This allows Admins to ban players even when they are not in the server.
+ Ban lengths are now sorted and grouped by Ban Levels, and the Admin's ban level will be
  displayed in the page footer.
+ Ban Profile page now lists the player name, SteamID, the date the ban was given,
  ban expiration date + hour, the Admin that gave the ban and the ban reason.
+ Ban Logs are no longer stored in files, but rather in their own database.
+ Ban History add_option now sorts bans by year + month.
+ Ban logs are now shown in a Info type message.
