import unittest
import ngram_lookup


class TestNGram(unittest.TestCase):

    def test_init(self):
        ngram = ngram_lookup.NGram(["don't", "look:", "'back"])
        self.assertEqual("don't look: 'back", ngram.ngram)
        self.assertEqual("dl'", ngram.initials)
        with self.assertRaises(ValueError):
            unused_ngram = ngram_lookup.NGram(["a", "b", "c", "d", "e", "f"])
        with self.assertRaises(ValueError):
            unused_ngram = ngram_lookup.NGram(["a", "", "c"])

    def test_clean_term(self):
        test_cases = [
            ("----yes", "yes"),
            ("N..o...", "N..o"),
            ("~^$maYbe!?--", "maYbe"),
            ("reno911", "reno")
        ]
        for test_input, expected in test_cases:
            self.assertEqual(expected, ngram_lookup.NGram.clean_term(test_input))

    def test_parse_short_sentence_to_ngrams(self):
        ngrams = ngram_lookup.NGram.parse_sentence_to_ngrams("Don't look: 'back !!")
        self.assertItemsEqual([n.ngram for n in ngrams],
                              ["don't", "don't look", "don't look back", "look", "look back", "back"])
        self.assertItemsEqual([n.initials for n in ngrams],
                              ["d", "dl", "dlb", "l", "lb", "b"])

    def test_parse_long_sentence_to_ngrams(self):
        ngrams = ngram_lookup.NGram.parse_sentence_to_ngrams("Don't look: 'back !!or youll see my hert braking")
        self.assertItemsEqual([n.ngram for n in ngrams],
                              ["don't", "don't look", "don't look back", "don't look back or",
                               "don't look back or youll", "look", "look back", "look back or",
                               "look back or youll", "look back or youll see", "back", "back or", "back or youll",
                               "back or youll see", "back or youll see my", "or", "or youll", "or youll see",
                               "or youll see my", "or youll see my hert", "youll", "youll see", "youll see my",
                               "youll see my hert", "youll see my hert braking", "see", "see my", "see my hert",
                               "see my hert braking", "my", "my hert", "my hert braking", "hert", "hert braking",
                               "braking"])
        self.assertItemsEqual([n.initials for n in ngrams],
                              ["d", "dl", "dlb", "dlbo", "dlboy", "l", "lb", "lbo", "lboy", "lboys", "b", "bo", "boy",
                               "boys", "boysm", "o", "oy", "oys", "oysm", "oysmh", "y", "ys", "ysm", "ysmh", "ysmhb",
                               "s", "sm", "smh", "smhb", "m", "mh", "mhb", "h", "hb", "b"])

    def test_parse_short_sentence_suffix_to_ngrams(self):
        ngrams = ngram_lookup.NGram.parse_sentence_suffix_to_ngrams("Don't look: 'back !!")
        self.assertItemsEqual([n.ngram for n in ngrams], ["don't look back", "look back", "back"])
        self.assertItemsEqual([n.initials for n in ngrams], ["dlb", "lb", "b"])

    def test_parse_long_sentence_suffix_to_ngrams(self):
        ngrams = ngram_lookup.NGram.parse_sentence_suffix_to_ngrams("Don't look: 'back !!or youll see my hert braking")
        self.assertItemsEqual([n.ngram for n in ngrams],
                              ["youll see my hert braking", "see my hert braking", "my hert braking", "hert braking",
                              "braking"])
        self.assertItemsEqual([n.initials for n in ngrams], ["ysmhb", "smhb", "mhb", "hb", "b"])


class TestInitialNGrams(unittest.TestCase):

    def test_init(self):
        ing = ngram_lookup.InitialNGrams("abc")
        self.assertEqual(ing.size(), 0)
        with self.assertRaises(ValueError):
            unused_ing = ngram_lookup.InitialNGrams("abcdef")

    def test_add_ngram_and_size(self):
        family = ngram_lookup.InitialNGrams("abc")
        self.assertEqual(family.initials, "abc")
        ng1 = ngram_lookup.NGram(["always", "be", "closing"])
        ng2 = ngram_lookup.NGram(["already", "been", "chewed"])
        ng3 = ngram_lookup.NGram(["alcoholic", "beverage", "control"])
        ng4 = ngram_lookup.NGram(["always", "be", "closing"])
        # The bad ones
        ng5 = ngram_lookup.NGram(["a", "mismatched", "ngram"])
        ng6 = ngram_lookup.NGram(["a", "bloody", "close", "mismatch"])

        d1 = family.add_ngram(ng1)
        self.assertDictEqual(family.ngrams, {"always be closing": 1})
        self.assertEqual(d1, 0)
        self.assertEqual(family.size(), 1)

        d2 = family.add_ngram(ng2)
        self.assertDictEqual(family.ngrams,
                             {"always be closing": 1, "already been chewed": 1})
        self.assertEqual(d2, 0)
        self.assertEqual(family.size(), 2)

        d3 =family.add_ngram(ng3)
        self.assertDictEqual(family.ngrams,
                             {"always be closing": 1, "already been chewed": 1, "alcoholic beverage control": 1})
        self.assertEqual(d3, 0)
        self.assertEqual(family.size(), 3)

        d4 = family.add_ngram(ng4)
        self.assertDictEqual(family.ngrams,
                             {"always be closing": 2, "already been chewed": 1, "alcoholic beverage control": 1})
        self.assertEqual(d4, 1)
        self.assertEqual(family.size(), 3)

        with self.assertRaises(ValueError):
            family.add_ngram(ng5)
        with self.assertRaises(ValueError):
            family.add_ngram(ng6)

    def test_parse_file_line(self):
        ng, c = ngram_lookup.InitialNGrams.parse_file_line("another bad creation\t45\n")
        self.assertEqual(ng.ngram, "another bad creation")
        self.assertEqual(ng.initials, "abc")
        self.assertEqual(c, 45)






if __name__ == "__main__":
    unittest.main()