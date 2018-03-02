from unittest import TestCase

from difflib import unified_diff
from lxml.etree import _Element

from meresco.html.tools.html_to_tag import html_to_tag, html_to_etree, etree_to_data, data_to_tag


class HtmlToTagTest(TestCase):
    def assertEquals_udiff(self, expected, result, n=3):
        exp = expected.splitlines()
        res = result.splitlines()
        diff = unified_diff(exp, res, fromfile='expected', tofile='result', n=3)
        if expected != result:
            self.assertEquals(expected, result, '\n'.join(diff))

    def test_bad_input(self):
        self.assertRaises(ValueError, lambda: html_to_tag(0))

    def test_empty_input(self):
        self.assertEquals('', html_to_tag(None))
        self.assertEquals('', html_to_tag(''))
        self.assertEquals('', html_to_tag(u''))
        self.assertEquals('', html_to_tag(' \t\r\n '))
        self.assertEquals('', html_to_tag(u' \t\r\n '))

    def test_simple_fragment(self):
        expected = """\
def main(tag, **kw):
    with tag('h1'):
        pass
    return
    yield
"""
        self.assertEquals_udiff(expected, html_to_tag('<h1></h1>'))
        self.assertEquals_udiff(expected, html_to_tag('<h1>')) # malformed is fine

        self.fail('TODO')       # more html_to_tag tests

    # html_to_etree
    def test_empty(self):
        self.assertEquals(None, html_to_etree(None))
        self.assertEquals(None, html_to_etree(''))

    def test_fragment_tag_only(self):
        res = html_to_etree('<h1></h1>')
        self.assertEquals('_Element', type(res).__name__)
        self.assertEquals({'tag': 'h1'}, etree_to_data(res))

    def test_fragment_tag_text_and_attrs(self):
        self.assertEquals({
            'tag': 'h1',
            'attribs': {'style': 'color: yellow;'},
            'text': 'text'
        }, etree_to_data(html_to_etree('<h1 style="color: yellow;">text</h1>')))

    def test_fragment_2tag_and_nested(self):
        self.assertEquals({
            'tag': 'div',
            'children': [
                {'tag': 'h1',
                 'text': 'text'
                },
                {'tag': 'p',
                 'children': [
                     {'tag': 'span',
                      'text': 'text'
                     }]
                }
            ]
        }, etree_to_data(html_to_etree('<h1>text</h1><p><span>text</span></p>')))

    def test_fragment_document_with_nested(self):
        self.assertEquals({
            'tag': 'html',
            'children': [
                {'tag': 'head',
                 'children': [
                     {'tag': 'title', 'text': 'ti'}]},
                {'tag': 'body', 'children': [
                    {'tag': 'h1'}]}]
        }, etree_to_data(html_to_etree('<html><head><title>ti</title></head><body><h1></h1></body></html>')))

    # data_to_tag
    def test_data_one_tag(self):
        expected = '''\
def main(tag, **kw):
    with tag('h2'):
        pass
    return
    yield
'''
        self.assertEquals(
            expected,
            data_to_tag({'tag': 'h2'}))

        self.fail('TODO')
        # test & create code for correct convertsion of more things:
        #  - attribs
        #  - text
        #  - tail
        #  - children
        # ... etc.!

    def test_full_cicle(self):
        # Parse html -> to py_str -> exec -> call main with tag -> extract generated html -> parse to data -> compare with expected.
        self.fail('TODO')
