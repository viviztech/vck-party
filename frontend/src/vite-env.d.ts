/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_URL: string;
  readonly VITE_WS_URL: string;
  readonly VITE_APP_NAME: string;
  readonly VITE_APP_VERSION: string;
  readonly VITE_ENABLE_MOCK_DATA: string;
  readonly VITE_ENABLE_ANALYTICS: string;
  readonly VITE_ENABLE_LOGGING: string;
  readonly VITE_TOKEN_KEY: string;
  readonly VITE_REFRESH_TOKEN_KEY: string;
  readonly VITE_GA_TRACKING_ID?: string;
  readonly VITE_SENTRY_DSN?: string;
  readonly DEV: boolean;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
  readonly hot: {
    accept: (modulePath: string, callback: () => void) => void;
    dispose: (callback: () => void) => void;
    invalidate: () => void;
  };
}
