from bs4 import BeautifulSoup


def is_marginalia(word):

    if len(word) == 1 and word in "1234567890QWERTYUIOPLKJHGFDSAZXCVBNM":
        return True
    if len(word) in [2, 3] and all(w in "1234567890" for w in word):
        return True
    return False


def is_safe(word):
    html_tags = 'href', 'iframe', 'www', 'http', '@'
    if len(word) > 60:
        return False
    if any(tag in word for tag in html_tags):
        return False
    return True


def clean_from_dots(word):
    # this is insane, but i want to keep them 'ere
    all_greek_letters = [u'\u1f40', u'\u03b4', u'\u03cd', u'\u03bd', u'\u03b7', u'\u03c4', u'\u03ad', u'\u03bb', u'\u03b5', u'\u03b9', u'\u03bf', u'\u03c2', u'\u03c3', u'\u03af', u'\u03b1', u'\u1f00', u'\u03c0', u'\u03c1', u'\u03ae', u'\u03c9', u'\u1f24', u'\u03b3', u'\u03ba', u'\u03bc', u'\u03c5', u'\u03b8', u'\u1f73', u'\u1f79', u'\u1f11', u'\u03b2', u'\u03ac', u'\u03c7', u'\u03ce', u'\u1fc6', u'\u1f55', u'\u1ff3', u'\u1f71', u'\u1f77', u'\u1f75', u'\u03cc', u'\u1f76', u'\u1f7d', u'\u1f20', u'\u1f14', u'\u03be', u'\u1f51', u'\u1f72', u'\u03c6', u'\u1ff6', u'\u1f10', u'\u1fd6', u'\u1f66', u'\u1f30', u'\u1f15', u'\u1f27', u'\u03b6', u'\u1fe6', u'\u1f05', u'\u1fb3', u'\u1f45', u'\u1fc3', u'\u1f7b', u'\u1f50', u'\u1f04', u'\u1f94', u'\u1f54', u'\u1fb7', u'\u1f25', u'\u1ff7', u'\u1f70', u'\u1f41', u'\u1f78', u'\u1f21', u'\u1fc7', u'\u1f35', u'\u1fe5', u'\u1fb6', u'\u1f7a', u'\u1f74', u'\u1f36', u'\u1f44', u'\u1f01', u'\u1fbd', u'\u1fc2', u'\u1fbf', u'\u1f60', u'\u1f7c', u'\u1f57', u'\u03c8', u'\u1f96', u'\u1fe4',
                         u'\u1f31', u'\u1fc4', u'\u1fa7', u'\u1f23', u'\u1f34', u'\u03ca', u'\u0390', u'\u02d9', u'\u1fa4', u'\u1f67', u'\u0313', u'\u1f37', u'\u1f90', u'\u1f84', u'\u0384', u'\u1f65', u'\u0375', u'\u1ff4', u'\u1f61', u'\u1f26', u'\u1f56', u'\u1f85', u'\u1f63', u'\u2019', u'\u014d', u'\u1f06', u'\u1f64', u'\u1fa0', u'\u1f43', u'\u1f33', u'\u03b0', u'\u2219', u'\u1f86', u'\u1f97', u'\u1f13', u'\u1f03', u'\u2018', u'\u1fa6', u'\u1fb4', u'\u1f02', u'\u03cb', u'\u1f62', u'\u1f42', u'\u1f22', u'\u1f53', u'\u1f48', u'\u1fd3', u'\u1fe3', u'\u03a5', u'\u0391', u'\u1f91', u'\u039f', u'\u0399', u'\u1f07', u'\u0397', u'\u0395', u'\u03a6', u'\u0393', u'\u03a4', u'\u1f08', u'\u0396', u'\u039a', u'\u039d', u'\u039c', u'\u039b', u'\u03a3', u'\u0398', u'\u03a7', u'\u03a1', u'\u1fec', u'\u0394', u'\u0392', u'\u03a0', u'\u03a9', u'\u1f18', u'\u1f4f', u'\u03a8', u'\u1f29', u'\u1f38', u'\u1fe2', u'\u1f0c', u'\u1fd2', u'\u1f59', u'\u1f19', u'\u1f1d', u'\u1f09', u'\u039e', u'\u1f39', u'\u1f68', u'\u1f28', u'\u1f0e', u'\xad', ]

    for letter in word:
        if letter not in all_greek_letters:
            word = word.replace(letter, "")
    return word

def clean(word):
    '''
    If word ends with . or ,
    clean it
    '''
    perks = list(".,{}[](){}[]]().,;")
    BADSEEDS = [unicode(l) for l in perks]
    BADSEEDS.append(u'\xb7')
    word = word.strip()
    while len(word) > 0 and word[-1] in BADSEEDS:
        word = word[:-1]
    while len(word) > 0 and word[0] in BADSEEDS:
        word = word[1:]
    return word


def replace_node(notepad, word, word_id=None):
    '''
    this function should be used in two situations:
    1. user manually corrects specific word - then word_id is provided
    2.  user click "this word is correct" and we correct it globally, ie across all documents
    Take a notepad from the text /notepad is where changes are saved/
    find the word and correct it, but save all values of html node
    like id, corr, lang, etc
    return: corrected notepad
    '''
    soup = BeautifulSoup(notepad, 'html.parser')
    if word_id is not None:
        node = soup.find("span", {"id": word_id})
        nodes_to_replace = [node]
    else:
        all_nodes = soup.findAll("span", {"lang": "grc", "corr": "0"})
        nodes_to_replace = [n for n in all_nodes if clean(n.text) == word]
    for old_node in nodes_to_replace:
        if old_node.has_attr("half"):
            if old_node["half"] == "2":
                # we do not correct the second half
                return
            if old_node.has_attr("full"):
                    # first let's find the other half
                next_node_id = old_node["id"] + 1
                next_node = soup.find("span", {"id": next_node_id})
                if not next_node:
                    return
                old_node["full"] = word
                old_node["corr"] = "1"
                next_node["corr"] = "1"
                half_cut = len(old_node.text)
                old_node.string = word[0:half_cut]
                next_node.string = word[half_cut:]

        else:
            old_node["corr"] = "1"
            # if word has dot or comma at the end, keep it
            if old_node.string[-1] in [',', '.']:
                old_node.string = word + old_node.string[-1]
            else:
                old_node.string = word
            # notepad = notepad.replace(str(old_node), str(new_node))

    # return notepad
    return str(soup)
