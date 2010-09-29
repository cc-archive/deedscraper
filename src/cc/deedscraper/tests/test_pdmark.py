import unittest
import base
try:
    import json
except ImportError:
    import simplejson as json

from cc.deedscraper import metadata

CC = lambda pred: "http://creativecommons.org/ns#%s" % pred
SIOC = lambda pred: "http://rdfs.org/sioc/ns#%s" % pred
SIOC_SERVICE = lambda pred: "http://rdfs.org/sioc/services#%s" % pred
POWDER = lambda pred: "http://www.w3.org/2007/05/powder#%s" % pred
DC = lambda pred: "http://purl.org/dc/elements/1.1/%s" % pred
DCT = lambda pred: "http://purl.org/dc/terms/%s" % pred
XHTML = lambda pred: "http://www.w3.org/1999/xhtml/vocab#%s" % pred
FOAF = lambda pred: "http://xmlns.com/foaf/0.1/%s" % pred

REFERER = {'Referer': 'http://creativecommons.org/licenses/by/3.0/us/'}
        
class PDMarkMetadataTests(unittest.TestCase):
    
    def setUp(self):
        self.app = base.test_app()

    def test_get_creator(self):
        """ Returns dct:creator or dc:creator or cc:attributionURL """
        triples = {
            'subjects': [
                'http://example.com',],
            'triples': {
                'http://example.com' : {
                    CC('attributionURL') : [
                        'http://nigerianprince.com'],
                    }
                }
            }
        self.assertEqual(metadata.get_creator('http://example.com',triples),
                         'http://nigerianprince.com')

        triples['triples']['http://example.com'][DC('creator')] = [
            'http://testing.com']
        self.assertEqual(metadata.get_creator('http://example.com',triples),
                         'http://testing.com')

        triples['triples']['http://example.com'][DCT('creator')] = [
            'http://overrides.com']
        self.assertEqual(metadata.get_creator('http://example.com',triples),
                         'http://overrides.com')
        
    def test_get_curator(self):
        """ Returns dct:publisher or dc:publisher """
        triples = {
            'subjects': [
                'http://example.com',],
            'triples': {
                'http://example.com' : {
                    DC('publisher') : [
                        'http://testing.com'],
                    }
                }
            }

        self.assertEqual(metadata.get_publisher('http://example.com',triples),
                         'http://testing.com')

        triples['triples']['http://example.com'][DCT('publisher')] = ['http://overrides.com']
        self.assertEqual(metadata.get_publisher('http://example.com',triples),
                         'http://overrides.com')

        
        
    def test_get_curator_title(self):
        """ Returns the curator's title """
        triples = {
            'subjects': [
                'http://example.com',
                'http://testing.com'],
            'triples': {
                'http://example.com' : {
                    DC('publisher') : [
                        'http://testing.com'],
                    },
                'http://testing.com': {
                    DC('title') : [
                        'Publisher'],
                    }
                }
            }

        self.assertEqual(metadata.get_publisher('http://example.com',triples),
                         'http://testing.com')
        self.assertEqual(metadata.get_title(metadata.get_publisher('http://example.com',triples),triples),
                         'Publisher')

    def test_get_attribution_name(self):
        """ attributionName should fall back to foaf:name of dc:creator """

        triples = {
            'subjects': [
                'http://example.com',
                'http://testing.com'],
            'triples': {
                'http://example.com' : {
                    DC('creator') : [
                        'http://testing.com'],
                    },
                'http://testing.com': {
                    FOAF('name') : [
                        'Seymour Butts'],
                    }
                }
            }

        self.assertEqual(metadata.get_attribution_name('http://example.com',
                                                       triples),
                         'Seymour Butts')

        triples['triples']['http://example.com'][CC('attributionName')] = [
            'Dr. Seymour Butts']

        self.assertEqual(metadata.get_attribution_name('http://example.com',
                                                       triples),
                         'Dr. Seymour Butts')
                                                 
        
        
