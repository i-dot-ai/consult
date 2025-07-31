export const prerender = false;

import type { APIRoute } from 'astro';

import { getBackendUrl } from '../../global/utils';


export const POST: APIRoute = async ({ request, cookies }) => {
  let message = "success";
  let status = 200;

  interface TokenData {
    access?: string;
    refresh?: string;
  }
  let data: TokenData = {};

  const requestBody = await request.json();

  try {
    const backendResponse = await fetch(`${getBackendUrl(request.url)}/api/token/`, {
      method: "POST",
      body: JSON.stringify({
        "token": requestBody.token
      }),
      headers: {
        "Content-Type": "application/json",
      }
    })

    const responseJson = await backendResponse.json();
    if (!backendResponse.ok) {
      message = "Response not ok:" + JSON.stringify(responseJson);
      status = 500;
    }
    data = responseJson;

    if (data.access) {
      cookies.set("access", data.access, { path: "/" });
    }
    if (data.refresh) {
      cookies.set("refresh", data.refresh, { path: "/" });
    }
  } catch(err: any) {
    message = err.message;
    status = 500;
  }
  
  return new Response(
    JSON.stringify(data),
    {
      status: status,
    }
  );
};