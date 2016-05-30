import re
import sys

class Wikipedia(object):
    def __init__(self, wiki_filename):
        self._wikifile = open(wiki_filename, 'r')

    @staticmethod
    def resolve_brackets(text):
        n = len(text)
        out = ""
        brack_depth = 0
        brack_result = ""
        a = 0
        while a < n-1:
            pair = text[a:a+2]
            if pair == "[[":
                brack_depth += 1
                brack_result = ""
                a += 2
            elif pair == "]]":
                brack_depth -= 1
                if brack_depth == 0:
                    out += brack_result
                a += 2
            else:
                if brack_depth == 0:
                    out += pair[0]
                else:
                    if pair[0] == "|":
                        brack_result = ""
                    else:
                        brack_result += pair[0]
                a += 1
        return out

    @staticmethod
    def clean_page(text):
        ref_free = re.sub("&lt;ref.*?(/&gt;|&lt;/ref&gt;|\]\]|\}\})", "", text, flags=re.DOTALL)
        comment_free = re.sub("&lt;!--.*?--&gt;", "", ref_free, flags=re.DOTALL)
        curly_free = re.sub("\{\{.*?\}\}", "", comment_free, flags=re.DOTALL)
        nonsense_free = re.sub("&lt;.*?&gt;", "", curly_free)
        quote_fix = re.sub("&quot;", '"', nonsense_free)
        amp_fix = re.sub("&amp;", "&", quote_fix)
        return Wikipedia.resolve_brackets(amp_fix)

    def yield_page(self, clean=True):
        page_lines = []
        page_started = False
        while True:
            line = self._wikifile.readline()
            if len(line) == 0:
                break
            if not page_started and "<text" in line:
                page_started = True
            if page_started:
                page_lines.append(line[:-1])
                if "</text>" in line:
                    break
        if len(page_lines) == 0:
            return ""
        if clean:
            return Wikipedia.clean_page("\n".join(page_lines))
        return "\n".join(page_lines)

    def __del__(self):
        self._wikifile.close()

if __name__ == "__main__":
    wiki = Wikipedia(sys.argv[1])
    page = wiki.yield_page()
    while len(page) > 0:
        print page, "\n\n\n\n"
        page = wiki.yield_page("dirty" not in sys.argv)
