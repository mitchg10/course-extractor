// Define log levels to match Python's logging levels
const LOG_LEVELS = {
  DEBUG: 10, // Matching Python's logging.DEBUG
  INFO: 20, // Matching Python's logging.INFO
  WARN: 30, // Matching Python's logging.WARNING
  ERROR: 40, // Matching Python's logging.ERROR
};

// Get current environment
const IS_DEVELOPMENT = import.meta.env.NODE_ENV === "development";

// Configuration object for logger
import { endpoints } from "../config/api.js";
const config = {
  minLevel: IS_DEVELOPMENT ? LOG_LEVELS.DEBUG : LOG_LEVELS.INFO,
  enabled: true,
  prefix: "📋 [CourseExtractor]",
  backendLogEndpoint: endpoints.frontendLogs,
  logToBackend: true,
};

// Immediate initialization log
console.log("Logger initialized with config:", config);

// Function to send logs to backend
const sendToBackend = async (level, message, details = {}) => {
  if (!config.logToBackend) return;

  try {
    const logData = {
      name: "frontend",
      level,
      message,
      details,
      environment: IS_DEVELOPMENT ? "development" : "production",
    };

    console.log("Attempting to send log to backend:", logData);
    console.log("Backend endpoint:", config.backendLogEndpoint);
    
    const response = await fetch(config.backendLogEndpoint, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(logData),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const result = await response.json();
    console.log("Backend logging response:", result);
  } catch (error) {
    console.error("Failed to send log to backend:", error);
  }
};

// Core logging function
const log = async (level, style, message, ...args) => {
  if (!config.enabled || level < config.minLevel) {
    return;
  }

  // Console logging
  const timestamp = new Date().toISOString();
  const formattedMessage = `${config.prefix} ${timestamp} - ${message}`;

  if (typeof message === "object") {
    console.log(formattedMessage, style);
    console.log(message);
  } else {
    console.log(`%c${formattedMessage}`, style, ...args);
  }

  // Backend logging
  await sendToBackend(level, message, { args });
};

// Logger object with different log levels
export const logger = {
  debug: async (message, ...args) => {
    await log(LOG_LEVELS.DEBUG, "color: #6b7280;", message, ...args);
  },

  info: async (message, ...args) => {
    await log(LOG_LEVELS.INFO, "color: #2563eb;", message, ...args);
  },

  warn: async (message, ...args) => {
    await log(LOG_LEVELS.WARN, "color: #d97706;", message, ...args);
  },

  error: async (message, ...args) => {
    await log(LOG_LEVELS.ERROR, "color: #dc2626;", message, ...args);
  },

  // Special method for logging API responses
  apiResponse: async (endpoint, response) => {
    if (!config.enabled || LOG_LEVELS.DEBUG < config.minLevel) return;

    const logMessage = `API Response: ${endpoint}`;
    console.group(`${config.prefix} ${logMessage}`);
    console.log("Status:", response.status);
    console.log("Headers:", response.headers);
    console.log("Data:", response);
    console.groupEnd();

    await sendToBackend(LOG_LEVELS.DEBUG, logMessage, {
      status: response.status,
      headers: Object.fromEntries(response.headers.entries()),
      data: response,
    });
  },

  // Method for logging file operations
  fileOperation: async (operation, files) => {
    if (!config.enabled || LOG_LEVELS.DEBUG < config.minLevel) return;

    const fileDetails = files.map((file) => ({
      name: file.name,
      size: `${(file.size / 1024).toFixed(2)} KB`,
      type: file.type,
    }));

    const logMessage = `File Operation: ${operation}`;
    console.group(`${config.prefix} ${logMessage}`);
    fileDetails.forEach((file) => console.log("File:", file));
    console.groupEnd();

    await sendToBackend(LOG_LEVELS.DEBUG, logMessage, { files: fileDetails });
  },

  // Configuration methods
  setLevel: (level) => {
    if (LOG_LEVELS[level] !== undefined) {
      config.minLevel = LOG_LEVELS[level];
      console.log(`Log level set to: ${level}`);
    }
  },

  enable: () => {
    config.enabled = true;
    console.log("Logger enabled");
  },

  disable: () => {
    config.enabled = false;
    console.log("Logger disabled");
  },

  enableBackendLogging: () => {
    config.logToBackend = true;
    console.log("Backend logging enabled");
  },

  disableBackendLogging: () => {
    config.logToBackend = false;
    console.log("Backend logging disabled");
  },

  setBackendEndpoint: (endpoint) => {
    config.backendLogEndpoint = endpoint;
    console.log(`Backend endpoint set to: ${endpoint}`);
  },

  // Development-only logging
  dev: async (message, ...args) => {
    if (IS_DEVELOPMENT) {
      await log(
        LOG_LEVELS.DEBUG,
        "color: #8b5cf6;",
        `[DEV] ${message}`,
        ...args
      );
    }
  },
};

// Test log to verify initialization
logger.info("Logger system initialized");
