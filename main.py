#from telegram.ext import Updater, InlineQueryHandler, CommandHandler
import requests
import re
import logging
from telegram.ext import *
from telegram import *
import json
import os, sys

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

#States for ConversationHandler
OPENING, BIDHELPER = range(2)

#Open bidding library data
with open("library.json", "r") as bidlibrary_file:
	BIDLIBRARY = json.load(bidlibrary_file)
	
#Open bidhelper memory data
with open("bidhelper_memory.json", "r+") as bidhelper_mem_file:
	BIDHELPER_MEM = json.load(bidhelper_mem_file)

#/start command
def start(bot,update):
	logger.info("User {} started bot".format(update.effective_user["id"]))
	bot.send_message(update.message.chat_id,"Hello! This is the USP Bridge Buddy Bot! Hopefully this will help you be a meaner bidder ^__^\n\nUse /help for help.")

#/hi command: Greets user
def hi(bot,update):
	logger.info("User {} said hi".format(update.effective_user["id"]))
	update.message.reply_text("Hello {0}".format(update.message.from_user.first_name))

#/openings command: Gives info about the 4 usual openings	
def openings(bot,update):
	reply_keyboard = [["1C", "1D", "1H", "1S"], ["1NT", "2C", "2NT"]]
	logger.info("User {} issued command: /openings".format(update.effective_user["id"]))
	update.message.reply_text("Which opening do you want to learn more about?", reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard = True))
	return OPENING

#Handling Conversation with User through /openings	
def openings_part2(bot,update):
	bid = update.message.text
	open_dict = {'1C':"1C Opening: 12+ HCP, 3+ Clubs, Clubs > Diamonds (can be equal if 3-3 C,D)",
		'1D':"1D Opening: 12+ HCP, 3+ Diamonds, Diamonds > Clubs (can be equal if 4-4 or above C,D)",
		'1H':"1H Opening: 12+ HCP, 5+ Hearts",
		'1S':"1S Opening: 12+ HCP, 5+ Spades",
		'1NT':"1NT Opening: 15-17 HCP, Balanced (Strictly No 1- Suits or 6+ Suits)",
		'2C':"2C Opening: Super Strong 22+ HCP",
		'2NT':"2NT Opening: 20-21 HCP, Balanced (Strictly No 1- Suits or 6+ Suits)"
		}
	if bid in open_dict:
		update.message.reply_text(open_dict[bid])
		return ConversationHandler.END
	else:
		update.message.reply_text("w0t u high m8, no such opening: {}".format(update.message.text))
		return OPENING

#/cancel command during conversation		
def cancel(bot,update):
	logger.info("User {} issued command: /cancel".format(update.effective_user["id"]))
	update.message.reply_text("oof")
	return ConversationHandler.END

#/bidhelp command: give bidding options 	
def bid_library(bot, update, args):
	bidseq = args
	bidseq_txt = bidding_tolist(bidseq)
	logger.info("User {0} issued command: /bidhelp {1}".format(update.effective_user["id"], bidseq_txt))
	reply_str = bidhelp_reply_str_builder("",bidseq)
	update.message.reply_text(reply_str)	

#bidhelp helper command: convert list to bidding sequence string
def bidding_tolist(bidseq):
	result = ""
	for i in bidseq:
		result += i + " - "
	return result[:-3]
	
def bidhelp_reply_str_builder(reply_str, bidseq):
	reply_str = "*** {0} Info ***\nCurrent Bidding Seq:\n".format(bidding_tolist(bidseq))
	curr = BIDLIBRARY
	for i in bidseq:
		if i not in curr:
			return "You derped with this bid: {0}".format(i)
		curr = curr[i]
		reply_str += "\n{0}: {1}".format(i, curr["text"])
	reply_str += "\n\nYour Options:"
	for j in curr:
		if j == "text":
			continue
		reply_str += "\n{0}: {1}".format(j, curr[j]["text"])
	return reply_str
	
#/bidhelper command: conversation version of bidhelp
def bidhelper(bot, update, args):
	logger.info("User {0} issued command: /bidhelper {1}".format(update.effective_user["id"], args))
	#using old seq from memory
	if not args:
		bidhelper_read_mem()
		if str(update.effective_user["id"]) in BIDHELPER_MEM:
			bidseq = BIDHELPER_MEM[str(update.effective_user["id"])]
			update.message.reply_text("Continuing previous bidding sequence: {0}\n\n To start new bidhelper from opening bids, use /bidhelper open".format(bidding_tolist(bidseq)))
			return bidhelper(bot, update, bidseq)
		else:
			update.message.reply_text("Please input a bidding sequence after /bidhelper as there is no sequence in memory")
			return ConversationHandler.END
	#providing new bidseq to replace memory
	else:
		opening = False
		if type(args[0]) == type([]):
			bidseq = args[0]
		elif args[0] == "open":
			bidseq = []
			opening = True
		else:
			bidseq = args
		reply_text = bidhelp_reply_str_builder("", bidseq)
		update.message.reply_text(reply_text)
		if not reply_text.__contains__("derped"):	#validity check
			bidhelper_update_mem(bot, update, bidseq)
			update.message.reply_text("Please enter next bid.\nPress /cancel to end bidhelper.")
			return BIDHELPER
		else:
			return ConversationHandler.END

#read from BIDHELPER_MEM.json
def bidhelper_read_mem():
	global BIDHELPER_MEM
	with open("bidhelper_memory.json", "r") as f:
		data = json.load(f)
	BIDHELPER_MEM = data
	return data

#update BIDHELPER_MEM.json			
def bidhelper_update_mem(bot, update, bidseq):
	global BIDHELPER_MEM
	data = bidhelper_read_mem()
	data[update.effective_user["id"]] = bidseq
	BIDHELPER_MEM = data
	with open("bidhelper_memory.json", "w") as f:
		json.dump(data, f)
		f.close()
	bidhelper_read_mem()
			
def bidhelper_continue(bot, update):
	newbid = update.message.text
	logger.info("User {0} responded to bidhelper convo with: {1}".format(update.effective_user["id"],newbid))
	bidhelper_read_mem()
	bidseq = list(BIDHELPER_MEM[str(update.effective_user["id"])])
	bidseq.append(newbid)
	reply_text = bidhelp_reply_str_builder("", bidseq)
	update.message.reply_text(reply_text)
	if not reply_text.__contains__("derped"):
		bidhelper_update_mem(bot, update, bidseq)
		update.message.reply_text("Please enter next bid.\nPress /cancel to end bidhelper.")
		return BIDHELPER
	else:
		return ConversationHandler.END

		
#/help
def user_help(bot, update):
	logger.info("User {} used command: /help".format(update.effective_user["id"]))
	update.message.reply_text("/bidhelp <BID_SEQUENCE>: replace <BID_SEQUENCE> with, well, bidding sequence in the following format (e.g.): 1H 2C 2D\n\n\
	/openings: learn more about openings\n\n\
	!!BETA function!! /bidhelper <BID_SEQUENCE>: initiate chat bot. If you used the bot before, you can return to your last sequence by not inputting a new bid_seq. To start from opening, use /bidhelper open")
	
#/version. See version history after main()
def version_text(bot, update):
	logger.info("User {} used command: /ver".format(update.effective_user["id"]))
	update.message.reply_text("---Version 0.3 (25/8/19) Features---\nBidding Library:\n  1NT\n  1S with fit\n  1H - 2C and higher responses\n\nCommands:\n /start\n /hi\n /help\n /ver\n /bidhelp\n /bidhelper (base, memory and open)\n /openings")
		
#Handler listener
def main():
	logger.info("Starting bot...")
	updater = Updater(TOKEN)
	dp = updater.dispatcher
	#depreciated: examples of RegexHandler(<Regex>, <command>)
	#conv_handler = ConversationHandler(entry_points = [CommandHandler("openings", openings)], states = {OPENING: [RegexHandler('^1C$', open_1c), RegexHandler('^1D$',open_1d), RegexHandler('^1H$', open_1h), RegexHandler('^1S$', open_1s)]}, fallbacks = [CommandHandler('cancel', cancel)])
	#conv_handler2 = ConversationHandler(entry_points = [CommandHandler("openings", openings)], states = {OPENING: [RegexHandler('^1C|1D|1H|1S$', open)]}, fallbacks = [CommandHandler('cancel', cancel)])
	openings_conv_handler3 = ConversationHandler(entry_points = [CommandHandler("openings", openings)], states = {OPENING: [MessageHandler(Filters.text, openings_part2)]}, fallbacks = [CommandHandler('cancel', cancel)])
	bidhelper_conv_handler = ConversationHandler(entry_points = [CommandHandler("bidhelper", bidhelper, pass_args = True)], states = {BIDHELPER: [MessageHandler(Filters.text, bidhelper_continue)]}, fallbacks = [CommandHandler('cancel',cancel)])
	dp.add_handler(CommandHandler('help',user_help))
	dp.add_handler(CommandHandler('start', start))
	dp.add_handler(CommandHandler('hi',hi))
	dp.add_handler(CommandHandler('bidhelp', bid_library, pass_args = True ))
	dp.add_handler(openings_conv_handler3)
	dp.add_handler(bidhelper_conv_handler)
	dp.add_handler(CommandHandler('ver',version_text))
	run(updater)
	updater.idle()

if __name__ == '__main__':
	main()
	
"""Version History
v0.1: /bidhelp 1S fit bids
v0.2: /bidhelp 1H 2C
v0.3: /bidhelper
"""