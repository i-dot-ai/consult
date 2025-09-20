import type { APIRoute } from 'astro';

export const GET: APIRoute = async ({ request, redirect }) => {
    const url = new URL(request.url);
    const backendUrl = import.meta.env.PUBLIC_BACKEND_URL || 'http://localhost:8000';
    
    // Construct the backend OAuth login URL with all query parameters
    const backendLoginUrl = new URL('/accounts/oidc/gds/login/', backendUrl);
    
    // Forward all query parameters (process=login, etc.)
    url.searchParams.forEach((value, key) => {
        backendLoginUrl.searchParams.set(key, value);
    });

    try {
        // Forward the request to the backend
        const response = await fetch(backendLoginUrl.toString(), {
            method: 'GET',
            headers: {
                'Host': url.host,
                'User-Agent': request.headers.get('User-Agent') || '',
                'Accept': request.headers.get('Accept') || 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': request.headers.get('Accept-Language') || 'en-US,en;q=0.5',
                'Accept-Encoding': request.headers.get('Accept-Encoding') || 'gzip, deflate',
                'Connection': 'keep-alive',
                // Forward any cookies from the original request
                ...(request.headers.get('Cookie') && {
                    'Cookie': request.headers.get('Cookie')!
                })
            },
            redirect: 'manual', // Handle redirects manually
        });

        // Backend should return a redirect to the OAuth provider
        if (response.status >= 300 && response.status < 400) {
            const location = response.headers.get('Location');
            if (location) {
                // Redirect to OAuth provider (external URL, so no need to make absolute)
                return new Response(null, {
                    status: response.status,
                    headers: {
                        'Location': location,
                        // Forward any Set-Cookie headers from the backend
                        ...(response.headers.get('Set-Cookie') && {
                            'Set-Cookie': response.headers.get('Set-Cookie')!
                        })
                    }
                });
            }
        }

        // For other responses, forward them
        const body = await response.text();
        
        return new Response(body, {
            status: response.status,
            headers: {
                'Content-Type': response.headers.get('Content-Type') || 'text/html',
                // Forward any Set-Cookie headers from the backend
                ...(response.headers.get('Set-Cookie') && {
                    'Set-Cookie': response.headers.get('Set-Cookie')!
                })
            }
        });

    } catch (error) {
        console.error('OAuth login proxy error:', error);
        return new Response('OAuth login failed', { status: 500 });
    }
};