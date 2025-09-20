import type { APIRoute } from 'astro';

export const GET: APIRoute = async ({ request, redirect }) => {
    const url = new URL(request.url);
    const backendUrl = import.meta.env.PUBLIC_BACKEND_URL || 'http://localhost:8000';
    
    // Construct the backend OAuth callback URL with all query parameters
    const backendCallbackUrl = new URL('/accounts/oidc/gds/login/callback/', backendUrl);
    
    // Forward all query parameters (code, state, etc.) from OAuth provider
    url.searchParams.forEach((value, key) => {
        backendCallbackUrl.searchParams.set(key, value);
    });

    try {
        console.log('Frontend OAuth callback - forwarding to:', backendCallbackUrl.toString());
        
        // Forward the request to the backend with all original headers
        const response = await fetch(backendCallbackUrl.toString(), {
            method: 'GET',
            headers: {
                // Forward essential headers
                'Host': url.host,
                'User-Agent': request.headers.get('User-Agent') || 'Frontend-Proxy/1.0',
                'Accept': request.headers.get('Accept') || 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': request.headers.get('Accept-Language') || 'en-US,en;q=0.5',
                'Accept-Encoding': request.headers.get('Accept-Encoding') || 'gzip, deflate',
                'Connection': 'keep-alive',
                'X-Forwarded-For': request.headers.get('X-Forwarded-For') || '',
                'X-Forwarded-Proto': url.protocol.slice(0, -1), // Remove trailing :
                'X-Forwarded-Host': url.host,
                // Forward any existing cookies
                ...(request.headers.get('Cookie') && {
                    'Cookie': request.headers.get('Cookie')!
                })
            },
            redirect: 'manual', // Handle redirects manually to preserve Set-Cookie headers
        });

        console.log('Backend response status:', response.status);
        console.log('Backend response headers:', [...response.headers.entries()]);

        // Handle redirects from backend (typical after successful OAuth)
        if (response.status >= 300 && response.status < 400) {
            const location = response.headers.get('Location');
            if (location) {
                // Create response with redirect and forward ALL Set-Cookie headers
                const redirectResponse = new Response(null, {
                    status: response.status,
                    headers: new Headers()
                });

                // Set the redirect location
                redirectResponse.headers.set('Location', location);

                // Forward ALL Set-Cookie headers (there might be multiple)
                const setCookieHeaders = response.headers.getSetCookie?.() || [];
                if (setCookieHeaders.length > 0) {
                    setCookieHeaders.forEach(cookie => {
                        redirectResponse.headers.append('Set-Cookie', cookie);
                    });
                } else {
                    // Fallback for older fetch implementations
                    const setCookie = response.headers.get('Set-Cookie');
                    if (setCookie) {
                        redirectResponse.headers.set('Set-Cookie', setCookie);
                    }
                }

                console.log('Forwarding redirect with cookies:', [...redirectResponse.headers.entries()]);
                return redirectResponse;
            }
        }

        // For non-redirect responses, forward the response body and headers
        const body = await response.text();
        const forwardedResponse = new Response(body, {
            status: response.status,
            headers: new Headers()
        });

        // Forward content type
        const contentType = response.headers.get('Content-Type');
        if (contentType) {
            forwardedResponse.headers.set('Content-Type', contentType);
        }

        // Forward ALL Set-Cookie headers for non-redirect responses too
        const setCookieHeaders = response.headers.getSetCookie?.() || [];
        if (setCookieHeaders.length > 0) {
            setCookieHeaders.forEach(cookie => {
                forwardedResponse.headers.append('Set-Cookie', cookie);
            });
        } else {
            // Fallback for older fetch implementations
            const setCookie = response.headers.get('Set-Cookie');
            if (setCookie) {
                forwardedResponse.headers.set('Set-Cookie', setCookie);
            }
        }

        return forwardedResponse;

    } catch (error) {
        console.error('OAuth callback proxy error:', error);
        return new Response('OAuth callback failed', { 
            status: 500,
            headers: {
                'Content-Type': 'text/plain'
            }
        });
    }
};