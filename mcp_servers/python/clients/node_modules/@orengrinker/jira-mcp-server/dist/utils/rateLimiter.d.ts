export declare class RateLimiter {
    private requests;
    private maxRequests;
    private windowMs;
    constructor(maxRequests?: number, windowMs?: number);
    waitForSlot(): Promise<void>;
}
