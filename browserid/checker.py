
import re, json
from zope.interface import Interface, implements

import OpenSSL

from twisted.cred.checkers import ICredentialsChecker
from twisted.web.client import Agent, HTTPConnectionPool, Headers
from twisted.web.iweb import IBodyProducer
from twisted.internet import reactor, defer, protocol, ssl
from twisted.python.filepath import FilePath

class IBrowserIDCredentials(Interface):
    pass
class BrowserIDAssertion:
    implements(IBrowserIDCredentials)
    def __init__(self, assertion):
        self.assertion = assertion

class BadBrowserIDCredentials(Exception):
    pass

VERIFIER_URL = "https://browserid.org/verify"
CERTS_DIR = "/etc/ssl/certs"

# this code is copied from twisted/internet/endpoints.py, and will eventually
# be made public so we don't have to copy it

def _loadCAsFromDir(directoryPath):
    """
    Load certificate-authority certificate objects in a given directory.

    @param directoryPath: a L{FilePath} pointing at a directory to load .pem
        files from.

    @return: a C{list} of L{OpenSSL.crypto.X509} objects.
    """

    caCerts = {}
    for child in directoryPath.children():
        if not child.basename().split('.')[-1].lower() == 'pem':
            continue
        try:
            data = child.getContent()
        except IOError:
            # Permission denied, corrupt disk, we don't care.
            continue
        try:
            theCert = ssl.Certificate.loadPEM(data)
        except (ssl.SSL.Error, OpenSSL.crypto.Error):
            # Duplicate certificate, invalid certificate, etc.  We don't care.
            pass
        else:
            caCerts[theCert.digest()] = theCert.original
    return caCerts.values()


class GetBodyProtocol(protocol.Protocol):
    def __init__(self, deferred):
        self.deferred = deferred
        self.buf = ''
    def dataReceived(self, bytes):
        self.buf += bytes
    def connectionLost(self, reason):
        self.deferred.callback(self.buf)

def getBody(response):
    d = defer.Deferred()
    response.deliverBody(GetBodyProtocol(d))
    return d

class MemoryBodyProducer:
    implements(IBodyProducer)
    def __init__(self, body):
        self.body = body
        self.length = len(body)
    def startProducing(self, consumer):
        consumer.write(self.body)
        return defer.succeed(None)

class _NormalToWebContextFactory:
    def __init__(self, factory):
        self.factory = factory
    def getContext(self, host, port):
        return self.factory.getContext()

class BrowserIDChecker:
    implements(ICredentialsChecker)
    credentialInterfaces = [IBrowserIDCredentials]
    
    def __init__(self, audience,
                 verifierURL=VERIFIER_URL,
                 certsDir=CERTS_DIR,
                 persistentConnections=True):
        assert re.search("^https?://", audience), "'audience' must be a domain like 'https://example.com'"
        self.audience = audience
        self.verifier_url = verifierURL
        caCerts = _loadCAsFromDir(FilePath(certsDir))
        sslFactory = ssl.CertificateOptions(method=ssl.SSL.SSLv23_METHOD,
                                            verify=True, caCerts=caCerts)
        cf = _NormalToWebContextFactory(sslFactory)
        pool = HTTPConnectionPool(reactor, persistent=persistentConnections)
        self.agent = Agent(reactor, contextFactory=cf, pool=pool)

    def requestAvatarId(self, credentials):
        # 'credentials' is a single string, the browserid assertion coming
        # from the web client. We send it to the online verifier service for
        # checking. In the long run (i.e. after the protocol has settled
        # down), it is better (i.e. removes browserid.org from the reliance
        # set) to perform the cryptographic verification locally. This will
        # require fetching a pubkey from the IdP's /.well-known/ directory
        # and performing signature checking with the result.
        body = json.dumps({"assertion": credentials.assertion,
                           "audience": self.audience})
        headers = Headers()
        headers.addRawHeader("Content-Type", "application/json")
        d = self.agent.request("POST", self.verifier_url,
                               headers=headers,
                               bodyProducer=MemoryBodyProducer(body))
        d.addCallback(getBody)
        d.addCallback(json.loads)
        d.addCallback(self._parse_response)
        return d

    def _parse_response(self, response):
        if response["status"] == "okay":
            return response["email"]
        print "bad"
        print response
        print "bad"
        raise BadBrowserIDCredentials()

class DetailedBrowserIDChecker(BrowserIDChecker):
    def _parse_response(self, response):
        if response["status"] == "okay":
            return response
        raise BadBrowserIDCredentials()

if __name__ == '__main__':
    import sys
    assertion = sys.argv[1]
    d = defer.Deferred()
    reactor.callLater(0, d.callback, "http://localhost:8081")
    d.addCallback(BrowserIDChecker)
    d.addCallback(lambda c: c.requestAvatarId(assertion))
    def _done(res):
        print res
        reactor.stop()
    d.addBoth(_done)
    reactor.run()
