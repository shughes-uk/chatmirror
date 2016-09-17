#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import logging
import os
import sys
import time

from yaml import load

from twitchchat import twitch_chat
from youtubechat import YoutubeLiveChat, get_live_chat_id_for_stream_now

logger = logging.getLogger('charmirror')


def get_config():
    logger.info('Loading configuration from config.txt')
    config = None
    if os.path.isfile('config.txt'):
        config = load(open('config.txt', 'r'))
        required_settings = ['twitch_username', 'twitch_oauth', 'twitch_channel', 'client_id']
        for setting in required_settings:
            if setting not in config:
                msg = '{} not present in config.txt, put it there! check config_example.txt!'.format(setting)
                logger.critical(msg)
                sys.exit()
    else:
        logger.critical('config.txt doesn\'t exist, please create it, refer to config_example.txt for reference')
        sys.exit()
    logger.info('Configuration loaded')
    return config


class Chatmirror(object):

    def __init__(self, config):
        self.config = config
        self.tirc = twitch_chat(config['twitch_username'], config['twitch_oauth'], [config['twitch_channel']],
                                config['client_id'])
        self.tirc.subscribeChatMessage(self.new_twitchmessage)
        self.chatId = get_live_chat_id_for_stream_now('oauth_creds')
        self.ytchat = YoutubeLiveChat('oauth_creds', [self.chatId])
        self.ytchat.subscribe_chat_message(self.new_ytmessage)

    def start(self):
        self.ytchat.start()
        self.tirc.start()

    def join(self):
        self.tirc.join()

    def stop(self):
        self.tirc.stop()
        self.ytchat.stop()

    def new_ytmessage(self, msgs, chat_id):
        for msg in msgs:
            to_send = u"{0} : {1}".format(msg.author.display_name, msg.message_text)
            logger.debug(to_send)
            self.tirc.send_message(config['twitch_channel'], to_send)

    def new_twitchmessage(self, msg):
        uname = msg['display-name'] or msg['username']
        to_send = "{0} : {1}".format(uname, msg['message'])
        logger.debug(to_send)
        self.ytchat.send_message(to_send, self.chatId)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-d',
        '--debug',
        help="Enable debugging statements",
        action="store_const",
        dest="loglevel",
        const=logging.DEBUG,
        default=logging.INFO,)
    args = parser.parse_args()

    logging.basicConfig(
        level=args.loglevel, format='%(asctime)s.%(msecs)d %(levelname)s %(name)s : %(message)s', datefmt='%H:%M:%S')
    config = get_config()
    mirror = Chatmirror(config)
    mirror.start()
    try:
        while True:
            time.sleep(0.2)
    finally:
        mirror.stop()
