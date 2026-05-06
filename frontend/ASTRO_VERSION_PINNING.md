# Astro Version Pinning

## ⚠️ CRITICAL: Do Not Upgrade These Packages

The following packages are **pinned to specific versions** due to a breaking change that prevents CSRF tokens from being properly forwarded when proxying Django admin requests:

- **astro**: `5.16.6` (DO NOT upgrade to 5.17+)
- **@astrojs/node**: `9.3.3` (DO NOT upgrade to 9.5+)

## Issue Details

**Affected Versions:**
- Astro 5.17.0 through at least 5.18.1
- @astrojs/node 9.5.4 through at least 9.5.5

**Symptoms:**
- Django admin form submissions fail with `403 Forbidden` error
- Error message: "Cross-site POST form submissions are forbidden"
- CSRF tokens in POST body are not properly forwarded through the Astro proxy

## History

1. **March 3, 2026** (commit `ca7091541`): Downgraded from 5.17.3 to 5.16.6 to fix CSRF issue
2. **April 24, 2026** (commit `8070caa9e`): Aikido security bot upgraded to 6.1.6 / 10.0.5, re-introducing the bug
3. **April 28, 2026** (commit `a37744af0`): Partial downgrade to 5.18.1 / 9.5.5, but issue persisted
4. **May 1, 2026** (commit `04ed44ea8`): Full downgrade back to 5.16.6 / 9.3.3

## Before Upgrading

If security vulnerabilities require upgrading these packages:

1. Test Django admin form submissions thoroughly in preprod
2. Verify CSRF tokens are properly forwarded through the Astro middleware
3. Test specifically:
   - Creating consultations
   - Cloning consultations  
   - Any bulk admin actions
   - Theme generation from admin

## Related Files

- `frontend/src/middleware.ts` - Contains CSRF header forwarding logic
- `backend/middleware.py` - Django CSRF handling
- `backend/settings/base.py` - CSRF_TRUSTED_ORIGINS configuration

## References

- Original fix commit: https://github.com/i-dot-ai/consult/commit/ca7091541
- Issue discussion: [Link to PR or issue if created]
