/**
 * Interactive REPL mode
 */

import * as readline from 'readline';
import { RunAIAgentClient } from '../api/client.js';
import { logger } from '../utils/logger.js';
import { loadConfig } from '../utils/config.js';
import { sanitizeInput } from '../utils/validation.js';

export async function replCommand(): Promise<void> {
  const config = loadConfig();
  const client = new RunAIAgentClient(config.agentUrl, config.timeout);
  
  // Check server health
  logger.startSpinner('Connecting to agent...');
  const health = await client.healthCheck();
  logger.stopSpinner();
  
  if (!health.running) {
    logger.error(`Agent server is not running at ${config.agentUrl}`);
    logger.info('Start the server with: runai-cli server start');
    process.exit(1);
  }
  
  // Print header
  console.log('');
  logger.header('🤖 RunAI Agent CLI - Interactive Mode');
  logger.info(`Connected to: ${config.agentUrl}`);
  logger.plain('Type your query and press Enter. Type "exit" or "quit" to leave.\n');
  
  // Create readline interface
  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout,
  });
  
  // Show prompt
  rl.setPrompt('> ');
  rl.prompt();
  
  rl.on('line', async (line: string) => {
    const input = sanitizeInput(line);
    
    // Handle special commands
    if (input === 'exit' || input === 'quit') {
      logger.plain('\n👋 Goodbye!\n');
      rl.close();
      process.exit(0);
      return;
    }
    
    if (input === 'clear' || input === 'cls') {
      console.clear();
      rl.prompt();
      return;
    }
    
    if (input === 'help' || input === '?') {
      showHelp();
      rl.prompt();
      return;
    }
    
    if (input.trim().length === 0) {
      rl.prompt();
      return;
    }
    
    // Process query
    try {
      console.log(''); // Newline
      
      if (config.stream) {
        // Streaming mode
        let output = '';
        for await (const chunk of client.queryStream(input)) {
          process.stdout.write(chunk);
          output += chunk;
        }
        console.log('\n'); // Final newline
      } else {
        // Non-streaming mode
        logger.startSpinner('Processing...');
        const response = await client.query(input, false);
        logger.stopSpinner();
        
        if (response.status === 'error') {
          logger.error('Error:');
          logger.plain(response.error || 'Unknown error');
        } else {
          logger.plain(response.output);
        }
        
        console.log(''); // Newline
      }
    } catch (error) {
      logger.clearSpinner();
      
      if (error instanceof Error) {
        logger.error(error.message);
      } else {
        logger.error('Unknown error occurred');
      }
      
      console.log(''); // Newline
    }
    
    rl.prompt();
  });
  
  rl.on('close', () => {
    logger.plain('\n👋 Goodbye!\n');
    process.exit(0);
  });
  
  // Handle Ctrl+C gracefully
  process.on('SIGINT', () => {
    logger.plain('\n👋 Goodbye!\n');
    process.exit(0);
  });
}

function showHelp(): void {
  console.log('');
  logger.section('Available Commands:');
  logger.plain('  exit, quit         Exit the REPL');
  logger.plain('  clear, cls         Clear the screen');
  logger.plain('  help, ?            Show this help message');
  logger.plain('');
  logger.section('Example Queries:');
  logger.plain('  Show me all projects');
  logger.plain('  Submit a training job with 2 GPUs');
  logger.plain('  Check the status of my-job in project-01');
  logger.plain('  Create a Jupyter workspace');
  console.log('');
}

