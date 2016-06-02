from bs4 import BeautifulSoup, Tag
from bson.objectid import ObjectId
from pymongo import MongoClient
from db_access import update_documents_notepad

client = MongoClient()
manu_tironis = client['manu_tironis']
lace_texts = manu_tironis.lace_texts


def join_words(dikt):
    '''
    23/03 -- looks ready - now frontend
    Take a word with it's id and join it
    if it is a simple concatenation of two words
    save it as legal word and set corr=1
    if it is a concatenation AND correction
    first correct the word
    next save it as legal, next set corr=1
    for mvp we join only two words: word_id and word_id+1
    : param: dikt  dictonary
    # TODO allow to join more words - for now user can do that in two stages
    '''
    word_id = dikt['word_id']
    word = dikt['word']
    query = {'_id': ObjectId(dikt['page_id'])}
    record_to_correct = manu_tironis.lace_texts.find_one(query)
    notepad = record_to_correct['notepad']
    # step 2 - replace both words with joined word
    soup = BeautifulSoup(notepad, 'html.parser')
    node = soup.find("span", {"id": word_id})
    second_word_id = int(word_id) + 1
    second_node = soup.find("span", {"id": second_word_id})
    if any(n.has_attr("half") for n in [node, second_node]):
        print "ONE IS HALF"
        return
    try:
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
                    print "Magick needed!"
                    # then do the magic with half and full
                    raise NotImplementedError("Cant join words across lines, but will do that soon")
    except:
        return
    #if node.has_attr('full'):
    #    do
    # import pdb; pdb.set_trace()
    # new node is the word that will replace both
    # the new node is corr=0, we can't assume that it was corrected
    # only after it was joined, user can click on "it is correct"
    # new node's lang must be greek, else we will not allow to correct it
    new_node = Tag(name="span", attrs={"id": node['id'], 'corr': "0", 'lang': "grc"})
    new_node.string = word
    # replace the first chunk with full word
    new_notepad = notepad.replace(unicode(node), unicode(new_node))
    # delete second word
    new_notepad = new_notepad.replace(unicode(second_node), "")
    # step 4 - update the document
    doc_id = record_to_correct['_id']
    update_documents_notepad(doc_id, new_notepad)
    return


def divide_word(dikt):
    '''
    23/03 -- looks ready
    Take a word with it's id divide it
    : param: dikt dictonary
    '''
    doc_id = ObjectId(dikt['page_id'])
    record_to_correct = manu_tironis.lace_texts.find_one({"_id": doc_id})
    notepad = record_to_correct['notepad']
    # step 2 - replace one word with two words
    soup = BeautifulSoup(notepad, 'html.parser')
    node = soup.find("span", {"id": dikt['word_id']})
    # word come separated by whitestring
    list_of_divided_words = dikt['word'].split()
    print 'list_of_divided_words is there '
    nodes = []
    counter = 1
    for word in list_of_divided_words:
        new_node = soup.new_tag("span")
        # only after it was joined, user can click on "it is correct"
        new_node["corr"] = "0"
        # new node's lang must be greek, else we will not allow to correct it
        new_node["lang"] = "grc"
        # add id to the new node by appending number to existing node ids
        new_node["id"] = unicode(dikt['word_id']) + unicode(counter)
        counter += 1
        new_node.string = word
        nodes.append(unicode(new_node))
    all_nodesas_str = " ".join(nodes)
    new_notepad = notepad.replace(unicode(node), all_nodesas_str)
    update_documents_notepad(record_to_correct['_id'], new_notepad)
