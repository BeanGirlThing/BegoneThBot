from telegram.ext import Updater, MessageHandler, CommandHandler, Filters
from telegram.error import InvalidToken,Unauthorized,TelegramError,NetworkError
import json
import sqlite3

class main:

    def __init__(self):
        print("Launching BEGONETHBOT")
        with open("config.json","r") as cfg:
            self.config = json.loads(cfg.read())
        print("Connecting to bot")
        try:
            self.bot = Updater(token=self.config["botauthtoken"])
        except InvalidToken:
            print("Bot connection failed: Invalid Token")

        if self.config["database"]["enabled"] == True:
            print(f"Connecting to database {self.config['database']['filename']}")
            try:
                self.db = sqlite3.connect(f"file:{self.config['database']['location']}{self.config['database']['filename']}.db?mode=rw",uri=True)
                self.cursor = self.db.cursor()
            except sqlite3.OperationalError:
                self.db = sqlite3.connect(f"{self.config['database']['location']}{self.config['database']['filename']}.db")
                self.cursor = self.db.cursor()
                self.cursor.executescript(
                    """
                    CREATE TABLE botlogger (handle TEXT, name TEXT, bio TEXT, iconpresence BOOL, sandscritname BOOL);
                    """
                )
        ping_handler = CommandHandler("ping",self.ping)
        newuser_handler = MessageHandler(Filters.status_update.new_chat_members,self.newuser)
        self.bot.dispatcher.add_handler(ping_handler)
        self.bot.dispatcher.add_handler(newuser_handler)
        try:
            print("Starting bot")
            self.bot.start_polling()
            self.bot.idle()
        except Exception as e:
            print(e)
            self.bot.stop()

    def ping(self,update,context):
        context.message.chat.send_message("Pong!")

    def newuser(self,update,context):
        id,first_name,username = context["message"]["new_chat_members"][0]["id"],context["message"]["new_chat_members"][0]["first_name"],context["message"]["new_chat_members"][0]["username"]




if __name__ == "__main__":
    main()