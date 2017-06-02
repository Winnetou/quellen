import psycopg2
import psycopg2.extras

connect_quellen = psycopg2.connect("dbname=quellen user=quellen")
quellen_cursor = connect_quellen.cursor()
dict_cur = connect_quellen.cursor(cursor_factory=psycopg2.extras.DictCursor)


def psql_get_distinct_authors():
    """
    Gets a list of unique authors
    Called by :func ~`quellen.main`
    :rtype list
    """
    result = []
    try:
        # UNION
        quellen_cursor.execute("""SELECT DISTINCT author_2 FROM quotes""")
        result = quellen_cursor.fetchall()
        list_authors = [w[0] for w in result]
        quellen_cursor.execute("""SELECT DISTINCT author_1 FROM quotes""")
        second_result = quellen_cursor.fetchall()
        list_authors_2 = [w[0] for w in second_result]
        final_result = list_authors + list_authors_2
        final_result = [p for p in set(final_result)]
        return final_result
    except:
        connect_quellen.rollback()
    return []


def psql_get_authors_titles(author):
    """Get all titles from given author

    :return list
    :rtype list
    """
    try:
        quellen_cursor.execute(
            '''SELECT DISTINCT title_1 FROM quotes WHERE author_1 = %s''', (author,))
        result = quellen_cursor.fetchall()
        presult = [item for sublist in result for item in sublist]
        quellen_cursor.execute(
            '''SELECT DISTINCT title_2 FROM quotes WHERE author_2 = %s''', (author,))
        second_result = quellen_cursor.fetchall()
        sec_presult = [item for sublist in second_result for item in sublist]
        fin_result = [i for i in set(presult + sec_presult)]
        return fin_result
    except:
        print "DUPA"
        connect_quellen.rollback()


def psql_get_authors_and_titles_for_one_title(author, title):
    """For a given author and title
    get all title/author pairs
    Called by :func ~`quellen.authors`
    :return list of dicts
    every dicts must have four keys:
    author_1, title_1, author_2, title_2
    :rtype list
    """
    author, title = unicode(author), unicode(title)
    try:
        qury = '''SELECT DISTINCT author_1, title_1, author_2, title_2 FROM quotes WHERE (author_2 = %s AND title_2 = %s) OR (author_1 = %s AND title_1 = %s)'''
        dict_cur.execute(qury, (author, title, author, title))
        fin_result = dict_cur.fetchall()

        for dyct in fin_result:
            for key, value in dyct.iteritems():
                dyct[key] = unicode(value.decode('utf-8'))
        return fin_result
    except:
        print "DUPA"
        connect_quellen.rollback()


def psql_get_quotes_to_file(author, title):
    '''
    Called by :func ~`quellen.to_file`
    params author, title,
    '''
    fullquery = '''SELECT id, author_1, title_1, quote_1_unicode, locum_1, author_2, title_2, quote_2_unicode, locum_2 FROM quotes WHERE author_1=%s AND title_1=%s'''
    reversed_query = '''SELECT id, author_1, title_1, quote_1_unicode, locum_1, author_2, title_2, quote_2_unicode, locum_2 FROM quotes WHERE author_2=%s AND title_2=%s'''
    args = [author, title]
    dict_cur.execute(fullquery, args)
    # at that point we shall have dicts
    list_of_quotes_1 = reversed_query.fetchall()
    dict_cur.execute(reversed_query, args)
    list_of_quotes_2 = dict_cur.fetchall()
    quotes = list_of_quotes_1 + list_of_quotes_2
    quotes = map(lambda x:
                 reverse(x) if x['author_1'] != 'author_1' else x, quotes)
    # reverse if author_1 is author_2
    return quotes


def psql_get_quotes(author_1, title_1, author_2, title_2):
    '''
    Called by :func ~`quellen.quotes` and
    by :func ~`quellen.to_file`
    Uses dict as a param, because that way it serves
    two different purposes in these two functions
    :param dykt - dict with keys author_1, title_1, author_2, title_2
    or just author_1, title_1,
    '''
    args = [author_1, title_1, author_2, title_2]
    fullquery = '''SELECT id, author_1, title_1, quote_1_unicode, locum_1, author_2, title_2, quote_2_unicode, locum_2 FROM quotes WHERE author_1=%s AND title_1=%s AND author_2=%s AND title_2=%s'''
    reversed_query = '''SELECT id, author_1, title_1, quote_1_unicode, locum_1, author_2, title_2, quote_2_unicode, locum_2 FROM quotes WHERE author_2=%s AND title_2=%s AND author_1=%s AND title_1=%s'''
    #! single_query = '''SELECT DISTINCT id, author_1, title_1, quote_1_unicode, locum_1, author_2, title_2, quote_2_unicode, locum_2 FROM quotes WHERE (author_1=%s AND title_1=%s AND author_2=%s AND title_2=%s) OR (author_2=%s AND title_2=%s AND author_1=%s AND title_1=%s)'''

    dict_cur.execute(fullquery, args)
    # at that point we shall have dicts
    list_of_quotes_1 = dict_cur.fetchall()
    dict_cur.execute(reversed_query, args)
    list_of_quotes_2 = dict_cur.fetchall()
    quotes = list_of_quotes_1 + list_of_quotes_2
    #!args = [author_1, title_1, author_2, title_2, author_1, title_1, author_2, title_2]
    #!dict_cur.execute(single_query, args)
    #!quotes = dict_cur.fetchall()
    for element in quotes:
        element['quote_1_unicode'] = unicode(element['quote_1_unicode'].decode('utf-8'))
        element['quote_2_unicode'] = unicode(element['quote_2_unicode'].decode('utf-8'))
    quotes = map(lambda x:
                 reverse(x) if x['author_1'] != 'author_1' else x, quotes)
    # reverse if author_1 is author_2
    return quotes


def get_single_quote(id_number):
    """
    called by :func ~`quellen.quote`
    """
    try:
        fullquery = "SELECT id, author_1, title_1, quote_1_unicode, quote_1_betacode, locum_1, author_2,title_2, quote_2_unicode, locum_2 FROM quotes WHERE id=%s"
        dict_cur.execute(fullquery, (id_number,))
        quote = dict_cur.fetchone()
        non_unicode = quote['quote_1_betacode']
        quote['quote_1_unicode'] = unicode(quote['quote_1_unicode'].decode('utf-8'))
        quote['quote_2_unicode'] = unicode(quote['quote_2_unicode'].decode('utf-8'))
        if quote is None:
            return [None, None]
        # http://stackoverflow.com/questions/11249635/finding-similar-strings-with-postgresql-quickly
        # trgrm_query = '''SELECT quote_1_betacode, quote_1_betacode <-> 'KAI TA' AS dist FROM QUOTES ORDER BY dist LIMIT 10;'''
        similar_query = '''SELECT id, author_1, title_1, quote_1_unicode, locum_1, author_2, title_2,  quote_2_unicode, locum_2 FROM quotes WHERE similarity(quote_1_betacode, %s) > 0.80 ORDER BY author_1 LIMIT 40;'''
        #trgrm_query = '''SELECT id, author_1, title_1, quote_1_unicode, locum_1, author_2, quote_2_unicode, locum_2  FROM QUOTES WHERE quote_1_betacode <-> %s >0.99 LIMIT 40;'''
        regexargs = (non_unicode,)
        dict_cur.execute(similar_query, regexargs)
        similar = dict_cur.fetchall()
        for element in similar:
            element['quote_1_unicode'] = unicode(element['quote_1_unicode'].decode('utf-8'))
            element['quote_2_unicode'] = unicode(element['quote_2_unicode'].decode('utf-8'))
        return quote, similar
    except Exception, e:
        connect_quellen.rollback()
        print "WRONG WRONG GET SINGLE QUOTE"
        raise e


def psql_get_library_list():
    """
    Return unique vals author:title
    rtype: list of dicts, hm?
    """
    fullquery = '''SELECT DISTINCT author, title FROM texts'''
    dict_cur.execute(fullquery)
    authors = dict_cur.fetchall()
    return authors


def psql_get_library_text(author, title):
    """
    """
    fullquery = '''SELECT * FROM texts WHERE author=%s AND title=%s'''
    dict_cur.execute(fullquery, (author, title))
    text = dict_cur.fetchone()
    text['text'] = unicode(text['text'].decode('utf-8'))
    return text


def psql_get_about_data():
    """
    Few numbers to be displayed on `about` page
    """
    data = {'author_number': 276, 'item_number': 442080, 'works_number': 843}
    # quellen_cursor.execute('''SELECT COUNT(id) from quotes''')
    # result = quellen_cursor.fetchone()
    # data['item_number'] = int(result[0])
    # quellen_cursor.execute('''SELECT COUNT(DISTINCT author_1) from quotes''')
    # result = quellen_cursor.fetchone()
    # data['author_number'] = int(result[0])
    # quellen_cursor.execute('''SELECT COUNT(DISTINCT title_1) from quotes''')
    # result = quellen_cursor.fetchone()
    # data["works_number"] = int(result[0])
    return data


# Helpers

def reverse(dictionary):
    '''
    Reverses the order of the document:
    author_1 to author_2 etc by swapping the keys.
    Ugly but necessary '''

    new_dictionary = {}
    for key in dictionary.iterkeys():
        if "1" in key:
            new_key = key.replace("1", "2")
            new_dictionary[new_key] = dictionary[key]
        elif "2" in key:
            new_key = key.replace("2", "1")
            new_dictionary[new_key] = dictionary[key]
        else:
            new_dictionary[key] = dictionary[key]
            # important - not to lose the _id!
    return new_dictionary


def psql_to_file(author, title):
    ''' Returns quotes in a raw string format'''

    querydic = {'author_1': author, 'title_1': title}
    quotes = psql_get_quotes_to_file(querydic)
    result = "Results for " + quotes[0]["author_1"]\
        + ", " + quotes[0]["title_1"] + "\n"
    result += " - " * 30 + "\n"
    for record in quotes:
        result += record["author_1"] + ", "
        result += record["title_1"] + ": "
        result += record["quote_1_unicode"]
        result += "\n"
        result += record["author_2"] + ", "
        result += record["title_2"] + ": "
        result += record["quote_2_unicode"]
        result += "\n"
        result += " - " * 30 + "\n"
    return result
