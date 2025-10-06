import { ClientStore } from '../src/datastore/clientStore';
import { FeatureFlagService } from '../src/services/featureFlagService';
import { ClientProfile, ClientSeed } from '../src/types';

const FEATURE_NAME = 'GPT-5-Codex (Preview)';

function buildService(initialClients: ClientProfile[] = []) {
  const store = new ClientStore(initialClients);
  const service = new FeatureFlagService(FEATURE_NAME, store);
  return { service, store };
}

describe('FeatureFlagService', () => {
  it('bootstrap enforces the feature for seed clients without existing features', () => {
    const seeds: ClientSeed[] = [
      { id: 'acme', name: 'Acme Corp' },
      { id: 'globex', name: 'Globex' },
    ];

    const { service } = buildService();
    service.bootstrap(seeds);

    const clients = service.listClients();
    expect(clients).toHaveLength(seeds.length);
    clients.forEach((client) => {
      expect(client.features.some((feature) => feature.name === FEATURE_NAME)).toBe(true);
      expect(
        client.features.find((feature) => feature.name === FEATURE_NAME)?.enabled,
      ).toBeTruthy();
    });
  });

  it('registerClient enforces the feature and preserves metadata', () => {
    const { service } = buildService();

    const registered = service.registerClient({
      id: 'initech',
      name: 'Initech',
      contact: 'tech@initech.example',
    });

    const feature = registered.features.find((item) => item.name === FEATURE_NAME);
    expect(feature).toBeDefined();
    expect(feature?.enabled).toBe(true);
    expect(feature?.enforced).toBe(true);
    expect(feature?.reason).toBe('auto:global-rule');
  });

  it('ensureClientHasFeature re-enables the feature if it was manually disabled', () => {
    const disabledClient: ClientProfile = {
      id: 'umbrella',
      name: 'Umbrella Corp',
      features: [
        {
          name: FEATURE_NAME,
          enabled: false,
          enabledAt: new Date(2025, 0, 1).toISOString(),
          reason: 'manual-disable',
          enforced: false,
        },
      ],
    };

    const { service } = buildService([disabledClient]);

    const repaired = service.ensureClientHasFeature('umbrella');
    const feature = repaired.features.find((item) => item.name === FEATURE_NAME);

    expect(feature).toBeDefined();
    expect(feature?.enabled).toBe(true);
    expect(feature?.enforced).toBe(true);
    expect(feature?.reason).toBe('auto:global-rule');
  });

  it('audit reports non-compliant clients prior to enforcement', () => {
    const seed: ClientProfile = {
      id: 'wonka',
      name: 'Wonka Industries',
      features: [],
    };
    const { service } = buildService([seed]);

    const before = service.audit();
    expect(before.nonCompliantClients).toContain('wonka');

    service.ensureClientHasFeature('wonka');

    const after = service.audit();
    expect(after.nonCompliantClients).toHaveLength(0);
    expect(after.compliantClients).toBe(after.totalClients);
  });
});
