import { JiraApiClient } from '../jiraApiClient.js';
import { ToolResult, BoardIssueParams } from '../types/index.js';
export declare class BoardService {
    private apiClient;
    private logger;
    constructor(apiClient: JiraApiClient);
    getBoards(params?: {
        type?: string;
        projectKey?: string;
    }): Promise<ToolResult>;
    getBoardDetails(boardId: string): Promise<ToolResult>;
    getBoardIssues(params: BoardIssueParams): Promise<ToolResult>;
}
