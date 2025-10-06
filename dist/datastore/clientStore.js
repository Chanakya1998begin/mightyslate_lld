"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ClientStore = void 0;
function cloneClient(client) {
    return JSON.parse(JSON.stringify(client));
}
class ClientStore {
    constructor(initialClients = []) {
        this.clients = new Map();
        initialClients.forEach((client) => {
            this.clients.set(client.id, cloneClient(client));
        });
    }
    seedFrom(descriptors) {
        descriptors.forEach((descriptor) => {
            if (!this.clients.has(descriptor.id)) {
                this.clients.set(descriptor.id, {
                    ...descriptor,
                    features: [],
                });
            }
        });
    }
    list() {
        return Array.from(this.clients.values()).map((client) => cloneClient(client));
    }
    get(clientId) {
        const client = this.clients.get(clientId);
        return client ? cloneClient(client) : undefined;
    }
    upsert(client) {
        this.clients.set(client.id, cloneClient(client));
        const stored = this.clients.get(client.id);
        if (!stored) {
            throw new Error('Failed to persist client profile.');
        }
        return cloneClient(stored);
    }
    update(clientId, mutator) {
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
    has(clientId) {
        return this.clients.has(clientId);
    }
}
exports.ClientStore = ClientStore;
//# sourceMappingURL=clientStore.js.map