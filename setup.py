from distutils.core import setup


about = "Twisted Cred support for Browser ID (Mozilla Persona)."


setup(
    name="txBrowserID",
    version="0.1",
    description=about,
    author="Brian Warner",
    author_email="warner@lothar.com",
    url="https://github.com/warner/browserid-cred",
    license="MIT",
    packages=["browserid"],
    install_requires=["twisted", "pyopenssl"],
    long_description=about)

