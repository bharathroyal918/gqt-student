export type ProgrammingLanguage = "python" | "java" | "c" | "cpp" | "javascript";

export type SubmissionStatus =
  | "PENDING"
  | "RUNNING"
  | "ACCEPTED"
  | "WRONG_ANSWER"
  | "TIME_LIMIT_EXCEEDED"
  | "COMPILATION_ERROR"
  | "RUNTIME_ERROR";

export interface TestCaseResult {
  testCaseId: string;
  isVisible: boolean;
  status: "PASSED" | "FAILED" | "TLE" | "MLE" | "ERROR";
  executionTimeSeconds?: number;
  stdout?: string;
  stderr?: string;
}

export interface SubmissionResponse {
  submissionId: string;
  status: SubmissionStatus;
  passedTestCasesCount: number;
  totalTestCasesCount: number;
  scoreAwarded: number;
  scoringPolicy: "FULL" | "HALF" | "ZERO";
  testCaseResults: TestCaseResult[];
}
