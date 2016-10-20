Profile a Tornado application through a REST API
================================================

.. image:: https://travis-ci.org/makearl/tornado-profile.svg?branch=master
    :target: https://travis-ci.org/makearl/tornado-profile

Add this library to your routes to add a REST API for profiling your Tornado application.

Usage
-----

.. code-block::python

    import tornado

    routes += TornadoProfiler().get_routes()
    app = tornado.web.Application(routes)
    app.listen(port)
    tornado.ioloop.IOLoop.current().start()

    # Create with optional route prefix and base class for handlers
    routes += TornadoProfiler(prefix="", handler_base_class=custom_base_class).get_routes()



API
---

.. code-block::

    # Start the profiler
    POST /profiler

    # Stop the profiler
    DELETE /profiler

    # Get the profiler status
    GET /profiler
    {"running": true/false}

    # Get the profiler statistics
    GET /profiler/stats
    {
        "statistics": [
            {
                "path": ...,
                "line": ...,
                "func_name": ...,
                "num_calls": ...,
                "total_time": ...,
                "total_time_per_call": ...,
                "cum_time": ...,
                "cum_time_per_call": ...
            }
            ...
        ]
    }

    # Clear the profiler statistics
    DELETE /profiler/stats


