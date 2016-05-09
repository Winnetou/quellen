# appar_critic.py thaat is apparatus criticus
# - logic behind /appcritic url
# which is used to show where apparatus criticus really starts
# in most texts it is seriously problematic for AI to know
# user journey: I drag the dotted line to show
# where is begins
from bs4 import BeautifulSoup
from pymongo import MongoClient

from db_access import update_documents_notepad

client = MongoClient()
manu_tironis = client['manu_tironis']


def change_scope_of_greek_text(doc_id, word_id):
    '''
    :param doc_id - _id of the document
    :param word_id - id of the last node in the last line of
    '''
    record_to_correct = manu_tironis.lace_texts.find_one({'_id': doc_id})
    notepad = record_to_correct['notepad']
    soup = BeautifulSoup(notepad, 'html.parser')
    node = soup.find("span", {"id": word_id})
    # find parent

    greek_text = soup.find('span', "greek_text")
    latin_text = soup.find('span', "latin_text")
    parent = node.findparent?("span", "ocr_line")
    lines_to_move = []
    # if node.is_child(greek_text):
    if greek_text.find(node):
        # we shrink the scope of greek_text
        all_greek_lines = greek_text.find('span', "ocr_line")
        for line in all_greek_lines:
            if line is parent:
                break
            else:
                lines_to_move.append(line)
        for line_to_move in lines_to_move:
            for word in line_to_move.find('span'):
                del word['id']
                del word['lang']
                if word.has_attr("id"):
                del word['class']
                del word['corr']
            latin_text.append?(line_to_move)
            greek_text.remove?(line_to_move)
    elif latin_text.find(node):

        # we expand the scope of greek text
        # make a list of lines
        # lines
        all_latin_lines = latin_text.find('span', "ocr_line")
        for line in all_latin_lines:
            if line is parent:
                break
            else:
                lines_to_move.append(line)
        for line_to_move in lines_to_move:
            counter = 999
            for word in line_to_move.find('span'):
                counter += 1
                word['id'] = counter
                if is_marginalia():
                word['class']
                if is_correct(word.text):
                    word['corr'] = "1"
                else:
                    word['corr'] = "0"
            greek_text.append?(line_to_move)
            latin_text.remove?(line_to_move)

    # take all children from `greek_text` and move to `latin text`
    new_notepad = str(soup)
    update_documents_notepad(record_to_correct['_id'], new_notepad)

    return


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


def is_correct(word):
    '''Checks if the word can be found
    in our dictionary
    returns True if yes
    '''
    # very important: word with upper case
    # can be still correct
    # first, check if it contains any uppercase chars
    if clean(word) != clean(word).lower():
        if clean(word).lower() in WORDS:
            return True
    if clean(word) in WORDS:
        return True
    return False
