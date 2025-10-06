export interface ClientSeed {
  id: string;
  name: string;
  contact?: string;
}

export interface FeatureGrant {
  name: string;
  enabled: boolean;
  enabledAt: string;
  reason: string;
  enforced: boolean;
}

export interface ClientProfile extends ClientSeed {
  features: FeatureGrant[];
}

export interface FeatureRuleConfig {
  featureName: string;
  seedClients: ClientSeed[];
}

export interface FeatureComplianceReport {
  featureName: string;
  totalClients: number;
  compliantClients: number;
  nonCompliantClients: string[];
}
