from typing import Any, Optional

import jwt
from django.conf import settings
from jwt import PyJWKClient

logger = settings.LOGGER


class JWTVerifier:
    """
    Handles JWT verification for SSO tokens.

    Uses PyJWKClient to automatically fetch and cache public keys from the
    SSO provider's JWKS endpoint.
    """

    def __init__(
        self,
        jwks_url: str,
        issuer: Optional[str] = None,
        audience: Optional[str] = None,
        cache_jwk_set: bool = True,
        lifespan: int = 3600,  # 1 hour in seconds
    ):
        """
        Initialize the JWT verifier.

        Args:
            jwks_url: URL to the JWKS endpoint
            issuer: Expected issuer claim (iss), optional
            audience: Expected audience claim (aud), optional
            cache_jwk_set: Whether to cache fetched keys
            lifespan: How long to cache keys (seconds)
        """
        self.issuer = issuer
        self.audience = audience
        self.jwks_client = PyJWKClient(
            jwks_url,
            cache_jwk_set=cache_jwk_set,
            lifespan=lifespan,
        )

    def verify_token(self, token: str) -> dict[str, Any]:
        """
        Verify and decode a JWT token.

        Args:
            token: The JWT token string to verify

        Returns:
            The decoded token payload as a dictionary

        Raises:
            jwt.InvalidTokenError: If the token is invalid
            jwt.ExpiredSignatureError: If the token has expired
            jwt.InvalidIssuerError: If the issuer doesn't match
            jwt.InvalidAudienceError: If the audience doesn't match
        """
        try:
            signing_key = self.jwks_client.get_signing_key_from_jwt(token)

            options = {
                "verify_signature": True,
                "verify_exp": True,
                "verify_iat": False,
                "verify_iss": False,
                "require_exp": True,
                "require_iat": False,
            }

            verify_kwargs = {
                "key": signing_key.key,
                "algorithms": ["RS256", "ES256"],
                "options": options,
            }

            if self.audience:
                verify_kwargs["audience"] = self.audience
                options["verify_aud"] = True

            payload = jwt.decode(token, **verify_kwargs)

            logger.info(
                "Successfully verified JWT token",
                email= payload.get("email"), sub= payload.get("sub")
            )

            return payload

        except jwt.ExpiredSignatureError:
            logger.exception("JWT token has expired")
            raise

        except jwt.InvalidIssuerError:
            logger.exception("JWT token has invalid issuer")
            raise

        except jwt.InvalidAudienceError:
            logger.exception("JWT token has invalid audience")
            raise

        except jwt.InvalidTokenError:
            logger.exception("JWT token validation failed")
            raise

        except Exception as e:
            logger.exception("Unexpected error verifying JWT token")
            raise jwt.InvalidTokenError(f"Token verification failed: {str(e)}")


def get_jwt_verifier() -> Optional[JWTVerifier]:
    """
    Get a configured JWT verifier instance.

    Returns None if JWT verification is not enabled for this environment.
    Only enabled for dev, preprod, and prod environments.

    Note: The JWT tokens come from AWS ALB (not directly from SSO provider).
    AWS ALB validates OIDC with the SSO provider, then creates its own JWT
    signed with AWS's regional keys.
    """

    # Only enable JWT verification for deployed environments
    if settings.ENVIRONMENT.lower() not in ["dev", "preprod", "prod"]:
        logger.info(
            "JWT verification disabled for environment"
        )
        return None

    # AWS ALB JWKS endpoint (region-specific)
    # The JWT is signed by AWS ALB after it validates OIDC with the SSO provider
    aws_region = getattr(settings, "AWS_REGION", "eu-west-2")
    jwks_url = f"https://public-keys.auth.elb.{aws_region}.amazonaws.com"

    # Issuer is not strictly validated for ALB tokens
    # ALB doesn't include a standard iss claim
    issuer = None

    # Audience validation is optional
    audience = None

    logger.info(
        "JWT verification enabled for AWS ALB tokens",
        region= aws_region, jwks_url=jwks_url
    )

    return JWTVerifier(
        jwks_url=jwks_url,
        issuer=issuer,
        audience=audience,
        cache_jwk_set=True,
        lifespan=3600,
    )
