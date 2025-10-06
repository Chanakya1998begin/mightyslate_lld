import { ClientProfile, ClientSeed } from '../types';

function cloneClient(client: ClientProfile): ClientProfile {
  return JSON.parse(JSON.stringify(client)) as ClientProfile;
}

export class ClientStore {
  private readonly clients = new Map<string, ClientProfile>();

  constructor(initialClients: ClientProfile[] = []) {
    initialClients.forEach((client) => {
      this.clients.set(client.id, cloneClient(client));
    });
  }

  seedFrom(descriptors: ClientSeed[]): void {
    descriptors.forEach((descriptor) => {
      if (!this.clients.has(descriptor.id)) {
        this.clients.set(descriptor.id, {
          ...descriptor,
          features: [],
        });
      }
    });
  }

  list(): ClientProfile[] {
    return Array.from(this.clients.values()).map((client) => cloneClient(client));
  }

  get(clientId: string): ClientProfile | undefined {
    const client = this.clients.get(clientId);
    return client ? cloneClient(client) : undefined;
  }

  upsert(client: ClientProfile): ClientProfile {
    this.clients.set(client.id, cloneClient(client));
    const stored = this.clients.get(client.id);
    if (!stored) {
      throw new Error('Failed to persist client profile.');
    }

    return cloneClient(stored);
  }

  update(clientId: string, mutator: (client: ClientProfile) => ClientProfile): ClientProfile {
    const existing = this.clients.get(clientId);

    if (!existing) {
      throw new Error(`Client '${clientId}' does not exist.`);
    }

    const mutated = mutator(cloneClient(existing));
    this.clients.set(clientId, cloneClient(mutated));

    const stored = this.clients.get(clientId);
    if (!stored) {
      throw new Error('Failed to persist mutated client.');
    }

    return cloneClient(stored);
  }

  has(clientId: string): boolean {
    return this.clients.has(clientId);
  }
}
