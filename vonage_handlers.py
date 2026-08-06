from config import settings
from vonage import Auth, Vonage
from vonage_verify import (
    EmailChannel,
    VerifyRequest,
    StartVerificationResponse,
    CheckCodeResponse,
)

client = Vonage(
    Auth(
        application_id=settings.vonage_application_id,
        private_key=settings.vonage_private_key_path,
    )
)


def start_email_verification(email: str) -> StartVerificationResponse:
    verify_request = VerifyRequest(
        brand=settings.verify_brand_name,
        workflow=[
            EmailChannel(to=email),
        ],
        channel_timeout=120,
        code_length=5,
    )
    response = client.verify.start_verification(verify_request)
    return response


def check_code(request_id: str, code: str) -> CheckCodeResponse:
    response = client.verify.check_code(request_id=request_id, code=code)
    return response
