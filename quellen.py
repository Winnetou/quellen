import logging
from bson.objectid import ObjectId  # needed to find by _id
from bson.errors import InvalidId
from collections import defaultdict
from datetime import datetime as dt
from flask import Flask, request, jsonify, render_template, abort, Response
from Levenshtein import ratio
from pymongo import MongoClient

from db_access import get_all_words
from join_divide import join_words, divide_word
from mark import mark_save
from update import save_corrected

#logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
logging.basicConfig(filename='db_access_logger.log', level=logging.DEBUG)

# Get an instance of a logger
logger = logging.getLogger(__name__)

app = Flask(__name__)

app.config.update(
    DEBUG=True,
    # DEBUG=False,
)
app.config.from_object(__name__)
app.config.from_envvar("QUELLEN_SETTINGS", silent=True)

con = MongoClient()
mongo = con["quellen"]
tironis = con['manu_tironis']

WORDS = get_all_words()


def is_greek(s):
    ''' Returns True if s is in greek'''
    if any([letter not in "qwertyuioplkjhgfdsazxcvbnm,.& 1234567890'[]()-" for letter in s.lower()]):
        return True
    return False
app.jinja_env.filters['is_greek'] = is_greek


@app.route('/')
def main():
    ''' Main page: displays all authors in a list nested in the nav,
    from a defaultdict mapping letters of alphabet to lists of
    authors beggining with that letter '''
    authors = querydistinct({}, {}, "author_1", "author_2")
    authorsdict = defaultdict(list)
    for author in authors:
        authorsdict[author[0]].append(author)  # first letter of auth's name
    return render_template("home.html", authors=authorsdict)


@app.route('/titles')
def titles():
    ''' Triggered by click on author's name
    on main page nav section returns titles in json '''
    if not request.args:
        abort(404)
    author = request.args.get("author", "", type=unicode)
    titles = querydistinct({"author_1": author},
                           {"author_2": author}, "title_1", "title_2")
    return jsonify(result=titles)


@app.route('/authors/<author>/<title>')
def authors(author, title):
    ''' Returns all the authors for whose works there is at least
    one match for the given work TITLE of a given AUTHOR'''

    querydict = {'$or': [{"author_1": author, "title_1": title},
                         {"author_2": author, "title_2": title}]}
    authortitles = mongo.quotes.aggregate([{'$match': querydict},
                                           {"$group": {"_id": {"title_2": "$title_2", "author_2": "$author_2",
                                                               "title_1": "$title_1", "author_1": "$author_1"}}}])
    authortitles = [d["_id"] for d in authortitles["result"]]
    # get just the dicts
    if not authortitles:
        abort(404)
    authortitles = map(lambda x:
                       reverse(x) if x['author_2'] == author else x, authortitles)
    # reverse if author_1 is author_2
    authortitles.sort()  # ExpliZit ist besser als implizit!
    return render_template("authors.html", authorstitles=authortitles)


@app.route('/download/<author>/<title>')
def download(author, title):
    ''' return raw text file with results '''
    ffile = to_file(author, title)
    return Response(ffile, mimetype='text/plain')


@app.route('/quotes')
def quotes():
    '''Returns quotes for author_1 and his work title_1
    and author_2 and his title_2'''

    author_1 = request.args.get("author_1", "", type=unicode)
    author_2 = request.args.get("author_2", "", type=unicode)
    title_1 = request.args.get("title_1", "", type=unicode)
    title_2 = request.args.get("title_2", "", type=unicode)
    querydic = {'author_1': author_1, 'title_1': title_1,
                'author_2': author_2, 'title_2': title_2}
    quotes = get_quotes(querydic)
    return render_template("quotespartial.html", quotes=quotes)


@app.route('/quote/<object_id>')
def quote(object_id):
    ''' returns single item plus a number of similar with regex search'''

    try:
        id_number = ObjectId(object_id)
    except InvalidId:
        abort(404)
    quote = mongo.quotes.find_one({"_id": id_number})
    if quote is None:
        abort(404)
    similar_query = {"$or": [{"quote_1_unicode": quote["quote_1_unicode"]},
                             {"quote_2_unicode": quote["quote_2_unicode"]},
                             {"quote_1_unicode": {"$regex": quote["quote_1_unicode"]}},
                             {"quote_2_unicode": {"$regex": quote["quote_2_unicode"]}}],
                     "_id": {"$ne": ObjectId(object_id)}}
    similar = mongo.quotes.find(similar_query)
    # TODO: SORTING! find some way to introduce order
    return render_template("quote.html", quote=quote, similar=similar)


@app.route('/flag')
def flag():
    ''' +1 to is_interesting or is_trivial via ajax, returns updated value'''

    value = request.args.get("value", "", type=unicode)
    object_id = request.args.get("object_id", "", type=unicode)
    try:
        id_number = ObjectId(object_id)
    except InvalidId:
        return None
    mongo.quotes.update({"_id": id_number}, {"$inc": {value: 1}}, safe=True)
    retrn_value = mongo.quotes.find_one({"_id": id_number}, {value: 1, "_id": 0})
    return jsonify(result=retrn_value[value])


@app.route('/library')
def library():
    ''' Return list of authors whose works we have'''
    authors = list(mongo.texts.find({}, {"author": 1, "title": 1}))
    return render_template("library.html", authors=authors)


@app.route('/text/<author>/<title>')
def text(author, title):
    ''' Returns single text'''
    text = mongo.texts.find_one({"author": author, "title": title})
    if not text:
        abort(404)
    return render_template("text.html", text=text)


@app.route('/about')
def about():
    '''About page: returns few figures '''

    data = {}
    data['item_number'] = mongo.quotes.find().count()
    data['author_number'] = len(querydistinct({}, {}, "author_1", "author_2"))
    # same as above: cant be done via map reduce,
    # since return value from map reduce cant be an array!
    data["works_number"] = len(querydistinct({}, {}, "title_1", "title_2"))
    return render_template("about.html", q=data)

# MANU TIRONIS SECTION


@app.route('/scriptorium')
def scriptorium():
    '''scriptorium page: returns titles of
    works being transcribed'''
    # TODO - mve scriptorium and tiro to one link
    titles = list(tironis.lace_texts.find({}, {'title': 1}).distinct('title'))
    return render_template("scriptorium.html", titles=titles)


@app.route('/tiro/<title>/<int:pagenumber>')
def tiro(title, pagenumber):
    # print "{}::{}".format(title, pagenumber)
    needed_vals = {"_id": 1, "title": 1, "pagenumber": 1, "notepad": 1, "image_url": 1}
    # TODO - next page and prev page
    if pagenumber == 0:
        page = tironis.lace_texts.find(
            {"title": title}, needed_vals).sort("pagenumber",).limit(1)[0]

    else:
        page = tironis.lace_texts.find_one(
            {"title": title, "pagenumber": pagenumber},
            needed_vals)
    if not page:
        abort(404)
    if tironis.lace_texts.find_one(
            {"title": title, "pagenumber": page["pagenumber"] - 1}):
        page["next_page"] = page["pagenumber"] - 1
    if tironis.lace_texts.find_one(
            {"title": title, "pagenumber": page["pagenumber"] + 1}):
        page["prev_page"] = page["pagenumber"] + 1
    # return render_template("tiro.html", page=page)
    return render_template("tiro2.html", page=page)

# AJAX SECTION


@app.route("/suggest")
def suggest():
    """ Ajax - receive incorrect form, suggest correction"""
    incorrect = unicode(request.args.get('word'))
    vals = {}
    for correct in WORDS:
        ratjo = ratio(incorrect, correct)
        if ratjo > 0.75:
            vals[correct] = ratjo
    #import pdb; pdb.set_trace()
    if len(vals) > 5:
        ratios = [v for v in reversed(sorted(vals.values()))][:5]

        suggestions = {c: c for c, v in vals.iteritems() if v in ratios}
    else:
        suggestions = {c: c for c, v in vals.iteritems()}
    return jsonify(suggestions)


@app.route("/update", methods=['POST'])
def update():
    """
    here we deal with 2 user journeys:
    1. User clicked 'this word is correct'
    2. User clicked 'this word is NOT correct' AND picks suggested word
    3. User clicked 'this word is NOT correct' AND corrected word manually
    """
    correct_word = request.form.get('correct_form')
    page_id = request.form.get('page_id')
    word_id = request.form.get('word_id')
    # is_hand_corrected = request.form.get('word_id')
    # mvp shows only suggestions - no chance to edit manually
    is_hand_corrected = False
    mess = "Received:{} {}, {}".format(correct_word.encode('utf-8'), page_id, word_id)
    logger.info(mess)
    save_corrected(correct_word, page_id, word_id, is_hand_corrected)

    return jsonify(result={'status': "OK"})


@app.route("/divideorjoin", methods=['POST'])
def divideorjoin():
    """
    Two user stories:
    1. User clicks: 'split that word'
    2. User clicks: 'join that word with next one'
    Flag 'action' will tell you which
    """

    dikt = {
        'page_id': request.form.get('page_id'),
        'word_id': request.form.get('word_id'),
        'word': request.form.get('word')
    }
    mess = "Received:{} {}, {}".format(dikt['page_id'], dikt['word_id'], dikt['word'])
    logger.info(mess)
    if request.args.get('action') == 'divide':
        divide_word(dikt)
    elif request.args.get('action') == 'join':
        # for mvp, we join word with the next one only
        join_words(dikt)

    return jsonify(result={'status': "OK"})


@app.route("/mark", methods=['POST'])
def mark():
    '''
    Two user stories:
    1. User clicks: 'this word is correct' - we set corr to 1
    2. User clicks: 'this word is not correct' - we set corr to 0
    Flag 'action' will tell you which way to go
    '''
    mark = request.form.get('mark')
    doc_id = request.form.get('page_id')
    word_id = request.form.get('word_id')
    # logger.info("{} - `mark` got :: args:{}-{}-{}".format(dt.now(), mark, doc_id, word_id))
    print "{} - `mark` got :: args:{}-{}-{}".format(dt.now(), mark, doc_id, word_id)
    try:
        mark_save(mark, doc_id, word_id)
        # print "{} - Success in `mark` :: args:{}-{}-{}".format(dt.now(), mark, doc_id, word_id)
        logger.info(
            "{} - Success in `mark` :: args:{}-{}-{}".format(dt.now(), mark, doc_id, word_id))
        return jsonify(result={'status': "OK"})
    except Exception as err:
        # print "{} -Error in `mark` :: args:{}-{}-{}".format(dt.now(), mark, doc_id, word_id)
        logger.error(
            "{} -Error {} in `mark` :: args:{}-{}-{}".format(err, dt.now(), mark, doc_id, word_id))
        return jsonify(result={'status': "ERROR"})


# END MANU TIRONIS


@app.errorhandler(404)
def page_not_found(error):
    ''' 404 '''

    return render_template("404.html"), 404


# HELPERS # SECTION ### MOVE ME TO SEPARATE NAMEPSACE


def querydistinct(querydict_1, querydict_2, distinct_value_1, distinct_value_2):
    ''' Returns list of distinct authors or titles/the fastest solution'''

    x = set(mongo.quotes.find(querydict_1).distinct(distinct_value_1))
    y = set(mongo.quotes.find(querydict_2).distinct(distinct_value_2))
    x.update(y)
    return sorted(x)


def get_quotes(querydict):
    '''Helper - to get the dirty job of db queries out of the view'''

    limit_query = {'_id': 1, 'author_1': 1, 'title_1': 1, 'quote_1_unicode': 1,
                   'locum_1': 1, 'author_2': 1, 'title_2': 1, 'quote_2_unicode': 1, 'locum_2': 1}
    fullquery = {'$or': [querydict, reverse(querydict)]}
    quotes = list(mongo.quotes.find(fullquery, limit_query))
    quotes = map(lambda x:
                 reverse(x) if x['author_1'] != querydict['author_1'] else x, quotes)
    # reverse if author_1 is author_2
    return quotes


def to_file(author, title):
    ''' Returns quotes in a raw string format'''

    querydic = {'author_1': author, 'title_1': title}
    quotes = get_quotes(querydic)
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


def reverse(dictionary):
    ''' Reverses the order of the document:
    author_1 to author_2 etc by swapping the keys. Ugly but necessary '''

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


if __name__ == '__main__':
    app.run()
