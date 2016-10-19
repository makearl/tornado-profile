Profile a Tornado application through a REST API
================================================

.. image:: https://travis-ci.org/makearl/tornado-profile.svg?branch=master
    :target: https://travis-ci.org/makearl/tornado-profile

Add this library to your routes to add a REST API for profiling your Tornado application.

Usage
-----

.. code-block:: python

    routes += TornadoProfiler(prefix='', handler_base_class=BaseHandler)
