"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const express_1 = __importDefault(require("express"));
const config_1 = require("./config");
const clientStore_1 = require("./datastore/clientStore");
const featureFlagService_1 = require("./services/featureFlagService");
const app = (0, express_1.default)();
app.use(express_1.default.json());
const configuration = (0, config_1.loadConfiguration)();
const store = new clientStore_1.ClientStore();
const featureService = new featureFlagService_1.FeatureFlagService(configuration.featureName, store);
featureService.bootstrap(configuration.seedClients);
function validateClientPayload(payload) {
    if (typeof payload !== 'object' || payload === null) {
        throw new Error('Payload must be an object.');
    }
    const candidate = payload;
    const id = typeof candidate.id === 'string' ? candidate.id : '';
    const name = typeof candidate.name === 'string' ? candidate.name : '';
    const contact = typeof candidate.contact === 'string' ? candidate.contact : undefined;
    if (!id.trim()) {
        throw new Error('Client `id` is required.');
    }
    if (!name.trim()) {
        throw new Error('Client `name` is required.');
    }
    return {
        id: id.trim(),
        name: name.trim(),
        contact: contact?.trim(),
    };
}
app.get('/health', (_req, res) => {
    const audit = featureService.audit();
    res.json({
        status: 'ok',
        feature: audit.featureName,
        clients: audit.totalClients,
        compliant: audit.compliantClients,
    });
});
app.get('/clients', (_req, res) => {
    res.json({ data: featureService.listClients() });
});
app.get('/clients/:id', (req, res) => {
    try {
        const client = featureService.getClient(req.params.id);
        res.json({ data: client });
    }
    catch (error) {
        res.status(404).json({ error: error.message });
    }
});
app.post('/clients', (req, res) => {
    try {
        const descriptor = validateClientPayload(req.body);
        const client = featureService.registerClient(descriptor);
        res.status(201).json({ data: client });
    }
    catch (error) {
        res.status(400).json({ error: error.message });
    }
});
app.post('/clients/:id/refresh', (req, res) => {
    try {
        const client = featureService.ensureClientHasFeature(req.params.id);
        res.json({ data: client });
    }
    catch (error) {
        res.status(404).json({ error: error.message });
    }
});
app.get('/audit', (_req, res) => {
    res.json({ data: featureService.audit() });
});
const port = Number(process.env.PORT ?? 3000);
app.listen(port, () => {
    console.log(`Feature flag service listening on port ${port}`);
});
exports.default = app;
//# sourceMappingURL=index.js.map