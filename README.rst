====================
Download Station API
====================


.. image:: https://img.shields.io/pypi/v/download_station_api.svg
        :target: https://pypi.python.org/pypi/download_station_api

.. image:: https://img.shields.io/travis/paul-armstrong-dev/download_station_api.svg
        :target: https://travis-ci.com/paul-armstrong-dev/download_station_api

.. image:: https://readthedocs.org/projects/download-station-api/badge/?version=latest
        :target: https://download-station-api.readthedocs.io/en/latest/?version=latest
        :alt: Documentation Status




Small python wrapper for interacting with the Synology Download Station.


* Free software: MIT license
* Documentation: https://download-station-api.readthedocs.io.


Features
--------

* TODO: Write this readme


From Synology docs
    5 Basic elements of requests to their APIS
         API name: Name of the API requested
         version: Version of the API requested
         path: cgi path of the API. The path information can be retrieved by
            requesting SYNO.API.Info
         method: Method requested
         _sid: Authorized session ID. Each API request should pass a sid value
            via either HTTP

GET
/webapi/<CGI_PATH>?api=<API_NAME>&version=<VERSION>&method=<METHOD>[&<PARAMS>][&_sid=<SID>]


Credits
-------

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
