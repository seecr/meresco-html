from lxml.etree import Element
from lxml.html.html5parser import document_fromstring, fragments_fromstring, fromstring, HTMLParser

from unicodedata import normalize

_html5Parser = HTMLParser(
    # tree=TreeBuilder  -> done by lxml.html.html5parser.HTMLParser.__init__
    strict=False,                 # default
    namespaceHTMLElements=False,  # non-default
    debug=False                   # default
)


def html_to_tag(in_str):
    tree = html_to_etree(in_str)
    if tree is None:
        return ''

    data = etree_to_data(tree)
    return data_to_tag(data)

def html_to_etree(in_str):
    """
    Parses a tree of possibly malformed HTML5, according to WHATWG HTML5 rules.

    Result is either:
     - parsed input, or;
     - if multiple fragments (> 1 top-level tags) are given: parsed input wrapped in either a `div' or `span', or;
     - None for empty input.
    """
    if in_str is None:
        return None

    if not isinstance(in_str, basestring):
        raise ValueError('input must be a string')

    in_str = _nfc(in_str).strip()

    if not in_str:
        return None

    return fromstring(in_str, parser=_html5Parser)

def _ident_ln(ident, a_str):
    return (' ' * ident) + a_str + '\n'

def data_to_tag(d):      # TODO: use trampoline i.s.o. recusive calls (deep nesting support?)
    _pre = 'def main(tag, **kw):\n'
    ident = 4
    _post = _ident_ln(ident, 'return') + _ident_ln(ident, 'yield')
    def dtt(v, ident, d):
        def step(acc, ident_d):
            # Unpack & save originals
            ident, d = ident_d
            orig_ident = ident
            ident = ident + 4

            # Unpack element-data
            tag = d['tag']
            ch = d.get('children')

            # write `with tag'
            acc += _ident_ln(orig_ident, "with tag('{}'):".format(tag))

            # write `inside "with tag"'
            if not ch:
                acc += _ident_ln(ident, 'pass')
            else:
                raise Hell

            return acc

        return step(v, (ident, d))

    tags = dtt('', ident, d)
    return _pre + tags + _post

def _nfc(aString):
    """
    Normalization Form 'C'

    Canonical decomposition followed by canonical composition
    """
    return normalize('NFC', unicode(aString)).encode('utf-8')

def _():
    def first(iterable, default=None):
        if iterable:
            for v in iterable:
                return v
        return default

    def iter_ch(el):
        return el.iterchildren(tag=Element)

    def has_ch(el):
        if first(iter_ch(el)) is not None:
            return True
        return False

    def attribs(el):
        as_ = el.attrib
        return {_nfc(k): _nfc(as_[k]) for k in as_.keys()}


    def etree_to_data(el):      # TODO: use trampoline i.s.o. recusive calls (deep nesting support?)
        el_d = {
            'tag': _nfc(el.tag),
        }
        attrs = attribs(el)
        if attrs:
            el_d['attribs'] = attrs

        if el.text:
            el_d['text'] = _nfc(el.text)

        if el.tail:
            el_d['tail'] = _nfc(el.tail)

        if has_ch(el):
            el_d['children'] = map(etree_to_data, iter_ch(el))

        return el_d

    return etree_to_data

etree_to_data = _()
del _
