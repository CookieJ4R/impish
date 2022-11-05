import json
import unittest
from unittest.mock import patch, MagicMock

from impish.util.socket_util import send_data, try_unlink


class TestSocketUtil(unittest.TestCase):
    """
    Test class for socket_util.py
    """

    def test_socket_util_send_data_broken_pipe_returns_false(self):
        """
        Test: send_data returns False on BrokenPipeError
        """
        socket = MagicMock()
        socket.sendall.side_effect = BrokenPipeError()
        self.assertFalse(send_data(socket, MagicMock()))

    def test_socket_util_send_data_os_error_returns_false(self):
        """
        Test: send_data returns False on OSError
        """
        socket = MagicMock()
        socket.sendall.side_effect = OSError()
        self.assertFalse(send_data(socket, MagicMock()))

    def test_socket_util_send_data_returns_true_on_success(self):
        """
        Test: send_data returns True on success
        """
        self.assertTrue(send_data(MagicMock(), MagicMock()))

    def test_socket_util_send_data_sends_two_times(self):
        """
        Test: sendall of used socket gets called two times in successful cases
        """
        socket = MagicMock()
        send_data(socket, MagicMock())
        self.assertEqual(len(socket.sendall.mock_calls), 2)

    def test_socket_util_send_data_correct_data_and_length(self):
        """
        Test: sendall gets called with the correct data on both calls in successful cases
        """
        socket: MagicMock = MagicMock()
        data_to_send = json.dumps({"test_data_key": "test_data_value"}).encode('utf-8')
        correct_length = len(data_to_send).to_bytes(4, "little")
        send_data(socket, data_to_send)
        socket.sendall.assert_any_call(correct_length)
        socket.sendall.assert_any_call(data_to_send)

    @patch("os.unlink")
    @patch("os.path.exists")
    def test_socket_util_try_unlink_path_exists(self, mocked_exists, mocked_unlink):
        """
        Test: try_unlink calls os.unlink if path to unlink exists
        """
        mocked_exists.return_value = True
        test_path = ""
        try_unlink(test_path)
        mocked_unlink.assert_called_once_with(test_path)

    @patch("os.unlink")
    @patch("os.path.exists")
    def test_socket_util_try_unlink_path_does_not_exist(self, mocked_exists, mocked_unlink):
        """
        Test: try_unlink doesnt call os.unlink if path to unlink does not exist
        """
        mocked_exists.return_value = False
        test_path = ""
        try_unlink(test_path)
        mocked_unlink.assert_not_called()
