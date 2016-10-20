import json
import mock
import tornado.web
from tornado.testing import AsyncHTTPTestCase
from tornado_profile import TornadoProfiler


class TornadoProfilerTestCase(AsyncHTTPTestCase):
    def setUp(self):
        super(TornadoProfilerTestCase, self).setUp()
        self.maxDiff = None

    def get_app(self):
        routes = [] + TornadoProfiler().get_routes()
        return tornado.web.Application(routes)

    @mock.patch('yappi.is_running', autospec=True)
    @mock.patch('yappi.start', autospec=True)
    def test_post_profiler_if_profiler_not_running_returns_201_status_code(self, mock_start, mock_is_running):
        mock_is_running.return_value = False
        result = self.fetch("/profiler", method="POST", body=json.dumps({}))
        assert result.code == 201

    @mock.patch('yappi.is_running', autospec=True)
    @mock.patch('yappi.start', autospec=True)
    def test_post_profiler_starts_profiler_if_profiler_not_running(self, mock_start, mock_is_running):
        mock_is_running.return_value = False
        self.fetch("/profiler", method="POST", body=json.dumps({}))
        assert mock_start.mock_calls == [mock.call(builtins=False, profile_threads=False)]

    @mock.patch('yappi.is_running', autospec=True)
    @mock.patch('yappi.start', autospec=True)
    def test_post_profiler_if_profiler_already_runnning_returns_201_status_code(self, mock_start, mock_is_running):
        mock_is_running.return_value = True
        result = self.fetch("/profiler", method="POST", body=json.dumps({}))
        assert result.code == 201

    @mock.patch('yappi.is_running', autospec=True)
    @mock.patch('yappi.start', autospec=True)
    def test_post_profiler_does_not_start_profiler_if_profiler_already_runnning(self, mock_start, mock_is_running):
        mock_is_running.return_value = True
        self.fetch("/profiler", method="POST", body=json.dumps({}))
        assert mock_start.mock_calls == []

    def test_delete_profiler_returns_204_status_code(self):
        result = self.fetch("/profiler", method="DELETE")
        assert result.code == 204

    @mock.patch('yappi.stop', autospec=True)
    def test_delete_profiler_stops_profiler(self, mock_stop):
        self.fetch("/profiler", method="DELETE")
        assert mock_stop.mock_calls == [mock.call()]

    @mock.patch('yappi.is_running', autospec=True)
    def test_get_profiler_when_profiler_not_running_returns_correct_result(self, mock_is_running):
        mock_is_running.return_value=False
        result = self.fetch("/profiler", method="GET")
        assert json.loads(result.body) == {'running': False}

    @mock.patch('yappi.is_running', autospec=True)
    def test_get_profiler_when_profiler_is_running_returns_correct_result(self, mock_is_running):
        mock_is_running.return_value=True
        result = self.fetch("/profiler", method="GET")
        assert json.loads(result.body) == {'running': True}

    def test_get_profiler_stats_when_no_stats_available_returns_404_status_code(self):
        result = self.fetch("/profiler/stats", method="GET")
        assert result.code == 404

    def test_get_profiler_stats_when_no_stats_available_returns_error_message(self):
        result = self.fetch("/profiler/stats", method="GET")
        assert json.loads(result.body) == {
            'error': 'No stats available. Start and stop the profiler before trying to retrieve stats.'
        }

    @mock.patch('tornado_profile.get_profiler_statistics', autospec=True)
    def test_get_profiler_stats_when_stats_available_returns_200_status_code(self, mock_get_profiler_statistics):
        mock_get_profiler_statistics.return_value = []
        result = self.fetch("/profiler/stats", method="GET")
        assert result.code == 200

    @mock.patch('tornado_profile.get_profiler_statistics', autospec=True)
    def test_get_profiler_stats_when_stats_available_returns_correct_result(self, mock_get_profiler_statistics):
        mock_get_profiler_statistics.return_value = []
        result = self.fetch("/profiler/stats", method="GET")
        assert json.loads(result.body) == {'statistics': []}

    def test_delete_profiler_stats_returns_200_status_code(self):
        result = self.fetch("/profiler/stats", method="DELETE")
        assert result.code == 204

    @mock.patch('yappi.clear_stats', autospec=True)
    def test_delete_profiler_stats_clears_profiler_stats(self, mock_clear_stats):
        self.fetch("/profiler/stats", method="DELETE")
        assert mock_clear_stats.mock_calls == [mock.call()]
