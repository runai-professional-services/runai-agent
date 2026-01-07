/**
 * Server management commands
 */

import { spawn } from 'child_process';
import { logger } from '../utils/logger.js';
import { loadConfig, isRemoteAgent } from '../utils/config.js';
import { RunAIAgentClient } from '../api/client.js';
import * as fs from 'fs';
import * as path from 'path';
import * as os from 'os';

const PID_FILE = path.join(os.homedir(), '.runai-cli', 'server.pid');

/**
 * Check if the server is running
 */
export async function statusCommand(): Promise<void> {
  const config = loadConfig();
  const client = new RunAIAgentClient(config.agentUrl, 5000);
  const isRemote = config.remoteMode || isRemoteAgent(config.agentUrl);
  
  logger.startSpinner('Checking server status...');
  const health = await client.healthCheck();
  logger.stopSpinner();
  
  if (health.running) {
    logger.success(`Agent server is running at ${config.agentUrl}`);
    
    // Show mode
    if (isRemote) {
      logger.info('Mode: Remote Agent');
      logger.plain('');
      logger.info('💡 Tip: You can manage queries but cannot start/stop the remote server.');
    } else {
      logger.info('Mode: Local Agent');
    }
    
    // Try to get version info
    try {
      const version = await client.getVersion();
      if (Object.keys(version).length > 0) {
        logger.plain('');
        logger.table(version as Record<string, string>);
      }
    } catch {
      // Version endpoint not available
    }
    
    // Check for PID file (only for local)
    if (!isRemote && fs.existsSync(PID_FILE)) {
      try {
        const pid = parseInt(fs.readFileSync(PID_FILE, 'utf-8'), 10);
        logger.info(`Process ID: ${pid}`);
      } catch {
        // Ignore PID file errors
      }
    }
  } else {
    logger.error(`Agent server is not running at ${config.agentUrl}`);
    if (isRemote) {
      logger.info('The remote agent appears to be offline or unreachable.');
      logger.info('Contact your system administrator or check the agent deployment.');
    } else {
      logger.info('Start it with: runai-cli server start');
    }
    process.exit(1);
  }
}

/**
 * Start the agent server
 */
export async function startCommand(options: { background?: boolean }): Promise<void> {
  const config = loadConfig();
  
  // Check if connected to remote agent
  if (config.remoteMode || isRemoteAgent(config.agentUrl)) {
    logger.error('Cannot start a remote agent server');
    logger.info(`You are connected to a remote agent at: ${config.agentUrl}`);
    logger.info('To manage a local server, run: runai-cli connect local');
    logger.plain('');
    logger.info('To check if the remote agent is running, use: runai-cli server status');
    process.exit(1);
  }
  
  // Check if already running
  const client = new RunAIAgentClient(config.agentUrl, 5000);
  const health = await client.healthCheck();
  
  if (health.running) {
    logger.warning(`Server is already running at ${config.agentUrl}`);
    return;
  }
  
  logger.info('Starting RunAI Agent server...');
  logger.plain('');
  
  // Find the runai-agent directory (renamed from nemo-agent-toolkit-custom)
  const projectRoot = process.cwd();
  let agentDir = path.join(projectRoot, 'runai-agent');
  
  // Fallback to old name for backward compatibility
  if (!fs.existsSync(agentDir)) {
    agentDir = path.join(projectRoot, 'nemo-agent-toolkit-custom');
  }
  
  if (!fs.existsSync(agentDir)) {
    logger.error('Cannot find runai-agent or nemo-agent-toolkit-custom directory');
    logger.info('Make sure you are running this command from the project root');
    process.exit(1);
  }
  
  // Check for config file (try multiple locations)
  let configFile = path.join(agentDir, 'configs', 'workflow.yaml');
  if (!fs.existsSync(configFile)) {
    configFile = path.join(agentDir, 'config', 'workflow.yaml');
  }
  if (!fs.existsSync(configFile)) {
    logger.error(`Config file not found: ${configFile}`);
    process.exit(1);
  }
  
  // Find the nat command (prefer venv version)
  let natCmd = path.join(agentDir, '.venv', 'bin', 'nat');
  if (!fs.existsSync(natCmd)) {
    // Fallback to system nat
    natCmd = 'nat';
  }
  
  // Build the command
  const args = [
    'serve',
    '--config_file', configFile,
    '--host', '0.0.0.0',
    '--port', '8000',
  ];
  
  logger.info(`Command: ${natCmd} ${args.join(' ')}`);
  logger.info(`Working directory: ${agentDir}`);
  logger.plain('');
  
  if (options.background) {
    // Start in background
    const server = spawn(natCmd, args, {
      cwd: agentDir,
      detached: true,
      stdio: 'ignore',
    });
    
    server.unref();
    
    // Save PID
    const pidDir = path.dirname(PID_FILE);
    if (!fs.existsSync(pidDir)) {
      fs.mkdirSync(pidDir, { recursive: true });
    }
    fs.writeFileSync(PID_FILE, server.pid?.toString() || '', 'utf-8');
    
    logger.success('Server started in background');
    logger.info(`Process ID: ${server.pid}`);
    logger.info(`Server URL: ${config.agentUrl}`);
    logger.info('Check status with: runai-cli server status');
    logger.info('Stop with: runai-cli server stop');
  } else {
    // Start in foreground
    logger.info('Starting server in foreground (press Ctrl+C to stop)...');
    logger.plain('');
    
    const server = spawn(natCmd, args, {
      cwd: agentDir,
      stdio: 'inherit',
    });
    
    server.on('error', (error) => {
      logger.error(`Failed to start server: ${error.message}`);
      process.exit(1);
    });
    
    server.on('exit', (code) => {
      if (code !== 0 && code !== null) {
        logger.error(`Server exited with code ${code}`);
        process.exit(code);
      }
    });
    
    // Handle Ctrl+C
    process.on('SIGINT', () => {
      logger.plain('\n');
      logger.info('Stopping server...');
      server.kill('SIGTERM');
      process.exit(0);
    });
  }
}

/**
 * Stop the agent server
 */
export async function stopCommand(): Promise<void> {
  const config = loadConfig();
  
  // Check if connected to remote agent
  if (config.remoteMode || isRemoteAgent(config.agentUrl)) {
    logger.error('Cannot stop a remote agent server');
    logger.info(`You are connected to a remote agent at: ${config.agentUrl}`);
    logger.info('Contact your system administrator to manage the remote agent.');
    logger.plain('');
    logger.info('To manage a local server, run: runai-cli connect local');
    process.exit(1);
  }
  
  if (!fs.existsSync(PID_FILE)) {
    logger.warning('No PID file found. Server might not be running in background.');
    logger.info('If the server is running in foreground, press Ctrl+C in that terminal.');
    return;
  }
  
  try {
    const pid = parseInt(fs.readFileSync(PID_FILE, 'utf-8'), 10);
    
    logger.info(`Stopping server (PID: ${pid})...`);
    
    // Try to kill the process
    try {
      process.kill(pid, 'SIGTERM');
      
      // Wait a bit and check if it's still running
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      try {
        process.kill(pid, 0); // Check if process exists
        logger.warning('Server did not stop gracefully, forcing...');
        process.kill(pid, 'SIGKILL');
      } catch {
        // Process is gone, good
      }
      
      logger.success('Server stopped');
    } catch (error: any) {
      if (error.code === 'ESRCH') {
        logger.warning('Server process not found (might have already stopped)');
      } else {
        throw error;
      }
    }
    
    // Remove PID file
    fs.unlinkSync(PID_FILE);
  } catch (error) {
    if (error instanceof Error) {
      logger.error(`Failed to stop server: ${error.message}`);
    }
    process.exit(1);
  }
}

/**
 * Show server logs
 */
export function logsCommand(): void {
  logger.info('Log viewing not yet implemented');
  logger.info('For now, check the terminal where you started the server');
  logger.info('Or run the server in foreground: runai-cli server start --no-background');
}

