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
    const url = context.url;
    const backendUrl = getBackendUrl(url.hostname);
    const fullBackendUrl = backendUrl + url.pathname + url.search;

    // TODO: add logic to skip as new pages are moved to astro
    // if (context.url.pathname === "url/to/skip") {
    //     return next();
    // }

    const response = await fetch(fullBackendUrl, {
        method: context.request.method,
        headers: context.request.headers,
        body: ["GET", "HEAD"].includes(context.request.method)
            ? undefined
            : context.request.body,
    });

    const body = await response.arrayBuffer();

    return new Response(body, {
        status: response.status,
        headers: response.headers,
    })
}