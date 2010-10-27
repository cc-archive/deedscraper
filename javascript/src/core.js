

// ************************************************************************
// ************************************************************************
// ** 
// **  Parsing/Scraping/Dispatch
// **

YAHOO.cc.success = function (response) {

    var popups = YAHOO.lang.JSON.parse(response);
    
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
