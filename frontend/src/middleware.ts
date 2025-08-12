import type { MiddlewareHandler } from "astro";
import { getBackendUrl } from "./global/utils";


export const onRequest: MiddlewareHandler = async (context, next) => {
    const accessToken = context.cookies.get("access")?.value;
    const url = context.url;

    // 404 if not logged in
    const protectedRoutes = [
        /^\/sign-out[\/]?$/,
        /^\/consultations.*/,
        /^\/design.*/,
    ];

    for (const protectedRoute of protectedRoutes) {
        if (protectedRoute.test(url.pathname) && !context.cookies.get("access")?.value) {
            return new Response(null, { status: 404 });
        }
    }

    const backendUrl = getBackendUrl(url.hostname);
    const fullBackendUrl = backendUrl + url.pathname + url.search;

    // skip as new pages are moved to astro
    const toSkip = [
        // /^\/$/,
        /^\/sign-in[\/]?$/,
        /^\/sign-out[\/]?$/,
        /^\/magic-link\/[A-Za-z0-9\-]*[\/]?$/,
        /^\/api\/astro\/.*/,
        /^\/api\/health[\/]?$/,
        /^\/health[\/]?$/,
        /^\/.well-known\/.*/,
        /^\/consultations.*(?<!\/review-questions\/)$/,
        /^\/design.*/,
    ];

    for (const skipPattern of toSkip) {
        if (skipPattern.test(context.url.pathname)) {
            return next();
        }
    }

    const hasBody = !["GET", "HEAD"].includes(context.request.method);
    const csrfCookie = context.cookies.get("csrftoken");

    try {
        // Get all cookies and forward them
        const cookieHeader = context.request.headers.get("cookie") || "";
        
        // Handle request body properly for forms
        let requestBody = undefined;
        if (hasBody) {
            try {
                requestBody = await context.request.arrayBuffer();
            } catch (e) {
                console.error("Error reading request body:", e);
            }
        }

        const response = await fetch(fullBackendUrl, {
            method: context.request.method,
            headers: {
                ...context.request.headers,
                "Authorization": `Bearer ${accessToken}`,
                "Cookie": cookieHeader, // Ensure cookie header is forwarded
                ...(csrfCookie && {
                    "X-CSRFToken": csrfCookie.value
                })
            },
            body: requestBody,
            redirect: "manual",
        });

        if (response.status === 401){
            return context.redirect("/sign-out");
        }

        const redirectStatuses = [301, 302, 303, 307, 308] as const;
        type RedirectStatus = typeof redirectStatuses[number];
        if (redirectStatuses.includes(response.status as RedirectStatus)) {
            const location = response.headers.get("location");
            if (location) {
                return context.redirect(location, response.status as RedirectStatus);
            }
        }

        const body = await response.arrayBuffer();

        // Create new response and forward all headers including Set-Cookie
        const newResponse = new Response(body, {
            status: response.status,
            headers: response.headers,
        });

        return newResponse;
    } catch {
        return new Response(null, { status: 500 });
    }
}