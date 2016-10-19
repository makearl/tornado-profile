"""Profile a Tornado application via REST."""
from operator import itemgetter

import tornado.web
import yappi

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


def get_profiler_statistics(sort="cum_time", count=20):
    """Return profiler statistics.

    :param str sort: dictionary key to sort by
    :param int|None count: the number of results to return, None returns all results.
    """
    json_stats = []
    pstats = yappi.convert2pstats(yappi.get_func_stats())
    pstats.strip_dirs()

    for func, func_stat in pstats.stats.iteritems():
        path, line, func_name = func
        cc, num_calls, total_time, cum_time, callers = func_stat
        json_stats.append({
            "path": path,
            "line": line,
            "func_name": func_name,
            "num_calls": num_calls,
            "total_time": total_time,
            "total_time_per_call": total_time/num_calls if total_time else 0,
            "cum_time": cum_time,
            "cum_time_per_call": cum_time/num_calls if cum_time else 0
        })

    return sorted(json_stats, key=itemgetter(sort))[:count]


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
