# A Discord Bot for University Community Servers

This bot is used to generate and maintain text channels for courses taken by UON students to collaborate and chat. It also provides a number of other moderation tools

Commands are restricted to discord users with roles authorised in the config file under "trustedRoles"

## Automated channel creation

The bot also has functionality to read courses from a JSON file and automatically create text and voice channels accordingly.
The format is as follows:
1. A category for each item in the `courses` dictionary in the specified JSON
2. Nested in this category, a text channel for each item in that category's list
3. Nested in this category, a single voice channel

Prefix is `$rain` followed by some command. All commands and arguments are case sensitive!

`$raincreate <filename>` will create course channels, roles, and voice channels based on a JSON file with the specified filename

`$rainedit <rolemenu name> <arg1> <arg2> [<arg3>]` will edit the role menu of the specified name. This command must be sent in the channel that the role menu exists in. It will only edit the role menu - if the reason you are editing is because you are adding or removing channels or roles, you need to manually create or remove these channels or roles. I figure this will be an infrequent thing and so I decided to leave the option open regarding what to do here.

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

## Reporting and Verification

There is a number of reasons why you might wish messages to be automatically deleted and reposted elsewhere. Whether it is for sending in personal data to the moderation team for verification, or as a reporting system for people to bring things to the moderators attention.

In the "reportingChannels" section of `config.json` you can add a list of lists to specify what channels should be listened to and where messages should be reposted. The first item in the list is the listening channel, the second item is the channel to repost the message in, and the final item is the message that should be reposted.
 The `@user` and `@message` keywords will be replaced with the author (As a mention) and message of the sender, respectively
 
Feature can be disabled by leaving "reportingChannels" an empty list `[]`

## Message edit and delete monitoring
To allow for academic integrity moderation, any edited or deleted message will be reposted in a channel specified in `config.json` under "moderationChannel". By default this is `edit-delete-log`

Feature can be disabled by leaving "moderationChannel" an empty string `""`

## Channel locking
Channels that have been created with the automated channel creation can also be locked for a period of time by disabling send message permissions to the role that makes that channel available. This can be helpful during exams and assessment tasks in order to help moderate for academic integrity.

`$rainlock` will disable send message permissions to the role with the same name as the channel the command is sent. A message will be sent by the bot with an unlocked padlock, a user with a "trustedRole" adding their reaction to this message will unlock the channel again.

## File Manipulation

It is possible to update the config file or add a new json file for channel creation straight from discord!

`$rainaddfile` with an attached file will add a file to the cwd - if the file already exists you can pass either `-o` to overwrite, or `-a` to add a copy in which case the file will be added with `(1)` added to the filename

`$rainremfile <filename>` will remove a file from the cwd  - Source files are protected

`$rainlistfiles` will list all files currently the cwd - Source files are excluded

## Updating Bot
RainbowBot has a built in method of running a shell script on demand. Primarily this is designed to pull the latest master from GitHub and restart the bot, but it can have many other applications.

`$rainupdate` is the command that will run an executable shell script in the cwd named `updatebot.sh`

## Direct Message support

The bot has the capability to receive Direct Messages from users and repost their questions in a moderators channel. The bot looks through all mutual servers it has with the user and posts in all channels where the name matches the name specified in "logChannel".

Feature can be disabled by leaving "logChannel" an empty string `""`

## TODO

- [ ] Use argparse instead of the current janky setup
- [ ] Change the format of `rolemenu.dat` to allow for multiple different rolemenus and channels. Fix the arguments to make -c be optional properly

## Planned features
- [ ] Delete messages for moderation by passing a number of messages to clear

## License
[MIT](https://github.com/LachlanCourt/rainbowBot/blob/master/LICENCE)
