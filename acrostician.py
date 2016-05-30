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


def get_target_follower(api):
    best = 1.1
    target_id = -1
    id_gen = tweepy.Cursor(api.followers_ids, screen_name="Acrostician").pages()
    for id_page in id_gen:
        for id_num in id_page:
            r = random.random()
            if r < best:
                best = r
            target_id = id_num
        time.sleep(2)
    if target_id > 0:
        return api.get_user(target_id).screen_name
    raise ValueError("Couldn't select a follower")


class StoreStatusTextListener(StreamListener):
    """ Records the text of streamed-in statuses in a list field """

    def __init__(self, api, limit=5):
        self.texts = set()
        self.myLimit = limit
        self.api = api or API()

    def on_status(self, status):
        self.texts.add(status.text)
        return len(self.texts) < self.myLimit

    def on_error(self, status):
        print "error", status


def subseqs(s):
    for a in xrange(len(s)):
        yield s[a:]


def first_char(word):
    if len(word) == 0:
        return ''
    if len(word) == 1:
        return word
    if word[0] == "#":
        return word[1]
    return word[0]


def get_ngrams(text):
    clean_words = [w.strip("""./?<>!,:;-+&*"'""") for w
                   in text.lower().split()]
    clean_nonempty_words = [cw for cw in clean_words if len(cw) > 0]
    return subseqs(clean_nonempty_words)


def initials(words):
    first_chars = [first_char(word).lower() for word in words if len(word) > 0]
    return "".join(first_chars)


def scrape_twitter(acrostic, api, dbpath):
    sub_acros = set(subseqs(acrostic))
    acros_n = len(acrostic)

    l = StoreStatusTextListener(api, limit=10000)
    try:
        stream = Stream(auth, l, timeout=5.0)
        stream.filter(track=("a", "of", "the", "it", "i"), languages=("en",))
    except:
        print "Problem after", len(l.texts)

    print len(l.texts), "tweets scraped"
    with sqlite3.connect(dbpath + "/acrostician.db") as conn:
        cur = conn.cursor()

        for n in xrange(1, acros_n + 1):
            s = str(n)
            cur.execute("create table if not exists GRAM_" + s +
                        " (Term text, Initials text, Count integer, "
                        "Used integer);")
            cur.execute("create unique index if not exists IDX_TERM_GRAM_" + s +
                        " on GRAM_" + s + " (Term);")
            cur.execute("create index if not exists IDX_INIT_GRAM_" + s +
                        " on GRAM_" + s + " (Initials);")
            conn.commit()

        ngram_counts = {}
        for text in l.texts:
            ngrams = [s for s in get_ngrams(text) if initials(s) in sub_acros]
            for n in ngrams:
                term = " ".join(n)
                if "http" in term.lower() or acrostic in term.lower():
                    continue
                ngram_counts[term] = ngram_counts.get(term, 0) + 1
        i = 1
        for term in ngram_counts:
            n = term.split()
            inits = initials(n)
            cur.execute("select Count from GRAM_" + str(len(n)) +
                        " where Term=:term", {"term": term})
            results = cur.fetchall()
            if len(results) == 0:
                count = ngram_counts[term]
                cur.execute("insert into GRAM_" + str(len(n)) +
                            " values (?,?,?,1)", (term, inits, count))
            else:
                count = ngram_counts[term] + results[0][0]
                cur.execute("update GRAM_" + str(len(n)) +
                            " set Count=? where Term=?", (count, term))
            if i % 100 == 0:
                conn.commit()
            i += 1
            conn.commit()


def capitalize_tweet(tw):
    sp_tw = tw.split()
    out = []
    for w in sp_tw:
        if w[0] == "#":
            x = "#" + w[1:].capitalize()
        else:
            x = w.capitalize()
        out.append(x)
    return "\n".join(out)


def score_tup(t):
    """
    Score an ngram tuple returned from a database ngram table. A higher scoring
    term is more deserving of inclusion in the resulting acrostic
    :param t: (Term string, initials string, Corpus count, Used count)
    :return: Fitness score for this term
    """
    term = t[0]
    inits = t[1]
    pop = t[2]
    used = t[3]
    raw = (len(term) * pop / (10 * used * used * used)) ** (len(inits))
    if "#" in term:
        score = 2 * raw
    else:
        score = raw
    return max(score, 1)


def post_tweet(target, api, dbpath, test_only=False):
    target_len = len(target)
    with sqlite3.connect(dbpath + "/acrostician.db") as conn:

        print target
        cur = conn.cursor()

        cur.execute("create table if not exists TWEETED (Tweet text)")
        cur.execute("create unique index if not exists IDX_TEXT "
                    "on TWEETED(Tweet)")

        not_yet_posted = True
        tries = 100

        while not_yet_posted and tries > 0:
            tweet = ""
            tweet_word_count = len([t for t in tweet.split() if len(t) > 0])
            while tweet_word_count < target_len:
                desired_inits = target[tweet_word_count:target_len]

                words_left = target_len - tweet_word_count
                options = []
                while len(options) < 200 and words_left > 0:
                    cur.execute("select Term, Initials, Count, Used "
                                "from GRAM_" + str(words_left) +
                                " where Initials=? order by " +
                                "random() limit 200",
                                (desired_inits[:words_left],))
                for tup in cur.fetchall():
                    if target not in tup[0]:
                        options.append(tup)
                        words_left -= 1
                if len(options) == 0:
                    print "No options left", tweet, desired_inits
                    raise RuntimeError
                total_count = int(sum([score_tup(o) for o in options]))

            r = random.randint(1, total_count)
            i = 0
            while i < len(options):
                r = r - score_tup(options[i])
                if r <= 0:
                    break
                i += 1
                if r > 0:
                    new_word = options[-1][0]
                else:
                    new_word = options[i][0]
                tweet = tweet + "\n" + new_word
                tweet_word_count = len([t for t in tweet.split() if len(t) > 0])

            cap_tweet = capitalize_tweet(tweet)
            length_check = len(cap_tweet) < 141  # Check the length's okay

            dupe_check = True  # Assume it's not a dupe...
            for _ in cur.execute("select Tweet from TWEETED where Tweet = ?",
                                 (cap_tweet.lower(),)):
                print "Duplicate... trying again"
                dupe_check = False  # But if it is, don't post it
                break

            if length_check and dupe_check:
                # Post the poem
                try:
                    print cap_tweet
                except:
                    print "[Trouble printing tweet]"
                api.update_status(cap_tweet)
                not_yet_posted = False

                # Update the used counts for this poem's ngrams
                selected_ngrams = get_ngrams(tweet)
                for ngram in selected_ngrams:
                    n = len(ngram)
                    inits = initials(ngram)
                    term = " ".join(ngram)
                    cur.execute("select Used from GRAM_" + str(n) +
                                " where Term = ?", (term,))
                    rows = cur.fetchall()
                    for tup in rows:  # Should just be a single row...
                        used_count = tup[0]
                        cur.execute("update GRAM_" + str(n) + " set Used = ? " +
                                    "where Term = ?", (used_count + 1, term))
                        if len(rows) == 0:
                            cur.execute("insert into GRAM_" + str(n) +
                                        " values (?,?,1,1)", (term, inits))
                    if test_only:
                        print "usage update for", term, inits
                    # Add the tweet to our list of already-posted
                    cur.execute("insert into TWEETED values (?)",
                                (cap_tweet.lower(),))
                    conn.commit()

            tries -= 1
            print tries, "tries left"


def usage():
  print ("Usage: python acrosticBot.py [config file] "
         "[acrostic word] [read or write]")


def main():
    if not (len(sys.argv) == 4 or len(sys.argv) == 5):
        usage()
        sys.exit(0)

    config = get_config(sys.argv[1])
    ckey = config["CONSUMER_KEY"]
    csec = config["CONSUMER_SECRET"]
    akey = config["ACCESS_KEY"]
    asec = config["ACCESS_SECRET"]
    worddb = config["NGRAM_DB_PATH"]

    auth = tweepy.OAuthHandler(ckey, csec)
    auth.set_access_token(akey, asec)
    configapi = tweepy.API(auth)
    testmode = "test" in sys.argv

    if random.randint(1, 69) == 69:
        target_word = "benghazi"
    else:
        target_word = sys.argv[2].lower().split()[0]

    if sys.argv[3] == 'read':
        scrape_twitter(target_word, configapi, worddb)
    elif sys.argv[3] == 'write':
        post_tweet(target_word, configapi, worddb, testmode)
    elif sys.argv[3] == 'both':
        scrape_twitter(target_word, configapi, worddb)
        post_tweet(target_word, configapi, worddb, testmode)
    else:
        usage()


if __name__ == "__main__":
    # main()
    if not (len(sys.argv) == 4 or len(sys.argv) == 5):
        usage()
        sys.exit(0)

    config = get_config(sys.argv[1])
    ckey = config["CONSUMER_KEY"]
    csec = config["CONSUMER_SECRET"]
    akey = config["ACCESS_KEY"]
    asec = config["ACCESS_SECRET"]

    auth = tweepy.OAuthHandler(ckey, csec)
    auth.set_access_token(akey, asec)
    configapi = tweepy.API(auth)

    print get_target_follower(configapi)
