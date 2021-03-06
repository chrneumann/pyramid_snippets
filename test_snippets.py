from pyramid.response import Response
from pyramid_snippets import render_snippets
from unittest import TestCase


def test_non_existing(request):
    out = render_snippets(None, request, '[foo /]')
    assert out == u'<div class="alert alert-error">No snippet with name \'foo\' registered.</div>'


def test_rendering(config, request):
    def foo(context, request):
        return Response(u"Foo")
    config.add_snippet(name='foo', snippet=foo)
    out = render_snippets(None, request, '[foo /]')
    assert out == u'Foo'


def test_arguments(config, request):
    def foo(context, request):
        return Response("{0} - {1}".format(
            request.POST.get('body'),
            request.POST.get('ham')))
    config.add_snippet(name='foo', snippet=foo)
    out = render_snippets(None, request, '[foo ham=egg]Blubber[/foo]')
    assert out == u'Blubber - egg'


def test_baseurl(config, request):
    def foo(context, request):
        return Response(request.application_url)
    config.add_snippet(name='foo', snippet=foo)
    out = render_snippets(None, request, '[foo/]')
    assert out == u'http://example.com'


class TestSnippetsRegexp(TestCase):
    def setUp(self):
        from pyramid_snippets import snippet_regexp
        self.regexp = snippet_regexp
        self.results = []

    def tearDown(self):
        del self.results

    def _sub(self, match):
        infos = match.groupdict()
        if infos['selfclosing'] is None and infos['content'] is None:
            return match.group(0)
        self.results.append(match)
        return 'matched%s' % len(self.results)

    def test_selfclosing(self):
        out = self.regexp.sub(self._sub, "slkdfj [foo egg=ham/] slkdfj")
        assert out == "slkdfj matched1 slkdfj"
        assert len(self.results) == 1
        assert self.results[0].groupdict() == {
            'arguments': ' egg=ham',
            'content': None,
            'escapeclose': '',
            'escapeopen': '',
            'name': 'foo',
            'selfclosing': '/'}
        assert self.results[0].groups() == (
            '', 'foo', ' egg=ham', '/', None, '')

    def test_normal(self):
        out = self.regexp.sub(self._sub, "slkdfj [bar egg=ham]Blubber[/bar] slkdfj")
        assert out == "slkdfj matched1 slkdfj"
        assert len(self.results) == 1
        assert self.results[0].groupdict() == {
            'arguments': ' egg=ham',
            'content': 'Blubber',
            'escapeclose': '',
            'escapeopen': '',
            'name': 'bar',
            'selfclosing': None}
        assert self.results[0].groups() == (
            '', 'bar', ' egg=ham', None, 'Blubber', '')

    def test_escaped(self):
        self.regexp.sub(self._sub, "slkdfj [[foo egg=ham/]] slkdfj")
        assert len(self.results) == 1
        assert self.results[0].groupdict() == {
            'arguments': ' egg=ham',
            'content': None,
            'escapeclose': ']',
            'escapeopen': '[',
            'name': 'foo',
            'selfclosing': '/'}
        assert self.results[0].groups() == (
            '[', 'foo', ' egg=ham', '/', None, ']')

    def test_not_selfclosing(self):
        self.regexp.sub(self._sub, "slkdfj [foo egg=ham] slkdfj")
        assert len(self.results) == 0

    def test_two_not_selfclosing(self):
        self.regexp.sub(self._sub, "slkdfj [foo egg=ham] [bar egg=ham] slkdfj")
        assert len(self.results) == 0

    def test_non_matching_names(self):
        self.regexp.sub(self._sub, "slkdfj [foo egg=ham]Blubber[/bar] slkdfj")
        assert len(self.results) == 0

    def test_quotes_in_args(self):
        out = self.regexp.sub(self._sub, "slkdfj [foo egg='ham/]'/] slkdfj")
        assert out == "slkdfj matched1'/] slkdfj"

    def test_snippet_name_chars(self):
        out = self.regexp.sub(self._sub, "slkdfj [Moo_foo-2000 egg=ham]Blubber[/Moo_foo-2000] slkdfj")
        assert out == "slkdfj matched1 slkdfj"
        assert len(self.results) == 1
        assert self.results[0].groupdict()['name'] == 'Moo_foo-2000'
