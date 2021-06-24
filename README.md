# Optimised Blackboard Bot

This bot is used to generate and maintain text channels for courses taken by UON students to collaborate and chat. It also provides a number of other moderation tools

# Student Number verification

If a message is sent in the channel `student-number-for-verification`, it will automatically be deleted and reposted in `pending-verifications`. `pending-verifications` can then be a moderator only channel and be used to verify students

# Edit and delete monitoring
To allow for academic integrity moderation, any edited or deleted message will be reposted in a channel specified in `config.json`. By default this is `edit-delete-log`

# Automated channel creation

The bot also has functionality to read courses from a JSON file and automatically create text and voice channels accordingly.
The format is as follows:
1. A category for each item in the `courses` dictionary in the specified JSON
2. Nested in this category, a text channel for each item in that category's list
3. Nested in this category, a single voice channel

These are available by default to anyone with Mods role or Admin role - permission is just shared as a "trusted" role.

Prefix is `$obb` followed by some command. All commands and arguments are case sensitive!

`$obbcreate <filename>` will create course channels, roles, and voice channels based on a JSON file with the specified filename

`$obbedit <rolemenu name> <arg1> <arg2> [<arg3>]` will edit the role menu of the specified name. This command must be sent in the channel that the role menu exists in. It will only edit the role menu - if the reason you are editing is because you are adding or removing channels or roles, you need to manually create or remove these channels or roles. I figure this will be an infrequent thing and so I decided to leave the option open regarding what to do here.

`<arg1>` should be one of the following commands `add`, `remove`, `update`

`add` will add a role to a rolemenu
    `arg2` should be the name of the role to be added
    `arg3` is not required

`remove` will remove a role from a rolemenu
    `arg2` should be the name of the role to be removed
    `arg3` is not required

`update` will edit the name of a role in a rolemenu
    `arg2` should be the name of the role to change
    `arg3` should be the name you wish to change it to