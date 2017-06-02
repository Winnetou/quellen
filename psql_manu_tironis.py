#
import logging

# from helpers import renumber_ids as renumber
# from bs4 import BeautifulSoup
import psycopg2
import psycopg2.extras
connect_manu = psycopg2.connect("dbname=manu_tironis user=quellen")
manu_cursor = connect_manu.cursor()

logging.basicConfig(filename='db_access_logger.log', level=logging.DEBUG)

# Get an instance of a logger
logger = logging.getLogger(__name__)


def get_just_titles():
    """scriptorium page: returns titles of
    works being transcribed
    :rtype: list
    """
    try:
        manu_cursor.execute('''SELECT DISTINCT title FROM lace_texts''')
        result = manu_cursor.fetchall()
        presult = [item for sublist in result for item in sublist]
        return presult
    except Exception, e:
        logger.error("get_just_titles FAILED: {}".format(e))
        connect_manu.rollback()



def get_page(title, pagenumber):
    """
    Gets single page for a given title and pagenumber - if 0, then
    it takes first
    rtype: dict
    """
    pagenumber = str(pagenumber)
    try:
        # id, title, pagenumber, notepad, image_url
        if pagenumber == "0":
            manu_cursor.execute('''SELECT id, title, pagenumber, notepad, image_url FROM lace_texts WHERE title = %s ORDER BY pagenumber::int LIMIT 1''', (title,))
        else:
            manu_cursor.execute('''SELECT id, title, pagenumber, notepad, image_url FROM lace_texts WHERE title = %s AND pagenumber = %s''', (title, pagenumber))
        record = manu_cursor.fetchone()
        page = {"id": record[0], "title": record[1], "pagenumber": record[
            2], "notepad": unicode(record[3].decode('utf-8')), "image_url": record[4]}
        pagenumber_minus = str(int(page["pagenumber"]) - 1)
        pagenumber_plus = str(int(page["pagenumber"]) + 1)
        manu_cursor.execute('''SELECT EXISTS (SELECT id, title, pagenumber, notepad, image_url FROM lace_texts WHERE title = %s AND pagenumber = %s)''', (title, pagenumber_minus))
        res = manu_cursor.fetchone()
        if res[0]:
            page["next_page"] = pagenumber_minus
        manu_cursor.execute('''SELECT EXISTS (SELECT id, title, pagenumber, notepad, image_url FROM lace_texts WHERE title = %s AND pagenumber = %s)''', (title, pagenumber_plus))
        res = manu_cursor.fetchone()
        if res[0]:
            page["prev_page"] = pagenumber_plus
        return page
    except Exception, e:
        connect_manu.rollback()
        print e, title, pagenumber
        raise e


def update_documents_notepad(doc_id, new_notepad):
    '''
    SQL UPDATE on a single db record
    '''
    new_notepad = renumber(new_notepad)

    sql_command = '''UPDATE lace_texts SET notepad = %s WHERE id = %s'''
    # args = [new_notepad]
    try:
        manu_cursor.execute(sql_command, (doc_id, new_notepad))
        connect_manu.commit()
        logger.info("UPDATED: {}".format(doc_id))
    except Exception, e:
        logger.error("UPDATE for id {} FAILED: {}".format(doc_id, e.pgcode))
        connect_manu.rollback()
    return


def get_all_words():
    '''
    Returns all words as a list
    '''
    # oldwords = list(manu_tironis.words.find({}, {"word": 1}).distinct("word"))
    # words = manu_tironis.all_words.find_one()['words']
    try:
        # so that failes because words_array is empty at the moment
        # manu_cursor.execute('''SELECT words FROM words WHERE id=1''')
        manu_cursor.execute('''SELECT words FROM words_array WHERE id=1''')
        c = manu_cursor.fetchone()
        words = [unicode(word.decode('utf-8')) for word in c[0]]
        return words
    except Exception as e:
        logger.error("get_all_words FAILED: {}".format(str(e)))
        connect_manu.rollback()
        raise e


def get_single_record(doc_id):
    """
    """
    try:
        manu_cursor.execute('''SELECT notepad FROM lace_texts where id=%s''', (doc_id,))
        c = manu_cursor.fetchone()
        record = c[0]
        return unicode(record.decode('utf-8'))
    except Exception, e:
        logger.error("get_single_record FAILED: {}".format(e))
        connect_manu.rollback()


def renumber(final_text):
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

def get_similar_by_trgm(incorrect):
    """
    Using pg_trgm find similar strings
    """
    incorrect = incorrect.encode('utf-8')
    query = "SELECT word, similarity(word, '{}') AS sml FROM words WHERE word % '{}' ORDER BY sml DESC, word LIMIT 8;"
    sql_command = query.format(incorrect, incorrect)
    manu_cursor.execute(sql_command)
    result = manu_cursor.fetchall()
    words_only = [a[0] for a in result]
    dyct = {w: w for w in words_only}
    return dyct
