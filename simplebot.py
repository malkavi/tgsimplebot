#!/usr/bin/env python
# encoding: utf-8
#
# Based on Robô Ed Telegram Bot
# Copyright (C) 2015 Leandro Toledo de Souza <leandrotoeldodesouza@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see [http://www.gnu.org/licenses/].

import logging
import telegram
import urllib
from configobj import ConfigObj
import sys, getopt


def main(argv):
    tgtext = None
    tgphoto = None
    try:
        opts, args = getopt.getopt(argv,"ht:p:",["text=","photo="])
    except getopt.GetoptError:
        print 'test.py -t <inputtext> -p <photopath>'
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
             print 'test.py -t <inputtext> -p <photopath>'
             sys.exit()
        elif opt in ("-t", "--text"):
             tgtext = arg
        elif opt in ("-p", "--photo"):
             tgphoto = arg

    config = ConfigObj('settings')
    # Read variables
    token = config['token']
    user = config['user']
	
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    bot = telegram.Bot(token)  # Telegram Bot Authorization Token
    
    print bot.getMe()
    
    updates = bot.getUpdates()
    print [u.message.text for u in updates]
    


#    LAST_UPDATE_ID = bot.getUpdates()[-1].update_id  # Get lastest update
    chat_id = bot.getUpdates()[0].message.chat_id

    if tgtext:
        bot.sendMessage(chat_id=chat_id, text=tgtext)
        
    if tgphoto:
        local_photo_path = tgphoto
        with open(local_photo_path, 'rb') as photo:
            bot.sendPhoto(chat_id=chat_id, photo=photo)

if __name__ == '__main__':
    main(sys.argv[1:])
