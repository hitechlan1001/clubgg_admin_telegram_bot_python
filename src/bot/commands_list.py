# src/bot/commandsList.py
from telegram import BotCommand

# List of bot commands (for set_my_commands)
commands = [
    BotCommand("start", "Start the bot"),
    BotCommand("help", "Show available commands"),

    # Club limit management (auto-detected from chat)
    BotCommand("cl", "View current limits for this club"),
    BotCommand("addwl", "Add to Weekly Win Limit"),
    BotCommand("subwl", "Subtract from Weekly Win Limit"),
    BotCommand("setwl", "Set Weekly Win Limit"),
    BotCommand("addsl", "Add to Weekly Loss Limit"),
    BotCommand("subsl", "Subtract from Weekly Loss Limit"),
    BotCommand("setsl", "Set Weekly Loss Limit"),

    # Credit management (auto-detected from chat)
    BotCommand("scr", "Send credits to this club"),
    BotCommand("ccr", "Claim credits from this club"),
]

