/*
 * ccdeed.js
 * Core support for license deeds with metadata scraping
 * 
 * copyright 2007-2008, Creative Commons, Nathan R. Yergler, John E Doig III
 *
 * Permission is hereby granted, free of charge, to any person obtaining
 * a copy of this software and associated documentation files (the "Software"),
 * to deal in the Software without restriction, including without limitation
 * the rights to use, copy, modify, merge, publish, distribute, sublicense,
 * and/or sell copies of the Software, and to permit persons to whom the
 * Software is furnished to do so, subject to the following conditions:
 * 
 * The above copyright notice and this permission notice shall be included in
 * all copies or substantial portions of the Software.

 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
 * FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
 * DEALINGS IN THE SOFTWARE.
 * 
 * 
 */


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
    var cc_zero = document.location.pathname.match(
                     '^http://creativecommons.org/publicdomain/zero');
    
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
