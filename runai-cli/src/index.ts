#!/usr/bin/env node

/**
 * RunAI Agent CLI
 * 
 * A lightweight TypeScript CLI for interacting with the RunAI Agent backend.
 */

import { Command } from 'commander';
import { askCommand } from './commands/agent.js';
import { replCommand } from './commands/repl.js';
import { submitCommand, submitInteractiveCommand } from './commands/submit.js';
import { statusCommand, startCommand, stopCommand, logsCommand } from './commands/server.js';
import { submitJobCommand, statusJobCommand, listJobsCommand, deleteJobCommand } from './commands/job.js';
import { infoEnvironmentCommand, createEnvironmentCommand, listEnvironmentsCommand, deleteEnvironmentCommand } from './commands/environment.js';
import { loadConfig, saveConfig, getConfigPath, resetConfig, connectRemote, connectLocal, isRemoteAgent } from './utils/config.js';
import { logger } from './utils/logger.js';
import { RunAIAgentClient } from './api/client.js';

const program = new Command();

program
  .name('runai-cli')
  .description('Lightweight CLI for RunAI Agent')
  .version('0.1.0');

// Submit command - natural language job submission (NEW!)
program
  .command('submit [prompt]')
  .description('🚀 Submit a job using natural language (GenAI-style)')
  .option('-s, --stream', 'Stream the response in real-time')
  .option('-p, --project <project>', 'Target project name')
  .option('-e, --execute', 'Auto-execute the generated script (submit immediately)')
  .option('--no-confirm', 'Skip confirmation prompts')
  .action((prompt, options) => {
    if (prompt) {
      submitCommand(prompt, options);
    } else {
      submitInteractiveCommand();
    }
  });

// Ask command - send a query to the agent
program
  .command('ask <query>')
  .description('Send a query to the RunAI agent')
  .option('-s, --stream', 'Stream the response')
  .action(askCommand);

// Chat command - interactive REPL mode
program
  .command('chat')
  .alias('repl')
  .description('Start interactive REPL mode')
  .action(replCommand);

// Server management commands
const serverCmd = program
  .command('server')
  .description('Manage the agent server');

serverCmd
  .command('status')
  .description('Check if the agent server is running')
  .action(statusCommand);

serverCmd
  .command('start')
  .description('Start the agent server')
  .option('-b, --background', 'Run in background', false)
  .action(startCommand);

serverCmd
  .command('stop')
  .description('Stop the agent server')
  .action(stopCommand);

serverCmd
  .command('logs')
  .description('Show server logs')
  .action(logsCommand);

// Job management commands
const jobCmd = program
  .command('job')
  .description('Manage RunAI jobs');

jobCmd
  .command('submit <spec>')
  .description('Submit a job from a JSON spec file')
  .action(submitJobCommand);

jobCmd
  .command('status <name>')
  .description('Check the status of a job')
  .option('-p, --project <project>', 'Project name')
  .action(statusJobCommand);

jobCmd
  .command('list')
  .description('List all jobs')
  .option('-p, --project <project>', 'Filter by project name')
  .action(listJobsCommand);

jobCmd
  .command('delete <name>')
  .description('Delete a job')
  .option('-p, --project <project>', 'Project name')
  .option('-f, --force', 'Skip confirmation')
  .action(deleteJobCommand);

// Environment management commands
const envCmd = program
  .command('env')
  .description('Manage environments');

envCmd
  .command('info')
  .description('Show environment information')
  .action(infoEnvironmentCommand);

envCmd
  .command('create <spec>')
  .description('Create an environment from a JSON spec file')
  .action(createEnvironmentCommand);

envCmd
  .command('list')
  .description('List all environments')
  .action(listEnvironmentsCommand);

envCmd
  .command('delete <name>')
  .description('Delete an environment')
  .option('-f, --force', 'Skip confirmation')
  .action(deleteEnvironmentCommand);

// Config management commands
const configCmd = program
  .command('config')
  .description('Manage CLI configuration');

configCmd
  .command('show')
  .description('Show current configuration')
  .action(() => {
    const config = loadConfig();
    const isRemote = config.remoteMode || isRemoteAgent(config.agentUrl);
    logger.header('Current Configuration');
    logger.table({
      'Agent URL': config.agentUrl,
      'Mode': isRemote ? 'Remote' : 'Local',
      'Timeout': `${config.timeout}ms`,
      'Stream': config.stream ? 'enabled' : 'disabled',
      'Debug': config.debug ? 'enabled' : 'disabled',
      'Config File': getConfigPath(),
    });
  });

configCmd
  .command('set <key> <value>')
  .description('Set a configuration value')
  .action((key: string, value: string) => {
    const validKeys = ['agentUrl', 'timeout', 'stream', 'debug'];
    
    if (!validKeys.includes(key)) {
      logger.error(`Invalid config key: ${key}`);
      logger.info(`Valid keys: ${validKeys.join(', ')}`);
      logger.plain('');
      logger.info('💡 Tip: To change agent URL, use: runai-cli connect <url>');
      process.exit(1);
    }
    
    let parsedValue: any = value;
    
    // Parse value based on key
    if (key === 'timeout') {
      parsedValue = parseInt(value, 10);
      if (isNaN(parsedValue)) {
        logger.error('Timeout must be a number');
        process.exit(1);
      }
    } else if (key === 'stream' || key === 'debug') {
      parsedValue = value === 'true' || value === '1';
    } else if (key === 'agentUrl') {
      // When setting agentUrl directly, also update remote mode
      const isRemote = isRemoteAgent(value);
      saveConfig({ agentUrl: value, remoteMode: isRemote });
      logger.success(`Configuration updated: ${key} = ${parsedValue}`);
      logger.info(`Mode set to: ${isRemote ? 'Remote' : 'Local'}`);
      logger.plain('');
      logger.info('💡 Tip: Use "runai-cli connect <url>" for easier remote connection.');
      return;
    }
    
    saveConfig({ [key]: parsedValue });
    logger.success(`Configuration updated: ${key} = ${parsedValue}`);
  });

configCmd
  .command('reset')
  .description('Reset configuration to defaults')
  .action(() => {
    resetConfig();
    logger.success('Configuration reset to defaults');
  });

// Connect command - manage remote/local agent connections
program
  .command('connect <target>')
  .description('Connect to a remote agent or switch to local mode')
  .option('--no-verify', 'Skip connection verification')
  .action(async (target: string, options: { verify?: boolean }) => {
    const verify = options.verify !== false; // Default to true
    
    if (target.toLowerCase() === 'local') {
      // Switch to local mode
      connectLocal();
      logger.success('Switched to local agent mode');
      logger.info('Agent URL: http://localhost:8000');
      logger.plain('');
      logger.info('Start the local agent with: runai-cli server start');
    } else {
      // Connect to remote agent
      let agentUrl = target;
      
      // Add http:// if not present
      if (!agentUrl.startsWith('http://') && !agentUrl.startsWith('https://')) {
        agentUrl = `http://${agentUrl}`;
      }
      
      // Verify connection if requested
      if (verify) {
        logger.startSpinner(`Verifying connection to ${agentUrl}...`);
        const client = new RunAIAgentClient(agentUrl, 10000);
        const health = await client.healthCheck();
        logger.stopSpinner();
        
        if (!health.running) {
          logger.error(`Cannot connect to agent at ${agentUrl}`);
          logger.info('The agent might be offline or the URL is incorrect.');
          logger.plain('');
          logger.info('To skip verification, use: runai-cli connect <url> --no-verify');
          process.exit(1);
        }
        
        logger.success(`Successfully connected to remote agent!`);
      }
      
      // Save connection
      connectRemote(agentUrl);
      logger.success(`Connected to remote agent`);
      logger.info(`Agent URL: ${agentUrl}`);
      logger.plain('');
      logger.info('💡 Tip: You can now use all CLI commands except server start/stop.');
      logger.info('💡 Check status with: runai-cli server status');
    }
  });

// Parse arguments
program.parse(process.argv);

// Show help if no command provided
if (!process.argv.slice(2).length) {
  program.outputHelp();
}

