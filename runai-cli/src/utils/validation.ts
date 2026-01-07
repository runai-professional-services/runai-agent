/**
 * Input validation utilities
 */

import type { JobSpec, EnvironmentSpec } from '../types/index.js';

export class ValidationError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'ValidationError';
  }
}

/**
 * Validate job specification
 */
export function validateJobSpec(spec: Partial<JobSpec>): void {
  const errors: string[] = [];
  
  if (!spec.name || spec.name.trim().length === 0) {
    errors.push('Job name is required');
  }
  
  if (!spec.project || spec.project.trim().length === 0) {
    errors.push('Project name is required');
  }
  
  if (!spec.image || spec.image.trim().length === 0) {
    errors.push('Container image is required');
  }
  
  if (spec.gpu !== undefined && (spec.gpu < 0 || !Number.isInteger(spec.gpu))) {
    errors.push('GPU count must be a non-negative integer');
  }
  
  if (errors.length > 0) {
    throw new ValidationError(errors.join('\n'));
  }
}

/**
 * Validate environment specification
 */
export function validateEnvironmentSpec(spec: Partial<EnvironmentSpec>): void {
  const errors: string[] = [];
  
  if (!spec.name || spec.name.trim().length === 0) {
    errors.push('Environment name is required');
  }
  
  if (!spec.scope || !['cluster', 'project', 'tenant'].includes(spec.scope)) {
    errors.push('Scope must be one of: cluster, project, tenant');
  }
  
  if (!spec.image || spec.image.trim().length === 0) {
    errors.push('Container image is required');
  }
  
  if (errors.length > 0) {
    throw new ValidationError(errors.join('\n'));
  }
}

/**
 * Validate query string
 */
export function validateQuery(query: string): void {
  if (!query || query.trim().length === 0) {
    throw new ValidationError('Query cannot be empty');
  }
  
  if (query.length > 5000) {
    throw new ValidationError('Query is too long (max 5000 characters)');
  }
}

/**
 * Sanitize user input
 */
export function sanitizeInput(input: string): string {
  return input.trim().replace(/[\x00-\x1F\x7F]/g, '');
}


