import tweepy, sys, sqlite3, random

from tweepy.streaming import StreamListener
from tweepy import Stream
from tweepy.api import API

def getConfig(configFile):
    """
    :param configFile: Path to configuration file containing Twitter API keys
    :return: Dictionary of configuration variables, including Twitter API keys
    """
    with open(configFile, 'r') as config:
        splitLines = [line.split("=") for line in config.xreadlines()]
        out = {}
        for s in splitLines:
            if len(s) == 2:
                out[s[0].strip()] = s[1].strip()
        return out

class StoreStatusTextListener(StreamListener):
    """ Records the text of streamed-in statuses in a list field """
    
    def __init__(self, api, limit= 5):
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
        for b in xrange(a+1,len(s)+1):
            yield s[a:b]

def firstChar(word):
    if len(word) == 0:
        return ''
    if len(word) == 1:
        return word
    if word[0] == "#":
        return word[1]
    return word[0]

def getNgrams(text):
    cleanWords = [w.strip("""./?<>!,:;-+&*"'""") for w
                          in text.lower().split()]
    cleanNonemptyWords = [cw for cw in cleanWords if len(cw) > 0]
    return subseqs(cleanNonemptyWords)

def initials(words):
    firstChars = [firstChar(word).lower() for word in words if len(word) > 0]
    return "".join(firstChars)

def scrapeTwitter(acrostic, api, dbpath):
    
    subAcros = set(subseqs(acrostic))
    acrosN = len(acrostic)
    
    l = StoreStatusTextListener(api, limit = 10000)
    try:
        stream = Stream(auth, l, timeout=5.0)
        stream.filter(track =  ("a","of","the","it","i"), languages=("en",))
    except:
        print "Problem after", len(l.texts)
  
    print len(l.texts), "tweets scraped"
    with sqlite3.connect(dbpath+"/"+acrostic+".db") as conn:
        cur = conn.cursor()

        for n in xrange(1, acrosN+1):
            s = str(n)
            cur.execute("create table if not exists GRAM_" + s +
                " (Term text, Initials text, Count integer, Used integer);")
            cur.execute("create unique index if not exists IDX_TERM_GRAM_" + s +
                        " on GRAM_"+s+" (Term);")
            cur.execute("create index if not exists IDX_INIT_GRAM_" + s +
                        " on GRAM_"+s+" (Initials);")
            conn.commit()

        for text in l.texts:
            ngrams = [s for s in getNgrams(text) if initials(s) in subAcros]
            for n in ngrams:
                term = " ".join(n)
                if "http" in term.lower() or acrostic in term.lower():
                    continue
                inits = initials(n)
                cur.execute("select Count from GRAM_" + str(len(n)) +
                            " where Term=:term", {"term": term})
                results = cur.fetchall()
                if len(results) == 0:
                    count = 1
                    cur.execute("insert into GRAM_" + str(len(n)) +
                                " values (?,?,?,1)", (term, inits, count))
                else: 
                    count = 1 + results[0][0]
                    cur.execute("update GRAM_" + str(len(n)) +
                                " set Count=? where Term=?", (count, term))
                conn.commit()
        conn.commit()

def capitalizeTweet(tw):
    spTw = tw.split()
    out = []
    for w in spTw:
        if w[0] == "#":
            x = "#"+w[1:].capitalize()
        else:
            x = w.capitalize()
        out.append(x)
    return "\n".join(out)

def scoreTup(t):
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
    raw = len(term)*(float(pop)/(10*used))**(2*len(inits))
    if "#" in term:
        return 10*raw
    else:
        return raw

def postTweet(target, api, dbpath, testOnly = False):
    targetLen = len(target)
    with sqlite3.connect(dbpath+"/"+target+".db") as conn:
        cur = conn.cursor()

        tooLong = True
        tries = 100

        while tooLong and tries > 0:
            tweet = ""
            tweetWordCount = len([t for t in tweet.split() if len(t) > 0])
            while tweetWordCount < targetLen:
                desiredInits = target[tweetWordCount:targetLen]

                wordsLeft = targetLen - tweetWordCount
                options = []
                while len(options) < 200 and wordsLeft > 0:
                    cur.execute("select Term, Initials, Count, Used from GRAM_"+
                                str(wordsLeft)+" where Initials=? order by "+
                                "random() limit 200",
                                (desiredInits[:wordsLeft],))
                    for tup in cur.fetchall():
                        if target not in tup[0]:
                            options.append(tup)
                    wordsLeft = wordsLeft - 1                
                if len(options) == 0:
                    print "DAMMIT",tweet,desiredInits
                    raise RuntimeError
                totalCount = int(sum([scoreTup(o) for o in options]))

                r = random.randint(1, totalCount)
                i = 0
                while i < len(options):
                    r = r - scoreTup(options[i])
                    if r <= 0:
                        break
                    i = i + 1
                if r > 0:
                    newWord = options[-1][0]
                else:
                    newWord = options[i][0]
                tweet = tweet + "\n"+newWord
                tweetWordCount = len([t for t in tweet.split() if len(t) > 0])

            capTweet = capitalizeTweet(tweet)
            if len(capTweet) < 141:
                # Post the poem
                if testOnly:
                    print capTweet
                else:
                    api.update_status(capTweet)

                #Update the used counts for this poem's ngrams
                selectedNgrams = getNgrams(tweet)
                for ngram in selectedNgrams:
                    n = len(ngram)
                    inits = initials(ngram)
                    term = " ".join(ngram)
                    cur.execute("select Used from GRAM_"+str(n)+
                        " where Term = ?", (term,))
                    rows = cur.fetchall()
                    for tup in rows: # Should just be a single row...
                        usedCount = tup[0]
                        cur.execute("update GRAM_"+str(n)+" set Used = ? "+
                            "where Term = ?", (usedCount+1, term))
                    if len(rows) == 0:
                        cur.execute("insert into GRAM_" + str(n) +
                                " values (?,?,1,1)", (term, inits))
                    if testOnly:
                        print "usage update for", term, inits
                    conn.commit()

            tooLong = len(capTweet) > 140
            tries = tries - 1

def usage():
    print "Usage: python acrosticBot.py [config file] [acrostic word] [read or write]"

if __name__ == "__main__":
    if not (len(sys.argv) == 4 or len(sys.argv) == 5):
        usage()
        sys.exit(0)

    config = getConfig(sys.argv[1])
    ckey = config["CONSUMER_KEY"]
    csec = config["CONSUMER_SECRET"]
    akey = config["ACCESS_KEY"]
    asec = config["ACCESS_SECRET"]
    worddb = config["NGRAM_DB_PATH"]

    auth = tweepy.OAuthHandler(ckey, csec)
    auth.set_access_token(akey, asec)
    configapi = tweepy.API(auth)
    testmode = "test" in sys.argv

    if random.randint(1,69) == 69:
        targetWord = "benghazi"
    else:
        targetWord = sys.argv[2].lower().split()[0]

    if sys.argv[3] == 'read':
        scrapeTwitter(targetWord, configapi, worddb)
    elif sys.argv[3] == 'write':
        postTweet(targetWord, configapi, worddb, testmode)
    elif sys.argv[3] == 'both':
        scrapeTwitter(targetWord, configapi, worddb)
        postTweet(targetWord, configapi, worddb, testmode)
    else:
        usage()


