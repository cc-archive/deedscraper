
YAHOO.namespace("cc");

// **  Parsing/Scraping/Dispatch
// **
YAHOO.cc.toggle = function(fieldName, fieldValue) {
    var ele = document.getElementById(fieldName);
    ele.parentNode.style.display = '';
    return ele;
}

YAHOO.cc.success = function (popups) {

    var cc_zero = document.URL.match(
                     '^http://creativecommons.org/publicdomain/zero');
    
    if ( popups.norms != null || popups.waiver != null || 
         popups.title != null || popups.creator_title != null || popups.curator_title != null ) {
        if( popups.title != null || popups.creator_title != null || popups.curator_title !=null ) 
            document.getElementById('work-details-title').style.display = '';
        document.getElementById('work-details-block').style.display ='';
    }
    
    // Check if any norms have been specified
    if ( popups.norms != null)
        YAHOO.cc.toggle('usage_guidelines').href = popups.norms;
    // Check for attribution marking
    if ( popups.marking != null ) 
        YAHOO.cc.toggle('work-attribution').value = popups.marking;
    // Display the work's title
    if ( popups.title != null ) 
        YAHOO.cc.toggle('meta_title').innerHTML = popups.title;
    
    if(!cc_zero) {
      // Display any author information
      if ( popups.creator_title != null ) {
        var creator = popups.creator_title;
        if ( popups.creator != null ) 
            creator = "<a href='"+popups.creator+"'>" + popups.creator_title + "</a>";
        YAHOO.cc.toggle('meta_author').innerHTML = creator;
      }
      // Display any curator information
      if ( popups.curator_title != null ) {
        var curator = popups.curator_title;
        if ( popups.curator != null ) 
            curator = "<a href='"+popups.curator+"'>" + popups.curator_title + "</a>";
        YAHOO.cc.toggle('meta_curator').innerHTML = curator;
      }
      if ( popups.waiver != null)
        YAHOO.cc.toggle('zero_help');
    } else {
      // Display any affirmer information
      if ( popups.curator_title != null ) {
        var curator = popups.curator_title;
        if ( popups.curator != null )
            curator = "<a href='"+popups.curator+"'>" + popups.curator_title + "</a>";
        YAHOO.cc.toggle('meta_affirmer').innerHTML = curator;
      }
    }
    
    return;

} // success

YAHOO.cc.load = function () {
    var path = document.location.pathname;
    if(!path.match('/$')) path += '/';
        // monitor marking copy-and-paste
    YAHOO.util.Event.addListener('work-attribution', 'click', function() {
            var pageTracker = _gaq._getAsyncTracker('UA-2010376-1');
            pageTracker._trackPageview(path + 'deed-attribution-click');
            return true;
        });
    // webkit browser copy event
    if(typeof document.getElementById('work-attribution').oncopy) {
        document.getElementById('work-attribution').oncopy = function() {
            var pageTracker = _gaq._getAsyncTracker('UA-2010376-1');
            pageTracker._trackPageview(path + 'deed-attribution-copied');
            return true;
        };
    }
} // load

YAHOO.util.Event.onDOMReady(YAHOO.cc.load);