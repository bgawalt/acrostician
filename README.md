# Acrostician

Give it a word and it'll build you an acrostic poem from [n-grams|http://en.wikipedia.org/wiki/N-gram] built from a
vocabulary it scraped off of the Twitter public stream. I, Brian Gawalt, handle a bot, 
[@acrostician](http://twitter.com/acrostician) which is managed by this code. This README is a rundown of the bot's
typical behavior, BUT, there are some easter eggs inside (and more to come), so don't read the code if you'd like
the bot to surprise you!

## Usage

To execute this Python script, from an environment which has access to the [tweepy](http://www.tweepy.org/) library
installed, you'll need to provide three additional arguments:

```
$ python acrosticBot.py [config file] [acrostic word] ['read', 'write', or 'both']
```

If you provide fewer than four arguments (including the actual script name, `acrosticBot.py`), you'll raise a usage
message reiterating the above, and the program will exit. Similarly, if your fourth argument is anything other than
the literal keywords `read`, `write`, or `both`, you'll get the usage message and the program will exit. From here on,
the README is going to describe the third argument, `acrostic word`, as the target word for the program.

## Configuration File

The configuration file is expecting key-value pairs to appear line by line, separated by an `=` symbol. 
There are five mandatory keys:

 1. `CONSUMER_KEY`: The consumer key token for the app with which you'll be reading tweets and posting acrostics
 2. `CONSUMER_SECRET`: The corresponding secret for the above key
 3. `ACCESS_KEY`: The access key corresponding to the account that's going to use the above app for reading and writing
 4. `ACCESS_SECRET`: The corresponding secret for the above key 
 5. `NGRAM_DB_PATH`: Path to the directory in which you'd like the n-gram SQLite3 database file to live.
    
Note that it's expecting these five key strings, verbatim. Regarding the keys and secrets: my cryptography background 
is awful weak, so I'm pretty much just rote parroting what I've learned about setting up
these kinds of authorization handshakes from blogposts like 
[this one from Jeff Miller](http://talkfast.org/2010/05/31/twitter-from-the-command-line-in-python-using-oauth/)
 (thanks, Jeff!).
 
## Reading Tweets

If you include `read` or `both` in the fourth argument position, the program will stream in 10,000 tweets from the 
public stream of English-language tweets. For each tweet, the text of the tweet will be cleaned, converted into a 
collection of n-grams. The n-grams whose initials appear as consecutive letters in the target word will be counted in
the target word's n-gram database. (It considers the "initial" of a hashtag, like `#worldcup`, to be the first letter
after the `#` sign.)

For example, if the target word is **TARGET**, a tweet with the text `GREAT! Tegan and #Rob are here!!!` would increment 
the n-grams, `great`, `tegan`, `and`, `#rob`, `are`, `tegan and`, `and #rob`.
 

## Posting acrostics

Given a target word (let's say of length 6, as with **TARGET**), the program will try and greedily build an acrostic
from the beginning of the target. 
 
Given it's starting at position 0, the start of the target word, it will draw a pool of 200 random n-grams that have
 have initials `t`, `ta`, `tar`, ..., `target`.

It picks them in a biased fashion: it will specifically ask for 200 random n-grams of length 6 (hexagrams matching 
`target`).  Should it only receive 41 back from the database, since it's uncommon to actually read tweets with natural 
TARGET acrostics in them premade, it will ask for 159 random n-grams of length five (quintagrams matching `targe`). It
keeps asking the next-lower table in such a fashion until it has at least 200 candidate n-grams of any length.

There's then a scoring procedure where each candidate n-gram gets mapped to a positive real-number. I plan on frequently
playing around with exactly how this scoring works, but the score's always going to go up for an n-gram that:
 
 * Has been seen more often in the public twitter stream, or
 * has more terms in it, or 
 * has more characters/letters, or 
 * is/includes a hashtage, or
 * has been rarely included in previous acrostic poems.
 
From this pool of 200 scored n-grams, I draw a winning candidate randomly from the pool proportional to its score as a
fraction of the sum of all candidate scores. 

If in this case it picked `tegan and #rob`, it repeats this whole procedure trying now to match **GET**: it asks for
200 `get` trigrams, topping off the pool with `ge` bigrams and `g` unigrams.

This keeps going until a full acrostic poem is made. The constituent n-grams all see their "usage counts" incremented
in the database, to try and provide a signal for avoiding picking the same terms over and over. The poem is formatted
 nicely and tweeted out via the API keys provided in the configuration file.

## Work in progress

In all honesty, the above is more how I WANT the bot to behave than how this code currently instructs it to. For 
instance, the usage count mechanism isn't all there. I'll try and keep putting work in to patch things here and there,
and of course to add further kooky surprise behaviors. Issues and questions encouraged!

Love,
[Brian](http://gawalt.com/brian)
