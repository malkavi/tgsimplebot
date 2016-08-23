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

from db_manager import ChatIdEntry, Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

def main(argv):
    tgtext = None
    tgphoto = None
    tgdoc = None
    tgconfig = 'settings'
    try:
        opts, args = getopt.getopt(argv,"hc:t:p:d:",["config=","text=","photo=","document="])
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
        elif opt in ("-d", "--document"):
             tgdoc = arg

    config = ConfigObj(tgconfig)
    
    #prepare db
    engine = create_engine('sqlite:///' + tgconfig + '.db')
    Base.metadata.create_all(engine)
    Base.metadata.bind = engine
    Session = sessionmaker(bind=engine)
    session = Session()
    
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
    chat_ids = _get_chat_ids_n_update_db(bot, session, usernames, fullnames, groups)
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
                
        if tgdoc:
            local_doc_path = tgdoc
            with open(local_doc_path, 'rb') as doc:
                bot.sendDocument(chat_id=chat_id, document=doc)
                                        
    session.commit()
    session.close()


def _get_bot_updates(bot):
    """get updated chats info from telegram
    :type bot: telegram.Bot
    :rtype: (dict[str, telegram.User], dict[(str, str), telegram.User], dict[str, telegram.GroupChat])
    """
    updates = []
    last_upd = 0
    while 1:
            ups = bot.getUpdates(last_upd, limit=100)
            updates.extend(ups)
            if len(ups) < 100:
                break
            last_upd = ups[-1].update_id

    usernames = dict()
    fullnames = dict()
    groups = dict()

    for chat in (x.message.chat for x in updates):
        if chat.type == 'private':
            usernames[chat.username] = chat
            fullnames[(chat.first_name, chat.last_name)] = chat
        elif chat.type in ('group', 'supergroup' or 'channel'):
            groups[chat.title] = chat

    return usernames, fullnames, groups

def _get_new_chat_ids(bot, usernames, fullnames, groups):
    upd_usernames, upd_fullnames, upd_groups = _get_bot_updates(bot)

    len_ = len(usernames)
    for i, username in enumerate(reversed(usernames)):
        chat = upd_usernames.get(username)
        if chat is not None:
            entry = ChatIdEntry(id=chat.id, username=chat.username, firstname=chat.first_name,
                                surname=chat.last_name)
            yield entry
            usernames.pop(len_ - i - 1)

    len_ = len(fullnames)
    for i, fullname in enumerate(reversed(fullnames)):
        chat = upd_fullnames.get(fullname)
        if chat is not None:
            entry = ChatIdEntry(id=chat.id, username=chat.username, firstname=chat.first_name,
                                surname=chat.last_name)
            yield entry
            fullnames.pop(len_ - i - 1)

    len_ = len(groups)
    for i, grp in enumerate(reversed(groups)):
        chat = upd_groups.get(grp)
        if chat is not None:
            entry = ChatIdEntry(id=chat.id, group=chat.title)
            yield entry
            groups.pop(len_ - i - 1)

def _get_cached_chat_ids(session, usernames, fullnames, groups):
    chat_ids = list()
    cached_usernames = dict((x.username, x)
                            for x in session.query(ChatIdEntry).filter(ChatIdEntry.username != None).all())
    cached_fullnames = dict(((x.firstname, x.surname), x)
                            for x in session.query(ChatIdEntry).filter(ChatIdEntry.firstname != None).all())
    cached_groups = dict((x.group, x)
                            for x in session.query(ChatIdEntry).filter(ChatIdEntry.group != None).all())

    len_ = len(usernames)
    for i, username in enumerate(reversed(usernames)):
        item = cached_usernames.get(username)
        if item:
            chat_ids.append(item)
            usernames.pop(len_ - i - 1)

    len_ = len(fullnames)
    for i, fullname in enumerate(reversed(fullnames)):
        item = cached_fullnames.get(fullname)
        if item:
            chat_ids.append(item)
            fullnames.pop(len_ - i - 1)

    len_ = len(groups)
    for i, grp in enumerate(reversed(groups)):
        item = cached_groups.get(grp)
        if item:
            chat_ids.append(item)
            groups.pop(len_ - i - 1)

    return chat_ids

#def _get_chat_ids(bot, usernames, fullnames, groups):
#    chat_ids = list(_get_new_chat_ids(bot, usernames, fullnames, groups))
#
#    return chat_ids

def _get_chat_ids(session, bot, usernames, fullnames, groups):
    chat_ids = list()
    
    chat_ids = _get_cached_chat_ids(session, usernames, fullnames, groups)
              
    if not (usernames or fullnames or groups):
        print 'cached ids only'
        return chat_ids, False
                                 
    new_chat_ids = list(_get_new_chat_ids(bot, usernames, fullnames, groups))
                                       
    chat_ids.extend(new_chat_ids)
    return chat_ids, bool(new_chat_ids)
    
def _get_chat_ids_n_update_db(bot, session, usernames, fullnames, groups):
    chat_ids, has_new_chat_ids = _get_chat_ids(session, bot, usernames, fullnames, groups)
    if has_new_chat_ids:
        _update_db(session, chat_ids)
    return chat_ids

def _update_db(session, chat_ids):
    print 'updating db'
    session.add_all(chat_ids)

if __name__ == '__main__':
    main(sys.argv[1:])
