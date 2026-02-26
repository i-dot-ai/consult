"""
JWT verification utility for validating tokens from AWS ALB.

AWS ALB provides JWTs via the x-amzn-oidc-data header after validating
OIDC authentication. These JWTs are signed with AWS's regional keys.
"""

import urllib.request
from functools import lru_cache
from typing import Any, Optional

import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from django.conf import settings

logger = settings.LOGGER


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
        audience: Optional[str] = None,
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

    @lru_cache(maxsize=10)
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
        url = self.public_key_url_template.format(kid)
        
        try:
            with urllib.request.urlopen(url, timeout=10) as response:  # nosec B310
                return response.read().decode('utf-8')
        except Exception as e:
            logger.error(
                "Failed to fetch ALB public key",
                kid=kid,
                url=url,
                error=str(e)
            )
            raise jwt.InvalidTokenError(f"Cannot fetch public key for kid {kid}: {str(e)}")

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
            # Decode header to get kid
            header = jwt.get_unverified_header(token)
            kid = header.get("kid")
            
            if not kid:
                raise jwt.InvalidTokenError("Token missing 'kid' in header")
            
            # Fetch public key from AWS
            public_key_pem = self._fetch_public_key(kid)
            
            # Verify and decode the token
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

            logger.info(
                "Successfully verified ALB JWT token",
                email=payload.get("email"),
                sub=payload.get("sub"),
                kid=kid
            )

            return payload

        except jwt.ExpiredSignatureError:
            logger.warning("ALB JWT token has expired")
            raise

        except jwt.InvalidTokenError as e:
            logger.error("ALB JWT token validation failed", error=str(e))
            raise

        except Exception as e:
            logger.exception("Unexpected error verifying ALB JWT token")
            raise jwt.InvalidTokenError(f"Token verification failed: {str(e)}")


def get_jwt_verifier() -> Optional[ALBJWTVerifier]:
    """
    Get a configured JWT verifier instance for AWS ALB tokens.

    Returns None if JWT verification is not enabled for this environment.
    Only enabled for dev, preprod, and prod environments.
    
    Note: The JWT tokens come from AWS ALB (x-amzn-oidc-data header).
    AWS ALB validates OIDC with the SSO provider, then creates its own JWT
    signed with AWS's regional keys.
    """

    # Only enable JWT verification for deployed environments
    if settings.ENVIRONMENT.lower() not in ["dev", "preprod", "prod"]:
        logger.info(
            "JWT verification disabled for environment",
            environment=settings.ENVIRONMENT
        )
        return None

    # Get AWS region from settings
    aws_region = getattr(settings, "AWS_REGION", "eu-west-2")
    
    # Audience validation is optional for ALB tokens
    audience = None

    logger.info(
        "JWT verification enabled for AWS ALB tokens",
        region=aws_region,
        environment=settings.ENVIRONMENT
    )

    return ALBJWTVerifier(
        region=aws_region,
        audience=audience,
    )
