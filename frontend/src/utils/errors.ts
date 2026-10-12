/**
 * Safely extracts a meaningful error message from an unknown API or network error.
 */
export function getApiErrorMessage(
  error: unknown,
  fallback = "An unexpected error occurred."
): string {
  if (typeof error === "object" && error !== null) {
    const candidate = error as {
      message?: unknown;
      response?: {
        data?: {
          message?: unknown;
          error?: {
            message?: unknown;
          };
        };
      };
    };

    const responseData = candidate.response?.data;
    if (typeof responseData?.message === "string" && responseData.message.trim()) {
      return responseData.message;
    }
    if (typeof responseData?.error?.message === "string" && responseData.error.message.trim()) {
      return responseData.error.message;
    }
    if (typeof candidate.message === "string" && candidate.message.trim()) {
      return candidate.message;
    }
  }

  return fallback;
}
