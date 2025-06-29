import { JiraApiClient } from '../jiraApiClient.js';
import { ToolResult } from '../types/index.js';
export declare class ServerService {
    private apiClient;
    private logger;
    constructor(apiClient: JiraApiClient);
    getServerInfo(): Promise<ToolResult>;
}
