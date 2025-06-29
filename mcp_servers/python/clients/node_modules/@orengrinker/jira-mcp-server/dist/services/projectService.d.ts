import { JiraApiClient } from '../jiraApiClient.js';
import { ToolResult } from '../types/index.js';
export declare class ProjectService {
    private apiClient;
    private logger;
    constructor(apiClient: JiraApiClient);
    getProjects(): Promise<ToolResult>;
    getProjectDetails(projectKey: string): Promise<ToolResult>;
}
