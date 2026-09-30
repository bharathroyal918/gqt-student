import { describe, it, expect } from "vitest";

describe("Student Dashboard Telemetry Calculations", () => {
  it("calculates overall completion rate correctly", () => {
    const calculateCompletion = (completed: number, total: number): number => {
      if (total === 0) return 0;
      return Math.round((completed / total) * 100);
    };

    expect(calculateCompletion(5, 10)).toBe(50);
    expect(calculateCompletion(10, 10)).toBe(100);
    expect(calculateCompletion(0, 10)).toBe(0);
    expect(calculateCompletion(1, 3)).toBe(33);
    expect(calculateCompletion(0, 0)).toBe(0);
  });

  it("determines active streak status based on last activity date", () => {
    const isStreakActive = (lastActivityDate: string | null): boolean => {
      if (!lastActivityDate) return false;
      const today = new Date().toISOString().split("T")[0];
      const yesterday = new Date(Date.now() - 86400000).toISOString().split("T")[0];
      return lastActivityDate === today || lastActivityDate === yesterday;
    };

    const todayStr = new Date().toISOString().split("T")[0];
    const oldStr = "2020-01-01";

    expect(isStreakActive(todayStr)).toBe(true);
    expect(isStreakActive(oldStr)).toBe(false);
    expect(isStreakActive(null)).toBe(false);
  });

  it("orders leaderboard ranks deterministically", () => {
    const students = [
      { name: "Alice", points: 150, solved: 10 },
      { name: "Bob", points: 200, solved: 15 },
      { name: "Charlie", points: 150, solved: 12 },
    ];

    const sorted = [...students].sort((a, b) => {
      if (b.points !== a.points) return b.points - a.points;
      return b.solved - a.solved;
    });

    expect(sorted[0].name).toBe("Bob");
    expect(sorted[1].name).toBe("Charlie"); // tie broken by solved
    expect(sorted[2].name).toBe("Alice");
  });
});
