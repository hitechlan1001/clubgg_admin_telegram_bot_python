# src/bot/commandsList.py
from telegram import BotCommand

# List of bot commands (for set_my_commands)
commands = [
    BotCommand("start", "Start the bot"),
    BotCommand("help", "Show available commands"),

    # Club limit management
    BotCommand("cl", "View current limits for a club"),
    BotCommand("addwl", "Add to Weekly Win Limit"),
    BotCommand("subwl", "Subtract from Weekly Win Limit"),
    BotCommand("setwl", "Set Weekly Win Limit"),
    BotCommand("addsl", "Add to Weekly Loss Limit"),
    BotCommand("subsl", "Subtract from Weekly Loss Limit"),
    BotCommand("setsl", "Set Weekly Loss Limit"),

    # Credit management
    BotCommand("scr", "Send credits to a club"),
    BotCommand("ccr", "Claim credits from a club"),
]

