export var LogLevel;
(function (LogLevel) {
    LogLevel[LogLevel["ERROR"] = 0] = "ERROR";
    LogLevel[LogLevel["WARN"] = 1] = "WARN";
    LogLevel[LogLevel["INFO"] = 2] = "INFO";
    LogLevel[LogLevel["DEBUG"] = 3] = "DEBUG";
})(LogLevel || (LogLevel = {}));
export class Logger {
    context;
    logLevel;
    constructor(context) {
        this.context = context;
        this.logLevel = this.getLogLevel();
    }
    getLogLevel() {
        const level = process.env.LOG_LEVEL?.toUpperCase() || 'INFO';
        switch (level) {
            case 'ERROR': return LogLevel.ERROR;
            case 'WARN': return LogLevel.WARN;
            case 'INFO': return LogLevel.INFO;
            case 'DEBUG': return LogLevel.DEBUG;
            default: return LogLevel.INFO;
        }
    }
    log(level, message, metadata) {
        if (level <= this.logLevel) {
            const timestamp = new Date().toISOString();
            const levelName = LogLevel[level];
            const logMessage = `[${timestamp}] [${levelName}] [${this.context}] ${message}`;
            if (metadata) {
                console.error(`${logMessage}`, metadata);
            }
            else {
                console.error(logMessage);
            }
        }
    }
    error(message, metadata) {
        this.log(LogLevel.ERROR, message, metadata);
    }
    warn(message, metadata) {
        this.log(LogLevel.WARN, message, metadata);
    }
    info(message, metadata) {
        this.log(LogLevel.INFO, message, metadata);
    }
    debug(message, metadata) {
        this.log(LogLevel.DEBUG, message, metadata);
    }
}
