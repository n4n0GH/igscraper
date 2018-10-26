#!/usr/bin/python
#
# coding: utf-8

# igscraper is a standalone tool to mass download public Instagram
# accounts and save them to your disk for further """research"""

# import some libraries
from __future__ import print_function
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from datetime import datetime
import time
import json
import urllib2
import urlparse
import argparse
import subprocess
import sys
import os
import re

# set classes for colors
class fg:
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    WHITE = '\033[37m'


class bg:
    GREEN = '\033[42m'


class style:
    BLINK = '\33[5m'
    CLINE = '\x1b[2K'
    RESET_ALL = '\033[0m'


# set up notification module
def notify(message):
    subprocess.call(["notify-send", "-i", "document-save",
                    "IG scraper", message])
    return


# set up argparser
parser = argparse.ArgumentParser(description="""
                                 A standalone mass downloader for public
                                 Instagram profiles.\n
                                 Will find all image sources and save 
                                 the images to disk.
                                 """)
parser.add_argument("-u", "--user",
                    help="start a direct download from a provided \
                    username",
                    nargs=1, metavar="(USER)")
parser.add_argument("-d", "--delay",
                    help="set a custom delay for downloads in seconds. \
                    This helps to not get banned by IG. Default is 1.5", 
                    nargs=1, type=int, metavar="(SECONDS)")
args = parser.parse_args()


# set up Jason Parser's K9
# stolded from https://gist.github.com/douglasmiranda/5127251
def k9(key, dictionary):
    for k, v in dictionary.iteritems():
        if k == key:
            yield v
        elif isinstance(v, dict):
            for result in k9(key, v):
                yield result
        elif isinstance(v, list):
            for d in v:
                for result in k9(key, d):
                    yield result


# set up default delay
if args.delay:
    wait = args.delay[0]
else:
    wait = 1.5


# clear screen and set terminal title
if os.name == "nt":
    os.system("cls")
else:
    os.system("clear")
sys.stdout.write("\x1b]2;IG Scraper\x07")


# print ASCII intro, bitches love ASCII intros
print("""\033[32m
 _____ _____                                      
|_   _/ ____|                                     
  | || |  __   ___  ___ _ __ __ _ _ __   ___ _ __ 
  | || | |_ | / __|/ __| '__/ _` | '_ \ / _ \ '__|
 _| || |__| | \__ \ (__| | | (_| | |_) |  __/ |   
|_____\_____| |___/\___|_|  \__,_| .__/ \___|_|   
                                 | |              
Codename T.H.O.T.P.A.T.R.O.L.    |_|          \033[31mv0.1
\033[0m
""")


# set up UA
ua = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) '
      'AppleWebKit/537.11 (KHTML, like Gecko) '
      'Chrome/23.0.1271.64 Safari/537.11'}


# get thot from args or user
if args.user:
    thot = args.user[0].strip('@').rstrip('/')
    print("Scraping from: \n" + fg.GREEN + "> " + style.RESET_ALL 
        + thot)
else:
    thot = raw_input("Input username to scrape: \n" + fg.GREEN +
                    "> " + style.RESET_ALL).strip('@').rstrip('/')

# start counting time
start = datetime.now()


# construct the url
url = "https://instagram.com/" + thot

print(fg.GREEN + "Connecting..." + style.RESET_ALL, end="\r")
sys.stdout.flush()


# scroll down to bottom of page
# to load the complete content
driver = webdriver.PhantomJS()
driver.get(url)
lastHeight = driver.execute_script("return document.body.scrollHeight")

print(fg.GREEN + "Scrolling page..." + style.RESET_ALL, end="\r")
sys.stdout.flush()

while True:
    driver.execute_script("window.scrollTo(0, \
        document.body.scrollHeight);")
    time.sleep(wait)
    newHeight = driver.execute_script("return \
        document.body.scrollHeight")
    if newHeight == lastHeight:
        break
    lastHeight = newHeight

completeContent = driver.page_source


# make some soup, terminate on 404
try:
    soup = BeautifulSoup(completeContent, "html5lib")
except urllib2.URLError:
    print(fg.RED + "Host unreachable, stopping...")
    sys.exit()


# collect offending thots
print(style.CLINE + fg.GREEN + "Generating thot list...", end="\r")
sys.stdout.flush()

thotList = []

for thotLink in soup.select('div.kIKUG > a'):
    thotList.append(url + thotLink['href'])


# set up path names and other variables for downloads
home = os.path.expanduser("~")
fpath = os.path.join(home, "igscraper", thot)
i = e = s = 0


# create directory if necessary
if not os.path.exists(fpath):
    os.makedirs(fpath)
    print(fg.GREEN + "Setting up directory...", end="\r")
    sys.stdout.flush()


# start thot patrol
print(style.CLINE + fg.GREEN + "Grabbing fullsize thotpics...", 
    end="\r")
sys.stdout.flush()

thotGallery = []

for link in thotList:
    time.sleep(wait)
    thotReq = urllib2.urlopen(link).read()
    thotSoup = BeautifulSoup(thotReq, "html5lib")
    content = thotSoup.findAll('script', type="text/javascript", 
        text=re.compile('window._sharedData'))
    # call Jason Parser
    jsonContent = content[0].get_text().replace('window._sharedData = ',
    '')[:-1]
    jasonParser = json.loads(jsonContent)
    thotImage = list(k9('display_url', jasonParser))
    thotGallery.append(thotImage)

for img in thotGallery:
    img = str(img).lstrip('[u\'').rstrip('\']')
    file_name = img.split('/')[-1]
    full_path = os.path.join(fpath, file_name)
    if not os.path.exists(full_path):
        try:
            filedata = urllib2.urlopen(img, timeout=wait)
            i += 1
            print(style.CLINE + fg.GREEN +
                  "Grabbing file... [" + str(i) + "/" +
                  str(len(thotGallery) - s) + "]", end="\r")
            with open(full_path, 'wb') as f:
                f.write(filedata.read())
            sys.stdout.flush()
        except urllib2.HTTPError:
            e += 1
            print(style.CLINE + fg.RED + "HTTP error, skipping... [" +
                  str(e) + "]", end="\r")
        except urllib2.URLError:
            e += 1
            print(style.CLINE + fg.RED +
                  "Timeout or bad URL, skipping... [" + str(e) + "]",
                  end="\r")
    else:
        s += 1
        print(fg.YELLOW + "File already exists, skipping... [" +
              str(s) + "]", end="\r")
        sys.stdout.flush()


print(style.CLINE + fg.GREEN + "Grabbing file...", end="\r")
sys.stdout.flush()


# check passed time and convert to readable string
finish = datetime.now() - start
finish = str(finish.total_seconds())


# print success messages as notification window and in terminal
notify("Downloaded " + str(i - e) + " new files from " + thot +
       " in " + finish + " seconds!")
print(bg.GREEN + fg.BLACK +
      "Downloaded " + str(i - e) + " new files from " + thot +
      " in " + style.BLINK + finish + " seconds!\n" +
      style.RESET_ALL + fg.YELLOW + "Skipped: " + str(s) +
      style.RESET_ALL + " | " + fg.RED + "Errors: " + str(e))
