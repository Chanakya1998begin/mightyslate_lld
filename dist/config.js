"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.loadConfiguration = loadConfiguration;
const fs_1 = __importDefault(require("fs"));
const path_1 = __importDefault(require("path"));
const DEFAULT_CONFIG_PATH = path_1.default.resolve(process.cwd(), 'config', 'default.json');
function isClientSeed(input) {
    if (typeof input !== 'object' || input === null) {
        return false;
    }
    const candidate = input;
    return (typeof candidate.id === 'string' &&
        candidate.id.trim().length > 0 &&
        typeof candidate.name === 'string' &&
        candidate.name.trim().length > 0 &&
        (candidate.contact === undefined || typeof candidate.contact === 'string'));
}
function validateConfig(raw) {
    if (typeof raw !== 'object' || raw === null) {
        throw new Error('Feature configuration must be a JSON object.');
    }
    const candidate = raw;
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
        seedClients: seedClients,
    };
}
function loadConfiguration(configPath = process.env.FEATURE_CONFIG_PATH ?? DEFAULT_CONFIG_PATH) {
    if (!fs_1.default.existsSync(configPath)) {
        throw new Error(`Feature configuration file not found at ${configPath}`);
    }
    const contents = fs_1.default.readFileSync(configPath, 'utf-8');
    let parsed;
    try {
        parsed = JSON.parse(contents);
    }
    catch (error) {
        throw new Error(`Failed to parse feature configuration JSON: ${error.message}`);
    }
    return validateConfig(parsed);
}
//# sourceMappingURL=config.js.map