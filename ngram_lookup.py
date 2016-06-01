"""
Let's store a map from initials to n-grams: "LOL" -> {"laugh out loud", "lots of love", "Lucifer's oily loins", etc.}
We'll scan through phrase-blocks of text, and break them into n-grams up to some predefined limit, say, 5.
By phrase-block, I mean anything between punctuation. "By phrase-block", and "I mean... punctuation" would be the two
blocks from that previous sentence. Strip away leading and trailing punctuation. Dump blocks with invalid text.
If we tokenize by whitespace-plus-dashes, we may be left with some weird stuff, like numerals or $ or # or who knows.
Keep an in-memory map, then, when it gets too big, save all the ngram counts to file and proceed with a blank map.
"""

import re
import os

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
        self.initials = "".join(t[0] for t in terms)

    @staticmethod
    def clean_term(term):
        return re.sub("(^[^a-zA-Z]+)|([^a-zA-Z]+$)", "", term)

    @staticmethod
    def parse_sentence_to_ngrams(text):
        clean_terms = [NGram.clean_term(t) for t in text.lower().split()]
        clean_nonempty = [c for c in clean_terms if len(c) > 0]
        n = len(clean_nonempty)
        ngrams = []
        for a in xrange(n):
            for b in xrange(a+1, min([n+1, a + _NGRAM_LIMIT + 1])):
                ngrams.append(NGram([c for c in clean_nonempty[a:b]]))
        return ngrams

    @staticmethod
    def parse_sentence_suffix_to_ngrams(text):
        clean_terms = [NGram.clean_term(t) for t in text.lower().split()[-1*_NGRAM_LIMIT:]]
        clean_nonempty = [c for c in clean_terms if len(c) > 0]
        n = len(clean_nonempty)
        ngrams = []
        for a in xrange(n):
            ngrams.append(NGram(clean_nonempty[a:]))
        return ngrams


class InitialNGrams(object):
    """
    A family of n-grams who all share the same initials and the number of times each ngram has been seen.
    Comes with a specific file format for serializing a family to disk: `ngram [tab] count [end of line]`.
    """
    def __init__(self, initials):
        if len(initials) > _NGRAM_LIMIT:
            raise ValueError("The length of initials '%s' exceeds ngram limit of %d" % (initials, _NGRAM_LIMIT))
        self.initials = initials
        self.ngrams = {}

    def add_ngram(self, ngram, count=1):
        """
        :param ngram: an NGram object whose initials match
        :param count: Number of times ngram seen
        :return: 1 if ngram is new to this collection, 0 else
        :raises: Value error if ngram's initials don't match this collection's initials
        """
        if ngram.initials != self.initials:
            raise ValueError("Expected initials '%s', received initials '%s'" % (self.initials, ngram.initials))
        dupe = 1 if ngram.ngram in self.ngrams else 0
        self.ngrams[ngram.ngram] = self.ngrams.get(ngram.ngram, 0) + count
        return dupe

    def size(self):
        return len(self.ngrams)

    @staticmethod
    def parse_file_line(line):
        """
        Turn the lines from a file of this specifics InitialNGrams family format into NGram objects.
        :param line: Line from the file.
        :return: 2-tuple: A string for the ngram (NOT an NGram object), and the count associated with it.
        :raises: ValueError: if there's more than one tab character in `line`
        """
        spline = line.split("\t")
        if len(spline) != 2:
            raise ValueError("Incorrect number of tabs in line '%s'", line.strip())
        ngram = spline[0]
        count = int(spline[1])
        return ngram, count

    @staticmethod
    def create_file_line(ngram, count):
        """
        Turn an NGram and its current frequency count into a line of text suitable for storing in a file.
        Format: ngram string [tab] count [end of line]
        :param ngram: Single ngram string
        :param count:
        :return: String encoding this ngram and its frequency count
        """
        return "%s\t%d\n" % (re.sub("\\s+", " ", ngram), count)

    def filename(self, dir_path):
        return "%s/%d_%s.txt" % (dir_path, len(self.initials), self.initials)

    def append_to_file_and_reset(self, dir_path):
        """
        Store the ngrams in this initial-family to a file. If the file is already populated, increment the file's counts
        with the counts currently stored in this object. The name of the file will be '[X]_[initials].txt`, where
        X is the number of tokens in the ngram, and [initials] is the initials.
        :param dir_path: Path to the directory to find the file.
        """
        infilename = self.filename(dir_path)
        outfilename = "%s/TMP_%s.txt" % (dir_path, self.initials)
        with open(outfilename, 'w') as outfile:
            if os.path.isfile(infilename):
                with open(infilename, 'r') as infile:
                    for line in infile:
                        ngram, existing_count = InitialNGrams.parse_file_line(line)
                        if ngram not in self.ngrams:
                            outfile.write(line)
                        else:
                            new_count = existing_count + self.ngrams.pop(ngram)
                            outfile.write(InitialNGrams.create_file_line(ngram, new_count))
            for ngram, count in self.ngrams.iteritems():
                outfile.write(InitialNGrams.create_file_line(ngram, count))
        os.rename(outfilename, infilename)
        self.ngrams = {}

    @staticmethod
    def parse_family_filename(filename):
        """
        Generate the initials and dirpath from a valid file name.
        :param filename: path/to/file/5_abcde.txt
        :return: initials, dir_path
        """
        dir_path, fname = os.path.split(filename)
        if not re.match("\d+_[a-z]+\.txt", fname):
            raise ValueError("File name format mismatch for %s" % (filename,))
        sfname = fname[:-4].split("_")
        num_inits = int(sfname[0])
        inits = sfname[1]
        if len(inits) != num_inits:
            raise ValueError("Number of initials doesn't match numerals in file name %s" % (filename,))
        return inits, dir_path.rstrip("/")

    @staticmethod
    def from_file(filename):
        initials, dir_path = InitialNGrams.parse_family_filename(filename)
        ing = InitialNGrams(initials)
        with open(filename, 'r') as infile:
            for line in infile:
                ngram_str, count = InitialNGrams.parse_file_line(line)
                ngram = NGram(ngram_str.split())
                ing.add_ngram(ngram, count)
        return ing


class NGramCorpora(object):
    """
    A full collection of the ngrams detected, housed by initials. If too many are being kept in memory, flushes
    them all to files in the given directory.
    """
    def __init__(self, dir_path, max_count):
        self._initials = {}
        self._current_count = 0
        self._total_count = 0
        self._dir_path = dir_path
        self._max_count = max_count

    def add_ngram(self, ngram):
        family = self._initials.get(ngram.initials, InitialNGrams(ngram.initials))
        increase = family.add_ngram(ngram)
        self._initials = family
        self._current_count += increase
        self._total_count += increase
        if self._current_count > self._max_count:
            print "Dumping %d ngrams to file..." % (self._current_count,)
            self.dump_to_file()
            print "... complete. Dumped %d ngrams total." % (self._total_count,)

    def dump_to_file(self):
        for initials in self._initials:
            family = self._initials.pop(initials)
            family.append_to_file_and_reset(self._dir_path)
        self._current_count = 0

    def add_sentence(self, text):
        for ngram in NGram.parse_sentence_to_ngrams(text):
            ing = self._initials.get(ngram.initials, InitialNGrams(ngram.initials))
            ing.add_ngram(ngram)
            self._initials[ing.initials] = ing






