## Copyright (c) 2010 John E. Doig III Creative Commons

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

import gc
import cc.license
import cc.license.selectors
import web
import cgi
from urlparse import urlparse
import support
import metadata
import renderer

CC0_SELECTOR = cc.license.selectors.choose('zero')
# maintain a cache of the deeds' lang codes
LANGS = {}
    
from scraper import ScrapeRequestHandler

web.config.debug = False

urls = (
    '/triples', 'Triples',
    '/deed',    'DeedReferer',
    '/pddeed',  'PublicDomainReferer',
     )

class Triples(ScrapeRequestHandler):

    def GET(self):
        triples = self._triples(web.input().get('url',''))
        callback = web.input().get('callback')
        if callback:
            return "%s(%s)" % (callback, renderer.response(triples))
        else:
            return renderer.response(triples)

class RefererHandler(ScrapeRequestHandler):
    
    """ Base class for the handlers involved in scraping referrers and
    displaying information about that document on the deed. """
    
    # CACHE VARIABLES.
    # LOW MEMORY < RESPONSE TIME -- IN TERMS OF IMPORTANCE FOR THIS APPLICATION
    # cache mapping of license uri's and their rendered language
    # e.g.  http://creativecommons.org/licenses/by/3.0/deed.es => 'es'
    LANGS = {}
    # cache mapping of license uri's => cc.license License objects
    # e.g.  http://creativecommons.org/publicdomain/zero/1.0/ =>
    #       <License object 'http://creativecommons.org/publicdomain/zero/1.0/'>
    LICENSES = {} 
    
    def scrape_referer(self, action):
        # this is required argument

        url = web.input().get('url', None)
        license_uri = web.input().get('license_uri') or \
                      web.ctx.env.get('HTTP_REFERER', None)
        
        if license_uri is None or url is None or \
           not license_uri.startswith('http://creativecommons.org/'):
            raise Exception("A license URI and a subject URI must be provided.")
        
        if license_uri not in self.LICENSES.keys():
            try:
                if 'deed' in license_uri:
                    stripped_uri = license_uri[:(license_uri.rindex('/')+1)]
                    cclicense = cc.license.by_uri(str(stripped_uri))
                else:
                    cclicense = cc.license.by_uri(str(license_uri))
            except cc.license.CCLicenseError, e:
                raise Exception("Invalid license URI.")
            # cache the cc.license object so we dont have to fetch it again
            self.LICENSES[license_uri] = cclicense
        
        # deeds include a lang attribute in <html>
        if license_uri not in self.LANGS.keys():
            lang = support.get_document_locale(license_uri)
            if lang is None:
                # didn't find a lang attribute in the html
                lang = web.input().get('lang', 'en')
            # cache the lang code based on the deed's uri
            self.LANGS[license_uri] = lang
        
        # set the global lang variable in the renderer
        renderer.set_locale(self.LANGS[license_uri])
        
        triples = self._first_pass(url, action)
        if '_exception' in triples['triples'].keys():
            # should probably report the error but for now...
            raise Exception(triples['triples']['_exception'])
        
        subject = metadata.extract_licensed_subject(url, license_uri, triples)
        triples = self._triples(
            url=url, action=action, depth=1,
            sink=triples['sink'], subjects=triples['subjects'],
            redirects=triples['redirects']) 
        
        # check again for any exceptions
        if '_exception' in triples['triples'].keys():
            raise Exception(triples['triples']['_exception'])
        
        self.url = str(url)
        self.license_uri = str(license_uri)
        self.cclicense = self.LICENSES[license_uri]
        self.lang = self.LANGS[license_uri]
        self.subject = subject
        self.triples = triples

        return

class DeedReferer(RefererHandler):

    def GET(self):
        """ Scrape and process the referer's metadata. """
        try:
            self.scrape_referer('deed')
        except Exception, e:
            return renderer.response(dict(_exception=str(e)))

        # if there's a callback specified, wrap the results as a js function call
        callback = web.input().get('callback')
        if callback:
            return "%s(%s)" % (callback, renderer.response(self.results()))
        else:
            return renderer.response(self.results())

    def results(self):
        """ Interprets the scraped data for its significance to a deed """
        # returns dictionaries with values to CCREL triples
        attrib = metadata.attribution(self.subject, self.triples)
        regist = metadata.registration(self.subject, self.triples, self.license_uri) 
        mPerms = metadata.more_permissions(self.subject, self.triples)
        
        # check if a dc:title exists, if there is a title, it will replace
        # any place where "this work" would normally appear in the deed popups
        title = metadata.get_title(self.subject, self.triples)
        
        results = {
            'attribution': {
                'details': renderer.render(
                    'attribution_details.html', {
                        'subject': self.subject,
                        'license': self.cclicense,
                        'title':title,
                        'attributionName': attrib['attributionName'],
                        'attributionURL': attrib['attributionURL'],
                        }),
                'marking': renderer.render(
                    'attribution_marking.html', {
                        'subject': self.subject,
                        'license': self.cclicense,
                        'title': title,
                        'attributionName': attrib['attributionName'],
                        'attributionURL': attrib['attributionURL'],
                        }),
                },
            'registration':     renderer.render('registration.html', regist),
            'more_permissions': renderer.render('more_permissions.html',
                                                dict(subject=self.subject, **mPerms)),
            
            }
        
        return results

class PublicDomainReferer(RefererHandler):
    """ Request handler for the PD Mark deeds and CC0.

    The PD Mark makes a single GET on its page load, requesting
    the deedscraper to scrape the referring URI for any RDFa
    metadata relevant to the marking of a public domain or CC0 work.

    """
    def GET(self):
        """ Scrape and process the referer's metadata. """
        try:
            self.scrape_referer('pddeed')
        except Exception, e:
            return renderer.response(dict(_exception=str(e)))    

        callback = web.input().get('callback')
        if callback:
            return "%s(%s)" % (callback, renderer.response(self.results()))
        else:
            return renderer.response(self.results())
        
    def results(self):
        """ Process the scraped triples for the deed. """
        
        # extra all license relations to check for dual-licensing
        licenses = metadata.get_license_uri(self.subject, self.triples) or []
        cc0 = filter(lambda l: CC0_SELECTOR.has_license(l), licenses) or None
        if cc0: cc0 = cc0[0]
        
        regist = metadata.registration(self.subject, self.triples, self.license_uri)

        # empty values are represented by None
        results = {
            'waiver': cc0,
            'registration': renderer.render('registration.html', regist),
            'title': metadata.get_title(self.subject, self.triples),
            'norms': metadata.get_norms(self.subject, self.triples),
            'curator': metadata.get_publisher(self.subject, self.triples),
            'creator': metadata.get_creator(self.subject, self.triples),
            'curator_title': '',
            'creator_title': '',
            'curator_literal': False,
            'creator_literal': False,
            }

        results['curator_title'] = metadata.get_title(results['curator'], self.triples) or \
                                   metadata.get_name(results['curator'], self.triples)
        results['creator_title'] = metadata.get_title(results['creator'], self.triples) or \
                                   metadata.get_name(results['creator'], self.triples)
        
        if results['curator'] and not \
               (urlparse(results['curator']).scheme and \
                urlparse(results['curator']).netloc):
            results['curator_literal'] = True
        
        if results['creator'] and  not \
               (urlparse(results['creator']).scheme and \
                urlparse(results['creator']).netloc):
            results['creator_literal'] = True
        
        # escape and strip whitespaces
        for k,v in results.items():
            if type(v) in (str, unicode):
                results[k] = ' '.join(''.join(cgi.escape(v).split('\\n')).split())

        results['marking'] = renderer.render(
            'pd_marking.html',
            dict(results,
                 work=self.subject,
                 mark_uri=self.cclicense.uri,
                 mark_title=self.cclicense.title(self.lang)))
        
        return results

application = web.application(urls, globals(),)

if __name__ == "__main__": application.run()
