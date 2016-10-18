Profile a Tornado application through a REST API
================================================

Add this library to your routes to add a REST API for profiling your Tornado application.

Usage
-----

.. code-block:: python

    routes += TornadoProfiler(prefix='', handler_base_class=BaseHandler)
