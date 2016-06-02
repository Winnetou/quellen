# db_access.py - operations on the db
import logging
from copy import deepcopy
from bs4 import BeautifulSoup
from pymongo import MongoClient
from datetime import datetime
from deep_backend import clean, replace_node

client = MongoClient()
manu_tironis = client['manu_tironis']

logging.basicConfig(filename='db_access_logger.log', level=logging.DEBUG)

# Get an instance of a logger
logger = logging.getLogger(__name__)


def get_all_words():
    '''
    Returns all words as a list
    '''
    words = list(manu_tironis.words.find({}, {"word": 1}).distinct("word"))
    return words


def save_single_word(word):
    """Saves a word to the database
    if it is not there yet
    """
    # first - if word is already there, leave it
    word = clean(word)
    all_lower_words = [x.lower() for x in get_all_words()]
    if word.lower() in all_lower_words:
        return
    # TODO - what shall we do about uppercase?
    document = {'word': word, "added": datetime.now()}
    manu_tironis.words.insert(document)
    return


def update_really_all_texts(word):
    """
    Update texts by setting word corr=1
    Here be dragons:
    That is bottleneck
    check if fidning by regular expressions may be better
    and it gives word with trailing dot or comma
    try with:
        import re
        regx = re.compile("^foo", re.IGNORECASE)
        db.users.find_one({"files": regx})
    but check manually that it returns also full, with trailing dot
    and comma
    """
    find_re = {'notepad': {'$regex': word}}
    fields_dict = {'_id': 1, 'notepad': 1}
    all_to_be_updated = list(manu_tironis.lace_texts.find(find_re, fields_dict))

    for document in all_to_be_updated:
        notepad = document['notepad']
        notepad_copy = notepad
        soup = BeautifulSoup(notepad, 'html.parser')
        greek_text = soup.find('span', "greek_text")
        for node in greek_text.findAll("span", {"corr": "0"}):
            # do not correct just half of the word
            if not node.has_attr('half'):
                if clean(node.text) == word:
                    copy_node = unicode(node).replace('corr="0"', 'corr="1"')
                    notepad_copy = notepad_copy.replace(unicode(node), copy_node)
            else:
                # correct only full
                if node.has_attr('full'):
                    if clean(node["full"]) == word:
                        second_half_id = int(node["id"]) + 1
                        second_half = soup.find('span', {"id": second_half_id})
                        if second_half and second_half.has_attr('half') and second_half['half'] == "2":
                            copy_node = unicode(node).replace('corr="0"', 'corr="1"')
                            notepad_copy = notepad_copy.replace(unicode(node), copy_node)
                            copy_second_half = unicode(second_half).replace('corr="0"', 'corr="1"')
                            notepad_copy = notepad_copy.replace(unicode(second_half), copy_second_half)
        if notepad != notepad_copy:
            doc_id = document['_id']
            update_documents_notepad(doc_id, notepad_copy)
    return


def update_documents_notepad(doc_id, new_notepad):
    '''
    Essentialy its an SQL UPDATE on a single db record
    Because we invoke that in many places
    one function created is
    to update doc['notepad']
    '''
    new_notepad = renumber_ids(new_notepad)
    # print "UPDATED TEXT:: {}".format(new_notepad)
    x1 = {"_id": doc_id}
    x2 = {"$set": {"notepad": new_notepad}}
    x = manu_tironis.lace_texts.update(x1, x2)
    logger.info("UPDATE: {}".format(x))

    return


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


def run_best_guess(correct_word, doc_id, word_id):
    """
    If the word was corrected (eg w0rd to word)
    it may a common OCR mistake
    in that case run all identical incorrect words
    and change their text to corrected
    but still keep'em as corr=0 in case the best guess
    is not really 100% correct
    This func is called by `update.save_corrected`
    :param doc_id:  ObjectId(page_id)
    """
    # step 1 use correct_word, page_id, word_id to retrieve "old word"
    #raise AssertionError("NOT YET TESTED")
    record_to_correct = manu_tironis.lace_texts.find_one({"_id": doc_id})
    notepad = record_to_correct['notepad']
    soup = BeautifulSoup(notepad, 'html.parser')
    node = soup.find("span", {"id": word_id})
    if node.has_attr('full'):
        old_word = node["full"]
    else:
        old_word = node.text
    # make sure text has no trailing comma or dot
    old_word = clean(old_word)
    find_dict = {'notepad': {'$regex': old_word}}
    fields_dict = {'_id': 1, 'notepad': 1}
    all_to_be_updated = list(manu_tironis.lace_texts.find(find_dict, fields_dict))

    for document in all_to_be_updated:
        notepad = document['notepad']
        notepad_copy = notepad
        soup = BeautifulSoup(notepad, 'html.parser')
        greek_text = soup.find('span', "greek_text")
        for node in greek_text.findAll("span", {"corr": "0"}):
            # do not correct just half of the word
            if not node.has_attr('half'):
                if clean(node.text) == correct_word:
                    # test if that actually works!
                    copy_node = deepcopy(node)
                    copy_node.string = correct_word
                    notepad_copy = notepad_copy.replace(unicode(node), unicode(copy_node))
            else:
                # correct only full
                if node.has_attr('full'):
                    if clean(node["full"]) == correct_word:
                        second_half_id = int(node["id"]) + 1
                        second_half = soup.find('span', {"id": second_half_id})
                        if second_half and second_half.has_attr('half') and second_half['half'] == "2":
                            copy_node = deepcopy(node)
                            copy_node.string = correct_word
                            notepad_copy = notepad_copy.replace(unicode(node), copy_node)
                            copy_second_half = deepcopy(second_half)
                            copy_second_half.string = correct_word
                            notepad_copy = notepad_copy.replace(unicode(second_half), unicode(copy_second_half))
        if notepad != notepad_copy:
            doc_id = document['_id']
            update_documents_notepad(doc_id, notepad_copy)
    return
