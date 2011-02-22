## Copyright (c) 2010 John E. Doig III, Creative Commons

## Permission is hereby granted, free of charge, to any person obtaining
## a copy of this software and associated documentation files (the "Software"),
## to deal in the Software without restriction, including without limitation
## the rights to use, copy, modify, merge, publish, distribute, sublicense,
## and/or sell copies of the Software, and to permit persons to whom the
## Software is furnished to do so, subject to the following conditions:

## The above copyright notice and this permission notice shall be included in
## all copies or substantial portions of the Software.

## THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
## IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
## FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
## AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
## LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
## FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
## DEALINGS IN THE SOFTWARE.

import re

# RDF predicate shortcut functions 
CC = lambda part: "http://creativecommons.org/ns#%s" % part
SIOC = lambda part: "http://rdfs.org/sioc/ns#%s" % part
SIOC_SERVICE = lambda part: "http://rdfs.org/sioc/services#%s" % part
POWDER = lambda part: "http://www.w3.org/2007/05/powder#%s" % part
DC = lambda part: "http://purl.org/dc/elements/1.1/%s" % part
DCT = lambda part: "http://purl.org/dc/terms/%s" % part
XHTML = lambda part: "http://www.w3.org/1999/xhtml/vocab#%s" % part
FOAF = lambda part: "http://xmlns.com/foaf/0.1/%s" % part
MARCEL = lambda part: "http://id.loc.gov/vocabulary/relators/%s" % part

################################################################
##
## Common operations for extracting information from the triples
##
################################################################

def rdf_accessor(func):
    """ Decorator for functions that serve to check for a set of
    triples in a particular order for a specific subject.  """
    def check_subject_exists(subject, metadata):
        if subject not in metadata['subjects']:
            return None
        return func(subject, metadata)
    return check_subject_exists

def unique(objects):
    if objects and len(objects) == 1:
        return objects[0]
    return None

def get_license_uris(subject, metadata):
    """ Return a list of all licenses specified for the subject """
    if subject not in metadata['subjects']: return []
    return unique(metadata['triples'][subject].get(XHTML('license'))) or \
           unique(metadata['triples'][subject].get(DCT('license'))) or \
           unique(metadata['triples'][subject].get(CC('license'))) or \
           []

@rdf_accessor
def get_license_uri(subject, metadata):
    """ Returns the 1st license uri specified by rel=license, dct:license,
    dc:license, cc:license, in that order of precedence. """
    return get_license_uris(subject, metadata)

@rdf_accessor
def get_title(subject, metadata):
    """ Returns the dct:title or dc:title for the subject """
    return unique(metadata['triples'][subject].get(DCT('title'))) or \
           unique(metadata['triples'][subject].get(DC('title'))) or \
           None

@rdf_accessor
def get_name(subject, metadata):
    """ Returns the foaf:name for the subject """
    return metadata['triples'][subject].get( FOAF('name') ) or \
           None

@rdf_accessor
def get_creator(subject, metadata):
    """ Returns the dct:creator or dc:creator for the subject. """
    return unique(metadata['triples'][subject].get(DCT('creator'))) or \
           unique(metadata['triples'][subject].get(DC('creator'))) or \
           unique(metadata['triples'][subject].get(CC('attributionURL'))) or \
           None

@rdf_accessor
def get_publisher(subject, metadata):
    """ Returns the dct:publisher or dc:publisher for the subject. """
    return unique(metadata['triples'][subject].get( DCT('publisher'))) or \
           unique(metadata['triples'][subject].get( DC('publisher'))) or \
           unique(metadata['triples'][subject].get( MARCEL('dtc'))) or \
           None

@rdf_accessor
def get_norms(subject, metadata):
    """ Return the uri detailing the norms for this document """
    return unique(metadata['triples'][subject].get(CC('useGuidelines'))) or \
           None

@rdf_accessor
def get_attribution_name(subject, metadata):
    name = unique(metadata['triples'][subject].get(CC('attributionName'))) 
    if not name:
        creator = get_creator(subject, metadata)
        if creator and creator in metadata['subjects']:
            return unique(metadata['triples'][creator].get(FOAF('name')))
    return name

##############################################################
##
## work registration detection specific functions (mouthful) 
##                                                            
##############################################################


def match_iriset(metadata, irisets, subject):

    for iriset in [metadata['triples'][i] for i in irisets]:
        if iriset.has_key(POWDER('includeregex')):
            for regex in iriset[POWDER('includeregex')]:
                if re.compile(regex).search(subject) is None:
                    # the subject didn't match one of the includeregex's
                    return False

        if iriset.has_key(POWDER('excluderegex')):
            for regex in iriset[POWDER('excluderegex')]:
                if re.compile(regex).search(subject) is not None:
                    # the subject matched one of the excluderegex's
                    return False
                
    return True

def get_lookup_uri(network, metadata, work_uri):

    cc_protocol_uri = "http://wiki.creativecommons.org/work-lookup"

    if network not in metadata['subjects'] or \
       not metadata['triples'][network].has_key(SIOC_SERVICE('has_service')):
        return None

    for service in metadata['triples'][network][SIOC_SERVICE('has_service')]:
        if service in metadata['subjects'] and \
           metadata['triples'][service].has_key(SIOC_SERVICE('service_protocol')) and \
           cc_protocol_uri in metadata['triples'][service][SIOC_SERVICE('service_protocol')]:
            
            return service + "?uri=" + work_uri

    return None
    
def is_registered(subject, license_uri, metadata):
    """ Checks for work registration assertions """

    # shorthand accessor
    triples = metadata['triples']

    # first check for a has_owner assertion
    if subject not in metadata['subjects'] or \
       not triples[subject].has_key(SIOC('has_owner')):
        return False

    # an assertion exists
    owner_url = triples[subject][SIOC('has_owner')][0]

    # check if registry contains rdfa and if so,
    # are there any SIOC:owner_of triples?
    if owner_url not in metadata['subjects']:
        return False

    if not triples[owner_url].has_key(SIOC('owner_of')):
        # check if the owner_url was redirected in the scraping
        if metadata['redirects'].has_key(owner_url) and \
           triples[metadata['redirects'][owner_url]].has_key(SIOC('owner_of')):
            # the owner url was redirected to, use that url to find assertions
            owner_url = metadata['redirects'][owner_url]
        else:
            return False
    
    # check if the registry completes the assertion
    if subject in triples[owner_url][SIOC('owner_of')]:
        # woot, success!
        return True
    
    # check to see if the subject matches an iriset
    for work in triples[owner_url][SIOC('owner_of')]:
        
        # filter out subjects that don't share the same license 
        if get_license_uri(work, metadata) == license_uri and \
               triples[work].has_key(SIOC('has_parent')):
            
            parent = triples[work][SIOC('has_parent')][0]

            if triples[parent].has_key(POWDER('iriset')) and \
                   match_iriset(metadata,
                                triples[parent][POWDER('iriset')],
                                subject):

                return True
            
    return False


############################################################
##                                                          
##  extract relevant values from an rdfadict DictTripleSink 
##                                                          
############################################################

def extract_licensed_subject(subject, license_uri, metadata):
    
    if license_uri in get_license_uris(subject, metadata):
        return subject

    licensed = filter( lambda s: license_uri in get_license_uris(s,metadata),
                       metadata['subjects'] )
    
    if len(licensed) == 1:
        return licensed[0]
    else:
        return None

def attribution(subject, metadata):
    """ Queries a dictionary of triples for cc:attributionName and
    cc:attributionURL.  The result is returned as a tuple where the first
    element is the attributionName, followed by the attributionURL.  """

    attrib = {
        'attributionName': '',
        'attributionURL': '',
        }

    if subject not in metadata['subjects']:
        return attrib

    attrib['attributionName'] = get_attribution_name(subject, metadata) or ''
    attrib['attributionURL'] = unique(metadata['triples'][subject].get(CC('attributionURL'))) or ''
    
    return attrib

def registration(subject, metadata, license_uri):

    regis = {
        'owner_url': '',
        'owner_name': '',
        'network_url': '',
        'network_name': '',
        'lookup_uri': '',
        }

    if not is_registered(subject, license_uri, metadata):
        # try to extract another licensed subject and try again
        subject = extract_licensed_subject(subject, license_uri, metadata)
        if not is_registered(subject, license_uri, metadata):
            return regis
    
    try:
        # retrieve the relevant information
        owner = unique(metadata['triples'][subject][SIOC('has_owner')])
        owner_name = unique(metadata['triples'][owner][SIOC('name')])
        network_url = unique(metadata['triples'][owner][SIOC('member_of')])
        network_name = unique(metadata['triples'][network_url][DCT('title')])

        lookup_uri = get_lookup_uri(network_url, metadata, subject)

        if lookup_uri is None:
            return regis
        
        return {
            'owner_url': owner,
            'owner_name': owner_name,
            'network_url': network_url,
            'network_name': network_name,
            'lookup_uri': lookup_uri,
            }
    
    except KeyError: # if any of the attributes aren't included, then return an empty dict
        return regis

def more_permissions(subject, metadata):

    if subject not in metadata['subjects']:
        return {}

    morePermURLs = metadata['triples'][subject].get(CC('morePermissions'), '')
    commLicense = unique(metadata['triples'][subject].get(CC('commercialLicense'))) or ''
    
    morePermAgent = ''
    if commLicense and commLicense in metadata['subjects'] and \
       metadata['triples'][commLicense].has_key( DCT('publisher') ):
        
        publisher = unique(metadata['triples'][commLicense][ DCT('publisher')])
        if publisher and metadata['triples'][publisher].has_key( DCT('title') ):
            # if there is an available title for the agent,
            # then it'll included in the extra deed permission popup
            morePermAgent = unique(metadata['triples'][publisher][DCT('title')]) or ''
            
    
    # returns a tuple of with ('' or 1list, string, string) sig
    return {
        'morePermissionsURLs' : morePermURLs,
        'commercialLicense' : commLicense,
        'morePermAgent': morePermAgent,
        }
    
     
    
