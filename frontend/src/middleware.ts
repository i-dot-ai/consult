import type { MiddlewareHandler } from "astro";
import { getToken } from "./global/auth";
import { getBackendUrl } from "./global/utils";

// AuthMiddleware
// TODO: Activate after transfer. Currently disabled.
// export const onRequest: MiddlewareHandler = async ({request, redirect, url}, next) => {
//     const pathname = url.pathname;

//     const protectedRoutes = [
//         "/consultations",
//     ];

//     const isProtected = protectedRoutes.some(route => {
//         return pathname === route || pathname.startsWith(`${route}/`);
//     })

//     if (!isProtected) {
//         return next();
//     }

//     const cookie = request.headers.get("cookie") || "";
//     const token = getToken(cookie);

//     if (!token) {
//         // // TODO: Activate after auth implementation
//         // return redirect("/");
//     }
//     return next();
// }

export const onRequest: MiddlewareHandler = async (context, next) => {
    const accessToken = context.cookies.get("access")?.value;
    const url = context.url;
    const backendUrl = getBackendUrl(url.hostname);
    const fullBackendUrl = backendUrl + url.pathname + url.search;

    // TODO: add logic to skip as new pages are moved to astro
    const toSkip = [
        /^\/$/,
        /^\/sign-in[\/]?$/,
        /^\/magic-link\/[A-Za-z0-9\-]*[\/]?$/,
        /^\/api\/.*/,
        /^\/.well-known\/.*/,
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

    const body = await response.arrayBuffer();

    return new Response(body, {
        status: response.status,
        headers: response.headers,
    })
}