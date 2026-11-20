export interface HealthStatus {
  status: string;
  app: string;
  version: string;
  environment: string;
  database_configured: boolean;
  firecrawl_configured: boolean;
  auth_configured: boolean;
}

export * from './discovery';
export * from './opportunity';
export * from './matching';
export * from './application';
