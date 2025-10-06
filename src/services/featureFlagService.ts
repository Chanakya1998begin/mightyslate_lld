import { ClientStore } from '../datastore/clientStore';
import { ClientProfile, ClientSeed, FeatureComplianceReport, FeatureGrant } from '../types';

const AUTO_ENFORCEMENT_REASON = 'auto:global-rule';

function normalizeFeatureState(feature: FeatureGrant): FeatureGrant {
  if (!feature.enabled) {
    return {
      ...feature,
      enabled: true,
      enabledAt: new Date().toISOString(),
      reason: AUTO_ENFORCEMENT_REASON,
      enforced: true,
    };
  }

  return {
    ...feature,
    enforced: true,
    reason: feature.reason ?? AUTO_ENFORCEMENT_REASON,
  };
}

function buildGrant(featureName: string): FeatureGrant {
  return {
    name: featureName,
    enabled: true,
    enabledAt: new Date().toISOString(),
    reason: AUTO_ENFORCEMENT_REASON,
    enforced: true,
  };
}

function ensureFeature(featureName: string, profile: ClientProfile): ClientProfile {
  const updatedFeatures = profile.features ? [...profile.features] : [];
  const existingIndex = updatedFeatures.findIndex((feature) => feature.name === featureName);

  if (existingIndex >= 0) {
    updatedFeatures[existingIndex] = normalizeFeatureState(updatedFeatures[existingIndex]);
  } else {
    updatedFeatures.push(buildGrant(featureName));
  }

  return {
    ...profile,
    features: updatedFeatures,
  };
}

export class FeatureFlagService {
  constructor(
    private readonly featureName: string,
    private readonly store: ClientStore,
  ) {}

  bootstrap(seedClients: ClientSeed[]): void {
    this.store.seedFrom(seedClients);
    this.store.list().forEach((client) => {
      const enforced = ensureFeature(this.featureName, client);
      this.store.upsert(enforced);
    });
  }

  registerClient(descriptor: ClientSeed): ClientProfile {
    const sanitizedDescriptor: ClientSeed = {
      id: descriptor.id.trim(),
      name: descriptor.name.trim(),
      contact: descriptor.contact?.trim() ?? descriptor.contact,
    };

    if (!sanitizedDescriptor.id) {
      throw new Error('Client id must be provided.');
    }

    if (!sanitizedDescriptor.name) {
      throw new Error('Client name must be provided.');
    }

    const existing = this.store.get(sanitizedDescriptor.id);

    if (existing) {
      const merged: ClientProfile = {
        ...existing,
        name: sanitizedDescriptor.name || existing.name,
        contact: sanitizedDescriptor.contact ?? existing.contact,
      };

      const enforced = ensureFeature(this.featureName, merged);
      return this.store.upsert(enforced);
    }

    const profile: ClientProfile = {
      ...sanitizedDescriptor,
      features: [],
    };

    const enforced = ensureFeature(this.featureName, profile);
    return this.store.upsert(enforced);
  }

  ensureClientHasFeature(clientId: string): ClientProfile {
    const client = this.store.get(clientId);

    if (!client) {
      throw new Error(`Client '${clientId}' not found.`);
    }

    const enforced = ensureFeature(this.featureName, client);
    return this.store.upsert(enforced);
  }

  listClients(): ClientProfile[] {
    return this.store.list();
  }

  getClient(clientId: string): ClientProfile {
    const client = this.store.get(clientId);

    if (!client) {
      throw new Error(`Client '${clientId}' not found.`);
    }

    return client;
  }

  audit(): FeatureComplianceReport {
    const allClients = this.store.list();
    const nonCompliant = allClients.filter(
      (client) =>
        !client.features.some((feature) => feature.name === this.featureName && feature.enabled),
    );

    return {
      featureName: this.featureName,
      totalClients: allClients.length,
      compliantClients: allClients.length - nonCompliant.length,
      nonCompliantClients: nonCompliant.map((client) => client.id),
    };
  }
}
