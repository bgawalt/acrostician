import unittest
import os
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

        d4 = family.add_ngram(ng4, count=7)
        self.assertDictEqual(family.ngrams,
                             {"always be closing": 8, "already been chewed": 1, "alcoholic beverage control": 1})
        self.assertEqual(d4, 1)
        self.assertEqual(family.size(), 3)

        with self.assertRaises(ValueError):
            family.add_ngram(ng5)
        with self.assertRaises(ValueError):
            family.add_ngram(ng6)

    def test_parse_file_line(self):
        ng, c = ngram_lookup.InitialNGrams.parse_file_line("another bad creation\t45\n")
        self.assertEqual(ng, "another bad creation")
        self.assertEqual(c, 45)

        with self.assertRaises(ValueError):
            ngram_lookup.InitialNGrams.parse_file_line("another\tbad creation\t45\n")
        with self.assertRaises(ValueError):
            ngram_lookup.InitialNGrams.parse_file_line("another bad creation 45")
        with self.assertRaises(ValueError):
            ngram_lookup.InitialNGrams.parse_file_line("another bad creation\tforty five\n")

    def test_create_file_line(self):
        line1 = ngram_lookup.InitialNGrams.create_file_line("andrew bullwinkle carnegie", 45)
        self.assertEqual(line1, "andrew bullwinkle carnegie\t45\n")

        line2 = ngram_lookup.InitialNGrams.create_file_line("andr\n ew bull   winkle carn\tegie", 46)
        # TODO This is a bad outcome!! We should scrub whitespace from the tokens at time of NGram creation!!
        self.assertEqual(line2, "andr ew bull winkle carn egie\t46\n")

    def test_parse_family_filename(self):
        path1 = "/tmp/3_abc.txt"
        path2 = "/tmp/foo/5_defgh.txt"
        path3 = "/tmp/foo/bar/1_x.txt"
        path4 = "4_lmno.txt"
        self.assertEqual(ngram_lookup.InitialNGrams.parse_family_filename(path1), ("abc", "/tmp"))
        self.assertEqual(ngram_lookup.InitialNGrams.parse_family_filename(path2), ("defgh", "/tmp/foo"))
        self.assertEqual(ngram_lookup.InitialNGrams.parse_family_filename(path3), ("x", "/tmp/foo/bar"))
        self.assertEqual(ngram_lookup.InitialNGrams.parse_family_filename(path4), ("lmno", ""))
        with self.assertRaises(ValueError):
            ngram_lookup.InitialNGrams.parse_family_filename("baz/some_file.txt")
        with self.assertRaises(ValueError):
            ngram_lookup.InitialNGrams.parse_family_filename("hup/5_ab3de.txt")
        with self.assertRaises(ValueError):
            ngram_lookup.InitialNGrams.parse_family_filename("noooo/please/6_abcdEf.txt")
        with self.assertRaises(ValueError):
            ngram_lookup.InitialNGrams.parse_family_filename("this/is/boring/6_abcd.txt")

    def test_file_save_and_load(self):
        family1 = ngram_lookup.InitialNGrams("abc")
        try:
            os.remove(family1.filename("/tmp"))
        except OSError, oe:
            if oe.errno == 2:
                pass
            else:
                raise oe
        ng11 = ngram_lookup.NGram(["always", "be", "closing"])
        ng12 = ngram_lookup.NGram(["already", "been", "chewed"])
        ng13 = ngram_lookup.NGram(["alcoholic", "beverage", "control"])
        ng14 = ngram_lookup.NGram(["alabama", "bean", "chowder"])
        k = 0
        for ng in (ng11, ng12, ng13, ng14):
            for _ in xrange(k+1):
                family1.add_ngram(ng)
            k += 1
        self.assertEqual(family1.size(), 4)
        family1.append_to_file_and_reset("/tmp")
        self.assertEqual(family1.size(), 0)
        self.assertFalse(os.path.isfile("/tmp/TMP_abc.txt"))
        self.assertTrue(os.path.isfile("/tmp/3_abc.txt"))

        family2 = ngram_lookup.InitialNGrams("def")
        try:
            os.remove(family2.filename("/tmp"))
        except OSError, oe:
            if oe.errno == 2:
                pass
            else:
                raise oe.message
        ng21 = ngram_lookup.NGram(["don't", "ever", "forget"])
        ng22 = ngram_lookup.NGram(["ducks", "eat", "funny"])
        ng23 = ngram_lookup.NGram(["didn't", "exactly", "follow"])
        ng24 = ngram_lookup.NGram(["dozen", "egg", "formula"])
        for ng in (ng21, ng22, ng23, ng24):
            for _ in xrange(k+1):
                family2.add_ngram(ng)
            k += 1
        self.assertEqual(family2.size(), 4)
        family2.append_to_file_and_reset("/tmp")
        self.assertEqual(family2.size(), 0)
        self.assertFalse(os.path.isfile("/tmp/TMP_def.txt"))
        self.assertTrue(os.path.isfile("/tmp/3_def.txt"))

        ng15 = ngram_lookup.NGram(["angry", "birds", "champion"])
        family1.add_ngram(ng15, 2)
        family1.add_ngram(ng11, 1)
        self.assertEqual(family1.size(), 2)
        family1.append_to_file_and_reset("/tmp")
        self.assertEqual(family1.size(), 0)

        family3 = ngram_lookup.InitialNGrams.from_file(family1.filename("/tmp"))
        self.assertDictEqual(family3.ngrams,
                             {"always be closing": 2, "already been chewed": 2, "alcoholic beverage control": 3,
                              "alabama bean chowder": 4, "angry birds champion": 2})

        os.remove(family1.filename("/tmp"))
        os.remove(family2.filename("/tmp"))









if __name__ == "__main__":
    unittest.main()