"""
JWT verification utility for validating tokens from the SSO provider.

This module handles proper JWT verification including:
- Fetching and caching JWKS (JSON Web Key Set) from the SSO provider
- Validating JWT signature using the public keys
- Verifying token claims (issuer, audience, expiration)
"""

import logging
from typing import Any, Optional

import jwt
from django.conf import settings
from jwt import PyJWKClient

logger = logging.getLogger(__name__)


class JWTVerifier:
    """
    Handles JWT verification for SSO tokens.
    
    Uses PyJWKClient to automatically fetch and cache public keys from the
    SSO provider's JWKS endpoint.
    """

    def __init__(
        self,
        jwks_url: str,
        issuer: str,
        audience: Optional[str] = None,
        cache_keys: bool = True,
        cache_maxsize: int = 16,
        cache_timeout: int = 3600,  # 1 hour
    ):
        """
        Initialize the JWT verifier.

        Args:
            jwks_url: URL to the JWKS endpoint
            issuer: Expected issuer claim (iss)
            audience: Expected audience claim (aud), optional
            cache_keys: Whether to cache fetched keys
            cache_maxsize: Maximum number of keys to cache
            cache_timeout: How long to cache keys (seconds)
        """
        self.issuer = issuer
        self.audience = audience
        self.jwks_client = PyJWKClient(
            jwks_url,
            cache_keys=cache_keys,
            max_cached_keys=cache_maxsize,
            cache_jwk_set_timeout=cache_timeout,
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
            # Get the signing key from the JWKS endpoint
            signing_key = self.jwks_client.get_signing_key_from_jwt(token)

            # Verify and decode the token
            options = {
                "verify_signature": True,
                "verify_exp": True,
                "verify_iat": True,
                "verify_iss": True,
                "require_exp": True,
                "require_iat": True,
            }

            # Build verification kwargs
            verify_kwargs = {
                "key": signing_key.key,
                "algorithms": ["RS256"],
                "issuer": self.issuer,
                "options": options,
            }

            # Add audience verification if specified
            if self.audience:
                verify_kwargs["audience"] = self.audience

            # Decode and verify the token
            payload = jwt.decode(token, **verify_kwargs)

            logger.info(
                "Successfully verified JWT token",
                extra={
                    "email": payload.get("email"),
                    "sub": payload.get("sub"),
                    "exp": payload.get("exp"),
                },
            )

            return payload

        except jwt.ExpiredSignatureError:
            logger.warning("JWT token has expired")
            raise

        except jwt.InvalidIssuerError as e:
            logger.error("JWT token has invalid issuer", extra={"error": str(e)})
            raise

        except jwt.InvalidAudienceError as e:
            logger.error("JWT token has invalid audience", extra={"error": str(e)})
            raise

        except jwt.InvalidTokenError as e:
            logger.error("JWT token validation failed", extra={"error": str(e)})
            raise

        except Exception as e:
            logger.error("Unexpected error verifying JWT token", extra={"error": str(e)})
            raise jwt.InvalidTokenError(f"Token verification failed: {str(e)}")


# Initialize the verifier with SSO configuration
# This will be used in deployed environments (dev, preprod, prod)
def get_jwt_verifier() -> Optional[JWTVerifier]:
    """
    Get a configured JWT verifier instance.

    Returns None if JWT verification is not enabled for this environment.
    Only enabled for dev, preprod, and prod environments.
    """
    environment = getattr(settings, "ENVIRONMENT", "local").lower()

    # Only enable JWT verification for deployed environments
    if environment not in ["dev", "preprod", "prod"]:
        logger.info(
            "JWT verification disabled for environment",
            extra={"environment": environment},
        )
        return None

    # SSO configuration
    jwks_url = "https://sso.service.security.gov.uk/.well-known/jwks.json"
    issuer = "https://sso.service.security.gov.uk"

    # Audience can be configured via settings if needed
    audience = getattr(settings, "SSO_AUDIENCE", None)

    logger.info(
        "JWT verification enabled for environment",
        extra={"environment": environment, "issuer": issuer},
    )

    return JWTVerifier(
        jwks_url=jwks_url,
        issuer=issuer,
        audience=audience,
        cache_keys=True,
        cache_maxsize=16,
        cache_timeout=3600,  # Cache keys for 1 hour
    )
