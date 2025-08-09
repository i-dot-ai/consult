import type { MiddlewareHandler } from "astro";
import { getBackendUrl } from "./global/utils";


export const onRequest: MiddlewareHandler = async (context, next) => {
    const accessToken = context.cookies.get("access")?.value;
    const url = context.url;

    // 404 if not logged in
    const protectedRoutes = [
        /^\/sign-out[\/]?$/,
        /^\/consultations.*/,
    ];

    for (const protectedRoute of protectedRoutes) {
        if (protectedRoute.test(context.url.pathname) && !context.cookies.get("access")?.value) {
            return new Response(null, { status: 404 });
        }
    }

    const backendUrl = getBackendUrl(url.hostname);
    const fullBackendUrl = backendUrl + url.pathname + url.search;

    // skip as new pages are moved to astro
    const toSkip = [
        /^\/$/,
        /^\/sign-in[\/]?$/,
        /^\/sign-out[\/]?$/,
        /^\/magic-link\/[A-Za-z0-9\-]*[\/]?$/,
        /^\/api\/astro\/.*/,
        /^\/.well-known\/.*/,
        /^\/consultations.*(?<!\/review-questions\/)$/,
    ];

    for (const skipPattern of toSkip) {
        if (skipPattern.test(context.url.pathname)) {
            return next();
        }
    }

    const hasBody = !["GET", "HEAD"].includes(context.request.method);

    const response = await fetch(fullBackendUrl, {
        method: context.request.method,
        headers: {
            ...context.request.headers,
            "Authorization": `Bearer ${accessToken}`
        },
        duplex: "half",
        body: hasBody
            ? context.request.body
            : undefined,
    });

    if (response.status === 401) {
        return context.redirect("/sign-out");
    }

    const body = await response.arrayBuffer();

    return new Response(body, {
        status: response.status,
        headers: response.headers,
    })
}