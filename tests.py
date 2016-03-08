#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import requests
import time
from random import choice

from selenium import webdriver
from pymongo import MongoClient
#from quellen import app, querydistinct

uri = 'mongosoup-shared-db005.mongosoup.de'
port = 30389
mongouser = 'overlord'
mongopass = ''

client = MongoClient()
#client = MongoClient(uri, port)
db = client['quellen']

class QuellenTest(unittest.TestCase):

    def setUp(self):

        self.fox = webdriver.Firefox()
        self.fox.implicitly_wait(9)

    
    def test_mainpage(self):

        self.fox.get('http://127.0.0.1:5000')
        self.fox.implicitly_wait(10)
        assert 'Quellenforschung Database' in self.fox.title
        assert self.fox.find_element_by_id('header').text ==\
        self.fox.find_element_by_tag_name('h1').text == 'Quellenforschung'

        panta = [l.get_attribute("href") for l in self.fox.find_elements_by_tag_name("a")]
        assert "http://127.0.0.1:5000/" in panta #return to mainpage must be in base template!
        assert "http://127.0.0.1:5000/about" in panta
        assert "http://127.0.0.1:5000/library" in panta
        # now assert that click on authors name
        # return his works clickable
        # first get the second nav containing tabs
        # get the tabs from the ul
        # and click each tab to have authors visible
        all_navs = self.fox.find_elements_by_tag_name('nav')
        ul = all_navs[1].find_element_by_tag_name('ul')
        nav_tabs = ul.find_elements_by_tag_name('a')
        for nav_tab in nav_tabs:
            nav_tab.click() # click to make'em visible
            nav_div = self.fox.find_element_by_id('letter-' + nav_tab.text)
            div_authors = nav_div.find_elements_by_tag_name('a')
            for div_author in div_authors:
                div_author.click()
                time.sleep(3)
                self.fox.implicitly_wait(4)#??
                #now the ul with id being the name of author
                #shall contain links to all his works
                authors_name = div_author.text.replace('< ','').replace(' >','')
                ul_with_works = self.fox.find_element_by_id(authors_name)
                works = [a.text.replace('>> ','') for a in ul_with_works.find_elements_by_tag_name('a')]
                #first check if all works are returned from ajax call
                all_works_from_db = list(db.quotes.find({"author_1":authors_name}).distinct("title_1"))
                all_works_from_db.extend(list(db.quotes.find({"author_2":authors_name}).distinct("title_2")))
                all_works_from_db = set(all_works_from_db)
                assert len(works) == len(all_works_from_db)
                assert all(w in works for w in all_works_from_db)
                assert all(w in all_works_from_db for w in works)
                #then click them one by one
                works_links = [a.get_attribute('href') for a in ul_with_works.find_elements_by_tag_name('a')]
                for work_link in works_links:
                    if requests.get(work_link).status_code != 200:
                        print work_link
                    assert requests.get(work_link).status_code < 400


        self.fox.close()


    def test_no_empty_links(self):

        self.fox.get('http://127.0.0.1:5000')
        time.sleep(3)
        links = self.fox.find_elements_by_tag_name("a")
        hrevs = [link.get_attribute("href") for link in links]
        for href in hrevs:
            assert requests.get(href).status_code < 400
            self.fox.get(href)
            sublinks = [sb for sb in self.fox.find_elements_by_tag_name("a")]
            bad_subhrefs =  [k.get_attribute("href") for k in  self.fox.find_elements_by_class_name("titles")]
            subhrefs = [sublink.get_attribute("href") for sublink in sublinks ]
            subhrefs = [s for s in subhrefs if s not in bad_subhrefs]
            for sb in subhrefs:
                print sb
                assert requests.get(sb).status_code < 400
        self.fox.close()


    def test_all_authors_from_query(self):

        #unittest for querydistinct ''
        all_returned = querydistinct({}, {}, "author_1", "author_2")
        all_authors = []
        for a in db.quotes.find({}, {'author_2':1, 'author_1':1, '_id':0}):
            if a['author_2'] not in all_authors:
                all_authors.append(a['author_2'])
            if a['author_2'] not in all_authors:
                all_authors.append(a['author_2'])
        assert all(aut in all_returned for aut in all_authors)
        #assert all unique
        assert len(set(all_returned)) == len(all_returned)


    def test_all_authors_are_on_main(self):

        self.fox.get('http://127.0.0.1:5000')
        time.sleep(3)
        #all_a_href = self.fox.find_elements_by_tag_name('a')
        #ZLE KUCHNIA!
        #get the second nav containing tabs
        #get the tabs from the ul
        # and click each tab to have authors visible
        all_navs = self.fox.find_elements_by_tag_name('nav')
        ul = all_navs[1].find_element_by_tag_name('ul')
        nav_tabs = ul.find_elements_by_tag_name('a')
        all_from_main = []
        for nav_tab in nav_tabs:
            nav_tab.click()#that makes them visible
            nav_div = self.fox.find_element_by_id('letter-'+nav_tab.text)
            div_authors = nav_div.find_elements_by_tag_name('a')
            for div_author in div_authors:
                authors_name = div_author.text.replace('< ','').replace(' >','')
                all_from_main.append(authors_name)
        #all_from_main = [link.get_attribute("href") for  link in all_a_href]
        all_returned = querydistinct({}, {}, "author_1", "author_2")
        #assert all unique
        assert len(set(all_from_main)) == len(all_returned)
        #set_main = set(all_from_main)
        #set_returned = set(all_returned)
        assert len(set(all_from_main).symmetric_difference(set(all_returned))) == 0
        self.fox.close()


    def test_four_oh_four(self):

        nonsense = ['http://127.0.0.1:5000/mcrossft', 'http://127.0.0.1:5000/titles/fd',\
        'http://127.0.0.1:5000/titles/a/b/c/d', 'http://127.0.0.1:5000/authors/s/d/f/g'
         ]
        not_allowed = ['http://127.0.0.1:5000/titles',
        'http://127.0.0.1:5000/flag/', 'http://127.0.0.1:5000/flag/0000' ]
        for junk in nonsense:
            assert requests.get(junk).status_code == 404
        for junk in not_allowed:
            assert requests.get(junk).status_code == 404
        self.fox.close()


    def test_if_custom_404_pops_up(self):
        self.fox.get('http://127.0.0.1:5000/quotes/som3erubbi1sh#')
        #assert it gives you 404 rather then 200
        time.sleep(3)
        assert requests.get('http://127.0.0.1:5000/quotes/som3erubbi1sh#').status_code != 200
        assert self.fox.find_element_by_tag_name('h2').text == "Page Does Not Exist!"
        self.fox.close()



    def test_single_quote(self):

        pasa = list(db.quotes.find())
        for counter in range(0,10):
            one = choice(pasa)
            theulr = 'http://127.0.0.1:5000/quote/' + str(one['_id'])
            assert requests.get(theulr).status_code == 200
            #TODO: check if similar are there - just the number

            #or nothing found if not similar
            #TODO: check if all similar give 200
            raise AssertionError("NOT FINISHED!")
        self.fox.close()


    def test_flagging_single_quote(self):

        one = choice(list(db.quotes.find()))
        theulr = 'http://127.0.0.1:5000/quote/' + str(one['_id'])
        self.fox.get(theulr)#TODO
        the_one = db.quotes.find_one({'_id':one['_id']})
        # number of interesting
        interes = the_one.get('interesting', 0)
        triv = the_one.get('trivial', 0)
        assert isinstance(interes, int)#eh?
        assert isinstance(triv, int)
        #number of trivial
        if interes:
            assert self.fox.find_element_by_id('interesting').text == str(interes)
        else:
            assert self.fox.find_element_by_id('interesting').text == "No"
        if triv:
            assert self.fox.find_element_by_id('trivial').text == str(triv)
        else:
            assert self.fox.find_element_by_id('trivial').text == "No"
        #do the click
        self.fox.find_element_by_name('interesting').click()
        #SHALL WE WAIT?, yes, please
        time.sleep(2)
        #check if +1 returned
        assert self.fox.find_element_by_id('interesting').text ==str(interes+1)
        # check if links inactive
        assert 'disabled' in self.fox.find_element_by_name('interesting').get_attribute("class")
        assert 'disabled' in self.fox.find_element_by_name('trivial').get_attribute("class")
        assert self.fox.find_element_by_name('interesting').text == '< Flagged >'
        assert self.fox.find_element_by_name('trivial').text == '< Flagged >'

        self.fox.close()


    def test_the_library(self):
        authors_titles = db.texts.find({}, {'author':1, 'title':1, '_id':0})
        self.fox.get('http://127.0.0.1:5000/library')
        all_from_the_site = [link.get_attribute("href") for link in fox.find_elements_by_tag_name('a')]
        # that's nonsense, much faster by hand
        #raise AssertionError #TODO


    def test_authors(self):

        ''' thats functional test for ~/authors/ page '''
        #get random record
        random_record = choice(list(db.quotes.find()))
        #get the author_1 and title 1 from the record
        a1 = random_record['author_1']
        t1 = random_record['title_1']
        self.fox.get('http://127.0.0.1:5000/authors/'+ a1+'/'+t1)

        # and now if all the quotes are really on that page
        total = list(db.quotes.find({'author_1':a1, 'title_1':t1}))
        two = list(db.quotes.find({'author_2':a1, 'title_2':t1}))
        total.extend(two)
        all_from_page = [title.text.replace('< ','').replace(' >','') for title in fox.find_elements_by_class_name('titles')]
        all_from_page = [ w.split(', ') for w in all_from_page]
        # print all_from_page
        # find all span class title
        # ie all authors and titles
        for w in total:
            if w['author_1'] == a1:
                assert [w['author_2'], w['title_2']] in all_from_page
            elif w['author_2'] == a1:
                print w['author_1'], w['title_1']
                assert [w['author_1'], w['title_1']] in all_from_page
            else:
                raise AssertionError
        #now check if all quotes are also there
        for title in self.fox.find_elements_by_class_name('titles'):
            title.click()
            # just check if the number is correct by checking the tr tags number
            a2, t2 = title.text.replace('< ','').replace(' >','').split(', ')

            expected_number = len(list(db.quotes.find({'author_1':a1, 'title_1':t1, 'author_2':a2, 'title_2':t2})))
            expected_number += len(list(db.quotes.find({'author_1':a2, 'title_1':t2, 'author_2':a1, 'title_2':t1})))
            assert len(self.fox.find_elements_by_tag_name('tr')) == expected_number
            #if found nothing will raise Selenium's NoSuchElementException
        self.fox.close()


    
    def test_get_quotes(self):

        '' unittest for get_quotes ''
        a1 = 'Septuaginta'
        a2 = 'Clemens Alexandrinus'
        t1 = 'Psalmi'
        t2 = 'Proptrepticus'
        #check first if query_distinct works as expected
        round1 = db.quotes.find({'author_1':a1, 'title_1': t1, 'author_2': a2, 'title_2': t2})
        round2 = db.quotes.find({'author_1':a2, 'title_1': t2, 'author_2': a1, 'title_2': t1})

        all_quotes = round1.extend(round2)
        all_from_query = get_quotes({'author_1':a1, 'title_1': t1, 'author_2': a2, 'title_2': t2})
        assert all_quotes == all_from_query
        #TODO finish


        #now check if all are on website
        self.fox.close()
        raise AssertionError

        get_quotes


    def test_reversing_the_dictionary(self):

        # unittest for reversed_dict '
        test_dict = {}
        test_dict['author_1'] = 'NUMBER_ONE'
        test_dict['author_2'] = 'NUMBER_TWO'
        test_dict['_id'] = '1122vfdbghv7yckjh3vi38vo4'
        reversed_dict = reverse(test_dict)
        assert reversed_dict['author_1'] == 'NUMBER_TWO'
        assert reversed_dict['author_2'] == 'NUMBER_ONE'
        #self.assertRaises(KeyError, reversed_dict['_id'])
        assert reversed_dict['_id'] == '1122vfdbghv7yckjh3vi38vo4'
        assert len(test_dict) == len(reversed_dict)

    
    def tearDown(self):

        self.fox.quit()

if __name__ == '__main__':
    unittest.main()

