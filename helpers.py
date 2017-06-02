from bs4 import BeautifulSoup
# from pymongo import MongoClient
import psql_manu_tironis
import smart_suggest
PUNCT_MARKS = [".''", "''", '""', '"', ",''", ',', '.', ',,']
GREEK_ALPHABET = smart_suggest.GREEK_ALPHABET()
# client = MongoClient()
# manu_tironis = client['manu_tironis']


def renumber_ids(final_text):
    """
    ids get messy when we add another item - or drop one
    """
    counter = 1
    soup = BeautifulSoup(final_text, 'html.parser')
    greek_text = soup.find('span', "greek_text")
    for line in greek_text.findAll('span', 'ocr_line'):
        for word in line.findAll("span"):
            if word.has_attr("id"):
                word["id"] = counter
                counter += 1
    final_text = str(soup)
    return final_text


def get_word(notepad, word_id):
    """
    Take notepad, return word with given word_id
    """
    # FIXME move to helpers
    soup = BeautifulSoup(notepad, 'html.parser')
    node = soup.find("span", {"id": word_id})
    if node.has_attr('full'):
        return node["full"]
    else:
        return node.text

def token_is_first_in_line(doc_id, node_id):
    """
    """
    position, line_len = _get_tokens_position(doc_id, node_id)
    if line_len > 1:
        if position == 0:
            return True
    return False


def token_is_last_in_line(doc_id, node_id):
    """
    """
    position, line_len = _get_tokens_position(doc_id, node_id)
    if line_len > 1:
        if position == line_len:
            return True
    return False


def _get_tokens_position(doc_id, node_id):
    """
    Get token position in line:
    return list [token_position, line_len]
    """
    notepad = psql_manu_tironis.get_single_record(doc_id)
    # record_to_correct = manu_tironis.lace_texts.find_one({'_id': doc_id})
    # notepad = record_to_correct['notepad']
    # step 2 - replace both words with joined word
    soup = BeautifulSoup(notepad, 'html.parser')
    greek_text = soup.find('span', "greek_text")
    greek_lines = greek_text.findAll('span', 'ocr_line')
    # skip the last line, no idex error
    for line in greek_lines:
        _line = [o for o in line.findAll('span')]
        first_hyp = line.find("span", {"id": node_id})
        if first_hyp:
            return [_line.index(first_hyp), len(_line)]


def is_correct(word):
    WORDS = psql_manu_tironis.get_all_words()
    if word in WORDS:
        return True
    return False


def is_marginalia(word):

    if len(word) == 1 and word in "1234567890QWERTYUIOPLKJHGFDSAZXCVBNM":
        return True
    if len(word) in [2, 3] and all(w in "1234567890" for w in word):
        return True
    return False


def is_safe(word):
    html_tags = 'href', 'iframe', 'www', 'http', '@'
    if len(word) > 60:
        return False
    if any(tag in word for tag in html_tags):
        return False
    if len(word.split()) != 1:
        return False
    return True


def clean_from_dots(word):
    # this is insane, but i want to keep them 'ere
    for letter in word:
        if letter not in GREEK_ALPHABET:
            word = word.replace(letter, "")
    return word


def clean(word):
    '''
    If word ends with . or ,
    clean it
    '''
    perks = list(".,{}[](){}[]]().,;")
    BADSEEDS = [unicode(l) for l in perks]
    BADSEEDS.append(u'\xb7')
    word = word.strip()
    while len(word) > 0 and word[-1] in BADSEEDS:
        word = word[:-1]
    while len(word) > 0 and word[0] in BADSEEDS:
        word = word[1:]
    return word


def replace_node(notepad, word, word_id=None):
    '''
    this function should be used in two situations:
    1. user manually corrects specific word - then word_id is provided
    2.  user click "this word is correct" and we correct it globally, ie across all documents
    Take a notepad from the text /notepad is where changes are saved/
    find the word and correct it, but save all values of html node
    like id, corr, lang, etc
    return: corrected notepad
    '''
    soup = BeautifulSoup(notepad, 'html.parser')
    if word_id is not None:
        node = soup.find("span", {"id": word_id})
        nodes_to_replace = [node]
    else:
        all_nodes = soup.findAll("span", {"lang": "grc", "corr": "0"})
        nodes_to_replace = [n for n in all_nodes if clean(n.text) == word]
        # FIXME - also if clean(n["full"]) == word
    for old_node in nodes_to_replace:
        if old_node.has_attr("half"):
            if old_node["half"] == "2":
                # we do not correct the second half
                return
            if old_node.has_attr("full"):
                    # first let's find the other half
                next_node_id = old_node["id"] + 1
                next_node = soup.find("span", {"id": next_node_id})
                if not next_node:
                    return
                old_node["full"] = word
                old_node["corr"] = "1"
                next_node["corr"] = "1"
                half_cut = len(old_node.text)
                old_node.string = word[0:half_cut]
                next_node.string = word[half_cut:]

        else:
            old_node["corr"] = "1"
            # if word has dot or comma or qutation marks at the end, keep it
            # same when it's at the beginning
            if any(old_node.text.startswith(x) for x in PUNCT_MARKS):
                # raise AssertionError("FINISH ME!")
                old_node.string = old_node.string[0] + word
            elif any(old_node.text.endswith(x) for x in PUNCT_MARKS):
                # raise AssertionError("FINISH ME!")
                old_node.string = word + old_node.string[-1]
            else:
                old_node.string = word

    return str(soup)

