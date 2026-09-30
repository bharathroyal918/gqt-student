import { z } from "zod";

export const emailLoginSchema = z.object({
  email: z.string().email("Please provide a valid institutional email address"),
  password: z.string().min(8, "Password must be at least 8 characters long"),
});

export const requestOtpSchema = z.object({
  mobileNumber: z
    .string()
    .regex(/^\+?[1-9]\d{9,14}$/, "Enter a valid mobile number with country code (e.g. +919876543210)"),
});

export const verifyOtpSchema = z.object({
  mobileNumber: z
    .string()
    .regex(/^\+?[1-9]\d{9,14}$/, "Enter a valid mobile number with country code"),
  otp: z.string().length(6, "OTP must be exactly 6 digits"),
});

export type EmailLoginFormValues = z.infer<typeof emailLoginSchema>;
export type RequestOtpFormValues = z.infer<typeof requestOtpSchema>;
export type VerifyOtpFormValues = z.infer<typeof verifyOtpSchema>;
