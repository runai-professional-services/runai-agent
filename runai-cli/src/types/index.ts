/**
 * Shared TypeScript types for RunAI CLI
 */

export interface AgentRequest {
  input: string;
  stream?: boolean;
  context?: Record<string, unknown>;
}

export interface AgentResponse {
  output: string;
  metadata?: {
    tool_calls?: string[];
    execution_time?: number;
    iterations?: number;
  };
  status: 'success' | 'error';
  error?: string;
}

export interface JobSpec {
  name: string;
  project: string;
  image: string;
  gpu?: number;
  cpuCores?: number;
  memory?: string;
  command?: string;
  args?: string[];
  environmentVariables?: Record<string, string>;
}

export interface EnvironmentSpec {
  name: string;
  scope: 'cluster' | 'project' | 'tenant';
  scopeId?: string;
  description?: string;
  image: string;
  compute?: {
    gpu?: number;
    cpuCores?: number;
    memory?: string;
  };
  environmentVariables?: Record<string, string>;
  tools?: string[];
}

export interface ServerStatus {
  running: boolean;
  url?: string;
  pid?: number;
  uptime?: number;
}

export interface CLIConfig {
  agentUrl: string;
  timeout: number;
  stream: boolean;
  debug: boolean;
  remoteMode?: boolean;  // Whether connecting to a remote agent
}

export interface JobStatus {
  name: string;
  project: string;
  status: string;
  gpu?: number;
  image?: string;
  createdAt?: string;
  startedAt?: string;
  completedAt?: string;
}


