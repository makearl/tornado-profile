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
    def test_get_profiler_stats_when_stats_are_empty_returns_correct_result(self, mock_get_profiler_statistics):
        mock_get_profiler_statistics.return_value = []
        result = self.fetch("/profiler/stats", method="GET")
        assert json.loads(result.body) == {'statistics': []}

    def test_get_profiler_stats_when_stats_available_returns_correctly_formatted_result(self):
        # Start the profiler
        result = self.fetch("/profiler", method="POST", body=json.dumps({}))
        assert result.code == 201

        # Stop the profiler
        result = self.fetch("/profiler", method="DELETE")
        assert result.code == 204

        # Verify the returned statistics are a list
        result = self.fetch("/profiler/stats", method="GET")
        json_results = json.loads(result.body)
        assert isinstance(json_results["statistics"], list)

        # Verify each statistic has the correct format
        assert set(json_results["statistics"][0].keys()) == {"path",
                                                             "line",
                                                             "func_name",
                                                             "num_calls",
                                                             "total_time",
                                                             "total_time_per_call",
                                                             "cum_time",
                                                             "cum_time_per_call"}

    def test_get_profiler_stats_with_count_when_stats_available_returns_correct_number_of_results(self):
        # Start the profiler
        result = self.fetch("/profiler", method="POST", body=json.dumps({}))
        assert result.code == 201

        # Stop the profiler
        result = self.fetch("/profiler", method="DELETE")
        assert result.code == 204

        # Verify the returned statistics are a list
        result = self.fetch("/profiler/stats?count=1", method="GET")
        json_results = json.loads(result.body)
        statistics = json_results["statistics"]
        assert isinstance(statistics, list)

        # Verify one result was returned
        assert len(statistics) == 1

    @mock.patch('tornado_profile.get_profiler_statistics', autospec=True)
    def test_get_profiler_stats_with_no_query_parameters_uses_correct_default_arguments(self, mock_get_statistics):
        self.fetch("/profiler/stats", method="GET")

        # Verify get_profiler_statistics was called with the correct default arguments
        assert mock_get_statistics.mock_calls == [mock.call('cum_time', 20, True)]

    @mock.patch('tornado_profile.get_profiler_statistics', autospec=True)
    def test_get_profiler_stats_with_valid_sort_query_parameter_uses_correct_arguments(self, mock_get_statistics):
        self.fetch("/profiler/stats?sort=num_calls", method="GET")

        # Verify get_profiler_statistics was called with the correct arguments
        assert mock_get_statistics.mock_calls == [mock.call('num_calls', 20, True)]

    @mock.patch('tornado_profile.get_profiler_statistics', autospec=True)
    def test_get_profiler_stats_with_valid_count_query_parameter_uses_correct_arguments(self, mock_get_statistics):
        self.fetch("/profiler/stats?count=1", method="GET")

        # Verify get_profiler_statistics was called with the correct arguments
        assert mock_get_statistics.mock_calls == [mock.call('cum_time', 1, True)]

    @mock.patch('tornado_profile.get_profiler_statistics', autospec=True)
    def test_get_profiler_stats_with_count_of_0_uses_correct_arguments(self, mock_get_statistics):
        self.fetch("/profiler/stats?count=0", method="GET")

        # Verify get_profiler_statistics was called with the correct arguments
        assert mock_get_statistics.mock_calls == [mock.call('cum_time', None, True)]

    @mock.patch('tornado_profile.get_profiler_statistics', autospec=True)
    def test_get_profiler_stats_with_strip_dirs_false_query_parameter_uses_correct_arguments(self, mock_get_statistics):
        self.fetch("/profiler/stats?strip_dirs=false", method="GET")

        # Verify get_profiler_statistics was called with the correct arguments
        assert mock_get_statistics.mock_calls == [mock.call('cum_time', 20, False)]

    @mock.patch('tornado_profile.get_profiler_statistics', autospec=True)
    def test_get_profiler_stats_with_strip_dirs_no_query_parameter_uses_correct_arguments(self, mock_get_statistics):
        self.fetch("/profiler/stats?strip_dirs=no", method="GET")

        # Verify get_profiler_statistics was called with the correct arguments
        assert mock_get_statistics.mock_calls == [mock.call('cum_time', 20, False)]

    @mock.patch('tornado_profile.get_profiler_statistics', autospec=True)
    def test_get_profiler_stats_with_strip_dirs_0_query_parameter_uses_correct_arguments(self, mock_get_statistics):
        self.fetch("/profiler/stats?strip_dirs=0", method="GET")

        # Verify get_profiler_statistics was called with the correct arguments
        assert mock_get_statistics.mock_calls == [mock.call('cum_time', 20, False)]

    @mock.patch('tornado_profile.get_profiler_statistics', autospec=True)
    def test_get_profiler_stats_with_strip_dirs_none_query_parameter_uses_correct_arguments(self, mock_get_statistics):
        self.fetch("/profiler/stats?strip_dirs=None", method="GET")

        # Verify get_profiler_statistics was called with the correct arguments
        assert mock_get_statistics.mock_calls == [mock.call('cum_time', 20, False)]

    def test_get_profiler_stats_with_invalid_sort_returns_400_status_code(self):
        result = self.fetch("/profiler/stats?sort=total", method="GET")
        assert result.code == 400

    def test_get_profiler_stats_with_invalid_sort_returns_correct_error_message(self):
        result = self.fetch("/profiler/stats?sort=total", method="GET")
        assert json.loads(result.body) == {
            'error': "Invalid `sort` 'total', must be in ('num_calls', 'cum_time', 'total_time', 'cum_time_per_call', 'total_time_per_call')."
        }

    def test_get_profiler_stats_with_invalid_count_returns_400_status_code(self):
        result = self.fetch("/profiler/stats?count=total", method="GET")
        assert result.code == 400

    def test_get_profiler_stats_with_invalid_count_returns_correct_error_message(self):
        result = self.fetch("/profiler/stats?count=total", method="GET")
        assert json.loads(result.body) == {
            'error': "Can't cast `count` 'total' to int."
        }

    def test_delete_profiler_stats_returns_200_status_code(self):
        result = self.fetch("/profiler/stats", method="DELETE")
        assert result.code == 204

    @mock.patch('yappi.clear_stats', autospec=True)
    def test_delete_profiler_stats_clears_profiler_stats(self, mock_clear_stats):
        self.fetch("/profiler/stats", method="DELETE")
        assert mock_clear_stats.mock_calls == [mock.call()]
