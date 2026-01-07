/**
 * Natural language job submission command
 * 
 * This provides a GenAI-style interface where users can simply describe
 * what they want and the agent handles everything automatically.
 */

import { RunAIAgentClient } from '../api/client.js';
import { logger } from '../utils/logger.js';
import { loadConfig } from '../utils/config.js';
import { validateQuery, sanitizeInput } from '../utils/validation.js';

/**
 * Submit a job using natural language description
 * 
 * Examples:
 *   runai-cli submit "Create a training job with 2 GPUs using PyTorch"
 *   runai-cli submit "Launch a Jupyter workspace with 4 GPUs in project-01" --execute
 *   runai-cli submit "Start distributed training with 8 workers"
 */
export async function submitCommand(prompt: string, options: { 
  stream?: boolean;
  confirm?: boolean;
  project?: string;
  execute?: boolean;
}): Promise<void> {
  try {
    // Validate input
    validateQuery(prompt);
    const sanitizedPrompt = sanitizeInput(prompt);
    
    // Load config and create client
    const config = loadConfig();
    const client = new RunAIAgentClient(config.agentUrl, config.timeout);
    
    // Show what we're doing
    logger.info('🚀 Processing your request...');
    logger.plain('');
    logger.plain(`Request: "${sanitizedPrompt}"`);
    logger.plain('');
    
    // Check server health
    logger.startSpinner('Connecting to agent...');
    const health = await client.healthCheck();
    
    if (!health.running) {
      logger.stopSpinner(false);
      logger.error(`Agent server is not running at ${config.agentUrl}`);
      logger.info('Start the server with: runai-cli server start');
      process.exit(1);
    }
    
    // Enhance the prompt with context for better job submission
    let enhancedPrompt = sanitizedPrompt;
    
    // Add project context if provided
    if (options.project) {
      enhancedPrompt = `${sanitizedPrompt} in project ${options.project}`;
    }
    
    // Add confirmation preference
    if (options.confirm === false) {
      enhancedPrompt = `${enhancedPrompt}. Skip confirmation and submit directly.`;
    }
    
    logger.updateSpinner('Agent is processing your request...');
    
    // Handle streaming vs non-streaming response
    const useStream = options.stream || config.stream;
    
    let responseText = '';
    
    if (useStream) {
      logger.clearSpinner();
      logger.header('Response');
      logger.plain('');
      
      for await (const chunk of client.queryStream(enhancedPrompt)) {
        process.stdout.write(chunk);
        responseText += chunk;
      }
      
      logger.plain('\n');
    } else {
      const response = await client.query(enhancedPrompt, false);
      logger.stopSpinner();
      
      if (response.status === 'error') {
        logger.error('❌ Submission Failed');
        logger.plain('');
        logger.plain(response.error || 'Unknown error');
        process.exit(1);
      }
      
      responseText = response.output;
      
      logger.header('Response');
      logger.plain('');
      logger.plain(response.output);
      logger.plain('');
      
      // Show success indicators
      if (response.output.includes('✓') || 
          response.output.includes('submitted') || 
          response.output.includes('created')) {
        logger.success('✅ Request completed successfully!');
      }
    }
    
    // Auto-execute if flag is set
    if (options.execute) {
      await executeGeneratedScript(responseText);
    }
    
    logger.plain('');
    if (!options.execute) {
      logger.info('💡 Tip: Use --execute to automatically run the generated script');
    }
    
  } catch (error) {
    logger.stopSpinner(false);
    
    if (error instanceof Error) {
      logger.error('❌ Error: ' + error.message);
    } else {
      logger.error('❌ Unknown error occurred');
    }
    
    logger.plain('');
    logger.info('Need help? Try: runai-cli --help');
    
    process.exit(1);
  }
}

/**
 * Extract and execute the generated Python script
 */
async function executeGeneratedScript(responseText: string): Promise<void> {
  const { spawn } = await import('child_process');
  
  // Extract the script path from the response
  const pathMatch = responseText.match(/\/tmp\/runai\/output\/[^\s]+\.py/);
  
  if (!pathMatch) {
    logger.warning('⚠️  Could not find generated script path in response');
    logger.info('The agent may not have generated a script file');
    return;
  }
  
  const scriptPath = pathMatch[0];
  
  logger.plain('');
  logger.info(`🔄 Executing generated script: ${scriptPath}`);
  logger.plain('');
  
  return new Promise((resolve, reject) => {
    const pythonProcess = spawn('python3', [scriptPath], {
      stdio: 'inherit',
    });
    
    pythonProcess.on('error', (error) => {
      logger.error(`Failed to execute script: ${error.message}`);
      logger.info('Make sure Python 3 and required dependencies (runapy) are installed');
      reject(error);
    });
    
    pythonProcess.on('exit', (code) => {
      logger.plain('');
      if (code === 0) {
        logger.success('✅ Job submitted successfully!');
        resolve();
      } else {
        logger.error(`❌ Script exited with code ${code}`);
        logger.info('Check the output above for details');
        reject(new Error(`Script failed with exit code ${code}`));
      }
    });
  });
}

/**
 * Interactive submit command - asks clarifying questions if needed
 */
export async function submitInteractiveCommand(): Promise<void> {
  const { createInterface } = await import('readline');
  
  const rl = createInterface({
    input: process.stdin,
    output: process.stdout,
  });
  
  logger.header('🎯 Interactive Job Submission');
  logger.plain('');
  logger.plain('Describe what you want to create. Be as detailed or simple as you like.');
  logger.plain('');
  logger.plain('Examples:');
  logger.plain('  • "Training job with 2 GPUs"');
  logger.plain('  • "Distributed PyTorch training with 4 workers"');
  logger.plain('  • "Jupyter workspace in project-ml with 8GB memory"');
  logger.plain('');
  
  rl.question('What would you like to create? ', async (answer: string) => {
    rl.close();
    
    if (!answer.trim()) {
      logger.warning('No input provided. Exiting.');
      return;
    }
    
    await submitCommand(answer.trim(), {});
  });
}

