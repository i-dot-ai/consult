export const prerender = false;

import type { APIRoute } from 'astro';


export const POST: APIRoute = async ({ request }) => {
  let message = "success";
  let status = 200;

  const requestBody = await request.json();
  console.log(requestBody)

  try {
    const backendResponse = await fetch("http://localhost:8000/api/magic-link/", {
      body: JSON.stringify({
        "email": requestBody.email
      }),
      headers: {
        "Content-Type": "application/json",
      }
    })
    if (!backendResponse.ok) {
      message = "Something went wrong";
      status = 500;
    }
  } catch {
    message = "Something went wrong";
    status = 500;
  }
  
  // Return a 200 status and a response to the frontend
  return new Response(
    JSON.stringify({
      message: message,
    }),
    {
      status: status,
    }
  );
};