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
import support
import metadata
import renderer

CC0_SELECTOR = cc.license.selectors.choose('zero')

from scraper import ScrapeRequestHandler

web.config.debug = False

urls = (
    '/triples', 'Triples',
    '/deed',    'DeedReferer',
    '/mark',    'MarkReferer',
     )

class Triples(ScrapeRequestHandler):

    def GET(self):
        triples = self._triples(web.input().get('url',''))
        return renderer.response(triples)

class DeedReferer(ScrapeRequestHandler):

    # maintain a cache of the deeds' lang codes
    deed_langs = {}
    
    def GET(self):

        # this is required argument
        url = web.input().get('url')
        license_uri = web.input().get('license_uri') or \
                      web.ctx.env.get('HTTP_REFERER')

        # fail on missing arguments - TODO -- FAIL, REALLY?
        if license_uri is None or url is None or \
           not license_uri.startswith('http://creativecommons.org/'):
            return renderer.response(dict(
                _exception='A license URI and a subject URI must be provided.'))

        # get a cc license object
        # cclicense = metadata.LicenseFactory.from_uri(license_uri)
        try:
            if 'deed' in license_uri:
                stripped_uri = license_uri[:(license_uri.rindex('/')+1)]
                cclicense = cc.license.by_uri(str(stripped_uri))
            else:
                cclicense = cc.license.by_uri(str(license_uri))
        except cc.license.CCLicenseError, e:
            return renderer.response(dict(_exception=unicode(e)))
        
        triples = self._first_pass(url, 'deed')
        subject = metadata.extract_licensed_subject(url, license_uri, triples)
        triples = self._triples(url=url, action='deed', depth=1,
                                sink=triples['sink'],
                                subjects=triples['subjects'],
                                redirects=triples['redirects']) 
        
        if '_exception' in triples['subjects']:
            # should probably report the error but for now...
            return renderer.response(dict(
                _exception=triples['triples']['_exception']))

        # deeds include a lang attribute in <html>
        if license_uri not in self.deed_langs.keys():
            lang = support.get_document_locale(license_uri)
            if lang is None:
                # didn't find a lang attribute in the html
                lang = web.input().get('lang', 'en')
            # cache the lang code based on the deed's uri
            self.deed_langs[license_uri] = lang
        
        # prepare to render messages for this lang
        renderer.set_locale(self.deed_langs[license_uri])

        # returns dictionaries with values to cc-relevant triples
        attrib = metadata.attribution(subject, triples)
        regist = metadata.registration(subject, triples, license_uri) 
        mPerms = metadata.more_permissions(subject, triples)

        # check if a dc:title exists, if there is a title, it will replace
        # any place where "this work" would normally appear in the deed popups
        title = metadata.get_title(subject, triples)
        
        results = {
            'attribution': {
                'details': renderer.render(
                    'attribution_details.html', {
                        'subject': subject,
                        'license': cclicense,
                        'title': title,
                        'attributionName': attrib['attributionName'],
                        'attributionURL': attrib['attributionURL'],
                        }),
                'marking': renderer.render(
                    'attribution_marking.html', {
                        'subject': subject,
                        'license': cclicense,
                        'title': title,
                        'attributionName': attrib['attributionName'],
                        'attributionURL': attrib['attributionURL'],
                        }),
                },
            'registration':     renderer.render('registration.html', regist),
            'more_permissions': renderer.render('more_permissions.html',
                                                dict(subject=subject, **mPerms)),
            
            }
        
        return renderer.response(results)

class MarkReferer(ScrapeRequestHandler):
    """ Request handler for the PD Mark deeds.

    The PD Mark makes a single GET on its page load, requesting
    the deedscraper to scrape the referring URI for any RDFa
    metadata relevant to the marking of a public domain work.

    """

    # maintain a cache of the marks' lang codes
    pdmark_langs = {}
    
    def GET(self):
        
        # this is required argument
        url = web.input().get('url')
        mark_uri = web.input().get('mark_uri') or \
                       web.ctx.env.get('HTTP_REFERER')
        
        # fail on missing arguments - TODO -- finer-grained startswith
        if mark_uri is None or url is None or \
           not mark_uri.startswith('http://creativecommons.org/'):
            return renderer.response(dict(
                _exception='Invalid PD Mark URI.'))

        url, mark_uri = str(url), str(mark_uri)
        
        # need to collect referer-level graph first
        triples = self._first_pass(url, 'mark')
        # determine what the subject uri is based on the referer's rdf graph
        subject = metadata.extract_licensed_subject(url, mark_uri, triples)
        # remotely request for more RDFa following only specific predicates
        # resume building the graph returned from the first pass
        triples = self._triples(url=url, action='deed', depth=1,
                                sink=triples['sink'],
                                subjects=triples['subjects'],
                                redirects=triples['redirects'])
        
        # bail out if an exception occurred in the scraping
        if '_exception' in triples['subjects']:
            return renderer.response(dict(
                _exception=triples['triples']['_exception']))

        # PD Marks include a lang attribute in <html>
        if mark_uri not in self.pdmark_langs.keys():
            lang = support.get_document_locale(mark_uri)
            if lang is None:
                # didn't find a lang attribute in the html
                lang = web.input().get('lang', 'en')
            # cache the lang code based on the deed's uri
            self.pdmark_langs[mark_uri] = lang
        
        # prepare to render messages for this lang
        lang = self.pdmark_langs[mark_uri]
        mark = cc.license.by_uri(str(mark_uri))

        # extra all license relations to check for dual-licensing
        licenses = metadata.get_license_uri(subject, triples)
        cc0 = filter(lambda l: CC0_SELECTOR.has_license(l), licenses) or None
        if cc0: cc0 = cc0[0]
        
        results = {
            'title': metadata.get_title(subject, triples),
            'curator': metadata.get_curator(subject, triples),
            'creator': metadata.get_creator(subject, triples),
            'norms': metadata.get_norms(subject, triples),
            'dual_license': cc0,
            }
        
        results.update({
            'curator_title': metadata.get_title(results['curator'], triples),
            'creator_title': metadata.get_title(results['creator'], triples),
            })
        
        results['marking'] = renderer.render('pd_marking.html',
                                             dict(results,
                                                  work=subject,
                                                  mark_uri=mark.uri,
                                                  mark_title=mark.title(lang),
                                                  mark_version=mark.version))
        
        return renderer.response(results)

application = web.application(urls, globals(),)

if __name__ == "__main__": application.run()

