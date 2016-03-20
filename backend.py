from bs4 import BeautifulSoup
from pymongo import MongoClient
from datetime import datetime
client = MongoClient()
manu_tironis = client['manu_tironis']



def get_all_words():
    '''
    Returns all words as a list
    '''
    words = list(manu_tironis.words.find({}, {"word": 1}).distinct("word"))
    return words


def is_marginalia(word):

    if len(word) == 1 and word in "1234567890QWERTYUIOPLKJHGFDSAZXCVBNM":
        return True
    if len(word) == 2 and all(w in "1234567890" for w in word):
        return True
    return False


def save_corrected(corrected_word, page_id=None, node_id=None):
    '''
    We use it in follwoing user journeys:
    1. User clicks 'this word is correct' - we update db and all texts, it's not in db for sure
     -  this is 'safecorrect' journey
    2. user clicks on suggested words to correct a specific word - we update only one , word
    is surely in db -  this is 'savesuggested' journey
    3. user provides manual input to correct single node, we try to store the new word in db
    though we don't know if it's there or not -  this is 'savecorrected' journey
    '''
    # FINISH ME

    if not _is_safe(corrected_word):
        return
    # word can be not yet present in the dictionary
    # when it was corrected by hand from user's input
    # this is user journey 1
    if corrected_word not in get_all_words():
        if not is_marginalia(corrected_word):
            _save_single_word(corrected_word)
            _update_all_texts(corrected_word)
    else:
        record_to_correct = manu_tironis.lace_texts.find_one({'_id': 'page_id'})
        notepad = record_to_correct['notepad']
        new_notepad = _replace_node(notepad, corrected_word, semantic_role, word_id=node_id)
        _update_documents_notepad(record_to_correct['_id'], new_notepad)


def join_words(dikt):
    '''
    Take a word with it's id
    join it
    if it is a simple concatenation of two words
    save it as legal word and set corr=1
    if it is a concatenation AND correction
    first correct the word
    next save it as legal, next set corr=1
    for mvp we join only two words: node_id and node_id+1
    : param: dikt  dictonary
    # TODO allow to join more words - for now user can do that in two stages
    '''
    # step 1: find the page
    #query = {"title": dikt['text'], "pagenumber": dikt['page_id']}

    query = {'_id': dikt['page_id']}
    record_to_correct = manu_tironis.lace_texts.find_one(query)
    notepad = record_to_correct['notepad']
    # step 2 - replace both words with joined word
    soup = BeautifulSoup(notepad, 'html.parser')
    node = soup.find("span", {"id": word_id})
    second_word_id = word_id + 1
    second_node = soup.find("span", {"id": second_word_id})
    # TODO:
    # if the second word is in another line, make  this trick with
    #                  word["corr"] = 1
    #                  word["half"] = 1
    #                  word["full"] = joined_word
    # for now, front end will give us only chance to correct words not last line the line of text
    # leave it, later, implement it
    # new node is the word that will replace both
    # the new node is corr=0, we can't assume that it was corrected
    # only after it was joined, user can click on "it is correct"
    # new node's lang must be greek, else we will not allow to correct it
    new_node = Tag(name="span", attrs={"id": node['id'], 'corr': "0", 'lang': "grc"})
    new_node.string = word
    # replace the first chunk with full word
    new_notepad = notepad.replace(str(node), str(new_node))
    # delete second word
    new_notepad = notepad.replace(str(second_node), "")
    # step 4 - update the document
    doc_id = record_to_correct['_id']
    _update_documents_notepad(doc_id, new_notepad)
    return


def divide_word(dikt):
    '''
    Take a word with it's id
    divide it
    : param: dikt  dictonary
    '''
    query = {"title": dikt['text'], "pagenumber": dikt['page_number']}
    record_to_correct = manu_tironis.lace_texts.find_one(query)
    notepad = record_to_correct['notepad']
    # step 2 - replace both words with joined word
    soup = BeautifulSoup(notepad, 'html.parser')
    node = soup.find("span", {"id": word_id})
    # word come separated by whitestring
    divided_words = dikt['word'].split()
    nodes = []
    counter = 1
    for word in divided_words:
        new_node = soup.new_tag("span")
        # only after it was joined, user can click on "it is correct"
        new_node["corr"] = "0"
        # new node's lang must be greek, else we will not allow to correct it
        new_node["lang"] = "grc"
        # add id to the new node by appending number to existing node ids
        new_node["id"] = str(dikt['node_id']) + str(counter)
        counter += 1
        new_node.string = word
        nodes.append(str(new_node))
    all_nodesas_str = " ".join(nodes)
    new_notepad = notepad.replace(str(node), all_nodesas_str)
    _update_documents_notepad(record_to_correct['_id'], new_notepad)


def mark(mark, doc_id, word_id):
    """
    User journeys:
    """
    query = {"_id": doc_id}
    record_to_correct = manu_tironis.lace_texts.find_one(query)
    notepad = record_to_correct['notepad']
    soup = BeautifulSoup(notepad, 'html.parser')
    node = soup.find("span", {"id": word_id})
    if mark == "side_pagination":
        # add class `side_pagination`, remove lang,
        new_notepad = notepad.replace(str(node), str(new_node))
        _update_documents_notepad(record_to_correct['_id'], new_notepad)
    if mark == "incorrect":
        # set corr to 0
        new_notepad = notepad.replace(str(node), str(new_node))
        _update_documents_notepad(record_to_correct['_id'], new_notepad)
        pass
    if mark == "its_latin":
        # set corr to 0
        new_notepad = notepad.replace(str(node), str(new_node))
        _update_documents_notepad(record_to_correct['_id'], new_notepad)
        pass
    if mark == "its_greek":
        # set corr to 0
        new_notepad = notepad.replace(str(node), str(new_node))
        _update_documents_notepad(record_to_correct['_id'], new_notepad)
        pass

# internal


def _update_documents_notepad(doc_id, new_notepad):
    '''
    Because we invoke that in many places
    one function created is
    to update doc['notepad']
    '''
    x1 = {"_id": doc_id}
    x2 = {"$set": {"notepad": new_notepad}}
    manu_tironis.lace_texts.find(x1).update(x2)
    return


def _clean_from_dots(word):
    # this is insane, but i want to keep them 'ere
    all_greek_letters = [u'\u1f40', u'\u03b4', u'\u03cd', u'\u03bd', u'\u03b7', u'\u03c4', u'\u03ad', u'\u03bb', u'\u03b5', u'\u03b9', u'\u03bf', u'\u03c2', u'\u03c3', u'\u03af', u'\u03b1', u'\u1f00', u'\u03c0', u'\u03c1', u'\u03ae', u'\u03c9', u'\u1f24', u'\u03b3', u'\u03ba', u'\u03bc', u'\u03c5', u'\u03b8', u'\u1f73', u'\u1f79', u'\u1f11', u'\u03b2', u'\u03ac', u'\u03c7', u'\u03ce', u'\u1fc6', u'\u1f55', u'\u1ff3', u'\u1f71', u'\u1f77', u'\u1f75', u'\u03cc', u'\u1f76', u'\u1f7d', u'\u1f20', u'\u1f14', u'\u03be', u'\u1f51', u'\u1f72', u'\u03c6', u'\u1ff6', u'\u1f10', u'\u1fd6', u'\u1f66', u'\u1f30', u'\u1f15', u'\u1f27', u'\u03b6', u'\u1fe6', u'\u1f05', u'\u1fb3', u'\u1f45', u'\u1fc3', u'\u1f7b', u'\u1f50', u'\u1f04', u'\u1f94', u'\u1f54', u'\u1fb7', u'\u1f25', u'\u1ff7', u'\u1f70', u'\u1f41', u'\u1f78', u'\u1f21', u'\u1fc7', u'\u1f35', u'\u1fe5', u'\u1fb6', u'\u1f7a', u'\u1f74', u'\u1f36', u'\u1f44', u'\u1f01', u'\u1fbd', u'\u1fc2', u'\u1fbf', u'\u1f60', u'\u1f7c', u'\u1f57', u'\u03c8', u'\u1f96', u'\u1fe4',
                         u'\u1f31', u'\u1fc4', u'\u1fa7', u'\u1f23', u'\u1f34', u'\u03ca', u'\u0390', u'\u02d9', u'\u1fa4', u'\u1f67', u'\u0313', u'\u1f37', u'\u1f90', u'\u1f84', u'\u0384', u'\u1f65', u'\u0375', u'\u1ff4', u'\u1f61', u'\u1f26', u'\u1f56', u'\u1f85', u'\u1f63', u'\u2019', u'\u014d', u'\u1f06', u'\u1f64', u'\u1fa0', u'\u1f43', u'\u1f33', u'\u03b0', u'\u2219', u'\u1f86', u'\u1f97', u'\u1f13', u'\u1f03', u'\u2018', u'\u1fa6', u'\u1fb4', u'\u1f02', u'\u03cb', u'\u1f62', u'\u1f42', u'\u1f22', u'\u1f53', u'\u1f48', u'\u1fd3', u'\u1fe3', u'\u03a5', u'\u0391', u'\u1f91', u'\u039f', u'\u0399', u'\u1f07', u'\u0397', u'\u0395', u'\u03a6', u'\u0393', u'\u03a4', u'\u1f08', u'\u0396', u'\u039a', u'\u039d', u'\u039c', u'\u039b', u'\u03a3', u'\u0398', u'\u03a7', u'\u03a1', u'\u1fec', u'\u0394', u'\u0392', u'\u03a0', u'\u03a9', u'\u1f18', u'\u1f4f', u'\u03a8', u'\u1f29', u'\u1f38', u'\u1fe2', u'\u1f0c', u'\u1fd2', u'\u1f59', u'\u1f19', u'\u1f1d', u'\u1f09', u'\u039e', u'\u1f39', u'\u1f68', u'\u1f28', u'\u1f0e', u'\xad', ]

    for letter in word:
        if letter not in all_greek_letters:
            word = word.replace(letter, "")
    return word


def _save_single_word(word, semantic_role=None):
    """self explanatory, eh? """
    # first - if word is already there, leave it
    word = _clean_from_dots(word)
    if word.lower() in [x.lower() for x in get_all_words()]:
        return
    # TODO - what shall we do about uppercase?
    document = {'word': word, "added": datetime.now()}
    if semantic_role:
        document["semantic_role"] = semantic_role

    manu_tironis.words.insert(document)
    return


def _update_all_texts(word, semantic_role):
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
        new_notepad = _replace_node(document['notepad'], word, semantic_role)
        doc_id = document['_id']
        _update_documents_notepad(doc_id, new_notepad)
        manu_tironis.lace_texts.find(x1).update(x2)
    return


def _replace_node(notepad, word, semantic_role=None, word_id=None):
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
        nodes_to_replace = [n for n in all_nodes if n.text == word]
    for old_node in nodes_to_replace:
        node_id = old_node['id']
        new_node = soup.new_tag("span")
        new_node["id"] = node_id
        new_node["corr"] = "1"
        if semantic_role is not None:
            if semantic_role == 'side_pagination':
                new_node["class"] = "side_pagination"
            else:
                new_node['semantic'] = semantic_role
                # TODO: FIX ME when implement feature: "it's not greek"!
                new_node["lang"] = "grc"
        new_node.string = word
        notepad = notepad.replace(str(old_node), str(new_node))

    return notepad


def _is_safe(word):
    html_tags = 'href', 'iframe', 'www', 'http', '@'
    if len(word) > 60:
        return False
    if any(tag in word for tag in html_tags):
        return False
