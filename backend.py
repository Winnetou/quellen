from bs4 import BeautifulSoup
from pymongo import MongoClient
client = MongoClient()
manu_tironis = client['manu_tironis']


def get_all_words():
    '''
    Returns all words as a list
    '''
    words = list(manu_tironis.words.find({}, {"word": 1}).distinct("word"))
    return words


def save_and_correct(word):
    """ First save a correct word
    next, correct all lace_pages
    """
    _save_single_word(word)
    _update_all_texts(word)
    pass



def save_corrected(corrected_word, text, page_number, node_id):
    '''
    step 1. we assume, that `corrected_word` may possibly not be yet in `words`

    '''
    if not _is_safe(corrected_word):
        return
    if corrected_word not in get_all_words():
        save_and_correct(corrected_word)
    record_to_correct = manu_tironis.lace_texts.find({"title": text, "pagenumber": page_number})
    notepad = record_to_correct['notepad']
    new_notepad = _replace_node(notepad, corrected_word, word_id=node_id)
    x1 = {"_id": record_to_correct['_id']}
    x2 = {"$set": {"notepad": new_notepad}}
    manu_tironis.lace_texts.find(x1).update(x2)


# internal
def _save_single_word(word):
    """self explanatory, eh? """
    document = {'word': word}
    manu_tironis.words.insert(document)
    return


def _update_all_texts(word):
    """update `notepad`
    but bloody mongo does not allow to udpate with data from search :(
    """
    # step 1 - find all docs containing :param word
    # bulk = tironis.words.initialize_ordered_bulk_op()
    # bulk.find({'_id': 1}).update({'$set': {'foo': 'bar'}})
    # find by
    find_dict = {'notepad': {'$regex': word}}
    fields_dict = {'_id': 1, 'notepad': 1}
    all_to_be_updated = list(manu_tironis.lace_texts.find(find_dict, fields_dict))
    for document in all_to_be_updated:
        new_notepad = _replace_node(document['notepad'], word)
        doc_id = document['_id']
        x1 = {"_id": doc_id}
        x2 = {"$set": {"notepad": new_notepad}}
        manu_tironis.lace_texts.find(x1).update(x2)
    return


def _replace_node(notepad, word, word_id=None):
    '''
    Take a notepad from the text /notepad is where changes are saved/
    find the word and correct it, but save all values of html node
    like id, corr, lang, etc
    return: corrected notepad
    '''
    soup = BeautifulSoup(notepad, 'html.parser')
    if word_id is not None:
        node = soup.findAll("span", {"id": word_id})
        # TODO -
        pass
    all_nodes = soup.findAll("span", {"lang": "grc", "corr": "0"})
    nodes_to_replace = [n for n in all_nodes if n.text == word]
    for old_node in nodes_to_replace:
        node_id = old_node['id']
        new_node = soup.new_tag("span")
        new_node["lang"] = "grc"
        new_node["corr"] = "1"
        new_node["id"] = node_id
        new_node.string = word
        notepad = notepad.replace(str(old_node), str(new_node))

    return notepad


def _is_safe(word):
    if len(word) > 60:
        return False
    if html_tag in word:
        return False
