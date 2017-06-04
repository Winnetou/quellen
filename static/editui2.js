 $(document).ready(function(){
    $("#header").sticky({topSpacing:0});//make header sticky
    set_to_default()
    $("<hr>").insertAfter($('.greek_text'));


//thats wrong, whatever inside greek span is clicked, should trigger that function
$('span[lang="grc"]').click(function (event) {
    set_to_default()
    $(event.target).addClass("shining");
    var incorr;
    var full = $(this).attr('full');
    var half = $(this).attr('half');
    // if it is not
    if (typeof full !== typeof undefined && full !== false) {
        incorr = full;
        //also make shining the second half of the word
        //but first check if that's not pagination
        var next_id = parseInt($(event.target).attr('id'))+1;
        if ($("#"+next_id).attr('lang')=="grc")
            {
                $("#"+next_id).addClass("shining");
            }
        else
            {
                var next_plus_one = next_id+2;
                $("#"+next_plus_one).addClass("shining");
            }

    }
    // if the word clicked if half=2

    else if (typeof half !== typeof undefined && half !== false && $(this).attr('half')=="2")
    {

            var prev_id = parseInt($(event.target).attr('id'))-1;
            // look for the half=1 with full
            // var first_half = $(this).attr('half');
            if ($("#"+prev_id).attr('half')=="1")
            {
                incorr = $("#"+prev_id).attr('full');
                $("#"+prev_id).addClass("shining");
            }
            else
            {
                var prev_minus_one = prev_id-1;
                if ($("#"+prev_minus_one).attr('half')=="1")
                {
                    incorr = $("#"+prev_minus_one).attr('full');
                    $("#"+prev_minus_one).addClass("shining");
                }
            }
    }
    //just normal word
    else
    {
        incorr = $(event.target).text();

    }

    strip_and_send_to_asitis(incorr);
    //$('#asitis').text(incorr);
    var incorr_id = $(event.target).attr('id');
    //start with sending the id of the clicked word to hidden id input
    $("#word_id").val(incorr_id);

    // here we want to say that this form was recognized as either correct ot incorrect
    //and as either a word, pagination, number or proper name
    if ($(event.target).attr("corr")=="1")
    {

        $('#incorr').attr('disabled', false);
    }
    else if ($(event.target).attr("corr")=="0")
    {
        $('#corr').attr('disabled', false);
        $('#show_sugg').attr('disabled', false);
        $('#join').attr('disabled', false);
        $('#divide').attr('disabled', false);
        $('#remove').attr('disabled', false);
    }

})

$('#corr').click( function()
    {
        mark_as_correct()
})

$('#incorr').click( function()
    {
        mark_as_incorrect()
})

$('#remove').click( function()
    {
        $('#approve_word').attr("target","remove");
        disable()
        activate_save_button()
        var word_id = $("#word_id").val();
        //$("#"+word_id).removeClass("shining");
        $("#"+word_id).addClass("dying");

})

$('#show_sugg').click( function()
    {
        $('#corr').attr('disabled', true);
        $('#show_sugg').attr('disabled', true);
        $('#asitis').prop('contenteditable',false);
        deactivate_save_button()
        var incorr = $('#asitis').text()
        get_suggestions(incorr);
})

$('#approve_word').click(function(event)
    {
        var target = $(this).attr('target');
        if (target=="update")
        {
            $('#corr_list').empty();
            $('#asitis').prop('contenteditable',false);
            deactivate_save_button()
            $('#corr_list').empty();
            save();
            // id of the word clicked is word_id hidden field
            var incorr_id = "#"+$("#word_id").val();
            var text_of_correct = $('#asitis').text();
            // change the text
            $(incorr_id).text(text_of_correct);
            // change it to correct
            $(incorr_id).attr("corr")=="1";
        }
        if (target=="joindivide")
        {
            divideorjoin()
        }
        if (target=="remove")
        {
            really_remove()
        }


})

});


function deactivate_save_button()
{
    $('#approve_word').attr('disabled', true);
    //then, change the color and make transition
}

function activate_save_button()
{
    $('#approve_word').attr('disabled', false);
    //then, change the color and make transition
}

function accept_suggestion(incorr)
{
    // send the text to asitis
    $('#asitis').text(incorr);
    // fade all other buttons magnify clicked
    activate_save_button()
    $('#capitalise').prop('disabled', false);
}

function capitalise()
{
    var capitalised = $('#asitis').text();
    capitalised = capitalised.substr(0,1).toUpperCase()+capitalised.substr(1);
    $('#asitis').text(capitalised);
}

function set_to_default() //set all to default, called by click on word
{
    $('#approve_word').attr("target","update")
    $('span').each(function() {
            $(this).removeClass("shining");
            $(this).removeClass("dying");
        })
    //$("#play_correct").text("Start");
    $('#corr_list').empty(); // first, clean the list
    deactivate_save_button()//next, disable save button
    //third, values of both dropdowns back to zero
    $('#corr').attr('disabled', true);
    $('#incorr').attr('disabled', true);
    $('#show_sugg').attr('disabled', true);
    $('#join').attr('disabled', true);
    $('#divide').attr('disabled', true);
    $('#remove').attr('disabled', true);
    $('#asitis').prop('contenteditable',false);
    $('#asitis').css('color','inherit');
    $('#alphabet').hide();
    $('.diacritics').each(function() {
            $(this).hide();
        })

}
function disable() //called after saved button clicked
{
    $('span').each(function() {
            $(this).removeClass("shining");
        })
    $('#corr_list').hide();
    $('#alphabet').hide();
    $('#corr_list').empty(); // first, clean the list
    deactivate_save_button() //next, disable save button
    $('#corr').attr('disabled', true);
    $('#incorr').attr('disabled', true);
    $('#show_sugg').attr('disabled', true);
    $('#join').attr('disabled', true);
    $('#divide').attr('disabled', true);
    $('#asitis').prop('contenteditable',false);
    $('#asitis').attr('disabled', true);
    $('#remove').attr('disabled', true);

}

function get_suggestions(word)
{
    var incorr = $('#asitis').text();
    var url = '/suggest'
    $.getJSON( url, {word:incorr}
        ).done(function(data){
            if (! $.isEmptyObject(data))
            {
                $.each(data, function(i, item)
                {
                    var p = '<li><button onclick=accept_suggestion("'+item+'") class="suggestion">'+item+'</button></li>';
                    $('#corr_list').append(p);
                });

            }
            else
            {
                var p = '<li>No suggestions found!</li>';
                $('#corr_list').append(p);
            }
            var capital = '<li><button id="capitalise" disabled="disabled" onclick=capitalise() class="suggestion">Capitalise</button></li>';
            $('#corr_list').append(capital);
            var but = '<li><button onclick=make_editable() class="suggestion">Edit it manually</button></li>';
            $('#corr_list').append(but);
            $('#corr_list').show('slow')
        })
}
// func save is used when picked word
// from suggestions or hand-corrected
// and clicked on SAVE btn
function save()
{

    disable()
    var page_id = $("#page_id").val();
    var word_id = $("#word_id").val();
    var correct_form = $('#asitis').text();
    //now, send it all
    var url1 = '/update'
    var data1 = { 'page_id':page_id,
    'word_id':word_id,
    'correct_form':correct_form,
    }
    $.ajax({
        url: url1,
        type: "POST",
        data: data1,

    })

}
function mark_as_incorrect()
{
    var pre_id = $("#word_id").val();
    var id = '#'+pre_id;
    $(id).removeClass("shining");
    $(id).attr("corr", "0");
    mark_as("incorrect")
}
function mark_as_correct()
{
    var pre_id = $("#word_id").val();
    var id = '#'+pre_id;
    $(id).removeClass("shining");
    $(id).attr("corr", "1");
    mark_as("correct")
}
function mark_as(mark)
{
    disable()
    var page_id = $("#page_id").val();
    var word_id = $("#word_id").val();
    var data = { 'page_id':page_id,
    'word_id':word_id,
    'mark': mark
    }
    //now, send it all
    var url = '/mark'

    $.ajax({
        url: url,
        type: "POST",
        data: data,

    })
    return
}

function really_remove()
{
    disable()
    $('#approve_word').attr("target","update");
    var page_id = $("#page_id").val();
    var word_id = $("#word_id").val();
    var data = { 'page_id':page_id,
    'word_id':word_id,
    }
    //now, send it all
    var url = '/remove'

    $.ajax({
        url: url,
        type: "POST",
        data: data,

    })
    $("#"+word_id).hide("slow");
    return
}

function strip_and_send_to_asitis(incorr)
{
    if (incorr.slice(-1) == ".")
        {
            incorr = incorr.substring(0, incorr.length - 1);
        };
    if (incorr.slice(-1) == ",")
        {
            incorr = incorr.substring(0, incorr.length - 1);
        };

    $('#asitis').text(incorr);
}

//function is_hand_corrected(word){
    //check if value in ``
//    if (word is in )
//        {   return false
//        }
//        else {
//            return true
//        }

//    }
//function blink() {
//    $('.shining').fadeOut(500).fadeIn(500, blink);
//}
