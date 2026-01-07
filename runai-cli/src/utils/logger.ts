/**
 * Pretty logging utilities with colors and formatting
 */

import chalk from 'chalk';
import ora, { Ora } from 'ora';

export class Logger {
  private spinner: Ora | null = null;
  
  info(message: string): void {
    console.log(chalk.blue('ℹ'), message);
  }
  
  success(message: string): void {
    console.log(chalk.green('✓'), message);
  }
  
  warning(message: string): void {
    console.log(chalk.yellow('⚠'), message);
  }
  
  error(message: string): void {
    console.error(chalk.red('✗'), message);
  }
  
  debug(message: string): void {
    console.log(chalk.gray('→'), chalk.gray(message));
  }
  
  plain(message: string): void {
    console.log(message);
  }
  
  startSpinner(message: string): void {
    this.spinner = ora({
      text: message,
      color: 'cyan',
    }).start();
  }
  
  updateSpinner(message: string): void {
    if (this.spinner) {
      this.spinner.text = message;
    }
  }
  
  stopSpinner(success: boolean = true, message?: string): void {
    if (this.spinner) {
      if (success) {
        this.spinner.succeed(message);
      } else {
        this.spinner.fail(message);
      }
      this.spinner = null;
    }
  }
  
  clearSpinner(): void {
    if (this.spinner) {
      this.spinner.stop();
      this.spinner = null;
    }
  }
  
  header(text: string): void {
    console.log('\n' + chalk.bold.cyan(text));
    console.log(chalk.cyan('─'.repeat(text.length)) + '\n');
  }
  
  section(title: string): void {
    console.log('\n' + chalk.bold(title));
  }
  
  json(data: unknown): void {
    console.log(JSON.stringify(data, null, 2));
  }
  
  code(code: string, language?: string): void {
    const lines = code.split('\n');
    console.log(chalk.gray('```' + (language || '')));
    lines.forEach(line => console.log(line));
    console.log(chalk.gray('```'));
  }
  
  table(data: Record<string, string | number | undefined>): void {
    const maxKeyLength = Math.max(...Object.keys(data).map(k => k.length));
    
    Object.entries(data).forEach(([key, value]) => {
      const paddedKey = key.padEnd(maxKeyLength);
      console.log(`  ${chalk.cyan(paddedKey)}: ${value ?? 'N/A'}`);
    });
  }
}

export const logger = new Logger();


