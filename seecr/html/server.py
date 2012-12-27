
from meresco.core import Observable
from meresco.components.http import ObservableHttpServer, ApacheLogger, PathFilter, FileServer
from dynamichtml import DynamicHtml
from weightless.io import Reactor
from weightless.core import compose, be
from sys import stdout

def dna(reactor, port, dynamic, static, verbose=True):
    apacheLogger = ApacheLogger(stdout) if verbose else ApacheLogger()
    return (Observable(),
        (ObservableHttpServer(reactor, port=port),
            (apacheLogger,
                (PathFilter('/static'),
                    (FileServer(static),)
                ),
                (PathFilter('/', excluding=['/static']),
                    (DynamicHtml([dynamic], reactor=reactor, indexPage='/index'),)
                )
            )
        )
    )

def startServer(**kwargs):
    reactor = Reactor()

    server = be(dna(reactor=reactor, **kwargs))
    list(compose(server.once.observer_init()))

    print "Ready to rumble at", kwargs['port']
    reactor.loop()

