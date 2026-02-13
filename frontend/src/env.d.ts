/// <reference types="astro/client" />

interface ImportMetaEnv {
  readonly PUBLIC_BACKEND_URL?: string;
  readonly PUBLIC_INTERNAL_ACCESS_CLIENT_ID?: string;
  readonly PUBLIC_LANGFUSE_URL?: string;
  readonly PUBLIC_HOMEPAGE_URL?: string;
  readonly ENVIRONMENT?: string;
  readonly TEST_INTERNAL_ACCESS_TOKEN?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
