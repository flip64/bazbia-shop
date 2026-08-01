import jwt

from django.conf import settings
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed


class TorobServiceUser:
    """
    هویت سیستمی برای درخواست‌های معتبر ترب.
    """

    is_authenticated = True
    is_anonymous = False

    @property
    def username(self) -> str:
        return "torob"

    def __str__(self) -> str:
        return "Torob API"


class TorobJWTAuthentication(BaseAuthentication):
    """
    اعتبارسنجی JWT ترب با کلید عمومی Ed25519.
    """

    TOKEN_HEADER = "X-Torob-Token"
    SUPPORTED_ALGORITHM = "EdDSA"

    def authenticate(self, request):
        if not getattr(
            settings,
            "TOROB_JWT_ENABLED",
            True,
        ):
            return TorobServiceUser(), {
                "auth_status": "not_checked",
                "token_version": "",
                "payload": {},
            }

        token = request.headers.get(
            self.TOKEN_HEADER,
            "",
        ).strip()

        token_version = (
            request.headers.get(
                "X-Torob-Token-Version",
                "",
            )
            or request.headers.get(
                "C-Torob-Token-Version",
                "",
            )
        ).strip()

        if not token:
            raise AuthenticationFailed(
                "X-Torob-Token header is missing."
            )

        self.validate_token_version(
            token_version
        )

        payload = self.decode_token(token)

        return TorobServiceUser(), {
            "auth_status": "valid",
            "token_version": token_version,
            "payload": payload,
        }

    @staticmethod
    def validate_token_version(
        token_version: str,
    ) -> None:
        expected_version = str(
            getattr(
                settings,
                "TOROB_JWT_TOKEN_VERSION",
                "1",
            )
        )

        if not token_version:
            raise AuthenticationFailed(
                "X-Torob-Token-Version header is missing."
            )

        if token_version != expected_version:
            raise AuthenticationFailed(
                "Invalid Torob token version."
            )

    @classmethod
    def decode_token(
        cls,
        token: str,
    ) -> dict:
        public_key = getattr(
            settings,
            "TOROB_JWT_PUBLIC_KEY",
            "",
        ).strip()

        audience = getattr(
            settings,
            "TOROB_JWT_AUDIENCE",
            "",
        ).strip()

        if not public_key:
            raise AuthenticationFailed(
                "Torob public key is not configured."
            )

        if not audience:
            raise AuthenticationFailed(
                "Torob JWT audience is not configured."
            )

        try:
            return jwt.decode(
                token,
                key=public_key,
                algorithms=[
                    cls.SUPPORTED_ALGORITHM,
                ],
                audience=audience,
                options={
                    "verify_signature": True,
                    "verify_exp": True,
                    "verify_nbf": True,
                    "verify_aud": True,
                    "require": [
                        "aud",
                        "exp",
                        "nbf",
                    ],
                },
            )

        except jwt.ExpiredSignatureError as exc:
            raise AuthenticationFailed(
                "Torob token has expired."
            ) from exc

        except jwt.ImmatureSignatureError as exc:
            raise AuthenticationFailed(
                "Torob token is not valid yet."
            ) from exc

        except jwt.InvalidAudienceError as exc:
            raise AuthenticationFailed(
                "Invalid Torob token audience."
            ) from exc

        except jwt.MissingRequiredClaimError as exc:
            raise AuthenticationFailed(
                f"Missing JWT claim: {exc.claim}."
            ) from exc

        except jwt.InvalidAlgorithmError as exc:
            raise AuthenticationFailed(
                "Invalid Torob token algorithm."
            ) from exc

        except jwt.InvalidSignatureError as exc:
            raise AuthenticationFailed(
                "Invalid Torob token signature."
            ) from exc

        except jwt.InvalidTokenError as exc:
            raise AuthenticationFailed(
                "Invalid Torob token."
            ) from exc
