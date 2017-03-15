moody
=====

Moody is a CLI for the Mars ODE PDS Node. It implements some basic
queries against the ODE to download certain files from the ODE. Currently it is focused on
providing commands to download HiRISE and CTX raw files by productId instead of by wgeting the url directly.

The name 'moody' came from thinking about Mars, the ODE, and Python at the same time (but in a good way).

Installation
------------
Eventually this will be in pypi, but for now just clone and run ``python setup.py install``.
Moody will show up in your path as an executable.

Chat
----

There is a moody specific gitter room, but the maintainers also hang out in the `open planetary slack <https://openplanetary.slack.com/>`_

|Gitter|

.. |Gitter| image:: https://badges.gitter.im/AndrewAnnex/moody.svg
   :target: https://gitter.im/AndrewAnnex/moody?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge

Usage
-----

Moody by default will use https to download and query the ODE, but
this behavior can be changed by appending ``--nohttps`` to the end of any command.

Download a CTX EDR IMG file::

    moody ctx-edr P16_007428_1845

Will download the ctx edr IMG file ``P16_007428_1845_XN_04N029W.IMG`` to the current working directory

Download all HiRISE EDR IMG files for a particular observation::

    moody hirise-edr ESP_028335_1755

Will download all HiRISE EDR images for the ``ESP_028335_1755`` observation to the current working directory.

Commands
--------
A list of comands and usages are listed below and can be found directly from moody using the ``--help`` flag::

    moody [HTTPS]
    moody [--use-https HTTPS]

    moody ctx-edr PID [CHUNK_SIZE]
    moody ctx-edr --pid PID [--chunk-size CHUNK_SIZE]

    moody hirise-edr PID [CHUNK_SIZE]
    moody hirise-edr --pid PID [--chunk-size CHUNK_SIZE]

