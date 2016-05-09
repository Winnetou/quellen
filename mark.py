# all the logic that stands behind /mark url
import logging
from bson.objectid import ObjectId
from bs4 import BeautifulSoup
from pymongo import MongoClient
from deep_backend import clean, is_marginalia
from db_access import save_single_word, update_really_all_texts, update_documents_notepad
from datetime import datetime as dt

client = MongoClient()
manu_tironis = client['manu_tironis']
lace_texts = manu_tironis.lace_texts

logging.basicConfig(filename='db_access_logger.log', level=logging.DEBUG)

# Get an instance of a logger
logger = logging.getLogger(__name__)


def mark_save(as_what, doc_id, word_id):
    """
    POST to url /mark - callback to one of the :func: defined below
    """
    doc_id = ObjectId(doc_id)
    logger.info("{}  mark :: args:{}-{}-{}".format(dt.now(), as_what, doc_id, word_id))
    #print "{}  mark :: args:{}-{}-{}".format(dt.now(), as_what, doc_id, str(word_id))

    if as_what == "correct":
        mark_as_correct(doc_id=doc_id, word_id=word_id)
    if as_what == "incorrect":
        # mark as incorrect - it doesn't matter what it is
        mark_as('0', doc_id, word_id)
    # dead code below - will go live
    # when frontend will get that feature
    if as_what == "pagination":
        add_pagination_class(doc_id, word_id)
    return


def mark_as_correct(doc_id, word_id):
    '''
    Word is marked as incorrect - because it's not yet in db or because its marginalia
    user says it is correct
    word itself is not needed - we check it and if its marginalia, we just set to corr=1
    else we save it to db
    '''
    #print "mark_as_correct", doc_id, word_id
    record_to_correct = lace_texts.find_one({"_id": doc_id})
    notepad = record_to_correct['notepad']
    soup = BeautifulSoup(notepad, 'html.parser')
    node = soup.find("span", {"id": word_id})
    if node.has_attr('full'):
        text = node["full"]
    else:
        text = node.text
    # make sure text has no trailing comma or dot
    text = clean(text)
    # case 1: text has already class marginalia
    if node.has_attr('class'):
        if 'side_pagination' in node['class']:
            mark_as('1', doc_id, word_id)
            return
    # case 2: text is marginalia, but word has no class - we add class
    elif is_marginalia(text):
        # it's marginalia - change only corr to 1
        mark_as('1', doc_id, word_id)
        add_pagination_class(doc_id, word_id)
        return
    # the most important - it is a word, we will keep it
    # because it's not yet in the db
    else:
        save_single_word(text)
        update_really_all_texts(text)
        return


def mark_as(as_what, doc_id, word_id):
    '''
    :param as_what - 0 or 1
    '''
    record_to_correct = lace_texts.find_one({'_id': doc_id})
    notepad = record_to_correct['notepad']
    soup = BeautifulSoup(notepad, 'html.parser')
    node = soup.find("span", {"id": word_id})
    node['corr'] = as_what
    new_notepad = str(soup)
    update_documents_notepad(record_to_correct['_id'], new_notepad)

    return


def add_pagination_class(doc_id, word_id):
    record_to_correct = lace_texts.find_one({'_id': doc_id})
    notepad = record_to_correct['notepad']
    soup = BeautifulSoup(notepad, 'html.parser')
    lines = soup.findAll('span', 'ocr_line')
    # find the line where the word is -
    for line in lines:
        if line.find("span", {"id": word_id}):
            that_line = line
            break
    node = that_line.find("span", {"id": word_id})
    if len(line) == 1:
        # for now - we can only say that we don't know
        # later we can check page_number even or odd
        # and if node.text in [5, 10, 15, 20]
        return
    if that_line.index(node) == 0:
        node['class'] = "side_pagination left"
    elif that_line[::-1].index(node) == 0:
        node['class'] = "side_pagination right"
    new_notepad = str(soup)
    update_documents_notepad(record_to_correct['_id'], new_notepad)

    return
