"""
JWT verification utility for validating tokens from AWS ALB.

AWS ALB provides JWTs via the x-amzn-oidc-data header after validating
OIDC authentication. These JWTs are signed with AWS's regional keys.
"""

import urllib.request
from functools import lru_cache
from typing import Any

import jwt
from django.conf import settings

logger = settings.LOGGER


@lru_cache(maxsize=10)
def _fetch_public_key_cached(url_template: str, kid: str) -> str:
    """
    Fetch a public key from AWS ALB by key ID (module-level to avoid lru_cache on method).

    Args:
        url_template: URL template with {} placeholder for kid
        kid: Key ID from the JWT header

    Returns:
        PEM-formatted public key

    Raises:
        jwt.InvalidTokenError: If key cannot be fetched
    """
    url = url_template.format(kid)
    try:
        with urllib.request.urlopen(url, timeout=10) as response:  # nosec B310
            return response.read().decode("utf-8")
    except OSError as e:
        logger.error("Failed to fetch ALB public key")
        raise jwt.InvalidTokenError(f"Cannot fetch public key for kid {kid}: {e!s}")


class ALBJWTVerifier:
    """
    Handles JWT verification for AWS ALB tokens.

    AWS ALB doesn't provide a traditional JWKS endpoint. Instead, public keys
    must be fetched individually using:
    https://public-keys.auth.elb.{region}.amazonaws.com/{kid}
    """

    def __init__(
        self,
        region: str,
        audience: str | None = None,
    ):
        """
        Initialize the ALB JWT verifier.

        Args:
            region: AWS region (e.g., eu-west-2)
            audience: Expected audience claim (aud), optional
        """
        self.region = region
        self.audience = audience
        self.public_key_url_template = f"https://public-keys.auth.elb.{region}.amazonaws.com/{{}}"

    def _fetch_public_key(self, kid: str) -> str:
        """
        Fetch a public key from AWS ALB by key ID.

        Args:
            kid: Key ID from the JWT header

        Returns:
            PEM-formatted public key

        Raises:
            jwt.InvalidTokenError: If key cannot be fetched
        """
        return _fetch_public_key_cached(self.public_key_url_template, kid)

    def verify_token(self, token: str) -> dict[str, Any]:
        """
        Verify and decode an AWS ALB JWT token.

        Args:
            token: The JWT token string to verify

        Returns:
            The decoded token payload as a dictionary

        Raises:
            jwt.InvalidTokenError: If the token is invalid
            jwt.ExpiredSignatureError: If the token has expired
        """
        try:
            header = jwt.get_unverified_header(token)
            kid = header.get("kid")

            if not kid:
                raise jwt.InvalidTokenError("Token missing 'kid' in header")

            public_key_pem = self._fetch_public_key(kid)

            options = {
                "verify_signature": True,
                "verify_exp": True,
                "verify_iat": False,
                "verify_iss": False,
                "verify_aud": bool(self.audience),
                "require_exp": True,
                "require_iat": False,
            }

            verify_kwargs = {
                "key": public_key_pem,
                "algorithms": ["ES256", "RS256"],
                "options": options,
            }

            if self.audience:
                verify_kwargs["audience"] = self.audience

            payload = jwt.decode(token, **verify_kwargs)

            logger.info("Successfully verified ALB JWT token")

            return payload

        except jwt.ExpiredSignatureError:
            logger.warning("ALB JWT token has expired")
            raise

        except jwt.InvalidTokenError:
            logger.error("ALB JWT token validation failed")
            raise

        except Exception as e:
            logger.exception("Unexpected error verifying ALB JWT token")
            raise jwt.InvalidTokenError(f"Token verification failed: {e!s}")


def get_jwt_verifier() -> ALBJWTVerifier | None:
    """
    Get a configured JWT verifier instance for AWS ALB tokens.

    Returns None if JWT verification is not enabled for this environment.
    Only enabled for dev, preprod, and prod environments.
    """
    if settings.ENVIRONMENT.lower() not in ["dev", "preprod", "prod"]:
        logger.info("JWT verification disabled for environment")
        return None

    aws_region = getattr(settings, "AWS_REGION", "eu-west-2")
    audience = None

    logger.info("JWT verification enabled for AWS ALB tokens")

    return ALBJWTVerifier(region=aws_region, audience=audience)
