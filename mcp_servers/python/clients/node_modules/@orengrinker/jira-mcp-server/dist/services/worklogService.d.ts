import { JiraApiClient } from '../jiraApiClient.js';
import { ToolResult, WorklogRequest } from '../types/index.js';
export declare class WorklogService {
    private apiClient;
    private logger;
    constructor(apiClient: JiraApiClient);
    addWorklog(params: WorklogRequest): Promise<ToolResult>;
    getWorklogs(issueKey: string): Promise<ToolResult>;
    private formatDuration;
}
