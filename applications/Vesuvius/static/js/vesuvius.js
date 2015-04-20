

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

function clearField(field) {
    field.value = '';
}

// Add requirement field when + button clicked
function addReq(thisval) {
    if(thisval != "") {
        // Blank label for consistent formatting with rest of forms
        var labelstr = "<label class='create-form-label'></label>";
        // Readonly input containing name of requirement
        var inputstr = "<input value='%REQ%' type='text' readonly class='create-req-field'></input>".replace("%REQ%", thisval);
        // - Button for removing requirements
        var btnstr = "<input value='-' type='button' class='create-req-btn btn' style='width:34px;' onClick='removeReq(this.parentNode.id)'></input>";
        // Concat divs and append to wrapper div
        var concatDiv = "<div id=req%ID%>%LABEL%%INPUT%%BTN%</div>".replace("%ID%", thisval).replace("%LABEL%", labelstr).replace("%INPUT%", inputstr).replace("%BTN%", btnstr)
        $('#wrapper').append(concatDiv);
        updateReqList();
    }
}

// Remove requirement when - button clicked
function removeReq(id) {
    // Add # symbol to start of id and remove
    var rId = "#" + id.replace(/([ #;?&,.+*~\':"!%^$[\]()=>|\/@])/g,'\\$1');
    $(rId).remove()
    updateReqList();
}

// Workaround function that posts the list of requirements to a web2py function in order to keep track of them
// in the session variable
function updateReqList() {
    var reqs = [];
    // Get each relevant input field, and add its value to the list
    $('#wrapper').find('input.create-req-field').each(function(index,elem){reqs.push($(elem).val());})
    if(reqs.length > 0) {
        // Post the value to the function updateReqs() located in project.py
        $.post("/Vesuvius/project/updateReqs",{partialstr:reqs});
    } else {
        // If there are no requirements to post, post a list with an empty element.
        // This solves a bug with an empty post not being picked up by the web2py function
        $.post("/Vesuvius/project/updateReqs",{partialstr:['']});
    }
}

function errorMove(containerNode) {
    $(containerNode).find('.error_wrapper').each(function(index,elem){$(elem).remove();$(elem).appendTo($(containerNode));})
}

function errorClear(containerNode) {
    $(containerNode).find('.error_wrapper').each(function(index,elem){$(elem).remove();})
}

/* Fix javascript modulo bug, taken from http://javascript.about.com/od/problemsolving/a/modulobug.htm 15 Mar 1015*/
Number.prototype.mod = function(n) { return ((this%n)+n)%n; }

//Auto scale text areas to fit text.
function textAreaAutoResize(ta, maxHeight) {
    ta.style.height = "1px";
    var height = 25+ta.scrollHeight;
    height = Math.min(height, maxHeight);
    ta.style.height = height+"px";
}