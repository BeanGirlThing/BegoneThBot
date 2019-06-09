"""

BEGONETHBOT MAIN SCRIPT

Version 1.0.1

Please refer to LICENCE for licence information
Licence information for gibberish detection scripts can be found in the "gibdetect" directory

"""




from telegram.ext import Updater, MessageHandler, CommandHandler, Filters
from telegram.error import InvalidToken,Unauthorized,TelegramError
from telegram import Bot
from bs4 import BeautifulSoup
import requests
import json
import sqlite3
import logging
from googletrans import Translator
import gibdetect


class main:

    def __init__(self):

        print("Launching BEGONETHBOT")

        # Initialise logging at a basic level
        with open("config.json","r") as cfg:
            self.config = json.loads(cfg.read())

        self.debug = self.config["debugmode"]

        if self.debug:
            print("Debug mode is on")
            logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                            level=logging.DEBUG)
        else:
            logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                                level=logging.INFO)

        # Create the google translate translator object
        self.translator = Translator()

        # Load the config


        # Create the gibberish detection object
        self.gibdetector = gibdetect.gibdetect()


        print("Connecting to bot")

        try:
            # Create both an updator object for receving updates and a bot object for performing actions at the bot
            self.updater = Updater(token=self.config["botauthtoken"])
            self.bot = Bot(token=self.config["botauthtoken"])
        except InvalidToken:
            # If the bot token is invalid
            print("Bot connection failed: Invalid Token")

        # Handler section, this is defining handlers for commands and events
        # When someone uses the command /ping the self.ping function will be executed
        ping_handler = CommandHandler("ping",self.ping)
        # When a message appears and is filtered down to there being a new chat member the self.newuser function will be executed
        newuser_handler = MessageHandler(Filters.status_update.new_chat_members,self.newuser)
        # Add the handlers to the dispatcher contained within the updater
        self.updater.dispatcher.add_handler(ping_handler)
        self.updater.dispatcher.add_handler(newuser_handler)
        try:
            print("Starting bot")
            # Set the bot to listen for commands and events
            self.updater.start_polling()
            # Idle
            print("Bot started")
            self.updater.idle()
        except Exception as e:
            # If any error occours it is stored in e
            print(e)
            # The updator is stopped
            self.updater.stop()
            # The database gets gracefully closed

    def ping(self,update,context):
        # Send the message "Pong!" to a chat if user is an admin
        chatadmins = self.bot.get_chat_administrators(context.message.chat.id)
        sender = context.to_dict()["message"]["from"]["username"]
        for i in range(0,len(chatadmins)):
            if sender == chatadmins[i].user.username:
                context.message.chat.send_message("Pong!")



    def newuser(self,update,context):
        # Gather information about the user based on the join message
        id,first_name,username,is_bot = context["message"]["new_chat_members"][0]["id"],context["message"]["new_chat_members"][0]["first_name"],context["message"]["new_chat_members"][0]["username"],context["message"]["new_chat_members"][0]["is_bot"]
        dcontext = context.to_dict()

        try:
            dcontext["message"]["from"]["username"]
        except KeyError:
            return 0

        if username == dcontext["message"]["from"]["username"]:

            # Get a raw string of html data for the telegram profile page based on the username
            rawdata = requests.get(f"https://t.me/{username}")

            # Use BeautifulSoup to process and parse that html
            parsedhtml = BeautifulSoup(rawdata.content, features="html.parser")

            # From that parsed html find the users bio from the meta tags
            bio = parsedhtml.find("meta", attrs={"property": "og:description"})["content"]

            # From that parsed html get a link to the users current profile picture
            profilepic = parsedhtml.find("meta", attrs={"property": "og:image"})["content"]

            # Create the redflags variable which will be used to counting the number of redflags a profile has
            redflags = 0
            flaglist = []

            # Push the first name of the user into google translate to get information on its source language and translation when in english
            tranname = self.translator.translate(first_name, dest="en")

            # If the source language is arabic
            if tranname.src == "ar":
                # Add one to redflags
                redflags += 1
                # asp is used for database purposes and is used to tell the database wether the original name contained Arabic Script
                asp = "1"
                flaglist.append("Language arabic")

            elif tranname.src == "fa":
                redflags += 1
                asp = "1"
                flaglist.append("Language persian")
            else:
                asp = "0"


            if not self.gibdetector.scan(tranname.text):
                redflags += 1
                flaglist.append("First_name is gibberish")

            if profilepic == "https://telegram.org/img/t_logo.png":
                redflags += 1
                iconpresence = "0"
                flaglist.append("User does not have a profile pic")
            else:
                iconpresence = "1"

            if bio == f"You can contact @{username} right away.":
                redflags += 1
                flaglist.append("User has no/default bio")

            if not self.gibdetector.scan(username):
                redflags += 1
                flaglist.append("Username is gibberish")

            if is_bot == True:
                redflags = 0

            if self.debug == True:
                print(f"**Ooh its debug time!**\nUser connected to group!\n**Userdata:**\nFirst Name: {first_name}\nUsername: {username}\nProfile image link: {profilepic}\nBio: {bio}\nUsername language: {tranname.src}\nUsername translated: {tranname.text}\nUser has hit {str(redflags)} redflags! These being:\n{str(flaglist)}")

            if redflags >= 4:
                try:
                    self.bot.kickChatMember(context.message.chat.id, id, until_date=-1)
                except TelegramError:
                    context.message.chat.send_message("Attempted to kick detected bot user but I have insufficient permissions.")
                finally:
                    if self.config["database"]["enabled"]:
                        # Database operations
                        if self.config["database"]["enabled"] == True:
                            try:
                                # Try to connect to the database
                                self.db = sqlite3.connect(f"file:{self.config['database']['filename']}.db?mode=rw", uri=True)
                                # Create a cursor for that connection
                                self.cursor = self.db.cursor()
                            except sqlite3.OperationalError:
                                # If the database could not be connected to then create a database
                                self.db = sqlite3.connect(f"{self.config['database']['filename']}.db")
                                # Create a cursor for that connection
                                self.cursor = self.db.cursor()
                                # Create a table in the database that will store information on bots
                                self.cursor.executescript(
                                    """
                                    CREATE TABLE botlogger (handle TEXT, name TEXT, bio TEXT, iconpresence BOOL, arabicscriptpresence BOOL, datetime TEXT);
                                    """
                                )
                        # handle TEXT, name TEXT, bio TEXT, iconpresence BOOL, arabicscriptname BOOL, datetime TEXT
                        self.cursor.execute(f"""
                        INSERT INTO botlogger VALUES ("{username}","{tranname.text}","{bio}",{iconpresence},{asp},"{context.message.date}");
                        """)
                        self.db.commit()
                        self.db.close()


if __name__ == "__main__":
    main()