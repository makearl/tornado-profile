"""Profile a Tornado application via REST."""

import cProfile
import logging
import pstats
import StringIO
import tornado.web
import yappi

from operator import itemgetter

__author__ = "Megan Kearl Patten <megkearl@gmail.com>"


logger = logging.getLogger(__name__)


def start_profiling():
    """Start profiler."""
    # POST /profiler
    yappi.start(builtins=False, profile_threads=False)


def is_profiler_running():
    """Return True if the profiler is running."""
    # GET /profiler
    return yappi.is_running()


def stop_profiling():
    """Stop the profiler."""
    # DELETE /profiler
    yappi.stop()


def clear_stats():
    """Clear profiler statistics."""
    # DELETE /profiler/stats
    yappi.clear_stats()


def get_profiler_statistics(sort="cum_time", count=20, strip_dirs=True):
    """Return profiler statistics.

    :param str sort: dictionary key to sort by
    :param int|None count: the number of results to return, None returns all results.
    :param bool strip_dirs: if True strip the directory, otherwise return the full path
    """
    json_stats = []
    pstats = yappi.convert2pstats(yappi.get_func_stats())
    if strip_dirs:
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

    return sorted(json_stats, key=itemgetter(sort), reverse=True)[:count]


class YappiProfileStatsHandler(tornado.web.RequestHandler):
    def set_default_headers(self):
        self.set_header('Content-Type', 'application/json')

    def get(self):
        """Return current profiler statistics."""

        sort = self.get_argument('sort', 'cum_time')
        count = self.get_argument('count', 20)
        strip_dirs = self.get_argument('strip_dirs', True)
        error = ''
        sorts = ('num_calls', 'cum_time', 'total_time',
                 'cum_time_per_call', 'total_time_per_call')
        if sort not in sorts:
            error += "Invalid `sort` '%s', must be in %s." % (sort, sorts)
        try:
            count = int(count)
        except (ValueError, TypeError):
            error += "Can't cast `count` '%s' to int." % count
        if count <= 0:
            count = None
        strip_dirs = str(strip_dirs).lower() not in ('false', 'no', 'none',
                                                     'null', '0', '')
        if error:
            self.write({'error': error})
            self.set_status(400)
            self.finish()
            return

        try:
            statistics = get_profiler_statistics(sort, count, strip_dirs)
            self.write({'statistics': statistics})
            self.set_status(200)
        except TypeError:
            logger.exception('Error while retrieving profiler statistics')
            self.write({'error': 'No stats available. Start and stop the profiler before trying to retrieve stats.'})
            self.set_status(404)

        self.finish()

    def delete(self):
        """Clear profiler statistics."""
        clear_stats()
        self.set_status(204)
        self.finish()


class YappiProfilerHandler(tornado.web.RequestHandler):
    def set_default_headers(self):
        self.set_header('Content-Type', 'application/json')

    def post(self):
        """Start a new profiler."""
        if is_profiler_running():
            self.set_status(201)
            self.finish()
            return

        start_profiling()
        self.set_status(201)
        self.finish()

    def delete(self):
        """Stop the profiler."""
        stop_profiling()
        self.set_status(204)
        self.finish()

    def get(self):
        """Check if the profiler is running."""
        running = is_profiler_running()
        self.write({"running": running})
        self.set_status(200)
        self.finish()


class CProfileWrapper(object):
    """Wrap cProfile profiler so that it is static between request handlers"""

    profiler = None
    running = False


class CProfileStatsDumpHandler(tornado.web.RequestHandler):

    profiler = CProfileWrapper.profiler
    running = CProfileWrapper.running

    def set_default_headers(self):
        self.set_header('Content-Type', 'application/json')

    def post(self):
        """Dump current profiler statistics into a file."""
        filename = self.get_argument('filename', 'dump.prof')
        CProfileWrapper.profiler.dump_stats(filename)
        self.finish()


class CProfileStatsHandler(tornado.web.RequestHandler):

    profiler = CProfileWrapper.profiler
    running = CProfileWrapper.running
    
    def set_default_headers(self):
        self.set_header('Content-Type', 'application/json')

    def get(self):
        """Return current profiler statistics."""
        CProfileWrapper.profiler.print_stats()
        s = StringIO.StringIO()
        sortby = 'cumulative'
        ps = pstats.Stats(CProfileWrapper.profiler, stream=s).sort_stats(sortby)
        ps.print_stats()
        self.set_status(200)
        self.write(s.getvalue())
        self.finish()

    def delete(self):
        """Clear profiler statistics."""
        CProfileWrapper.profiler.create_stats()
        self.enable()
        self.set_status(204)
        self.finish()


class CProfileHandler(tornado.web.RequestHandler):

    profiler = CProfileWrapper.profiler
    running = CProfileWrapper.running

    def set_default_headers(self):
        self.set_header('Content-Type', 'application/json')

    def post(self):
        """Start a new profiler."""
        if not CProfileWrapper.profiler:
            CProfileWrapper.profiler = cProfile.Profile()
        CProfileWrapper.profiler.enable()
        self.running = True
        self.set_status(201)
        self.finish()

    def delete(self):
        """Stop the profiler."""
        CProfileWrapper.profiler.disable()
        self.running = False
        self.set_status(204)
        self.finish()

    def get(self):
        """Check if the profiler is running."""
        self.write({"running": self.running})
        self.set_status(200)
        self.finish()


class TornadoProfiler(object):

    def __init__(self, prefix="", handler_base_class=object, backend='yappi'):
        self.prefix = prefix
        self.handler_base_class = handler_base_class
        self.backend = backend

    def get_routes(self):

        if self.backend == 'yappi':
            class UpdatedProfilerHandler(
                YappiProfilerHandler, self.handler_base_class):
                pass

            class UpdatedProfileStatsHandler(
                YappiProfileStatsHandler, self.handler_base_class):
                pass

            return [
                (self.prefix + "/profiler", UpdatedProfilerHandler),
                (self.prefix + "/profiler/stats", UpdatedProfileStatsHandler)
            ]

        elif self.backend == "cprofile" or self.backend == "cProfile":
            class UpdatedProfilerHandler(
                CProfileHandler, self.handler_base_class):
                pass

            class UpdatedProfileStatsHandler(
                CProfileStatsHandler, self.handler_base_class):
                pass

            class UpdatedProfileStatsDumpHandler(
                CProfileStatsDumpHandler, self.handler_base_class):
                pass

            return [
                (self.prefix + "/profiler", UpdatedProfilerHandler),
                (self.prefix + "/profiler/stats", UpdatedProfileStatsHandler),
                (self.prefix + "/profiler/stats/dump", UpdatedProfileStatsDumpHandler)
            ]


        else:
            raise ValueError("No such backend.")


def main(port=8888):
    """Run as sample test server."""
    import tornado.ioloop

    routes = [] + TornadoProfiler().get_routes()
    app = tornado.web.Application(routes)
    app.listen(port)
    tornado.ioloop.IOLoop.current().start()


if __name__ == "__main__":
    main(port=8888)
