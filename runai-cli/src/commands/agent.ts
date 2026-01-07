/**
 * Agent query commands
 */

import { RunAIAgentClient } from '../api/client.js';
import { logger } from '../utils/logger.js';
import { loadConfig } from '../utils/config.js';
import { validateQuery, sanitizeInput } from '../utils/validation.js';

/**
 * Send a single query to the agent
 */
export async function askCommand(query: string, options: { stream?: boolean }): Promise<void> {
  try {
    // Validate and sanitize input
    validateQuery(query);
    const sanitizedQuery = sanitizeInput(query);
    
    // Load config and create client
    const config = loadConfig();
    const client = new RunAIAgentClient(config.agentUrl, config.timeout);
    
    // Check server health
    logger.startSpinner('Connecting to agent...');
    const health = await client.healthCheck();
    
    if (!health.running) {
      logger.stopSpinner(false);
      logger.error(`Agent server is not running at ${config.agentUrl}`);
      logger.info('Start the server with: runai-cli server start');
      process.exit(1);
    }
    
    logger.updateSpinner('Processing query...');
    
    // Handle streaming vs non-streaming
    if (options.stream || config.stream) {
      logger.clearSpinner();
      logger.plain(''); // Newline
      
      let output = '';
      for await (const chunk of client.queryStream(sanitizedQuery)) {
        process.stdout.write(chunk);
        output += chunk;
      }
      
      logger.plain('\n'); // Final newline
    } else {
      const response = await client.query(sanitizedQuery, false);
      logger.stopSpinner();
      
      if (response.status === 'error') {
        logger.error('Agent Error:');
        logger.plain(response.error || 'Unknown error');
        process.exit(1);
      }
      
      logger.plain(''); // Newline
      logger.plain(response.output);
      
      // Show metadata if available
      if (response.metadata && config.debug) {
        logger.plain('');
        logger.debug('Metadata:');
        logger.json(response.metadata);
      }
    }
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


