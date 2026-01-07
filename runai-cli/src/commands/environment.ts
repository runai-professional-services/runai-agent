/**
 * Environment operation commands
 */

import * as fs from 'fs';
import { logger } from '../utils/logger.js';
import { RunAIAgentClient } from '../api/client.js';
import { loadConfig } from '../utils/config.js';
import type { EnvironmentSpec } from '../types/index.js';
import { validateEnvironmentSpec } from '../utils/validation.js';

/**
 * Show environment information
 */
export async function infoEnvironmentCommand(): Promise<void> {
  try {
    const config = loadConfig();
    const client = new RunAIAgentClient(config.agentUrl, config.timeout);
    
    logger.startSpinner('Fetching environment information...');
    const response = await client.query('Show me the current environment setup', false);
    logger.stopSpinner();
    
    if (response.status === 'error') {
      logger.error('Failed to fetch environment info:');
      logger.plain(response.error || 'Unknown error');
      process.exit(1);
    }
    
    logger.plain('');
    logger.plain(response.output);
  } catch (error) {
    logger.stopSpinner(false);
    
    if (error instanceof Error) {
      logger.error(error.message);
    } else {
      logger.error('Unknown error occurred');
    }
    
    process.exit(1);
  }
}

/**
 * Create an environment
 */
export async function createEnvironmentCommand(specPath: string): Promise<void> {
  try {
    // Read environment spec from file
    if (!fs.existsSync(specPath)) {
      logger.error(`Environment spec file not found: ${specPath}`);
      process.exit(1);
    }
    
    const specContent = fs.readFileSync(specPath, 'utf-8');
    const envSpec: EnvironmentSpec = JSON.parse(specContent);
    
    // Validate spec
    validateEnvironmentSpec(envSpec);
    
    // Load config and create client
    const config = loadConfig();
    const client = new RunAIAgentClient(config.agentUrl, config.timeout);
    
    // Build query
    const query = `Create a new environment with the following specification: ${JSON.stringify(envSpec, null, 2)}`;
    
    logger.startSpinner('Creating environment...');
    const response = await client.query(query, false);
    logger.stopSpinner();
    
    if (response.status === 'error') {
      logger.error('Failed to create environment:');
      logger.plain(response.error || 'Unknown error');
      process.exit(1);
    }
    
    logger.success('Environment created successfully!');
    logger.plain('');
    logger.plain(response.output);
  } catch (error) {
    logger.stopSpinner(false);
    
    if (error instanceof Error) {
      logger.error(error.message);
    } else {
      logger.error('Unknown error occurred');
    }
    
    process.exit(1);
  }
}

/**
 * List environments
 */
export async function listEnvironmentsCommand(): Promise<void> {
  try {
    const config = loadConfig();
    const client = new RunAIAgentClient(config.agentUrl, config.timeout);
    
    logger.startSpinner('Fetching environments...');
    const response = await client.query('List all available environments', false);
    logger.stopSpinner();
    
    if (response.status === 'error') {
      logger.error('Failed to list environments:');
      logger.plain(response.error || 'Unknown error');
      process.exit(1);
    }
    
    logger.plain('');
    logger.plain(response.output);
  } catch (error) {
    logger.stopSpinner(false);
    
    if (error instanceof Error) {
      logger.error(error.message);
    } else {
      logger.error('Unknown error occurred');
    }
    
    process.exit(1);
  }
}

/**
 * Delete an environment
 */
export async function deleteEnvironmentCommand(envName: string, options: { force?: boolean }): Promise<void> {
  try {
    const config = loadConfig();
    const client = new RunAIAgentClient(config.agentUrl, config.timeout);
    
    // Build query
    let query = `Delete environment "${envName}"`;
    if (options.force) {
      query += ' (confirmed: yes)';
    }
    
    logger.startSpinner('Deleting environment...');
    const response = await client.query(query, false);
    logger.stopSpinner();
    
    if (response.status === 'error') {
      logger.error('Failed to delete environment:');
      logger.plain(response.error || 'Unknown error');
      process.exit(1);
    }
    
    logger.plain('');
    logger.plain(response.output);
  } catch (error) {
    logger.stopSpinner(false);
    
    if (error instanceof Error) {
      logger.error(error.message);
    } else {
      logger.error('Unknown error occurred');
    }
    
    process.exit(1);
  }
}


