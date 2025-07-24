export function getToken(cookie: string): string | null {
    const match = cookie.match(/authToken=([^;]+)/);
    return match ? decodeURIComponent(match[1]) : null;
}