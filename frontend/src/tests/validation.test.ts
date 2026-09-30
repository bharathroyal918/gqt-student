import { describe, it, expect } from "vitest";

describe("Frontend Form & Schema Validations", () => {
  it("validates email RFC formats correctly", () => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    expect(emailRegex.test("student@gqt.local")).toBe(true);
    expect(emailRegex.test("admin.user@gqt.edu.in")).toBe(true);
    expect(emailRegex.test("invalid-email")).toBe(false);
    expect(emailRegex.test("@missingusername.com")).toBe(false);
    expect(emailRegex.test("missingdomain@")).toBe(false);
  });

  it("validates 6-digit numeric OTP formats", () => {
    const otpRegex = /^\d{6}$/;
    expect(otpRegex.test("123456")).toBe(true);
    expect(otpRegex.test("000000")).toBe(true);
    expect(otpRegex.test("12345")).toBe(false);
    expect(otpRegex.test("1234567")).toBe(false);
    expect(otpRegex.test("12a456")).toBe(false);
  });

  it("validates E.164 mobile numbers", () => {
    const phoneRegex = /^\+?[1-9]\d{9,14}$/;
    expect(phoneRegex.test("+919876543210")).toBe(true);
    expect(phoneRegex.test("9876543210")).toBe(true);
    expect(phoneRegex.test("+14155552671")).toBe(true);
    expect(phoneRegex.test("123")).toBe(false);
  });

  it("validates GitHub repository URLs", () => {
    const githubRegex = /^https?:\/\/(www\.)?github\.com\/[A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+\/?$/;
    expect(githubRegex.test("https://github.com/bharath/gqt-project")).toBe(true);
    expect(githubRegex.test("http://github.com/org-name/repo.name/")).toBe(true);
    expect(githubRegex.test("https://notgithub.com/user/repo")).toBe(false);
    expect(githubRegex.test("invalid-url")).toBe(false);
  });

  it("validates contact inquiry message length bounds (10 to 2000 chars)", () => {
    const validateMessage = (msg: string) => msg.trim().length >= 10 && msg.trim().length <= 2000;
    expect(validateMessage("Too short")).toBe(false);
    expect(validateMessage("I am requesting assistance regarding assignment 3.")).toBe(true);
    expect(validateMessage("a".repeat(2001))).toBe(false);
  });
});
