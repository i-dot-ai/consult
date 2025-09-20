import type { APIRoute } from 'astro';

export const GET: APIRoute = async ({ request, redirect }) => {
    const url = new URL(request.url);
    const backendUrl = import.meta.env.PUBLIC_BACKEND_URL;
    
    if (!backendUrl) {
        console.error('FATAL: PUBLIC_BACKEND_URL environment variable is not set!');
        console.log('Available import.meta.env:', import.meta.env);
        throw new Error('PUBLIC_BACKEND_URL environment variable is required');
    }
    
    console.log('Using backend URL:', backendUrl);
    
    // Construct the backend OAuth login URL with all query parameters
    const backendLoginUrl = new URL('/accounts/oidc/gds/login/', backendUrl);
    
    // Forward all query parameters (process=login, etc.)
    url.searchParams.forEach((value, key) => {
        backendLoginUrl.searchParams.set(key, value);
    });

    try {
        console.log('Frontend OAuth login - forwarding to:', backendLoginUrl.toString());
        
        // Forward the request to the backend with proper host headers
        // This is crucial - Django allauth will use the Host header to generate the redirect_uri
        const response = await fetch(backendLoginUrl.toString(), {
            method: 'GET',
            headers: {
                // IMPORTANT: Use the frontend host so Django generates correct redirect_uri
                'Host': url.host,
                'User-Agent': request.headers.get('User-Agent') || 'Frontend-Proxy/1.0',
                'Accept': request.headers.get('Accept') || 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': request.headers.get('Accept-Language') || 'en-US,en;q=0.5',
                'Accept-Encoding': request.headers.get('Accept-Encoding') || 'gzip, deflate',
                'Connection': 'keep-alive',
                'X-Forwarded-For': request.headers.get('X-Forwarded-For') || '',
                'X-Forwarded-Proto': url.protocol.slice(0, -1), // Remove trailing :
                'X-Forwarded-Host': url.host,
                // Forward any existing cookies for session continuity
                ...(request.headers.get('Cookie') && {
                    'Cookie': request.headers.get('Cookie')!
                })
            },
            redirect: 'manual', // Handle redirects manually
        });

        console.log('Backend login response status:', response.status);

        // Django allauth should return a redirect to the OAuth provider
        if (response.status >= 300 && response.status < 400) {
            const location = response.headers.get('Location');
            if (location) {
                console.log('Redirecting to OAuth provider:', location);
                
                // Forward the redirect to the OAuth provider
                return new Response(null, {
                    status: response.status,
                    headers: {
                        'Location': location,
                        // Forward any Set-Cookie headers
                        ...(response.headers.get('Set-Cookie') && {
                            'Set-Cookie': response.headers.get('Set-Cookie')!
                        })
                    }
                });
            }
        }

        // For other responses, forward them as-is
        const body = await response.text();
        
        return new Response(body, {
            status: response.status,
            headers: {
                'Content-Type': response.headers.get('Content-Type') || 'text/html',
                // Forward any Set-Cookie headers
                ...(response.headers.get('Set-Cookie') && {
                    'Set-Cookie': response.headers.get('Set-Cookie')!
                })
            }
        });

    } catch (error) {
        console.error('OAuth login proxy error:', error);
        return new Response('OAuth login failed', { 
            status: 500,
            headers: {
                'Content-Type': 'text/plain'
            }
        });
    }
};