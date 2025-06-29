export declare enum LogLevel {
    ERROR = 0,
    WARN = 1,
    INFO = 2,
    DEBUG = 3
}
export declare class Logger {
    private context;
    private logLevel;
    constructor(context: string);
    private getLogLevel;
    private log;
    error(message: string, metadata?: any): void;
    warn(message: string, metadata?: any): void;
    info(message: string, metadata?: any): void;
    debug(message: string, metadata?: any): void;
}
