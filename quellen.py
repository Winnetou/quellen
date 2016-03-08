#!/usr/bin/python
# -*- coding: utf-8 -*-

from collections import defaultdict

from bson.objectid import ObjectId  # needed to find by _id
from bson.errors import InvalidId

from flask import Flask, request, jsonify, render_template, abort, Response

from pymongo import MongoClient

from Levenshtein import ratio

from backend import get_all_words, save_and_correct, save_corrected

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
    needed_vals = {"title": 1, "pagenumber": 1, "notepad": 1, "image_url": 1}
    # TODO - next page and prev page
    if pagenumber == 0:
        page = tironis.lace_texts.find({"title": title}, needed_vals).sort("pagenumber",).limit(1)[0]

    else:
        page = tironis.lace_texts.find_one(
            {"title": title, "pagenumber": pagenumber},
            needed_vals)
    if not page:
        abort(404)
    if tironis.lace_texts.find_one(
            {"title": title, "pagenumber": page["pagenumber"]-1}):
        page["next_page"] = page["pagenumber"]-1
    if tironis.lace_texts.find_one(
            {"title": title, "pagenumber": page["pagenumber"]+1}):
        page["prev_page"] = page["pagenumber"]+1
    return render_template("tiro.html", page=page)

# AJAX SECTION


@app.route("/suggest")
def suggest():
    # Ajax - receive incorrect form, suggest correction''
    incorrect = unicode(request.args.get('word'))
    # WORDS = list(tironis.words.find({}, {"word": 1}))
    suggestions = {correct: correct for correct in WORDS if ratio(incorrect, correct) > 0.65}
    return jsonify(suggestions)

'''
# good idea:
# in jquery we have one big form to be sent by GET to flask backend
# the form doesn't change, the only thing that changes is url
# of the HTTP endpoint
'''
@app.route("/savecorrect")
def savecorrect():
    """
    User clicked 'this word is correct'
    Now we want to save the word to db
    and check all docs for that word
    and set them to correct=1
    """
    correct_word = request.args.get('word')
    save_and_correct(correct_word)
    return


@app.route("/savesuggested")
def savesuggested():
    """
    User takes suggested word
    Now we want to save the word to db
    and check all docs for that word
    and set them to correct=1
    """
    suggested_word = request.args.get('word')
    text = request.args.get('text')
    node_id = request.args.get('node_id')
    semantic = request.args.get('semantic')
    save_corrected(suggested_word, text, node_id, semantic)
    return

@app.route("/savecorrected")
def savecorrected():
    """
    User corrects the word
    Now we want to save the word to db
    and check all docs for that word
    and set them to correct=1
    """
    corrected_word = request.args.get('word')
    # we don't need the author, unlikely it is that
    # we will ever have two texts with the same title
    text = request.args.get('text')
    node_id = request.args.get('node_id')
    page_number = request.args.get('page_number')
    semantic = request.args.get('semantic')
    save_corrected(corrected_word, text, page_number, node_id, semantic)
    return


# END MANU TIRONIS


@app.errorhandler(404)
def page_not_found(error):
    ''' 404 '''

    return render_template("404.html"), 404


### HELPERS # SECTION ###


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
