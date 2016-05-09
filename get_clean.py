# get_clean.py - logic behind /get_clean url
# which returns  text in read-only form

from bs4 import BeautifulSoup
from pymongo import MongoClient
client = MongoClient()
manu_tironis = client['manu_tironis']


def get_whole_text(title):
    """
    Returns a text not for editing
    but for viewing, even though its dirty
    """
    query = {"title": title}
    all_notepads = [page['notepad'] for page in manu_tironis.lace_texts.find(query)]
    full_text = " ".join([_turn_doc_to_page(nt) for nt in all_notepads])
    return full_text


def _turn_doc_to_page(notepad):
    '''
    Take a doc['notepad'] from the mongodb
    and return just text, well formatted
    '''
    soup = BeautifulSoup(notepad, 'html.parser')
    # take just greek text
    greek_text = soup.find("span", {"class": "greek_text"})
    lines = greek_text.findAll("span", {"class": "ocr_line"})
    all_lines = []
    # first line is header
    for line in lines[1:]:
        # we hope that side_pagination does not have lang
        words = [w for w in line.findAll("span", {"lang": "grc"})]
        result_line = []
        for word in words:
            result_line.append(word.text)

        result_line.append("\n")
        all_lines.append(" ".join(result_line))
    page = " ".join(all_lines)
    return page

