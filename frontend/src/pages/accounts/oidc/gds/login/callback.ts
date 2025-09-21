import type { APIRoute } from 'astro';

export const GET: APIRoute = async ({ request }) => {
    const backendUrl = process.env.PUBLIC_BACKEND_URL;
    if (!backendUrl) {
        throw new Error('PUBLIC_BACKEND_URL environment variable is required');
    }

    const url = new URL(request.url);
    const backendCallbackUrl = new URL('/accounts/oidc/gds/login/callback/', backendUrl);
    
    // Forward query parameters (code, state, etc.)
    url.searchParams.forEach((value, key) => {
        backendCallbackUrl.searchParams.set(key, value);
    });

    const response = await fetch(backendCallbackUrl.toString(), {
        headers: {
            'Host': url.host,
            'Cookie': request.headers.get('Cookie') || '',
            'User-Agent': request.headers.get('User-Agent') || 'Frontend-Proxy/1.0'
        },
        redirect: 'manual'
    });

    // Forward the response as-is (redirect with cookies or content)
    return new Response(await response.arrayBuffer(), {
        status: response.status,
        headers: response.headers
    });
};