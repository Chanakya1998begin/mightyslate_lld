import express, { Request, Response } from 'express';
import { loadConfiguration } from './config';
import { ClientStore } from './datastore/clientStore';
import { FeatureFlagService } from './services/featureFlagService';
import { ClientSeed } from './types';

const app = express();
app.use(express.json());

const configuration = loadConfiguration();
const store = new ClientStore();
const featureService = new FeatureFlagService(configuration.featureName, store);

featureService.bootstrap(configuration.seedClients);

function validateClientPayload(payload: unknown): ClientSeed {
  if (typeof payload !== 'object' || payload === null) {
    throw new Error('Payload must be an object.');
  }

  const candidate = payload as Record<string, unknown>;
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

app.get('/health', (_req: Request, res: Response) => {
  const audit = featureService.audit();
  res.json({
    status: 'ok',
    feature: audit.featureName,
    clients: audit.totalClients,
    compliant: audit.compliantClients,
  });
});

app.get('/clients', (_req: Request, res: Response) => {
  res.json({ data: featureService.listClients() });
});

app.get('/clients/:id', (req: Request, res: Response) => {
  try {
    const client = featureService.getClient(req.params.id);
    res.json({ data: client });
  } catch (error) {
    res.status(404).json({ error: (error as Error).message });
  }
});

app.post('/clients', (req: Request, res: Response) => {
  try {
    const descriptor = validateClientPayload(req.body);
    const client = featureService.registerClient(descriptor);
    res.status(201).json({ data: client });
  } catch (error) {
    res.status(400).json({ error: (error as Error).message });
  }
});

app.post('/clients/:id/refresh', (req: Request, res: Response) => {
  try {
    const client = featureService.ensureClientHasFeature(req.params.id);
    res.json({ data: client });
  } catch (error) {
    res.status(404).json({ error: (error as Error).message });
  }
});

app.get('/audit', (_req: Request, res: Response) => {
  res.json({ data: featureService.audit() });
});

const port = Number(process.env.PORT ?? 3000);
app.listen(port, () => {
  console.log(`Feature flag service listening on port ${port}`);
});

export default app;
