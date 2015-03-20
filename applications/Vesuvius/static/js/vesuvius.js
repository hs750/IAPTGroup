

//#######################################################################
// Search Form functions
//#######################################################################

// Run only when document is ready
jQuery(document).ready(function() {
    hide();
});

// Call on keyup to pass data to controller function
function getData(url, value) {
    if(value != "") {
        $("#liveresults").show();
        $.post(url,{partialstr:value},function(result){
            $("#liveresults").html(result);
        });
    } else {
        hide();
    }
}

// Hide live search dropdown
function hide() {
    $("#liveresults").hide();
}

// Fill search box with value
function copyIntoSearch(value) {
    $("#search").val(value);
    hide();
    $("#nav-search-form").submit();
}

function closeSearchFrame() {
    hide();
}

// Add requirement field when + button clicked
function addReq() {
    // Get name of requirement
    var thisval = $('#basereq').val();
    // Blank label for consistent formatting with rest of forms
    var labelstr = "<label class='create-form-label'></label>";
    // Readonly input containing name of requirement
    var inputstr = "<input value=%REQ% type='text' readonly class='create-form-field'></input>".replace("%REQ%", thisval);
    // - Button for removing requirements
    var btnstr = "<input value='-' type='button' class='create-req-btn btn' style='width:34px;' onClick='removeReq(this.parentNode.id)'></input>";

    // Concat divs and append to wrapper div
    var concatDiv = "<div id=req%ID%>%LABEL%%INPUT%%BTN%</div>".replace("%ID%", thisval).replace("%LABEL%", labelstr).replace("%INPUT%", inputstr).replace("%BTN%", btnstr)
    $('#wrapper').append(concatDiv);
}

// Remove requirement when - button clicked
function removeReq(id) {
    // Add # symbol to start of id and remove
    var rId = "#%ID%".replace("%ID%", id)
    $(rId).remove()
}

/* Fix javascript modulo bug, taken from http://javascript.about.com/od/problemsolving/a/modulobug.htm 15 Mar 1015*/
Number.prototype.mod = function(n) { return ((this%n)+n)%n; }