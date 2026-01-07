/**
 * RunAI Agent API Client
 */
import axios, { AxiosInstance, AxiosError } from 'axios';

export interface AgentResponse {
  output: string;
  status: 'success' | 'error';
  error?: string;
  metadata?: any;
}

export interface HealthCheckResponse {
  running: boolean;
  url: string;
}

export class RunAIAgentClient {
  private client: AxiosInstance;
  private baseUrl: string;

  constructor(baseUrl: string, timeout: number = 60000) {
    this.baseUrl = baseUrl;
    this.client = axios.create({
      baseURL: baseUrl,
      timeout,
      headers: {
        'Content-Type': 'application/json',
      },
    });
  }

  /**
   * Send a query to the agent
   */
  async query(input: string, stream: boolean = false): Promise<AgentResponse> {
    try {
      const request: any = {
        input_message: input,
      };
      
      // Only include stream field if streaming is enabled
      if (stream) {
        request.stream = true;
      }

      const response = await this.client.post('/generate', request);
      
      // Handle different response formats from NAT
      let output = '';
      if (response.data.value) {
        output = response.data.value;
      } else if (response.data.output) {
        output = response.data.output;
      } else if (response.data.response) {
        output = response.data.response;
      } else if (typeof response.data === 'string') {
        output = response.data;
      } else if (typeof response.data === 'object') {
        // If it's an object, stringify it nicely
        output = JSON.stringify(response.data, null, 2);
      } else {
        output = String(response.data);
      }
      
      return {
        output,
        status: 'success',
        metadata: response.data.metadata,
      };
    } catch (error) {
      if (axios.isAxiosError(error)) {
        return this.handleAxiosError(error);
      }
      throw error;
    }
  }

  /**
   * Stream a query response (yields chunks)
   */
  async *queryStream(input: string): AsyncGenerator<string, void, unknown> {
    try {
      const request = {
        input_message: input,
      };

      // Use the streaming endpoint for real progressive streaming
      const response = await this.client.post('/generate/stream', request, {
        responseType: 'stream',
        headers: {
          'Accept': 'text/event-stream',
        },
      });

      // Handle streaming response
      for await (const chunk of response.data) {
        const text = chunk.toString();
        
        // Try to parse as JSON first (NAT returns JSON chunks)
        try {
          const parsed = JSON.parse(text);
          // Check for different response field names (same as non-streaming)
          if (parsed.value) {
            yield parsed.value;
          } else if (parsed.output) {
            yield parsed.output;
          } else if (parsed.response) {
            yield parsed.response;
          } else if (typeof parsed === 'string') {
            yield parsed;
          }
        } catch {
          // If not JSON, check for SSE format
          if (text.startsWith('data: ')) {
            const data = text.slice(6).trim();
            if (data === '[DONE]') break;
            yield data;
          } else if (text.trim()) {
            // Yield raw text if not empty
            yield text;
          }
        }
      }
    } catch (error) {
      if (axios.isAxiosError(error)) {
        const errorResponse = this.handleAxiosError(error);
        throw new Error(errorResponse.error || 'Stream failed');
      }
      throw error;
    }
  }

  /**
   * Check if the agent server is healthy
   */
  async healthCheck(): Promise<HealthCheckResponse> {
    try {
      // Try to reach the /docs endpoint (always available in FastAPI)
      await this.client.get('/docs', {
        timeout: 5000,
        validateStatus: (status) => status < 500,
      });

      return {
        running: true,
        url: this.baseUrl,
      };
    } catch (error) {
      return {
        running: false,
        url: this.baseUrl,
      };
    }
  }

  /**
   * Get agent version info
   */
  async getVersion(): Promise<any> {
    try {
      const response = await this.client.get('/version');
      return response.data;
    } catch (error) {
      // Version endpoint might not exist, return empty
      return {};
    }
  }

  /**
   * Handle Axios errors and convert to AgentResponse
   */
  private handleAxiosError(error: AxiosError): AgentResponse {
    if (error.code === 'ECONNREFUSED') {
      return {
        output: '',
        status: 'error',
        error: `Cannot connect to agent server at ${this.baseUrl}. Is the server running?\nStart it with: runai-cli server start`,
      };
    }

    if (error.code === 'ETIMEDOUT' || error.code === 'ECONNABORTED') {
      return {
        output: '',
        status: 'error',
        error: 'Request timed out. The agent might be processing a complex query.',
      };
    }

    if (error.response) {
      const statusCode = error.response.status;
      const errorData = error.response.data as any;
      
      let errorMessage = errorData?.detail || errorData?.error || error.message;
      
      if (statusCode === 404) {
        errorMessage = 'Endpoint not found. Make sure the agent server is running the correct version.';
      } else if (statusCode === 500) {
        errorMessage = `Server error: ${errorMessage}`;
      }

      return {
        output: '',
        status: 'error',
        error: errorMessage,
      };
    }

    return {
      output: '',
      status: 'error',
      error: error.message || 'Unknown error occurred',
    };
  }
}

