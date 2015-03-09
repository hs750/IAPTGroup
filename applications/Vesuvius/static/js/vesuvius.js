

//#######################################################################
// Search Form functions
//#######################################################################

// Run only when document is ready
jQuery(document).ready(function() {
    hide();
});

// Call on keyup to pass data to controller function
    function getData(value) {
        if(value != "") {
            $("#liveresults").show();
            $.post("liveSearch",{partialstr:value},function(result){
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