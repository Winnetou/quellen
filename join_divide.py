from bs4 import BeautifulSoup, Tag

# from db_access import update_documents_notepad
# from deep_backend import is_correct, is_marginalia
#from psql_manu_tironis import get_single_record
from psql_tasks import async_update_documents_notepad
from helpers import (token_is_first_in_line, token_is_last_in_line,
                     is_correct, is_marginalia)

# from pymongo import MongoClient
# client = MongoClient()
# manu_tironis = client['manu_tironis']
# lace_texts = manu_tironis.lace_texts


def join_words(dikt):
    '''
    Take a word with it's id and join it
    if it is a simple concatenation of two words
    save it as legal word and set corr=1
    if it is a concatenation AND correction
    first correct the word
    next save it as legal, next set corr=1
    for mvp we join only two words: word_id and word_id+1
    : param: dikt  dictonary
    '''
    word_id, word = dikt['word_id'], dikt['word']
    doc_id = dikt['page_id']
    # psql
    raise AssertionError
    notepad = get_single_record(doc_id)

    # record_to_correct = manu_tironis.lace_texts.find_one({'_id': doc_id})
    # notepad = record_to_correct['notepad']
    # step 2 - replace both words with joined word
    soup = BeautifulSoup(notepad, 'html.parser')
    node = soup.find("span", {"id": word_id})
    second_word_id = int(word_id) + 1
    second_node = soup.find("span", {"id": second_word_id})
    if second_node is None:
        # something is totally wrong here - we can't find next
        return
    if node.has_attr("half") and node['half'] == '1':
        deal_with_joining_halves(dikt, 1)
        return
    if second_node.has_attr("half") and second_node['half'] == '2':
        deal_with_joining_halves(dikt, 2)
        return
    greek_text = soup.find('span', "greek_text")
    greek_lines = greek_text.findAll('span', 'ocr_line')
    # skip the last line, no idex error
    for line in greek_lines:
        first_hyp = line.find("span", {"id": word_id})
        if first_hyp:
            sec_hyp = line.find("span", {"id": second_word_id})
            if sec_hyp:
                break
            else:
                deal_with_joining_words_across_lines(dikt)
                return
    new_node = Tag(name="span", attrs={"id": node['id'], 'corr': "0", 'lang': "grc"})
    new_node.string = word
    if is_correct(word):
        new_node['corr'] = "1"
    if is_marginalia(word):
        del new_node['lang']
        if token_is_first_in_line(doc_id, node):
            new_node["class"] = "side_pagination left"
        else:
            new_node["class"] = "side_pagination right"

    # replace the first chunk with full word
    new_notepad = notepad.replace(unicode(node), unicode(new_node))
    # delete second word
    new_notepad = new_notepad.replace(unicode(second_node), "")
    # step 4 - update the document
    async_update_documents_notepad.delay(doc_id, new_notepad)
    return


def deal_with_joining_halves(dikt, half):
    """
    second_node is first half of the world, then
    attr `text` and `full` have to be updated
    looks ready for tests
    """
    word_id, word = dikt['word_id'], dikt['word']
    # record_to_correct = manu_tironis.lace_texts.find_one({'_id': dikt['page_id']})
    # notepad = record_to_correct['notepad']
    doc_id = dikt['page_id']
    # psql
    notepad = get_single_record(doc_id)

    soup = BeautifulSoup(notepad, 'html.parser')
    node = soup.find("span", {"id": word_id})
    second_word_id = int(word_id) + 1
    second_node = soup.find("span", {"id": second_word_id})

    if half == 1:
        # first word is just 'normal', the next one is half=1
        assert second_node.has_attr("full")
        new_node = Tag(name="span",
                       attrs={"id": node['id'], 'corr': "0", 'lang': "grc", 'half': '1'})
        new_node.string = word
        # eg ba + sile + us,
        full = second_node["full"].replace(second_node.text, word)
        new_node["full"] = full
        # if is_correct(full):
        #    new_node['corr'] = "1"
        #    # but also half=2 must be set to corr=1
        new_notepad = notepad.replace(unicode(second_node), unicode(new_node))
        # delete second word
        new_notepad = new_notepad.replace(unicode(node), "")
    if half == 2:
        assert second_node["half"] == 2
        # we have to find first half to update full
        full_node_id = int(word_id) - 1
        full_node = soup.find("span", {"id": full_node_id})
        if not full_node or not full_node.has_attr("full"):
            full_node_id = full_node_id - 1
            full_node = soup.find("span", {"id": full_node_id})
            if not full_node or not full_node.has_attr("full"):
                raise Exception("Something went terribly wrong!")
        full = full_node["full"].replace(second_node.text, word)
        full_node["full"] = full
        new_node = Tag(name="span",
                       attrs={"id": node['id'], 'corr': "0", 'lang': "grc", 'half': '2'})
        new_node.string = word
        # replace the first chunk with full word
        new_notepad = notepad.replace(unicode(node), unicode(new_node))
        # delete second word
        new_notepad = new_notepad.replace(unicode(second_node), "")
    # step 4 - update the document
    # doc_id = record_to_correct['_id']
    async_update_documents_notepad.delay(doc_id, new_notepad)

    return


def deal_with_joining_words_across_lines(dikt):
    """
    word 1 in one line, word 2 in next line
    possibly side pagination in between
    """
    word_id, word = dikt['word_id'], dikt['word']
    doc_id = dikt['page_id']
    notepad = get_single_record(doc_id)
    # record_to_correct = manu_tironis.lace_texts.find_one({'_id': dikt['page_id']})
    # notepad = record_to_correct['notepad']
    soup = BeautifulSoup(notepad, 'html.parser')
    node = soup.find("span", {"id": word_id})
    second_word_id = int(word_id) + 1
    second_node = soup.find("span", {"id": second_word_id})
    new_first_node = Tag(name="span", attrs={"id": node[
                         'id'], 'half': '1', 'corr': "0", 'lang': "grc"})
    new_first_node["full"] = word
    new_first_node.string = node.text + "-"
    new_second_node = Tag(name="span", attrs={
                          "id": second_word_id, 'half': '2', 'corr': "0", 'lang': "grc"})
    new_second_node.string = second_node.text
    if is_correct(word):
        new_first_node['corr'] = "1"
        new_second_node['corr'] = "1"

    new_notepad = notepad.replace(unicode(node), unicode(new_first_node))
    new_notepad = new_notepad.replace(unicode(second_node), unicode(new_second_node))
    # doc_id = record_to_correct['_id']
    async_update_documents_notepad.delay(doc_id, new_notepad)

    return


def divide_word(dikt):
    '''
    23/03 -- looks ready
    Take a word with it's id divide it
    : param: dikt dictonary
    '''
    node_id, doc_id = dikt['word_id'], dikt['page_id']
    notepad = get_single_record(doc_id)
    # record_to_correct = manu_tironis.lace_texts.find_one({"_id": dikt['page_id']})
    # notepad = record_to_correct['notepad']
    # step 2 - replace one word with two words
    soup = BeautifulSoup(notepad, 'html.parser')
    node = soup.find("span", {"id": node_id})
    # word come separated by whitestring
    list_of_divided_words = dikt['word'].split()
    nodes = []
    if node.has_attr("half"):
        # last new word must be half=1
        if node["half"] == "1":
            for word in list_of_divided_words[:-1]:
                new_node = Tag(name="span", attrs={"id": 'id', 'corr': "0", 'lang': "grc"})
                if is_correct(word):
                    new_node["corr"] = "1"
                new_node.string = word
                if is_marginalia(word):
                    del new_node['lang']
                    if token_is_first_in_line(doc_id, node_id):
                        new_node["class"] = "side_pagination left"
                    else:
                        new_node["class"] = "side_pagination right"
                nodes.append(unicode(new_node))
            new_node = Tag(name="span", attrs={"id": 'id', 'corr': "0", 'lang': "grc", "half": "1"})
            word = list_of_divided_words[-1]
            if is_correct(word):
                new_node["corr"] = "1"
            new_node.string = word
            if is_marginalia(word):
                del new_node['lang']
                if token_is_first_in_line(doc_id, node_id):
                    new_node["class"] = "side_pagination left"
                else:
                    new_node["class"] = "side_pagination right"
            nodes.append(unicode(new_node))

        elif node["half"] == "2":
            # first new word must be half=2
            new_node = Tag(name="span", attrs={"id": '', 'corr': "0", 'lang': "grc", "half": "2"})
            word = list_of_divided_words[0]
            if is_correct(word):
                new_node["corr"] = "1"
            new_node["half"] = "2"
            new_node.string = word
            if is_marginalia(word):
                del new_node['lang']
                if token_is_first_in_line(doc_id, node_id):
                    new_node["class"] = "side_pagination left"
                else:
                    new_node["class"] = "side_pagination right"
            nodes.append(unicode(new_node))
            for word in list_of_divided_words[1:]:
                new_node = Tag(name="span", attrs={"id": '', 'corr': "0", 'lang': "grc"})
                if is_correct(word):
                    new_node["corr"] = "1"
                if is_marginalia(word):
                    del new_node['lang']
                    if token_is_first_in_line(doc_id, node_id):
                        new_node["class"] = "side_pagination left"
                    else:
                        new_node["class"] = "side_pagination right"
                new_node.string = word
                nodes.append(unicode(new_node))
    else:
        for word in list_of_divided_words:
            new_node = Tag(name="span", attrs={"id": '', 'corr': "0", 'lang': "grc"})
            if is_correct(word):
                new_node["corr"] = "1"
            new_node.string = word
            if is_marginalia(word):
                del new_node['lang']
                if token_is_first_in_line(doc_id, node_id):
                    new_node["class"] = "side_pagination left"
                else:
                    new_node["class"] = "side_pagination right"
            nodes.append(unicode(new_node))
    all_nodesas_str = " ".join(nodes)
    new_notepad = notepad.replace(unicode(node), all_nodesas_str)
    async_update_documents_notepad.delay(doc_id, new_notepad)
