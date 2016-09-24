# all the logic that stands behind /update url
# user story - user corrects by hand or pick single suggestion

from helpers import get_word, is_correct, is_marginalia, is_safe, clean_from_dots, replace_node
from psql_manu_tironis import get_single_record
from psql_tasks import save_single_word, run_best_guess, async_update_documents_notepad
from mark import mark_as, add_pagination_class


def save_corrected(correct_word, page_id, word_id):
    '''
    User story:
    1. User picked on of the words suggested to him
    2. User corrected text by hand
    DONE DONE
    '''
    if not is_marginalia(correct_word):
        correct_word = clean_from_dots(correct_word)
    # get_single_record
    # record_to_correct = lace_texts.find_one({"_id": page_id})
    # notepad = record_to_correct['notepad']
    notepad = get_single_record(page_id)
    mistaken_word = get_word(notepad, word_id)
    # word is corrected by hand when is cannot be found among suggestions
    # so get the word that will be replaced and check if `correct_word`
    # can be found among
    if is_correct(correct_word):
        new_notepad = replace_node(notepad, correct_word, word_id=word_id)
        # TODO run me async
        async_update_documents_notepad.delay(page_id, new_notepad)
        #  TODO run me async
        run_best_guess.delay(correct_word, mistaken_word)
    else:
        # we cannot trust - it could have been hand corrected
        # is_hand_corrected = True
        if not is_safe(correct_word):
            return
        if is_marginalia(correct_word):
            mark_as('1', page_id, word_id)
            add_pagination_class(page_id, word_id)
            return
        else:
            save_single_word.delay(correct_word)
            # update_really_all_texts(correct_word)
            # run_best_guess(correct_word, mistaken_word)
            # return
            # IDIOT! is the word has been already replace with correct
            # you cannot retireve it to run best guess from it!
            new_notepad = replace_node(notepad, correct_word, word_id=word_id)
            # TODO run me async
            async_update_documents_notepad.delay(page_id, new_notepad)
            #  TODO run me async
            run_best_guess.delay(correct_word, mistaken_word)
    return
