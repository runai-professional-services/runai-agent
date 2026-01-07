/**
 * Configuration management for RunAI CLI
 */

import * as fs from 'fs';
import * as path from 'path';
import * as os from 'os';
import type { CLIConfig } from '../types/index.js';

const CONFIG_DIR = path.join(os.homedir(), '.runai-cli');
const CONFIG_FILE = path.join(CONFIG_DIR, 'config.json');

const DEFAULT_CONFIG: CLIConfig = {
  agentUrl: 'http://localhost:8000',
  timeout: 60000,
  stream: false,
  debug: false,
  remoteMode: false,
};

/**
 * Ensure config directory exists
 */
function ensureConfigDir(): void {
  if (!fs.existsSync(CONFIG_DIR)) {
    fs.mkdirSync(CONFIG_DIR, { recursive: true });
  }
}

/**
 * Load configuration from file or return defaults
 */
export function loadConfig(): CLIConfig {
  ensureConfigDir();
  
  if (!fs.existsSync(CONFIG_FILE)) {
    return DEFAULT_CONFIG;
  }
  
  try {
    const content = fs.readFileSync(CONFIG_FILE, 'utf-8');
    const userConfig = JSON.parse(content) as Partial<CLIConfig>;
    return { ...DEFAULT_CONFIG, ...userConfig };
  } catch (error) {
    console.warn(`Warning: Failed to parse config file, using defaults`);
    return DEFAULT_CONFIG;
  }
}

/**
 * Save configuration to file
 */
export function saveConfig(config: Partial<CLIConfig>): void {
  ensureConfigDir();
  
  const currentConfig = loadConfig();
  const newConfig = { ...currentConfig, ...config };
  
  fs.writeFileSync(CONFIG_FILE, JSON.stringify(newConfig, null, 2), 'utf-8');
}

/**
 * Get config file path
 */
export function getConfigPath(): string {
  return CONFIG_FILE;
}

/**
 * Reset configuration to defaults
 */
export function resetConfig(): void {
  ensureConfigDir();
  fs.writeFileSync(CONFIG_FILE, JSON.stringify(DEFAULT_CONFIG, null, 2), 'utf-8');
}

/**
 * Check if agent URL is remote (not localhost)
 */
export function isRemoteAgent(agentUrl: string): boolean {
  const url = agentUrl.toLowerCase();
  return !url.includes('localhost') && !url.includes('127.0.0.1');
}

/**
 * Connect to a remote agent
 */
export function connectRemote(agentUrl: string): void {
  const isRemote = isRemoteAgent(agentUrl);
  
  saveConfig({
    agentUrl,
    remoteMode: isRemote,
  });
}

/**
 * Connect to local agent (reset to localhost)
 */
export function connectLocal(): void {
  saveConfig({
    agentUrl: 'http://localhost:8000',
    remoteMode: false,
  });
}


