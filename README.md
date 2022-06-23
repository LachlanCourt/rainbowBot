# A Multitenanted Discord Bot for University Community Servers

This bot is used to generate and maintain text channels for courses taken by university students to collaborate and chat. It also provides a number of other moderation tools. It is multitenanted and can manage several discord servers with a single instance of the bot.

## Setup

1.  Install requirements

        pip install -r requirements.txt

2.  Create configuration files from examples

        cp config.json.example config.json
        cp .env.example .env

3.  Generate OAuth Token (see [here](https://discord.com/developers/applications)) - either add it to .env or run with an environment variable, and populate config.json using the ID of the server as a key. This can be found by right clicking the server icon in discord with developer settings turned on

4.  Run bot!

        OAuthToken=<token> python3 bot.py

## Authorisation and Command Structure

All commands are prefixed with `$rain`. All commands and arguments are case sensitive.

Commands are restricted by discord roles specified in the config file. There are three levels of authorisation that restrict the moderation and bot management commands, in the format `[[rolesWithHighLevelAuthorisation], [rolesWithModerateLevelAuthorisation], [rolesWithLowLevelAutherisation]]`. If a restriction is not specified for a command below, it can be used by anyone in the server. A lot of commands are restricted by role name so in order to make the most use of the functionality, be sure to fill this out correctly.

## Automated channel creation

Moderate level authorisation required

The bot has functionality to read courses from a JSON file and automatically create text and voice channels accordingly.
The format is as follows:

1. A category for each item in the `courses` dictionary in the specified JSON
2. Nested in this category, a text channel for each item in that category's list
3. Nested in this category, a single voice channel

`create <filename>` will create course channels, roles, and voice channels based on a JSON file with the specified filename

The format of the courses JSON can be seen in the examples directory. The channel structure should be a dictionary where the keys indicate the name of the category, and the items are a list of subjects to be nested in that category. In regards to custom overwrites, this will allow you to add restrictions accross the entire generated channels on a per-role basis. The dictionary keys should be the role name, and the items should be a list of lists with the name of the permission in snake case, and either a -1, 0, or 1 to indicate Deny, Inherit or Allow.

`edit <rolemenu name> <arg1> <arg2> [<arg3>]` will edit the role menu of the specified name. This command must be sent in the channel that the role menu exists in. It will only edit the role menu - if the reason you are editing is because you are adding or removing channels or roles, you need to manually create or remove these channels or roles. I figure this will be an infrequent thing and so I decided to leave the option open regarding what to do here.

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

In the "reportingChannels" section of `config.json` you can add a list of lists to specify what channels should be listened to and a channel where messages should be reposted. The first item in the list is the listening channel, the second item is the channel to repost the message in, and the final item is the message that should be reposted.
The `@user`, `@message`, and `@<Role>$` keywords will be replaced with the author (As a mention), message of the sender, and the role name respectively

Feature can be disabled by leaving "reportingChannels" an empty list `[]`

## Message edit and delete monitoring

To allow for full community moderation, any edited or deleted message can be reposted in a channel specified in `config.json` under "moderationChannel". By default this is `edit-delete-log`. Users and channels can be added to an allowlist in relevant fields in the config file to assist with custom moderation of specific parts of the server.

Feature can be disabled by leaving "moderationChannel" an empty string `""`

## Channel locking

Low level authorisation required

Channels that have been created with the automated channel creation can also be locked for a period of time by disabling send message permissions to the role that makes that channel available. This can be helpful during exams and assessment tasks in order to help moderate for academic integrity.

`lock [channelName]` is a manual command that will disable send message permissions to the role with the same name as the selected channel. If no argument is given, the selected channel is the name of the channel in which the command is sent. If an argument is given, the selected channel will be the channel whose name matches the argument. Either way, a message will be sent by the bot into the channel the command was sent with an unlocked padlock, a user with a "trustedRole" adding their reaction to this message will unlock the channel again.

### Tasks

Alternatively, a file with a schedule of lock and unlock times can be added into the root directory and registered with `regtask <filename>`. Registered task files will lock and unlock channels automatically according to the times specified. Note that the time will not fall exactly on the minute so it is recommended to choose a time slightly earlier than the exact time that you need a channel to be locked. The format of times in this file should match that of linux cron jobs. If at any point you are not using a specific file anymore, it is recommended that you run `unregtask <filename>` to unmount the task and save processing power. Files can be validated by using the command `checktask <filename>` which will validate the task file.

## File Manipulation

High level authorisation required

It is possible to update the config file or add a new json file for channel creation straight from discord!

`addfile` with an attached file will add a file to the cwd - if the file already exists you can pass either `-o` to overwrite, or `-a` to add a copy in which case the file will be added with an integer eg. `(1)` added to the filename

`remfile <filename>` will remove a file from the cwd - Source files are protected from being removed

`listfiles` will list all files currently the cwd - Source files are excluded

## Updating Bot

High level authorisation required

RainbowBot has a built in method of running a shell script on demand. This can be used to pull the latest update from GitHub and restart the bot, but it can have many other applications.

`update` will run an executable shell script in the cwd named `updatebot.sh`.

## Direct Message support

The bot has the capability to receive Direct Messages from users and repost their questions in a moderators channel. The bot looks through all mutual servers it has with the user and posts in all channels where the name matches the name specified in "logChannel".

Feature can be disabled by leaving "logChannel" an empty string `""`

## Deployment

Rainbow bot can be deployed in two different ways, on a local server or deployed in a cloud environment.

### Local

Local deployment can be setup as per the instructions specified at the start of this README. The OAuth token can either be stored in the config file or passed in as an environment variable. The bot will create a data file named `data.dat` in the current working directory along with a `tenants` directory, and will also look for the config file here by default. It is not necessary or recommended to change the data file or the tenants directory in any way. The location of the data file and config file can be modified using the command line arguments specified below.

### Cloud

Cloud deployment is optimised for Heroku with an AWS S3 bucket for persistent storage. Ensure that all required environment variables are defined or else the bot may not work as expected. It is recommended that the PaperTrail addon is included with a Heroku deployment to help manage logs.

The first time the bot is run, the `config.json` file will need to be uploaded to the S3 bucket manually. This requirement will be changing in a future update as you will soon be able to optionally start the bot without a config file. Subsequent updates to the config can be achieved by sending the command `addconfig` with the updated `config.json` file attached to the discord message.

In addition to `config.json`, the bot will create a second data file in the bucket which it will maintain. It is not necessary or recommended to change this in any way. By default this file will be named `data.dat`.

## Environment Variable Reference

- `OAuthToken`: Value should be the discord bot OAuth token. Can be optionally declared here on in the config file. Variable will override config value if both are defined.
- `ENVIRONMENT`: Value should be `PRODUCTION` when deployed to a cloud environment. Optional in other scenarios
- `AMAZON_S3_BUCKET_NAME`: Name of S3 bucket. Required when deployed to a cloud environment
- `AMAZON_S3_ACCESS_ID`: Access ID of Amazon IAM user with S3 bucket read/write permissions. Required when deployed to a cloud environment
- `AMAZON_S3_SECRET_ACCESS_KEY`: Secret Access Key of Amazon IAM user with S3 bucket read/write permissions. Required when deployed to a cloud environment

## Command Line Arguments

- `--config-file <filepath>` will modify the location that the bot looks for `config.json`
- `--data-file <filepath>` will modify the location that the bot saves its data file.

## Contribution

Contributions are welcome! Please read the [contribution guide](https://github.com/LachlanCourt/rainbowBot/blob/master/contribution%20guide.md) before commencing development

## TODO

Tasks for future development are maintained as [issues](https://github.com/LachlanCourt/rainbowBot/issues)

## License

[MIT](https://github.com/LachlanCourt/rainbowBot/blob/master/LICENCE)
