# -*- coding: utf-8 -*-
import re
import psql_manu_tironis
# from Levenshtein import ratio
def GREEK_ALPHABET():
    x = [u'\u0386', u'\u0388', u'\u0389', u'\u0390', u'\u0391', u'\u0392', u'\u0393', u'\u0394', u'\u0395', u'\u0396', u'\u0397', u'\u0398', u'\u0399', u'\u039a', u'\u039b', u'\u039c', u'\u039d', u'\u039e', u'\u039f', u'\u03a0', u'\u03a1', u'\u03a3', u'\u03a4', u'\u03a5', u'\u03a6', u'\u03a7', u'\u03a8', u'\u03a9', u'\u03ac', u'\u03ad', u'\u03ae', u'\u03af', u'\u03b0', u'\u03b1', u'\u03b2', u'\u03b3', u'\u03b4', u'\u03b5', u'\u03b6', u'\u03b7', u'\u03b8', u'\u03b9', u'\u03ba', u'\u03bb', u'\u03bc', u'\u03bd', u'\u03be', u'\u03bf', u'\u03c0', u'\u03c1', u'\u03c2', u'\u03c3', u'\u03c4', u'\u03c5', u'\u03c6', u'\u03c7', u'\u03c8', u'\u03c9', u'\u03ca', u'\u03cb', u'\u03cc', u'\u03cd', u'\u03ce', u'\u1f00', u'\u1f01', u'\u1f02', u'\u1f03', u'\u1f04', u'\u1f05', u'\u1f06', u'\u1f07', u'\u1f08', u'\u1f09', u'\u1f0c', u'\u1f0e', u'\u1f10', u'\u1f11', u'\u1f13', u'\u1f14', u'\u1f15', u'\u1f18', u'\u1f19', u'\u1f1d', u'\u1f20', u'\u1f21', u'\u1f22', u'\u1f23', u'\u1f24', u'\u1f25', u'\u1f26', u'\u1f27', u'\u1f28', u'\u1f29', u'\u1f30', u'\u1f31', u'\u1f33', u'\u1f34', u'\u1f35', u'\u1f36', u'\u1f37', u'\u1f38', u'\u1f39', u'\u1f40', u'\u1f41', u'\u1f42', u'\u1f43', u'\u1f44', u'\u1f45', u'\u1f48', u'\u1f4f', u'\u1f50', u'\u1f51', u'\u1f53', u'\u1f54', u'\u1f55', u'\u1f56', u'\u1f57', u'\u1f59', u'\u1f60', u'\u1f61', u'\u1f62', u'\u1f63', u'\u1f64', u'\u1f65', u'\u1f66', u'\u1f67', u'\u1f68', u'\u1f70', u'\u1f71', u'\u1f72', u'\u1f73', u'\u1f74', u'\u1f75', u'\u1f76', u'\u1f77', u'\u1f78', u'\u1f79', u'\u1f7a', u'\u1f7b', u'\u1f7c', u'\u1f7d', u'\u1f84', u'\u1f85', u'\u1f86', u'\u1f90', u'\u1f91', u'\u1f94', u'\u1f96', u'\u1f97', u'\u1fa0', u'\u1fa4', u'\u1fa6', u'\u1fa7', u'\u1fb3', u'\u1fb4', u'\u1fb6', u'\u1fb7', u'\u1fbd', u'\u1fbf', u'\u1fc2', u'\u1fc3', u'\u1fc4', u'\u1fc6', u'\u1fc7', u'\u1fd2', u'\u1fd3', u'\u1fd6', u'\u1fe2', u'\u1fe3', u'\u1fe4', u'\u1fe5', u'\u1fe6', u'\u1fec', u'\u1ff3', u'\u1ff4', u'\u1ff6', u'\u1ff7', u'\u2018', u'\u2019', u'\u2219']
    return x

LATIN_CHARSET = list(('''"1234567890!@#$%^&*()_-=+qQwWeErRtTyYuUiIoOpPaAsSdDfFgGhH
    jJkKlLmMnNbBvVcCxXzZ,<.>/?;:;'''))
# £™¢§§ˆ¶•ªªº–≠¡`

def translate_latin_chars(incorrect):
    dykt = {
        u'a': u'\u03b1',  # alpha
        # u'b':,
        # u'c':,
        u'd': u'\u03b4',  # delta
        u'e': u'\u03b5',  # epsilon
        # u'f':,
        u'g': u'\u03c2',  # final sigma
        # u'h':,
        u'i': u'\u03b9',  # iota
        # u'j':,
        # u'k':,
        # u'l':,
        # u'm':,
        u'n': u'\u03c0',  # pi
        u'o': u'\u03c3',  # sigma or omikron
        # u'p':,
        u'q': u'\u03c1',  # rho
        u'r': u'\u03b7',  # eta
        # u's':,
        u't': u'\u03b9',
        u'u': u'\u03b1',  # alpha,
        u'v': u'\u03bd',  # nu
        u'w': u'\u03c9',  # omega
        u'x': u'\u03ba',  # kappa
        u'y': u'\u03b3',  # gamma
        # u'z':,
        # u'A':,
        # u'B':,
        # u'C':,
        # u'D':,
        # u'E':,
        # u'F':,
        # u'G':,
        # u'H':,
        # u'I':,
        # u'J':,
        # u'K':,
        u'L': u'\u03af',  # iota with acutus
        # u'M':,
        # u'N':,
        # u'O':,
        # u'P':,
        u'Q': u'\u03c1',  # rho
        # u'R':,
        u'S': u'\u03b4',  # delta
        u'T': u'\u03c4',  # small tau
        # u'U':,
        # u'V':,
        # u'W':,
        u'X': u'\u03bb',  # small lambda
        # u'Y':,
        # u'Z':,
        u'\\': u'\u1f76',  # iota with gravis
        u'&': u'\u03b8',  # theta
        u'§': u'\u03be',  # ksi
        u'6': u'\u03b4',  # delta
        u'ŕ': u'\u03ae',  # eta z acutusem

    }
    diphthongs = {u'rj': u'\u1f21',  # eta
                  u'qp': u'\u03c6',  # hhi
                  u'ft': u'\u03bc',  # mi
                  u'fi': u'\u03b2',  # beta
                  }
    for d in diphthongs.keys():
        incorrect = incorrect.replace(d, diphthongs[d])
    greek_word = ""
    for latin_char in incorrect:
        greek_word += dykt.get(latin_char, latin_char)
    return greek_word



def replace_non_greek_with_dot(incorr):
    """
    incorr is a greek word that possibly has only one letter
    mis-ocred, so replace it with dot
    """
    #from pymongo import MongoClient
    #manu_tironis = MongoClient()['manu_tironis']
    GREEK_ALP = GREEK_ALPHABET()
    for letter in incorr:
        if letter not in GREEK_ALP:
            incorr = incorr.replace(letter, u'.')
    #suggestions = list(manu_tironis.words.find({"word":{"$regex": incorr}}, {"word": 1}))
    # FIXME
    # suggestions = [w for w in WORDS if andre.match(incorr+"$", w) is not None]
    WORDS = psql_manu_tironis.get_all_words()
    suggestions = [w for w in WORDS if len(w)==len(incorr) and re.match(incorr, w) is not None]
    return suggestions


def _all_leters_latin(word):
    """
    """
    if all(letter in LATIN_CHARSET for letter in word):
        return True
    return False


def _some_letters_non_greek(word):
    """
    """
    GREEK_ALP = GREEK_ALPHABET()
    if any(letter not in GREEK_ALP for letter in word):
        return True
    return False

cleaner_dict = {
        u"τͅ": u'\u03c4',  # small tau
        u"δ́": u'\u03b4',  # delta
        u"ἴ́": u'\u03af',
        u"ἶͅ": u'\u03af',
        u"γ́": u'\u03b3',  # gamma
        u"κ̣": u'\u03ba',  # kappa
        u"ξ͂": u'\u03be',  # ksi
        u"ὸ́": u'\u03c3',
        u"κ̣": u'\u03ba',  # kappa
        u"τ̀ͅ": u'\u03c4',  # small tau
        u'ν̀': u'\u03bd',  # nu
        u'γ̣': u'\u03b3',  # gamma
        u'κ̓': u'\u03ba',  # kappa
        u"ί̣": u'\u03af',
        u"σ́": u'\u03c3',  # sigma
        u'ῦͅ': u"ῦ",
        u'κ̓': u'\u03ba',  # kappa
        u'τ͂': u'\u03c4',  # small tau
        u'κ́': u'\u03ba',  # kappa
    }


def some_strange_caracters_in(incorrect):
    for strange in cleaner_dict.keys():
        if strange in incorrect:
            return True
        return False


def replace_strange_chars(incorrect):
    for strange in cleaner_dict.keys():
        incorrect = incorrect.replace(strange, cleaner_dict[strange])
    return incorrect

def smart_suggest(incorrect):
    """
    If word contains one or more letter that is
    not greek, replace it with dot, use re and return
    If word contains only latin letters, translate them
    given commonly mistaken vals
    :param incorrect - unicode !
    """
    if some_strange_caracters_in(incorrect):
        # print 333
        w = replace_strange_chars(incorrect)
        suggestions = {w: w}
        return suggestions
    if _all_leters_latin(incorrect):
        w = translate_latin_chars(incorrect)
        suggestions = {w: w}
        return suggestions
    if _some_letters_non_greek(incorrect):
        suggestions = {w: w for w in replace_non_greek_with_dot(incorrect)}
        return suggestions
    #http://stackoverflow.com/questions/11249635/finding-similar-strings-with-postgresql-quickly
    # WORDS = psql_manu_tironis.get_all_words()
    # vals = {}
    # for correct in WORDS:
    #    ratjo = ratio(incorrect, correct)
    #    if ratjo > 0.65:
    #        vals[correct] = ratjo
    # if len(vals) > 5:
    #    ratios = [v for v in reversed(sorted(vals.values()))][:5]
    #    suggestions = {c: c for c, v in vals.iteritems() if v in ratios}
    # else:
    #    suggestions = {c: c for c, v in vals.iteritems()}
    # return suggestions
    suggestions = psql_manu_tironis.get_similar_by_trgm(incorrect)
    return suggestions
