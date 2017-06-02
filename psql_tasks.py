from celery import Celery
import logging
import psycopg2
from helpers import clean, replace_node
from bs4 import BeautifulSoup
import psql_manu_tironis
connect_manu = psycopg2.connect("dbname=manu_tironis user=quellen")
manu_cursor = connect_manu.cursor()
logging.basicConfig(filename='db_access_logger.log', level=logging.DEBUG)
app = Celery('psql_manu_tironis', broker='amqp://guest@localhost//')


@app.task
def async_update_documents_notepad(doc_id, new_notepad):
    psql_manu_tironis.update_documents_notepad(doc_id, new_notepad)


@app.task
def save_single_word(word):
    """
    Saves a word to the database
    if it is not there yet
    """
    word = clean(word)
    # FIXME
    # there must be a way to do that in smarter way on posgtres
    # maybe upsert ?
    # TODO - what shall we do about uppercase?

    try:
        exists_query = "SELECT EXISTS (SELECT word from words WHERE word = %s)"
        manu_cursor.execute(exists_query, (word,))
        if manu_cursor.fetchone()[0]:
            return
        insert_command = "INSERT INTO words (word) VALUES (%s)"
        manu_cursor.execute(insert_command, (word,))
        connect_manu.commit()
    except:
        connect_manu.rollback()
        raise


@app.task
def delete_node(doc_id, node_id):
    """
    Remove node altogether
    """
    notepad = psql_manu_tironis.get_single_record(doc_id)
    # FIME - use replace node
    soup = BeautifulSoup(notepad, 'html.parser')
    node = soup.find("span", {"id": node_id})
    new_notepad = notepad.replace(unicode(node), "")

    psql_manu_tironis.update_documents_notepad(doc_id, new_notepad)


def _find_records_with_word_in(word):
    """
    Given word, find all record where
    notepad containt `word`
    """
    try:
        word = word.encode('utf-8')
        qry = "SELECT id, notepad FROM lace_texts where notepad LIKE '%>{}<%'".format(word)
        manu_cursor.execute(qry)
        records = manu_cursor.fetchall()
        records_as_dicts = []
        for result in records:
            records_as_dicts.append({"_id": result[0], "notepad": result[1]})
        return records_as_dicts
    except:
        connect_manu.rollback()
        raise


@app.task
def update_really_all_texts(word):
    """
    Update texts by setting word corr=1
    """
    all_to_be_updated = _find_records_with_word_in(word)

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
                    assert node in notepad_copy
                    assert str(node) in notepad_copy
                    assert unicode(node) in notepad_copy
                    notepad_copy = notepad_copy.replace(node, copy_node)
                    # notepad_copy = notepad_copy.replace(node, copy_node)
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
                            notepad_copy = notepad_copy.replace(
                                str(second_half), copy_second_half)
                            #notepad_copy = notepad_copy.replace(
                            #    second_half, copy_second_half)
        if notepad != notepad_copy:
            doc_id = document['_id']
            async_update_documents_notepad.delay(doc_id, notepad_copy)
    return


@app.task
def run_best_guess(correct_word, mistaken_word):
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
    # raise AssertionError("NOT YET TESTED")
    mistaken_word = clean(mistaken_word)
    all_to_be_updated = _find_records_with_word_in(mistaken_word)

    for document in all_to_be_updated:
        notepad = document['notepad']
        page_id = document['_id']
        notepad_copy = notepad
        soup = BeautifulSoup(notepad, 'html.parser')
        greek_text = soup.find('span', "greek_text")
        all_incorr = [n for n in greek_text.findAll("span", {"corr": "0"})]
        pt1 = [n for n in all_incorr if n.text == mistaken_word]
        pt2 = [n for n in all_incorr if n.has_attr('full') and n["full"] == mistaken_word]
        to_be_corrected = pt1 + pt2
        if not to_be_corrected:
            return
        # import pdb
        # pdb.set_trace()
        for node in to_be_corrected:
            notepad_copy = replace_node(notepad_copy, correct_word, word_id=node["id"])
            # TODO run me async
        async_update_documents_notepad.delay(page_id, notepad_copy)
