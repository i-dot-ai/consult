import { QueryClient, createMutation, createQuery, type MutateOptions, type RefetchOptions } from "@tanstack/svelte-query";
import { type HttpMethod } from "../global/types";

interface BuildQueryOptions {
  key?: string[],
  errorMessage?: string,
  method?: HttpMethod,
  headers?: HeadersInit,
  onSuccess?: (data?: unknown, variables?: MutationArgs) => Promise<void>,
  onError?: (error: any) => Promise<void>,
  getVariables?: <T>(...args: T[]) => unknown,
}

interface MutationArgs {
  body?: BodyInit,
  headers?: HeadersInit,
  params?: Record<string, string>,
}
type MutateArgs = [variables: unknown, options?: MutateOptions<unknown, unknown, unknown, unknown> | undefined];
type RefetchArgs = [options?: RefetchOptions | undefined];

interface DoFetchArgs {
  url: string,
  method: BuildQueryOptions["method"],
  errorMessage: BuildQueryOptions["errorMessage"],
  body?: BodyInit,
  headers?: HeadersInit,
}

export type FetchError<T> = {
  status: number,
  data: T,
  message: string,
}

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60, // 5 mins
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
    let errorData: unknown = null;
    try {
      errorData = await response.json();
    } catch {}

    const fetchError = {
      status: response.status,
      data: errorData,
      message: errorMessage || "Unknown",
    }

    throw fetchError;
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
    result = result.replaceAll(`:${key}`, params![key]);
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
    fetch: (...args: unknown[]) => {
      let variables;

      if (getVariables){
        variables = getVariables(...args);
      };

      // TODO: Refactor to simplify
      if (isMutation) {
        const mutationResult = result as ReturnType<typeof createMutation>;
        if (variables) {
          mutationResult.mutate(variables);
        } else {
          mutationResult.mutate.apply(this, args as MutateArgs);
        }
      } else {
        const queryResult = result as ReturnType<typeof createQuery>;
        if (variables) {
          queryResult.refetch(variables);
        } else {
          queryResult.refetch.apply(this, args as RefetchArgs);
        }
      }
    }
  })
}