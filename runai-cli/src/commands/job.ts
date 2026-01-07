/**
 * Job operation commands
 */

import * as fs from 'fs';
import { logger } from '../utils/logger.js';
import { RunAIAgentClient } from '../api/client.js';
import { loadConfig } from '../utils/config.js';
import type { JobSpec } from '../types/index.js';
import { validateJobSpec } from '../utils/validation.js';

/**
 * Submit a job to RunAI
 */
export async function submitJobCommand(specPath: string): Promise<void> {
  try {
    // Read job spec from file
    if (!fs.existsSync(specPath)) {
      logger.error(`Job spec file not found: ${specPath}`);
      process.exit(1);
    }
    
    const specContent = fs.readFileSync(specPath, 'utf-8');
    const jobSpec: JobSpec = JSON.parse(specContent);
    
    // Validate spec
    validateJobSpec(jobSpec);
    
    // Load config and create client
    const config = loadConfig();
    const client = new RunAIAgentClient(config.agentUrl, config.timeout);
    
    // Build query
    const query = `Submit a training job with the following specification: ${JSON.stringify(jobSpec, null, 2)}`;
    
    logger.startSpinner('Submitting job...');
    const response = await client.query(query, false);
    logger.stopSpinner();
    
    if (response.status === 'error') {
      logger.error('Failed to submit job:');
      logger.plain(response.error || 'Unknown error');
      process.exit(1);
    }
    
    logger.success('Job submitted successfully!');
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
 * Check job status
 */
export async function statusJobCommand(jobName: string, options: { project?: string }): Promise<void> {
  try {
    const config = loadConfig();
    const client = new RunAIAgentClient(config.agentUrl, config.timeout);
    
    // Build query
    let query = `Check the status of job "${jobName}"`;
    if (options.project) {
      query += ` in project "${options.project}"`;
    }
    
    logger.startSpinner('Checking job status...');
    const response = await client.query(query, false);
    logger.stopSpinner();
    
    if (response.status === 'error') {
      logger.error('Failed to check job status:');
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
 * List all jobs
 */
export async function listJobsCommand(options: { project?: string }): Promise<void> {
  try {
    const config = loadConfig();
    const client = new RunAIAgentClient(config.agentUrl, config.timeout);
    
    // Build query
    let query = 'List all jobs';
    if (options.project) {
      query += ` in project "${options.project}"`;
    }
    
    logger.startSpinner('Fetching jobs...');
    const response = await client.query(query, false);
    logger.stopSpinner();
    
    if (response.status === 'error') {
      logger.error('Failed to list jobs:');
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
 * Delete a job
 */
export async function deleteJobCommand(jobName: string, options: { project?: string; force?: boolean }): Promise<void> {
  try {
    const config = loadConfig();
    const client = new RunAIAgentClient(config.agentUrl, config.timeout);
    
    // Build query
    let query = `Delete job "${jobName}"`;
    if (options.project) {
      query += ` from project "${options.project}"`;
    }
    if (options.force) {
      query += ' (confirmed: yes)';
    }
    
    logger.startSpinner('Deleting job...');
    const response = await client.query(query, false);
    logger.stopSpinner();
    
    if (response.status === 'error') {
      logger.error('Failed to delete job:');
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


