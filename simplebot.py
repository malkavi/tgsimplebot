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
    tgconfig = 'settings'
    try:
        opts, args = getopt.getopt(argv,"hc:t:p:",["config=","text=","photo="])
    except getopt.GetoptError:
        print 'test.py -t <inputtext> -p <photopath>'
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
             print 'test.py -t <inputtext> -p <photopath>'
             sys.exit()
        elif opt in ("-c", "--config"):
             tgconfig = arg
        elif opt in ("-t", "--text"):
             tgtext = arg
        elif opt in ("-p", "--photo"):
             tgphoto = arg

    config = ConfigObj(tgconfig)
    # Read variables
    token = config['token']
    user = config['user']
	
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    bot = telegram.Bot(token)  # Telegram Bot Authorization Token
    
    print bot.getMe()

    usernames = []
    fullnames = []
    groups = []
    if isinstance(user, list):
        usernames = user
    else:
        usernames.append(user)

    print usernames
    chat_ids = _get_chat_ids(bot, usernames, fullnames, groups)
    updates = bot.getUpdates()
    print [u.message.text for u in updates]

    for chat_id in (x.id for x in chat_ids):
#    chat_id = bot.getUpdates()[0].message.chat_id
        if tgtext:
            bot.sendMessage(chat_id=chat_id, text=tgtext)
        
        if tgphoto:
            local_photo_path = tgphoto
            with open(local_photo_path, 'rb') as photo:
                bot.sendPhoto(chat_id=chat_id, photo=photo)


def _get_bot_updates(bot):
    """get updated chats info from telegram
    :type bot: telegram.Bot
    :rtype: (dict[str, telegram.User], dict[(str, str), telegram.User], dict[str, telegram.GroupChat])
    """
    updates = bot.getUpdates()
    usernames = dict()
    fullnames = dict()
    groups = dict()

    for chat in (x.message.chat for x in updates):
        if isinstance(chat, telegram.User):
            usernames[chat.username] = chat
            fullnames[(chat.first_name, chat.last_name)] = chat
        elif isinstance(chat, telegram.GroupChat):
            groups[chat.title] = chat

    return usernames, fullnames, groups

def _get_new_chat_ids(bot, usernames, fullnames, groups):
    upd_usernames, upd_fullnames, upd_groups = _get_bot_updates(bot)

    len_ = len(usernames)
    for i, username in enumerate(reversed(usernames)):
        chat = upd_usernames.get(username)
        if chat is not None:
            yield chat
            usernames.pop(len_ - i - 1)

    len_ = len(fullnames)
    for i, fullname in enumerate(reversed(fullnames)):
        chat = upd_fullnames.get(fullname)
        if chat is not None:
            yield chat
            fullnames.pop(len_ - i - 1)

    len_ = len(groups)
    for i, grp in enumerate(reversed(groups)):
        chat = upd_groups.get(grp)
        if chat is not None:
            yield chat
            groups.pop(len_ - i - 1)

def _get_chat_ids(bot, usernames, fullnames, groups):
    chat_ids = list(_get_new_chat_ids(bot, usernames, fullnames, groups))

    return chat_ids

if __name__ == '__main__':
    main(sys.argv[1:])
