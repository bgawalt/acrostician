import unittest
import ngram_lookup

class TestNgram(unittest.TestCase):

    def test_init(self):
        ngram = ngram_lookup.NGram(["don't", "look:", "'back"])
        self.assertEqual("don't look: 'back", ngram.ngram)
        self.assertEqual("dl'", ngram.initials)

    def test_clean_term(self):
        test_cases = [
            ("----yes", "yes"),
            ("No...", "No"),
            ("~^$maYbe!?--", "maYbe")
        ]
        for test_input, expected in test_cases:
            self.assertEqual(expected, ngram_lookup.NGram.clean_term(test_input))

    def test_parse_sentence_to_ngrams(self):
        ngrams = ngram_lookup.NGram.parse_sentence_to_ngrams("Don't look: 'back !!")
        self.assertItemsEqual([n.ngram for n in ngrams],
                              ["don't", "don't look", "don't look back",
                               "look", "look back", "back"])
        self.assertItemsEqual([n.initials for n in ngrams],
                              ["d", "dl", "dlb", "l", "lb", "b"])




if __name__ == "__main__":
    unittest.main()