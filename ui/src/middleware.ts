import type { MiddlewareHandler } from "astro";
import { getToken } from "./global/auth";


const authMiddleware: MiddlewareHandler = async ({request, redirect, url}, next) => {
    const pathname = url.pathname;

    const protectedRoutes = [
        "/consultations",
    ];

    const isProtected = protectedRoutes.some(route => {
        return pathname === route || pathname.startsWith(`${route}/`);
    })

    if (!isProtected) {
        return next();
    }

    const cookie = request.headers.get("cookie") || "";
    const token = getToken(cookie);

    if (!token) {
        // // TODO: Activate after auth implementation
        // return redirect("/");
    }
    return next();
}

export const onRequest = authMiddleware;

