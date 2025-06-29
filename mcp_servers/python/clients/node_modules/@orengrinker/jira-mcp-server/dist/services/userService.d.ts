import { JiraApiClient } from '../jiraApiClient.js';
import { ToolResult } from '../types/index.js';
export declare class UserService {
    private apiClient;
    private logger;
    constructor(apiClient: JiraApiClient);
    getCurrentUser(): Promise<ToolResult>;
    searchUsers(query: string): Promise<ToolResult>;
    getUserDetails(accountId: string): Promise<ToolResult>;
}
