# all the logic that stands behind /update url
# user story - user corrects by hand or pick single suggestion
# from bs4 import BeautifulSoup
from bson.objectid import ObjectId
from pymongo import MongoClient
from deep_backend import is_marginalia, is_safe, clean_from_dots, replace_node
from db_access import save_single_word, update_really_all_texts, update_documents_notepad
from mark import mark_as, add_pagination_class
client = MongoClient()
manu_tironis = client['manu_tironis']
lace_texts = manu_tironis.lace_texts


def save_corrected(correct_word, page_id, word_id, is_hand_corrected=False):
    '''
    User story:
    1. User picked on of the words suggested to him
    2. User corrected text by hand
    Because correcting by Hand comes later - now we hardcode it to False
    '''
    # import pdb; pdb.set_trace()
    doc_id = ObjectId(page_id)
    correct_word = clean_from_dots(correct_word)
    if is_hand_corrected:
        # surely it is not in db
        if not is_safe(correct_word):
            return
        if is_marginalia(correct_word):
            mark_as('1', doc_id, word_id)
            add_pagination_class(doc_id, word_id)
            return
        else:
            save_single_word(correct_word)
            update_really_all_texts(correct_word)

    record_to_correct = lace_texts.find_one({"_id": doc_id})
    notepad = record_to_correct['notepad']
    new_notepad = replace_node(notepad, correct_word, word_id=word_id)
    update_documents_notepad(doc_id, new_notepad)
    # update_all_texts(corrected_word)
    # at the end, save pair
    # document = {"incorrect": text, "correct": correct_word}
    # manu_tironis.corrections.insert(document)
    return
