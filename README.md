OVH API CLI
===========

| OVH API CLI is a command line tool that allows usage of OVH’s API from
| within a terminal.

Installation
------------

::

    python setup.py install
    source /etc/bash_completion.d/ovhcli

Usage
-----

Put credentials inside ``~/.ovhcli``

::

     $ echo '{\
         "AK": "Account_KEY",\
         "AS": "Account_SECRET",\
         "CK": "Consumer_KEY"\
     } > ~/.ovhcli

Use tab to trigger the completion

::

     $ ovhcli [TAB]
     $ ovhcli /[TAB][TAB]
     allDom                housing               freefax               directadmin           overTheBox            support
     auth                  installationTemplate  horizonView           office                database              telephony
     ...
     $ ovhcli /me
     me                              bill                            history                         subAccount
     backupCode                      changeEmail                     order                           subscription
     ...
     $ ovhcli /me/contact [TAB][TAB]
     get                             put
     $ ovhcli /me/contact PUT [TAB][TAB]
     --city=                         --line2=                        --province=
     --country=                      --line3=                        --zip=
     --line1=                        --otherDetails=

    # some parameters can be automagically listed:
    $ ovhcli /me/contact/\{contactId\} GET --contactId=[TAB][TAB]
    contact1                         contact2                        contact3