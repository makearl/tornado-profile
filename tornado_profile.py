"""Profile a Tornado application via REST."""
import tornado.web
import yappi

__version__ = "1.0.0"
__author__ = "Megan Kearl Patten <megkearl@gmail.com>"


def start_profiling():
    """Start profiler."""
    # POST /profiler
    yappi.start(builtins=False, profile_threads=False)


def is_profiler_running():
    """Return True if the profiler is running."""
    # GET /profiler
    yappi.is_running()


def stop_profiling():
    """Stop the profiler."""
    # DELETE /profiler
    yappi.stop()


def clear_stats():
    """Clear profiler statistics."""
    # DELETE /profiler/stats
    yappi.clear_stats()


def get_statistics():
    """Get profiler statistics."""
    # GET /profiler/stats?sort=cumulative&total=20
    y_func_stats = yappi.get_func_stats()
    pstats = yappi.convert2pstats(y_func_stats)
    pstats.strip_dirs()
    pstats.sort_stats("cumulative").print_stats(20)


class TornadoProfiler(object):

    def __init__(self, prefix="", handler_base_class=None):
        # class UpdatedClass(cls, handler_base_class): pass
        pass

    def get_routes(self):
        return []


def main(port=8888):
    """Run as sample test server."""
    import tornado.ioloop

    routes = [] + TornadoProfiler().get_routes()
    app = tornado.web.Application(routes)
    app.listen(port)
    tornado.ioloop.IOLoop.current().start()


if __name__ == "__main__":
    main(port=8888)
