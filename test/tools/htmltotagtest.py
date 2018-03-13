# -*- coding: utf-8 -*-
from seecr.test import SeecrTestCase, CallTrace

from difflib import unified_diff
from lxml.etree import _Element

from weightless.core import asString
from meresco.components.http.utils import parseResponse
from meresco.html import DynamicHtml

from meresco.html.tools.html_to_tag import html_to_tag, html_to_etree, etree_to_data, data_to_tag, _text_as_string_literal, _simple_str_literal, VALID_NON_UNICODE_IDENTIFIER_RE


class HtmlToTagTest(SeecrTestCase):
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

    def test_simple_str_literal(self):
        # lone newline
        self.assertEquals('"\\n"', _simple_str_literal('\n'))

                # double quoted (by default)
        self.assertEquals('""', _simple_str_literal(''))           # ident is ignored for non-newline text
        self.assertEquals('"text"', _simple_str_literal('text'))  # ident is ignored for non-newline text
        self.assertEquals('" te xt "', _simple_str_literal(' te xt '))

        # double-quote escaped
        self.assertEquals(r'"\""', _simple_str_literal('"'))
        self.assertEquals(r'"\"\"with\"-text"', _simple_str_literal('""with"-text'))

        # backslash too
        self.assertEquals(r'"\\"', _simple_str_literal('\\'))

        # with newlines
        self.assertEquals('"ape\\nnut\\nmies\\n"', _simple_str_literal('ape\nnut\nmies\n'))

    def test_escape_text(self):
        # double quoted (by default)
        self.assertEquals('""', _text_as_string_literal(0, ''))           # ident is ignored for non-newline text
        self.assertEquals('"text"', _text_as_string_literal(99, 'text'))  # ident is ignored for non-newline text
        self.assertEquals('" te xt "', _text_as_string_literal(0, ' te xt '))

        # double-quote escaped
        self.assertEquals(r'"\""', _text_as_string_literal(0, '"'))
        self.assertEquals(r'"\"\"with\"-text"', _text_as_string_literal(0, '""with"-text'))

        # backslash too
        self.assertEquals(r'"\\"', _text_as_string_literal(0, '\\'))

        # with newlines
        self.assertEquals('"\\n".join([\n"ape",\n"nut",\n"mies",\n""])', _text_as_string_literal(0, 'ape\nnut\nmies\n'))
        self.assertEquals('"\\n".join([\n  "ape",\n  "nut",\n  "mies",\n  ""])', _text_as_string_literal(2, 'ape\nnut\nmies\n'))
        self.assertEquals('"\\n".join([\n   "",\n   ""])', _text_as_string_literal(3, '\n'))
        self.assertEquals('"\\n".join([\n"x",\n"y\\"\\\\\r"])', _text_as_string_literal(0, 'x\ny"\\\r'))

    def test_identifiers_re(self):
        def f(maybe_identifier_txt):
            return bool(VALID_NON_UNICODE_IDENTIFIER_RE.match(maybe_identifier_txt))

        # not
        self.assertEquals(False, f(''))
        self.assertEquals(False, f('with space'))
        self.assertEquals(False, f('0'))
        self.assertEquals(False, f('012345abcABC'))
        self.assertEquals(False, f('ë'))  # Would be valid iff unicode taken into account.

        # is
        self.assertEquals(True, f('a'))
        self.assertEquals(True, f('id_'))
        self.assertEquals(True, f('id'))
        self.assertEquals(True, f('_'))
        self.assertEquals(True, f('_a'))
        self.assertEquals(True, f('_A'))
        self.assertEquals(True, f('class'))
        self.assertEquals(True, f('_0'))
        self.assertEquals(True, f('_012345'))
        self.assertEquals(True, f('_012345abcABC'))
        self.assertEquals(True, f('ABC'))

    def test_data_one_tag_all(self):
        expected = '''\
def main(tag, **kw):
    with tag('div', and_="value", class_=["val1", "val2"], key="or", **{"a-"=["dashing", "dash"], "with-dash"="-"}):
        yield "inside"
    yield "after"
    return
    yield
'''
        self.assertEquals(
            expected,
            data_to_tag({
                'tag': 'div',
                'attribs': {
                    'key': 'or',
                    'and': 'value',
                    'class': 'val1 val2',
                    'a-': ['dashing', 'dash'],
                    'with-dash': '-'
                },
                'text': 'inside',
                'tail': 'after',
            }))

    def test_data_tag_nested(self):
        expected = '''\
def main(tag, **kw):
    with tag('span', key="or"):
        yield "inside"
        with tag('a', href="#"):
            yield "hier"
        yield "between"
        with tag('a'):
            yield "daar"
        yield "inside-after"
    return
    yield
'''
        self.assertEquals(
            expected,
            data_to_tag({
                'tag': 'span',
                'attribs': {
                    'key': 'or',
                },
                'text': 'inside',
                'children': [
                    {'tag': 'a',
                     'attribs': {
                         'href': '#',
                     },
                     'text': 'hier',
                     'tail': 'between'},
                    {'tag': 'a',
                     'text': 'daar',
                     'tail': 'inside-after'}]}))

    def test_full_cicle(self):
        # Parse html -> to py_str -> exec -> call main with tag -> extract generated html -> parse to data -> compare with expected.
        def f(html_text, remove_blank_text=None):
            kw = {}
            if remove_blank_text is not None:
                kw['remove_blank_text'] = remove_blank_text

            return etree_to_data(html_to_etree(processTemplate(self, html_to_tag(html_text, **kw)), **kw))

        # simple
        self.assertEquals(
            {'tag': 'h1', 'text': 'Hi!'},
            f('<h1>Hi!</h1>'))

        # nested with "irrelevant" whitespace removed.
        chicken_soup = '''\
<html lang="en">
  <head>
    <title>Hello</title>
  </head>
  <body>
    <div id="container">
      <h1 class="red hero">Welcome !</h1>
      <p>
            According to Dr. Jason chicken soup is one of the <strong>best</strong> soups invented.
      </p>
    </div>
  </body>
</html>'''
        self.assertEquals(
            {'tag': 'html',
             'attribs': {'lang': 'en'},
             'children': [
                 {'tag': 'head',
                  'children': [
                      {'tag': 'title', 'text': 'Hello'}]},
                 {'tag': 'body',
                  'children': [
                      {'tag': 'div',
                       'attribs': {'id': 'container'},
                       'children': [
                           {'tag': 'h1',
                            'attribs': {'class': 'red hero'},
                            'text': 'Welcome !'},
                           {'tag': 'p',
                            'text': '\n            According to Dr. Jason chicken soup is one of the ',
                            'children': [
                                {'tag': 'strong',
                                 'text': 'best',
                                 'tail': ' soups invented.\n      ',
                                 }]}]}]}]},
            f(chicken_soup))

        # nested without "irrelevant" whitespace removed
        self.assertEquals(
            {'tag': 'html',
             'attribs': {'lang': 'en'},
             'children': [
                 {'tag': 'head',
                  'text': '\n    ',
                  'tail': '\n  ',
                  'children': [
                      {'tag': 'title',
                       'text': 'Hello',
                       'tail': '\n  ',
                      }],
                 },
                 {'tag': 'body',
                  'text': '\n    ',
                  'children': [
                      {'tag': 'div',
                       'text': '\n      ',
                       'tail': '\n  \n',
                       'attribs': {'id': 'container'},
                       'children': [
                           {'tag': 'h1',
                            'text': 'Welcome !',
                            'tail': '\n      ',
                            'attribs': {'class': 'red hero'},
                           },
                           {'tag': 'p',
                            'text': '\n            According to Dr. Jason chicken soup is one of the ',
                            'tail': '\n    ',
                            'children': [
                                {'tag': 'strong',
                                 'text': 'best',
                                 'tail': ' soups invented.\n      ',
                                }],
                           }],
                      }],
                 }],
            },
            f(chicken_soup, remove_blank_text=False))

def processTemplate(self, template):
    # print '>>>', template
    open(self.tempdir+'/afile.sf', 'w').write(template)
    d = DynamicHtml([self.tempdir], reactor=CallTrace('Reactor'))
    header, body = parseResponse(asString(d.handleRequest(path='/afile')))
    if header['StatusCode'] != '200':
        print body
        raise
    return body
