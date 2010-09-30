
YAHOO.namespace("cc");

// **  Parsing/Scraping/Dispatch
// **
YAHOO.cc.toggle = function(fieldName, fieldValue) {
    var ele = document.getElementById(fieldName);
    ele.parent.style.display = true;
    return ele;
}

YAHOO.cc.success = function (response) {

    if (response.status != 200) return;

    var popups = YAHOO.lang.JSON.parse(response.responseText);
    var cc_zero = document.location.match('^http://creativecommons.org/publicdomain/zero');
    
    if ( popups.norms || popups.waiver || 
         popups.title || popups.creator_title || popups.curator_title ) {
        if( popups.title || popups.creator_title || popups.curator_title ) 
            document.getElementById('work-details-title').style.display = true;
        document.getElementById('work-details-block').style.display = true;
    }
    
    // Check if any norms have been specified
    if ( popups.norms != '')
        YAHOO.cc.toggle('usage_guidelines').href = popups.norms;
    // Check for attribution marking
    if ( popups.marking != '' ) 
        YAHOO.cc.toggle('work-attribution').value = popups.marking;
    // Display the work's title
    if ( popups.title != '' ) 
        YAHOO.cc.toggle('meta_title').innerHTML = popups.title;
    // Display any author information
    if ( popups.creator_title != '' ) {
        var creator = popups.creator_title;
        if ( popups.creator != '' ) 
            creator = "<a href='"+popups.creator+"'>" + popups.creator_title + "</a>";
        YAHOO.cc.toggle('meta_author').innerHTML = creator;
    }
    // Display any curator information
    if ( popups.curator_title != '' ) {
        var curator = popups.curator_title;
        if ( popups.curator != '' ) 
            curator = "<a href='"+popups.curator+"'>" + popups.curator_title + "</a>";
        YAHOO.cc.toggle('meta_curator').innerHTML = curator;
    }
    
    if ( popups.waiver != '' && !cc_zero)
        YAHOO.cc.toggle('zero_help');
    
    return;

} // success

YAHOO.cc.failure = function () {

} // failure

YAHOO.cc.load = function () {

    if (document.referrer.match('^http://')) {

	// construct the request callback
	var callback = {
	    success: YAHOO.cc.success,
	    failure: YAHOO.cc.failure,
	    argument: document.referrer
	};

	// initialize the header to include the Referer
	YAHOO.util.Connect.initHeader('Referer', document.URL, true);

	var url = '/apps/pddeed?url=' + encodeURIComponent(document.referrer);
	YAHOO.util.Connect.asyncRequest('GET', url, callback, null);

    } // if refered from http:// request

} // load

YAHOO.util.Event.onDOMReady(YAHOO.cc.load);