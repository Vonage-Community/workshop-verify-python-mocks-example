import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient
from requests import Response
from vonage_http_client import AuthenticationError, HttpRequestError
from vonage_verify import (
    StartVerificationResponse,
    CheckCodeResponse,
)
from main import app, verify_sessions


# Helper functions
def make_auth_error() -> AuthenticationError:
    response = Response()
    response.status_code = 401
    return AuthenticationError(response)


def make_http_error(status_code: int) -> HttpRequestError:
    response = Response()
    response.status_code = status_code
    return HttpRequestError(response)


class TestSendCode(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    @patch("main.vonage_handlers.start_email_verification")
    def test_start_email_verification_success(self, mock_start_verification):

        test_data = {"email": "test@example.com", "request_id": "test-request-id"}

        mock_verification_response = StartVerificationResponse(
            request_id=test_data["request_id"]
        )
        mock_start_verification.return_value = mock_verification_response

        expected_result = 200
        test_result = self.client.post("/send-code", data=test_data)

        self.assertEqual(
            test_result.status_code,
            expected_result,
            msg=f"test_start_email_verification_success failed with: {test_result.status_code}. Expected: {expected_result}",
        )
        mock_start_verification.assert_called_once_with(email=test_data["email"])
        self.assertNotIn("Invalid verification code.", test_result.text)
        self.assertNotIn("Invalid request. Please try again.", test_result.text)
        self.assertNotIn("Something went wrong. Please try again.", test_result.text)

    @patch("main.vonage_handlers.start_email_verification")
    def test_start_email_verification_failure_authentication_error(
        self, mock_start_verification
    ):

        test_data = {"email": "test@example.com"}
        mock_start_verification.side_effect = make_auth_error()

        expected_result = 200
        test_result = self.client.post("/send-code", data=test_data)

        self.assertEqual(
            test_result.status_code,
            expected_result,
            msg=f"test_start_email_verification_failure_authentication_error failed with: {test_result.status_code}. Expected: {expected_result}",
        )
        self.assertIn("Invalid verification code.", test_result.text)

    @patch("main.vonage_handlers.start_email_verification")
    def test_start_email_verification_failure_http_request_error_400(
        self, mock_start_verification
    ):

        test_data = {"email": "test@example.com"}
        mock_start_verification.side_effect = make_http_error(400)

        expected_result = 200
        test_result = self.client.post("/send-code", data=test_data)

        self.assertEqual(
            test_result.status_code,
            expected_result,
            msg=f"test_start_email_verification_failure_http_request_error_400 failed with: {test_result.status_code}. Expected: {expected_result}",
        )
        self.assertIn("Invalid request. Please try again.", test_result.text)

    @patch("main.vonage_handlers.start_email_verification")
    def test_start_email_verification_failure_http_request_error_4xx(
        self, mock_start_verification
    ):

        test_data = {"email": "test@example.com"}
        mock_start_verification.side_effect = make_http_error(401)

        expected_result = 200
        test_result = self.client.post("/send-code", data=test_data)

        self.assertEqual(
            test_result.status_code,
            expected_result,
            msg=f"test_start_email_verification_failure_http_request_error_4xx failed with: {test_result.status_code}. Expected: {expected_result}",
        )
        self.assertIn("Something went wrong. Please try again.", test_result.text)


class TestCheckCode(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        verify_sessions["test@example.com"] = "test-request-id"

    def tearDown(self):
        verify_sessions.clear()
