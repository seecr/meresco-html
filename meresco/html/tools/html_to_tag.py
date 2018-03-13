import re
from lxml.etree import Element, parse, XMLParser, QName
from lxml.html.html5parser import document_fromstring, fragments_fromstring, fromstring, HTMLParser
from StringIO import StringIO

from unicodedata import normalize

from meresco.components import lxmltostring


def html_to_tag(in_str, remove_blank_text=True):
    tree = html_to_etree(in_str, remove_blank_text=remove_blank_text)
    if tree is None:
        return ''

    data = etree_to_data(tree)
    return data_to_tag(data)

def _etree_mutate_fix_localname(etree):
    for _x in etree.iter(Element):    # side-effect to remove some (wrongfully) surviving namespace stuff from HTML(5)Parser
        if _x.tag != QName(_x).localname:
            _x.tag = QName(_x).localname

    return etree

def html_to_etree(in_str, remove_blank_text=True):
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

    # Double-parse to remove (hopefully irrelevant) whitespace - some not-so-irrelevant whitespace will most likely be removed too
    etree = fromstring(in_str, parser=_html5Parser) # ATTENTION: tag/attributes namespace-info mangled here due to html5lib bugs.
    _etree_mutate_fix_localname(etree)
    if remove_blank_text:
        s = lxmltostring(etree)
        etree = parse(StringIO(s), parser=_xmlParser)
        etree = fromstring(lxmltostring(etree), parser=_html5Parser)
        _etree_mutate_fix_localname(etree)  # and they spawn again after fromstring, so remove them again.

    return etree.getroot() if hasattr(etree, 'getroot') else etree

def _():                        # close over helpers not needed elsewhere.
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


    def etree_to_data(el):
        el_d = {
            'tag': _nfc(QName(el).localname), # A'la HTML5 no namespaces here, so be explicit.
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

def data_to_tag(d):
    _pre = 'def main(tag, **kw):\n'
    ident = 4
    _post = _ident_ln(ident, 'return') + _ident_ln(ident, 'yield')
    def dtt(acc, ident, d):
        # save originals & ident
        orig_ident = ident
        ident = ident + 4

        # Unpack element-data
        tag = d['tag']
        attribs = d.get('attribs')
        text = d.get('text')
        tail = d.get('tail')
        ch = d.get('children')

        # write `with tag'
        acc += _ident_ln(orig_ident, "with tag('{}'{}):".format(tag, _attribs_f(attribs)))

        # write `inside "with tag"'
        if text:
            acc += _yield_str(ident, text)

        if not (ch or text):
            acc += _ident_ln(ident, 'pass')

        if ch:
            acc = reduce(lambda acc, d: dtt(acc, ident, d), ch, acc)

        if tail:
            acc += _yield_str(orig_ident, tail)

        return acc

    tags = dtt('', ident, d)
    return _pre + tags + _post


# Constants
VALID_NON_UNICODE_IDENTIFIER_RE = re.compile(r'^[_a-zA-Z][_a-zA-Z0-9]*$')
PY_KEYWORDS = { # from: https://docs.python.org/3.3/reference/lexical_analysis.html#keywords
    'False',      'class',      'finally',    'is',         'return',
    'None',       'continue',   'for',        'lambda',     'try',
    'True',       'def',        'from',       'nonlocal',   'while',
    'and',        'del',        'global',     'not',        'with',
    'as',         'elif',       'if',         'or',         'yield',
    'assert',     'else',       'import',     'pass',
    'break',      'except',     'in',         'raise',
}

_html5Parser = HTMLParser(
    # tree=TreeBuilder  -> done by lxml.html.html5parser.HTMLParser.__init__
    strict=False,                 # default
    namespaceHTMLElements=False,  # non-default
    debug=False                   # default
)

_xmlParser = XMLParser(
    encoding='utf-8',
    remove_blank_text=True,
    huge_tree=True,
    recover=True,   # ATTENTION: recover=True should *never* be needed at this point, but html5lib is broken in it's namespace-support (reading namespaced stuff correctly).  Disable this and see HtmlToTagTest.test_full_cicle fail horribly.

    # Default from LXML:
    # attribute_defaults=False,
    # dtd_validation=False,
    # load_dtd=False,
    # no_network=True,
    # ns_clean=False,
    # recover=False,
    # XMLSchema=None,
    # resolve_entities=True,
    # remove_comments=False,
    # remove_pis=False,
    # strip_cdata=True,
    # collect_ids=True,
    # target=None,
    # compact=True
)

# Various helpers
def _nfc(aString):
    """
    Normalization Form 'C'

    Canonical decomposition followed by canonical composition
    """
    return normalize('NFC', unicode(aString)).encode('utf-8')

def _ident_ln(ident, a_str, newline=True):
    return (' ' * ident) + a_str + ('\n' if newline else '')

def _simple_str_literal(text):
    return '"{}"'.format(text.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n'))

def _text_as_string_literal(ident, text):
    # ident all lines except the first accoring to ident
    # returns a string-literal or an expression resulting in a string.
    if not text:
        return '""'

    _end = ')'
    if '\n' in text:
        v = '"\\n".join([\n'
        lines = text.split('\n')
        numLines = len(lines)
        for i, l in enumerate(lines):
            v += _ident_ln(ident, _simple_str_literal(l), newline=False)
            if not ((i + 1) == numLines): # not at end
                v += ',\n'

        v += '])'

    else:
        v = _simple_str_literal(text)

    return v

def _yield_str(ident, text):
    return _ident_ln(ident, 'yield ' + _text_as_string_literal(ident+6, text))  # 'yield ' -> 6 chars

def _attribs_f(attribs):
    if not attribs:
        return ''

    # special cases:
    new_class = None
    if 'class' in attribs:
        new_class = attribs['class'].strip().split()

    # no reserved words as keyword-argument & remove special cases:
    attribs = {(k+'_' if k in PY_KEYWORDS else k): v for (k, v) in attribs.iteritems() if k not in {'class'}}

    # partition into kw_args and kw_dict values:
    def f(acc, kv):
        kw_args, kw_dict = acc
        k, v = kv
        if VALID_NON_UNICODE_IDENTIFIER_RE.match(k):
            kw_args.append((k, v))
        else:
            kw_dict.append((k, v))

        return acc              # in-place updated

    kw_args, kw_dict = reduce(
        f,
        attribs.iteritems(),
        [([('class_', new_class)] if new_class else []), []]) # re-add special cases
    kw_args.sort()
    kw_dict.sort()

    def list_to_list_lit_with_str_lit(l):
        return '[' + ', '.join(map(_simple_str_literal, l)) + ']'

    val = ''
    for k, v in kw_args:
        val += ', '
        val += '{}={}'.format(k, _simple_str_literal(v) if isinstance(v, str) else list_to_list_lit_with_str_lit(v))

    if kw_dict:
        val += ', **{'

        for i, (k, v) in enumerate(kw_dict):
            if i:
                val += ', '

            val += _simple_str_literal(k)
            val += '='
            val += _simple_str_literal(v) if isinstance(v, str) else list_to_list_lit_with_str_lit(v)

        val += '}'

    return val
