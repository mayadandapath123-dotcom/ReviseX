/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** Absolute origin of the API when it is NOT same-origin. Leave unset for dev
   *  (Vite proxy) and for single-origin deploys; both use the default '/api'. */
  readonly VITE_API_URL?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
