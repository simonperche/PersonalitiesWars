# IdolsBot

A [Mudae](https://top.gg/bot/432610292342587392) like bot only for KPop idols.

[![Codacy Badge](https://app.codacy.com/project/badge/Grade/e7e94a9dbe624ba4b520b265fbe728fc)](https://www.codacy.com/manual/Solidras/IdolsBot?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=Solidras/IdolsBot&amp;utm_campaign=Badge_Grade)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
 
## Tasks

| Feature                    | Progress     |
|----------------------------|--------------|
| Create database            | Done         |
| Roll random idol           | Done         |
| See information about idol | Done         |
| Wishlist                   | Done         |
| Trade                      | Done         |
| Change picture of idols    | Done         |
| Monetary system            | To do        |
| Custom groups and idols    | To do        |

## Commands

Commands are separated in multiple [Cogs](https://discordpy.readthedocs.io/en/latest/ext/commands/cogs.html) to add clarity and organization in the code.

| Category                   | Command *param* [opt_param]     | Description                                                | Alias       |
|----------------------------|---------------------------------|------------------------------------------------------------|-------------|
| **Roll**                   | roll                            | Roll a random idol                                         |             |
| **Information**            | information *name* [group]      | Show information about an idol                             | info        |
|                            | list *name*                     | List all idols with this name                              |             |
| **Profile**                | profile [mention_user]          | Show the profile (the deck) of a member                    | pr          |
|                            | time                            | Show claiming and rolling time reset                       | tu          |
| **Wishlist**               | wish *name* [group]             | Add idol to your wish list                                 |             |
|                            | wishremove *name* [group]       | Remove idol from your wish list                            |             |
|                            | wishlist                        | Show your wish list                                        | wl          |
| **Admin**                  | set_claiming_interval *minutes* | Set the claiming interval in minutes for this server       |             |
|                            | set_nb_rolls_per_hour *number*  | Set the number of rolls per hour for this server           |             |
|                            | set_time_to_claim *seconds*     | Set the time to claim an idol (in seconds) for this server |             |
|                            | show_configuration              | Show the configuration of this server                      | show_config |
| **Utilities**              | help                            | Display the help                                           |             |
|                            | ping                            | Ping the bot to see if it's active                         |             |


## Creating necessary files
You need to create one .env file to be able to launch the bot with the application you created on [Discord Developers Portal](https://discord.com/developers/applications).
This file must be named *.env* and placed in *src/* folder. It should contains one line with the bot token.
### Example 
```
# .env file
BOT_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```
