browserid-cred
==============

twisted.cred checking for BrowserID/Persona

"Cred" is Twisted's pluggable credential-checking framework: it allows services to remain ignorant of the protocol-specific details of various authentication backends. The [documentation](http://twistedmatrix.com/documents/current/core/howto/cred.html) explains how "Portals", "Realms", "Checkers", "Avatars", and "Minds" all fit together.

This module provides a Cred plugin for BrowserID. It uses the verifier service hosted at persona.org, rather than doing the cryptographic checking locally. To safely connect to this service over SSL, you must provide it with a list of CA roots (in .pem format): the code defaults to reading all cert files from /etc/ssl/certs/ , which should Just Work on many unix-style platforms (but not OS-X).

The server's Portal must be set up with something like the following (note that the audience **must** match the domain through which your site is accessed, since BrowserID assertions are tied to a specific audience):

    from twisted.cred.portal import Portal
    portal = Portal(realm)
    audience = "https://example.com"
    portal.registerChecker(BrowserIDChecker(audience))

The frontend must deliver an assertion string, by using navigator.id.request() and the "onlogin" callback, then sending the assertion to the server via XHR or similar. The web Resource which receives the assertion must submit it to the checker wrapped in a `BrowserIDAssertion` object, like this:

    d = portal.login(BrowserIDAssertion(assertion), None, IFoo)

If the assertion is valid, your Realm's `requestAvatar()` method will be called with an `avatarId` equal to the email address that was successfully claimed. The `portal.login` Deferred will then fire with the usual `(interface, avatar, logout)` tuple (but note that `logout` is always None).

For more details, take a look at the demo application in demo/server.rpy (use "make run" to execute it).
