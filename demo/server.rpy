import json
from zope.interface import Interface, implements
from twisted.web import server, static
from twisted.web.resource import Resource
from twisted.cred.portal import IRealm, Portal

from browserid import checker


# this part is generic, and depends only upon how your web application likes
# to manage accounts

class IAccount(Interface):
    pass # marker for callers who want these Account objects

class Account:
    def __init__(self, email):
        self.email = email
        # put other account-specific stuff here

class AccountRealm:
    implements(IRealm)

    def requestAvatar(self, avatarId, mind, *interfaces):
        if IAccount in interfaces:
            # this is a good place to pull information from a DB
            avatar = Account(avatarId)
            logout = None
            return (IAccount, avatar, logout)
        raise NotImplementedError("no interface")


# This part is BrowserID-specific, and assumes that your HTML+JS frontend
# will deliver a BrowserID assertion as a POST to the "/login" URL.

class Login(Resource):
    def __init__(self, portal):
        Resource.__init__(self)
        self.portal = portal

    def render_POST(self, req):
        body = json.load(req.content)
        credentials = checker.BrowserIDAssertion(body["assertion"])
        d = portal.login(credentials, None, IAccount)
        def _done(stuff):
            interface, avatar, logout = stuff
            account = avatar
            # We're logged in! You might actually want to set a session
            # cookie and maintain a table that maps it to this Account
            # object. Assertions are very short lived (5 minutes), so this
            # demo is basically one-shot.
            req.setHeader("content-type", "application/json")
            req.write(json.dumps({"results": "logged in as "+account.email}))
            req.finish()
        d.addCallback(_done)
        return server.NOT_DONE_YET

realm = AccountRealm()
portal = Portal(realm)
# the 'audience' *must* match the domain this page is served from: assertions
# are tied to a specific audience.
audience = "http://localhost:8081"
portal.registerChecker(checker.BrowserIDChecker(audience, certsDir="../certs"))

root = static.File(".")
root.putChild("login", Login(portal))

resource = root
