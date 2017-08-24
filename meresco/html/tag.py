from xml.sax.saxutils import quoteattr

class Tag(object):
    def __init__(self, write, tagname, **attrs):
        self.attrs = attrs
        self.write = write
        self.attrs['tag'] = tagname

    def set(self, name, value):
        self.attrs[name] = value
        return self

    def append(self, name, value):
        self.attrs[name].append(value)
        return self

    def delete(self, key):
        self.attrs.pop(key, None)
        return self

    def __enter__(self):
        self.tag = self.attrs.pop('tag', None)
        if not self.tag:
            return
        write = self.write
        write('<')
        write(self.tag)
        for k, v in sorted((k,v) for k,v in self.attrs.iteritems() if v):
            write(' ')
            write(k)
            write('=')
            write(quoteattr(' '.join(v) if hasattr(v, '__iter__') else v))
        if self.tag in ['br', 'hr']:
            write('/')
            self.tag = None
        write('>')

    def __exit__(self, *a, **kw):
        if self.tag:
            write = self.write
            write('</')
            write(self.tag)
            write('>')

class TagFactory(object):
    def __init__(self, stream):
        self.stream = stream
    def __call__(self, *args, **kwargs):
        return Tag(self.stream.write, *args, **kwargs)
