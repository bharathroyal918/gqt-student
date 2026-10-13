import { describe, it, expect } from "vitest";
import { getApiErrorMessage } from "../utils/errors";

describe("Frontend Error Message Handling & Toast Deduplication", () => {
  it("extracts Axios Network Error correctly", () => {
    const networkError = new Error("Network Error");
    const message = getApiErrorMessage(networkError, "Default fallback");
    expect(message).toBe("Network Error");
  });

  it("extracts DRF detail message when available", () => {
    const drfError = {
      response: {
        data: {
          detail: "Invalid credentials provided.",
        },
      },
    };
    const message = getApiErrorMessage(drfError);
    expect(message).toBe("Invalid credentials provided.");
  });

  it("extracts nested error.message structure", () => {
    const nestedError = {
      response: {
        data: {
          error: {
            message: "Student account is suspended.",
          },
        },
      },
    };
    const message = getApiErrorMessage(nestedError);
    expect(message).toBe("Student account is suspended.");
  });

  it("extracts top-level response.data.message", () => {
    const envelopeError = {
      response: {
        data: {
          message: "Account pending activation.",
        },
      },
    };
    const message = getApiErrorMessage(envelopeError);
    expect(message).toBe("Account pending activation.");
  });

  it("returns fallback message for empty or unknown error structures", () => {
    expect(getApiErrorMessage(null, "Fallback message")).toBe("Fallback message");
    expect(getApiErrorMessage({}, "Fallback message")).toBe("Fallback message");
    expect(getApiErrorMessage("string error", "Fallback message")).toBe("Fallback message");
  });

  it("deduplicates identical toast dispatches within throttling window", () => {
    // Test the exact deduplication algorithm used in ToastContext
    const recentToasts = new Map<string, number>();
    const toasts: Array<{ type: string; title: string; message: string }> = [];

    const dispatchToast = (type: string, title: string, message: string, now: number) => {
      const key = `${type}::${title}::${message}`;
      const lastDispatched = recentToasts.get(key);
      if (lastDispatched !== undefined && now - lastDispatched < 1500) {
        return false; // Throttled duplicate
      }
      recentToasts.set(key, now);

      const isDuplicateInList = toasts.some(
        (t) => t.type === type && t.title === title && t.message === message
      );
      if (isDuplicateInList) {
        return false;
      }
      toasts.push({ type, title, message });
      return true;
    };

    // First failed attempt
    const firstCall = dispatchToast("error", "Authentication Failed", "Network Error", 1000);
    expect(firstCall).toBe(true);
    expect(toasts.length).toBe(1);

    // Rapid second click on submit button 200ms later (same failed request / rapid user retry)
    const duplicateCall = dispatchToast("error", "Authentication Failed", "Network Error", 1200);
    expect(duplicateCall).toBe(false);
    expect(toasts.length).toBe(1); // Still 1 toast, duplicate suppressed

    // Third click 500ms later (still within 1500ms window)
    const thirdCall = dispatchToast("error", "Authentication Failed", "Network Error", 1500);
    expect(thirdCall).toBe(false);
    expect(toasts.length).toBe(1);

    // Different error message is NOT blocked
    const differentError = dispatchToast("error", "Request Failed", "Timeout", 1600);
    expect(differentError).toBe(true);
    expect(toasts.length).toBe(2);

    // Same error after throttle window has elapsed (e.g. 3000ms later)
    // Clear list to simulate previous toast auto-dismissed
    toasts.splice(0, 1);
    const subsequentAttempt = dispatchToast("error", "Authentication Failed", "Network Error", 3500);
    expect(subsequentAttempt).toBe(true);
  });
});
