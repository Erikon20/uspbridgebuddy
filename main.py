#from telegram.ext import Updater, InlineQueryHandler, CommandHandler
import requests
import re
import logging
from telegram.ext import *
from telegram import *
import json
import os

# Enabling logging
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger()

# Getting mode, so we could define run function for local and Heroku setup
mode = os.getenv("MODE")
TOKEN = os.getenv("TOKEN")
if mode == "dev":
    def run(updater):
        updater.start_polling()
elif mode == "prod":
    def run(updater):
        PORT = int(os.environ.get("PORT", "8443"))
        HEROKU_APP_NAME = os.environ.get("HEROKU_APP_NAME")
        # Code from https://github.com/python-telegram-bot/python-telegram-bot/wiki/Webhooks#heroku
        updater.start_webhook(listen="0.0.0.0",
                              port=PORT,
                              url_path=TOKEN)
        updater.bot.set_webhook("https://{}.herokuapp.com/{}".format(HEROKU_APP_NAME, TOKEN))
else:
    logger.error("No MODE specified!")
    sys.exit(1)

OPENING = range(1)

with open("library.json", "r") as read_file:
	BIDLIBRARY = json.load(read_file)

"""
def get_url():
	contents = requests.get('https://random.dog/woof.json').json()	  
	url = contents['url']
	return url

def bop(bot, update):
	url = get_url()
	chat_id = update.message.chat_id
	bot.send_photo(chat_id=chat_id, photo=url)
"""
def start(bot,update):
	logger.info("User {} started bot".format(update.effective_user["id"]))
	bot.send_message(update.message.chat_id,"Hello! This is the USP Bridge Buddy Bot! Hopefully this will help you be a meaner bidder ^__^")

def hi(bot,update):
	logger.info("User {} said hi".format(update.effective_user["id"]))
	update.message.reply_text("Hello {0}".format(update.message.from_user.first_name))
	
def openings(bot,update):
	reply_keyboard = [["1C", "1D", "1H", "1S"]]
	logger.info("User {} issued command: /openings".format(update.effective_user["id"]))
	update.message.reply_text("Which opening do you want to learn more about?", reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard = True))
	return OPENING

"""	   
def open_1c(bot,update):
	update.message.reply_text("1C Opening: 12+ HCP, 3+ Clubs, Clubs > Diamonds (can be equal if 3-3 C,D)")
	return ConversationHandler.END
	
def open_1d(bot,update):
	update.message.reply_text("1D Opening: 12+ HCP, 3+ Diamonds, Diamonds > Clubs (can be equal if 4-4 or above C,D)")
	return ConversationHandler.END
	
def open_1h(bot,update):
	update.message.reply_text("1H Opening: 12+ HCP, 5+ Hearts")
	return ConversationHandler.END
	
def open_1s(bot,update):
	update.message.reply_text("1S Opening: 12+ HCP, 5+ Spades")
	return ConversationHandler.END
	"""
	
def open(bot,update):
	bid = update.message.text
	open_dict = {'1C':"1C Opening: 12+ HCP, 3+ Clubs, Clubs > Diamonds (can be equal if 3-3 C,D)",
		'1D':"1D Opening: 12+ HCP, 3+ Diamonds, Diamonds > Clubs (can be equal if 4-4 or above C,D)",
		'1H':"1H Opening: 12+ HCP, 5+ Hearts",
		'1S':"1S Opening: 12+ HCP, 5+ Spades"
		}
	if bid in open_dict:
		update.message.reply_text(open_dict[bid])
		return ConversationHandler.END
	else:
		update.message.reply_text("w0t u high m8")
		return OPENING
	
def cancel(bot,update):
	logger.info("User {} issued command: /cancel".format(update.effective_user["id"]))
	update.message.reply_text("oof")
	return ConversationHandler.END
	
def bid_library(bot, update, args):
	#bidseq_txt = update.message.text
	bidseq = args
	bidseq_txt = str(bidseq)
	logger.info("User {0} issued command: /bidhelp {1}".format(update.effective_user["id"], bidseq_txt))
	#bidseq = bidseq_txt.split(" ")
	curr = BIDLIBRARY
	reply_str = "*** {0} Info ***\nCurrent Bidding Seq:\n".format(bidseq_txt)
	for i in bidseq:
		if i not in curr:
			update.message.reply_text("You derped with this bid: {0}".format(i))
			return
		curr = curr[i]
		reply_str += "\n{0}: {1}".format(i, curr["text"])
	reply_str += "\n\nYour Options:"
	#print(curr)
	for j in curr:
		if j == "text":
			continue
		reply_str += "\n{0}: {1}".format(j, curr[j]["text"])
	update.message.reply_text(reply_str)	

def main():
	logger.info("Starting bot...")
	updater = Updater(TOKEN)
	dp = updater.dispatcher
	#conv_handler = ConversationHandler(entry_points = [CommandHandler("openings", openings)], states = {OPENING: [RegexHandler('^1C$', open_1c), RegexHandler('^1D$',open_1d), RegexHandler('^1H$', open_1h), RegexHandler('^1S$', open_1s)]}, fallbacks = [CommandHandler('cancel', cancel)])
	#conv_handler2 = ConversationHandler(entry_points = [CommandHandler("openings", openings)], states = {OPENING: [RegexHandler('^1C|1D|1H|1S$', open)]}, fallbacks = [CommandHandler('cancel', cancel)])
	conv_handler3 = ConversationHandler(entry_points = [CommandHandler("openings", openings)], states = {OPENING: [MessageHandler(Filters.text, open)]}, fallbacks = [CommandHandler('cancel', cancel)])
	dp.add_handler(CommandHandler('start', start))
	dp.add_handler(CommandHandler('hi',hi))
	dp.add_handler(CommandHandler('bidhelp', bid_library, pass_args = True ))
	dp.add_handler(conv_handler3)
	run(updater)
	updater.idle()

if __name__ == '__main__':
	main()