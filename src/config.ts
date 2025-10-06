import fs from 'fs';
import path from 'path';
import { FeatureRuleConfig, ClientSeed } from './types';

const DEFAULT_CONFIG_PATH = path.resolve(process.cwd(), 'config', 'default.json');

function isClientSeed(input: unknown): input is ClientSeed {
  if (typeof input !== 'object' || input === null) {
    return false;
  }

  const candidate = input as Record<string, unknown>;
  return (
    typeof candidate.id === 'string' &&
    candidate.id.trim().length > 0 &&
    typeof candidate.name === 'string' &&
    candidate.name.trim().length > 0 &&
    (candidate.contact === undefined || typeof candidate.contact === 'string')
  );
}

function validateConfig(raw: unknown): FeatureRuleConfig {
  if (typeof raw !== 'object' || raw === null) {
    throw new Error('Feature configuration must be a JSON object.');
  }

  const candidate = raw as Record<string, unknown>;
  const featureName = candidate.featureName;
  const seedClients = candidate.seedClients;

  if (typeof featureName !== 'string' || featureName.trim().length === 0) {
    throw new Error('`featureName` must be a non-empty string.');
  }

  if (!Array.isArray(seedClients)) {
    throw new Error('`seedClients` must be an array of client descriptors.');
  }

  seedClients.forEach((seed, index) => {
    if (!isClientSeed(seed)) {
      throw new Error(`Seed client at index ${index} is invalid.`);
    }
  });

  return {
    featureName: featureName.trim(),
    seedClients: seedClients as ClientSeed[],
  };
}

export function loadConfiguration(
  configPath = process.env.FEATURE_CONFIG_PATH ?? DEFAULT_CONFIG_PATH,
): FeatureRuleConfig {
  if (!fs.existsSync(configPath)) {
    throw new Error(`Feature configuration file not found at ${configPath}`);
  }

  const contents = fs.readFileSync(configPath, 'utf-8');
  let parsed: unknown;

  try {
    parsed = JSON.parse(contents);
  } catch (error) {
    throw new Error(`Failed to parse feature configuration JSON: ${(error as Error).message}`);
  }

  return validateConfig(parsed);
}
