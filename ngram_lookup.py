"""
Let's store a map from initials to n-grams: "LOL" -> {"laugh out loud", "lots of love", "Lucifer's oily loins", etc.}
We'll scan through phrase-blocks of text, and break them into n-grams up to some predefined limit, say, 5.
By phrase-block, I mean anything between punctuation. "By phrase-block", and "I mean... punctuation" would be the two
blocks from that previous sentence. Strip away leading and trailing punctuation. Dump blocks with invalid text.
If we tokenize by whitespace-plus-dashes, we may be left with some weird stuff, like numerals or $ or # or who knows.
Keep an in-memory map, then, when it gets too big, save all the ngram counts to file and proceed with a blank map.
"""

import re

_NGRAM_LIMIT = 5


class NGram(object):
    def __init__(self, terms):
        """
        :param terms: List of strings that make up this ngram
        :return: NGram object with .ngram and .iniitals field
        :raises: Value error if terms is longer than length _NGRAM_LIMIT, or if any term is an empty string
        """
        if len(terms) > _NGRAM_LIMIT:
            raise ValueError("Too many terms in list %s" % (str(terms),))
        for t in terms:
            if len(t) == 0:
                raise ValueError("Supplied empty term in list %s" % (str(terms),))
        self.ngram = " ".join(terms)
        self.initials = tuple(t[0] for t in terms)

    @staticmethod
    def clean_term(term):
        return re.sub("(^[^a-z])|([^a-z]$)", "", term)


    @staticmethod
    def parse_sentence_to_ngrams(text):
        sptext = text.lower().split()
        n = len(sptext)
        ngrams = []
        for a in xrange(n):
            for b in xrange(a+1, n):
                ngrams.append(NGram([NGram.clean_term(t) for t in sptext[a:b]]))



class InitialNGrams(object):
    """
    A collection of n-grams and the number of times each has been seen.
    """
    def __init__(self, initials):
        if len(initials) > _NGRAM_LIMIT:
            raise ValueError("The length of initials '%s' exceeds ngram limit of %d" % (initials, _NGRAM_LIMIT))
        self._initials = initials
        self._ngrams = {}

    def add_ngram(self, ngram):
        """
        :param ngram: an NGram object whose initials match
        :return: 1 if ngram is new to this collection, 0 else
        :raises: Value error if ngram's initials don't match this collection's initials
        """
        if ngram.initials != self._initials:
            raise ValueError("Expected initials '%s', received initials '%s'" % (self._initials, ngram.initials))
        dupe = 1 if ngram.ngram in self._ngrams else 0
        self._ngrams[ngram.ngram] = self._ngrams.get(ngram.ngram, 0) + 1
        return dupe

    def size(self):
        return len(self._ngrams)

    @staticmethod
    def parse_file_line(line):
        spline = line.split("\t")
        ngram = spline[0]
        count = int(spline[1])
        return ngram, count

    @staticmethod
    def create_file_line(ngram, count):
        return "%s\t%d\n" % (ngram, count)

    def append_to_file_and_reset(self, dir_path):
        infilename = "%s/%s.txt" % (dir_path, self._initials)
        outfilename = "%s/TMP_%s.txt" % (dir_path, self._initials)
        with open(outfilename, 'w') as outfile:
            with open(infilename, 'r') as infile:
                for line in infile:
                    ngram, existing_count = InitialNGrams.parse_file_line(line)
                    if ngram not in self._ngrams:
                        outfile.write(line)
                    else:
                        new_count = existing_count + self._ngrams.pop(ngram)
                        outfile.write(InitialNGrams.create_file_line(ngram, new_count))
            for ngram, count in self._ngrams.iteritems():
                outfile.write(InitialNGrams.create_file_line(ngram, count))
        self._ngrams = {}


class NGramCorpora(object):
    """
    A full collection of the ngrams detected, housed by initials. If too many are being kept in memory, flushes
    them all to files in the given directory.
    """
    def __init__(self, dir_path, max_count):
        self._initials = {}
        self._total_count = 0
        self._dir_path = dir_path
        self._max_count = max_count

    def add_ngram(self, ngram):
        family = self._initials.get(ngram.initials, InitialNGrams(ngram.initials))
        increase = family.add_ngram(ngram)
        self._initials = family
        self._total_count += increase
        if self._total_count > self._max_count:
            self.dump_to_file()

    def dump_to_file(self):
        for initials in self._initials:
            family = self._initials.pop(initials)
            family.append_to_file_and_reset(self._dir_path)
        self._total_count = 0






