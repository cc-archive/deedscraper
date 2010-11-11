

// ************************************************************************
// ************************************************************************
// ** 
// **  Parsing/Scraping/Dispatch
// **

YAHOO.cc.success = function (popups) {
 
    // Check for attribution results
    if ( popups.attribution.details != '' ) 
        YAHOO.cc.attribution.show_info(popups.attribution);
    
    // Check for registration results
    if ( popups.registration != '' ) 
        YAHOO.cc.network.show_info(popups.registration);

    // Check for more permissions
    if ( popups.more_permissions != '' ) 
        YAHOO.cc.plus.show_info(popups.more_permissions);
    
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