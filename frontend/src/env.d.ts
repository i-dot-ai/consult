/// <reference types="astro/client" />

declare namespace App {
  interface Locals {
    contextId: string;
  }
}

interface ImportMetaEnv {
  readonly PUBLIC_BACKEND_URL?: string;
  readonly PUBLIC_INTERNAL_ACCESS_CLIENT_ID?: string;
  readonly PUBLIC_LANGFUSE_URL?: string;
  readonly PUBLIC_HOMEPAGE_URL?: string;
  readonly ENVIRONMENT?: string;
  readonly OTEL_EXPORTER_OTLP_ENDPOINT?: string;
  readonly LOGGING_ENABLED?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}