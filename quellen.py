#!/usr/bin/python
# -*- coding: utf-8 -*-
from  pymongo import Connection
from collections import defaultdict
import os

from flask import Flask, request, jsonify, session, render_template, abort, Response


from bson.objectid import ObjectId # needed to find by _id
from bson.errors import InvalidId

app = Flask(__name__)

app.config.update(
DEBUG=True,
)
app.config.from_object(__name__)
app.config.from_envvar("QUELLEN_SETTINGS", silent=True)

# establish pymongo Connection
con = Connection()
mongo = con["quellen"]
'''
TO JEST ZLE TO NIE TAK SIE ROBI
commented out since never used
def is_greek(elem):
    if any([letter in "νΘηβαῖοςΠάλχμὲἀπσἀτὸἘρεἰΤρξίδΣίἈλέἈόἈῖκἄὶάἀῶἰγωήἰτὰΦό" for letter in elem]):
        return True
    return False


# add custom filter for recognizing greek text to change the styles esp fonts
app.jinja_env.filters['is_greek'] = is_greek
'''
#JEST PROBLEM TERAZ TAKI ZE GRECKIE TYTULY NIE IDA AJAXEM KIEDY JUZ PROSISZ O KONKRETNY ZESTAW CYTATOW

@app.route('/')
def main():
	
    '''main page: displays all authors in a list nested in the nav'''
    authors = querydistinct({},{}, "author_1","author_2")
    slownik =defaultdict(list)# maps letters of alphabet to authors names
    for author in authors: 
        slownik[author[0]].append(author)  #  the value = list of authors whose names begin with the same letter, the key = that letter
    
    return render_template("home.html", authors=slownik)


@app.route('/titles')
def titles():

    '''this is triggered by click on author's name on main page nav section returns titles in json'''
    author = request.args.get("author", "", type=str)
    titles = querydistinct({"author_1":author},{"author_2":author}, "title_1", "title_2")
    return jsonify(result=titles) 


@app.route('/authors/<author>/<title>')
def authors(author, title):
	
    ''' that returns all the authors for whose works there is at least on match for the given work TITLE of a given AUTHOR '''
    querydict={'$or':[{"author_1":author,"title_1":title},{"author_2":author,"title_2":title} ]}
    authortitles = mongo.quotes.aggregate([{'$match' : querydict }, { "$group" : {"_id":{"title_2":"$title_2","author_2":"$author_2","title_1":"$title_1","author_1":"$author_1",} }} ])["result"]
    authortitles = [d["_id"] for d in authortitles] # get just the dicts
    authortitles = map(lambda x: reverse(x) if x['author_2'] == author else x, authortitles) #reverse if author_1 is author_2
    #TODO {PRZETESTOWAC}  sprawdzic czy nie bedzie szybciej jesli zrobimy to z pomoca querydistinct
    authortitles.sort()# ExpliZit ist besser als implizit!

    return render_template("authors.html", authorstitles=authortitles) 


@app.route('/download/<author>/<title>')
def download(author, title):
    
    ffile = to_file(author, title) 
    
    return Response(ffile, mimetype='text/plain')


@app.route('/quotes')
def quotes():

    ra= request.args
    author_1, author_2, title_1, title_2 = ra.get("author_1", "", type=str), ra.get("author_2", "", type=str), ra.get("title_1", "", type=str), ra.get("title_2", "", type=str) 
    d = {'author_1':author_1, 'title_1':title_1, 'author_2':author_2,'title_2':title_2 }
    quotes = get_quotes(d)

    return render_template("quotespartial.html",quotes=quotes)


@app.route('/quote/<object_id>')
def quote(object_id):
    
    try:
        id_number = ObjectId(object_id)
    except InvalidId:
        abort(404)	
    quote =mongo.quotes.find_one({"_id":id_number})
    similar_query = {"$or":[{"quote_1_unicode":quote["quote_1_unicode"] },{"quote_2_unicode":quote["quote_2_unicode"]},
    {"quote_1_unicode":{"$regex":quote["quote_1_unicode"] } },{"quote_2_unicode":{"$regex":quote["quote_2_unicode"] } }],
     "_id":{"$ne":ObjectId(object_id)}}
    similar = mongo.quotes.find(similar_query)
    
    # SORTOWANIE
    
    return render_template("quote.html", quote=quote, similar=similar)


@app.route('/flag')
def flag(): 

    value, object_id = request.args.get("value", "", type=str), request.args.get("object_id", "", type=str)
    try:
        id_number = ObjectId(object_id)
    except InvalidId:
        return None
    mongo.quotes.update({"_id":id_number},{"$inc":{value:1}}, safe=True)
    retrn_value =  mongo.quotes.find_one({"_id":id_number},{value:1, "_id":0})
    return jsonify(result=retrn_value[value]) 


@app.route('/library')
def library():
    #authors = mongo.texts.find({},{"author":1,"title":1})
    #authors = [{"author":"Marinus","title":"Vita Procli"} ,{ "author":"Demetrius","title":"De Bospori navigatio" }] 
    #authors = [doc  for doc  in mongo.texts.find({},{"author":1,"title":1})]
    authors = list(mongo.texts.find({},{"author":1,"title":1}))
    
    return render_template("library.html", authors=authors)


@app.route('/text/<author>/<title>')
def text(author, title):
    
    text = mongo.texts.find_one({"author":author,"title":title}) 
    return render_template("text.html", text=text)


@app.route('/about')
def about():
    
    q = {"item_number":mongo.quotes.find().count() }
    #can't nbe done by DB.COLLECTION.GROUP(KEY, REDUCE) 
    #a1 =  set([s for s in mongo.quotes.find().distinct("author_1")])
    #a2 =  set([s for s in mongo.quotes.find().distinct("author_2")])
    q['author_number'] = len(querydistinct({},{}, "author_1","author_2")) # same as above:cant be done via map reduce, since return value from map reduce cant be an array!
    #w1 =   set([a for a in mongo.quotes.find().distinct("title_1")])
    #w2 =  set([c for c in mongo.quotes.find().distinct("title_2")])
    q["works_number"] = len(querydistinct({},{}, "title_1","title_2"))

    return render_template("about.html", q=q)
    

@app.errorhandler(404)
def page_not_found(error):
    
    return render_template("404.html"), 404


#############################################################################################



def querydistinct(querydict_1,querydict_2, distinct_value_1, distinct_value_2):
    
    # returns list of distinct authors or titles
    #should be done in one quoery but in mongo its hopelessly complicated & slow
    #the fastest solution - incredible yet true - is this:
    x = set (mongo.quotes.find(querydict_1).distinct(distinct_value_1))
    y = set (mongo.quotes.find(querydict_2).distinct(distinct_value_2))
    x.update(y)
     
    return sorted(x)

def get_quotes(querydict):
    
    limit_query ={'_id':1,'author_1':1, 'title_1':1,'quote_1_unicode':1, 'locum_1':1, 'author_2':1, 'title_2':1,'quote_2_unicode':1, 'locum_2':1}
    fullquery= {'$or':[querydict, reverse(querydict)]}
    #quotes = [q for  q in mongo.quotes.find(fullquery, limit_query)]
    quotes = list(mongo.quotes.find(fullquery, limit_query))
    
    quotes = map(lambda x: reverse(x) if x['author_1'] != querydict['author_1'] else x, quotes) #reverse if author_1 is author_2
    #sort BY LoCUM
    
    return quotes


def to_file(author, title):

    d= {'author_1':author, 'title_1':title}
    quotes = get_quotes(d)
    result = "Results for " +quotes[0]["author_1"]+", "+ quotes[0]["title_1"] + "\n"
    result += " - "*30+"\n"
    for record in quotes:
        result += record["author_1"]+", "
        result += record["title_1"]+": "
        result += record["quote_1_unicode"]
        result += "\n"   
        result += record["author_2"]+", "
        result += record["title_2"]+ ": "
        result += record["quote_2_unicode"]
        result += "\n"
        result +=  " - "*30+"\n"
    return result


def reverse(dictionary):
	
    '''this reverses the order of the document: author_1 to author_2 etc by swapping the keys // ugly but necessary'''
    new_dictionary ={}
    for key in dictionary.iterkeys():
        if "1" in key:
            new_key = key.replace("1","2")
            new_dictionary[new_key] = dictionary[key]
        elif "2" in key:
            new_key = key.replace("2","1")
            new_dictionary[new_key] = dictionary[key]
        else: 
            new_dictionary[key] = dictionary[key] #important - not to lose _id!
    return new_dictionary

# poletko do testow
# trzeba napisac map-reduce



if __name__ == '__main__':
    app.run()