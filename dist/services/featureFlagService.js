"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.FeatureFlagService = void 0;
const AUTO_ENFORCEMENT_REASON = 'auto:global-rule';
function normalizeFeatureState(feature) {
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
function buildGrant(featureName) {
    return {
        name: featureName,
        enabled: true,
        enabledAt: new Date().toISOString(),
        reason: AUTO_ENFORCEMENT_REASON,
        enforced: true,
    };
}
function ensureFeature(featureName, profile) {
    const updatedFeatures = profile.features ? [...profile.features] : [];
    const existingIndex = updatedFeatures.findIndex((feature) => feature.name === featureName);
    if (existingIndex >= 0) {
        updatedFeatures[existingIndex] = normalizeFeatureState(updatedFeatures[existingIndex]);
    }
    else {
        updatedFeatures.push(buildGrant(featureName));
    }
    return {
        ...profile,
        features: updatedFeatures,
    };
}
class FeatureFlagService {
    constructor(featureName, store) {
        this.featureName = featureName;
        this.store = store;
    }
    bootstrap(seedClients) {
        this.store.seedFrom(seedClients);
        this.store.list().forEach((client) => {
            const enforced = ensureFeature(this.featureName, client);
            this.store.upsert(enforced);
        });
    }
    registerClient(descriptor) {
        const sanitizedDescriptor = {
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
            const merged = {
                ...existing,
                name: sanitizedDescriptor.name || existing.name,
                contact: sanitizedDescriptor.contact ?? existing.contact,
            };
            const enforced = ensureFeature(this.featureName, merged);
            return this.store.upsert(enforced);
        }
        const profile = {
            ...sanitizedDescriptor,
            features: [],
        };
        const enforced = ensureFeature(this.featureName, profile);
        return this.store.upsert(enforced);
    }
    ensureClientHasFeature(clientId) {
        const client = this.store.get(clientId);
        if (!client) {
            throw new Error(`Client '${clientId}' not found.`);
        }
        const enforced = ensureFeature(this.featureName, client);
        return this.store.upsert(enforced);
    }
    listClients() {
        return this.store.list();
    }
    getClient(clientId) {
        const client = this.store.get(clientId);
        if (!client) {
            throw new Error(`Client '${clientId}' not found.`);
        }
        return client;
    }
    audit() {
        const allClients = this.store.list();
        const nonCompliant = allClients.filter((client) => !client.features.some((feature) => feature.name === this.featureName && feature.enabled));
        return {
            featureName: this.featureName,
            totalClients: allClients.length,
            compliantClients: allClients.length - nonCompliant.length,
            nonCompliantClients: nonCompliant.map((client) => client.id),
        };
    }
}
exports.FeatureFlagService = FeatureFlagService;
//# sourceMappingURL=featureFlagService.js.map