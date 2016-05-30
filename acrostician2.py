import random
import sqlite3
import sys
import time
import tweepy
from tweepy.streaming import StreamListener
from tweepy import Stream
from tweepy.api import API


def get_config(config_file):
    """
    :param config_file: Path to configuration file containing Twitter API keys
    :return: Dictionary of configuration variables, including Twitter API keys
    """
    with open(config_file, 'r') as config_stream:
        split_lines = [line.split("=") for line in config_stream.xreadlines()]
        out = {}
        for s in split_lines:
            if len(s) == 2:
                out[s[0].strip()] = s[1].strip()
    return out


def get_api(config):
    """
    :param config:  Dictionary of configuration variables, including Twitter API keys
    :return: Tweepy API object
    """
    ckey = config["CONSUMER_KEY"]
    csec = config["CONSUMER_SECRET"]
    akey = config["ACCESS_KEY"]
    asec = config["ACCESS_SECRET"]

    auth = tweepy.OAuthHandler(ckey, csec)
    auth.set_access_token(akey, asec)
    return tweepy.API(auth)