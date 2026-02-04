import { QueryClient, createMutation, createQuery } from "@tanstack/svelte-query";
import { type HttpMethod } from "../global/types";

interface BuildQueryOptions {
  key?: string[],
  errorMessage?: string,
  method?: HttpMethod,
  headers?: HeadersInit,
  onSuccess?: (data?: unknown, variables?: MutationArgs) => Promise<void>,
  onError?: (error: FetchError) => Promise<void>,
}

interface MutationArgs {
  body?: BodyInit,
  headers?: HeadersInit,
  params?: { string: string },
}

interface DoFetchArgs {
  url: string,
  method: BuildQueryOptions["method"],
  errorMessage: BuildQueryOptions["errorMessage"],
  body?: BodyInit,
  headers?: HeadersInit,
}

export class FetchError extends Error {
  constructor(public response: Response, message?: string) {
    super(message);
  }
}

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60,
      refetchOnMount: false,
      refetchOnWindowFocus: false,
    }
  }
});

const doFetch = async ({
  url,
  method,
  errorMessage,
  body,
  headers,
}: DoFetchArgs) => {
  const response = await fetch(url, {
    method: method,
    body: JSON.stringify(body),
    headers: {
      "Content-Type": "application/json",
      ...headers,
    }
  });
  if (!response.ok) {
    let errorData = null;
    try {
      errorData = await response.json();
    } catch {}

    throw {
      status: response.status,
      data: errorData,
      message: errorMessage || "Unknown",
    }
  };

  try {
    return await response.json();
  } catch {
    return null;
    }
}

const applyParams = (url: string, params: MutationArgs["params"]): string => {
  let result = url.slice(0);

  Object.keys(params!).forEach(key => {
    result = result.replaceAll(`:${key}`, params[key]);
  })

  return result;
}

export const buildQuery = <T>(url: string, {
  key,
  errorMessage = "Query failed",
  method = "GET",
  headers,
  onSuccess,
  onError,
  getVariables,
}: BuildQueryOptions) => {
  let result;
  const isMutation = (["POST", "PUT", "PATCH", "DELETE"] as HttpMethod[]).includes(method);

  // Create mutation for mutating methods
  if (isMutation) {
    result = createMutation(() => ({
      queryKey: key,
      mutationFn: async ({ body, params, headers }: MutationArgs) => {
        const finalUrl = params ? applyParams(url, params) : url;
        return await doFetch({
          url: finalUrl,
          method: method,
          errorMessage: errorMessage,
          body: body,
          headers: headers,
        });
      },
      onSuccess: (data, variables) => {
        if (onSuccess) {
          onSuccess(data, variables);
        }
      },
      onError: (data) => {
        if (onError) {
          onError(data);
        }
      },
    }),
    () => queryClient
  )} else {
    // Create query for non-mutating methods
    result = createQuery<T>(() => ({
      queryKey: key!,
      queryFn: () => doFetch({
        url,
        method,
        errorMessage,
        headers,
      }),
      onSuccess: onSuccess,
      onError: onError,
    }),
    () => queryClient,
  )};

  return Object.assign(result, {
    fetch: (...args) => {
      let variables;

      if (getVariables){
        variables = getVariables(...args);
      };

      // TODO: Refactor to simplify
      if (isMutation) {
        if (variables) {
          result.mutate(variables);
        } else {
          result.mutate.apply(this, args);
        }
      } else {
        if (variables) {
          result.refetch(variables);
        } else {
          result.refetch.apply(this, args);
        }
      }
    }
  })
}
