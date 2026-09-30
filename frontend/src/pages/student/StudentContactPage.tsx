import React, { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import {
  Mail,
  Send,
  CheckCircle2,
  Phone,
  Building,
  Clock,
  ExternalLink,
  Loader2,
  MessageSquare,
  Share2,
} from "lucide-react";
import { useAuthStore } from "../../store/authStore";
import { studentApi, CompanyInfoData } from "../../api/studentApi";
import { Card } from "../../components/ui/Card";
import { Badge } from "../../components/ui/Badge";
import { Button } from "../../components/ui/Button";
import { FormField, Input, Textarea, Select } from "../../components/ui/Form";
import { useToast } from "../../context/ToastContext";

export const StudentContactPage: React.FC = () => {
  const { user, studentProfile } = useAuthStore();
  const { success, error: toastError } = useToast();

  const [formData, setFormData] = useState({
    name: studentProfile?.full_name || "",
    email: user?.email || "",
    category: "TECHNICAL_SUPPORT",
    subject: "",
    message: "",
    website: "", // Anti-spam honeypot
  });

  const [errors, setErrors] = useState<Record<string, string>>({});
  const [submittedSuccess, setSubmittedSuccess] = useState(false);

  // Fetch official institutional company info
  const { data: companyInfo } = useQuery<CompanyInfoData>({
    queryKey: ["company-info"],
    queryFn: studentApi.getCompanyInfo,
  });

  // Submit Inquiry Mutation
  const inquiryMutation = useMutation({
    mutationFn: studentApi.submitContactInquiry,
    onSuccess: () => {
      setSubmittedSuccess(true);
      success("Inquiry Submitted", "Your ticket has been assigned to academic support.");
      setFormData({
        name: studentProfile?.full_name || "",
        email: user?.email || "",
        category: "TECHNICAL_SUPPORT",
        subject: "",
        message: "",
        website: "",
      });
      setErrors({});
    },
    onError: (err: any) => {
      const errPayload = err?.response?.data?.error;
      if (errPayload?.details) {
        const fieldErrors: Record<string, string> = {};
        for (const [field, val] of Object.entries(errPayload.details)) {
          fieldErrors[field] = Array.isArray(val) ? val.join(" ") : String(val);
        }
        setErrors(fieldErrors);
      }
      toastError(
        "Submission Failed",
        errPayload?.message || "Could not submit inquiry. Please verify the form."
      );
    },
  });

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};
    if (!formData.name.trim() || formData.name.trim().length < 2) {
      newErrors.name = "Name must be at least 2 characters.";
    }
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!formData.email.trim() || !emailRegex.test(formData.email.trim())) {
      newErrors.email = "Please provide a valid email address.";
    }
    if (!formData.subject.trim() || formData.subject.trim().length < 3) {
      newErrors.subject = "Subject must be at least 3 characters.";
    }
    if (!formData.message.trim() || formData.message.trim().length < 10) {
      newErrors.message = "Message must be at least 10 characters.";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!validateForm()) return;

    inquiryMutation.mutate({
      name: formData.name,
      email: formData.email,
      category: formData.category,
      subject: formData.subject,
      message: formData.message,
      website: formData.website,
    });
  };

  const info = companyInfo || {
    company_name: "Global Quality Technologies (GQT)",
    tagline: "Empowering Future Software Engineers with Industrial Coding Mastery",
    support_email: "support@gqt.local",
    admissions_email: "admissions@gqt.local",
    phone_primary: "+91 80 4567 8900",
    phone_support: "+91 80 4567 8901",
    office_address: {
      street: "GQT Tech Park, 4th Floor, Electronic City Phase 1",
      city: "Bengaluru",
      state: "Karnataka",
      postal_code: "560100",
      country: "India",
    },
    office_hours: "Monday to Saturday: 9:00 AM – 6:30 PM IST",
    social_links: {
      linkedin: "https://linkedin.com/company/gqt-technologies",
      github: "https://github.com/gqt-technologies",
      youtube: "https://youtube.com/@gqt-learning",
      twitter: "https://twitter.com/gqt_tech",
    },
  };

  return (
    <div className="space-y-8 max-w-6xl pb-12">
      {/* Top Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
          <Mail className="h-6 w-6 text-brand-400" />
          Contact & Academic Support
        </h1>
        <p className="text-sm text-slate-400 mt-1">
          Have questions regarding curriculum tracks, sandbox challenges, or account credentials? Connect with our team.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-8 lg:grid-cols-12">
        {/* Left Column: Institutional Information & Hotlines (5 cols) */}
        <div className="space-y-6 lg:col-span-5">
          {/* Company Card */}
          <Card className="p-6 bg-gradient-to-br from-surface-900 to-surface-950 border-surface-800 space-y-4">
            <div>
              <div className="flex items-center gap-2">
                <Badge variant="indigo" size="sm">
                  Official Institutional Support
                </Badge>
              </div>
              <h2 className="text-lg font-bold text-white mt-2">{info.company_name}</h2>
              <p className="text-xs text-slate-400 mt-1 leading-relaxed">{info.tagline}</p>
            </div>

            <div className="pt-2 border-t border-surface-800/80 space-y-3.5 text-xs">
              {/* Phone */}
              <div className="flex items-start gap-3 text-slate-300">
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-brand-500/10 text-brand-400 border border-brand-500/20">
                  <Phone className="h-4 w-4" />
                </div>
                <div>
                  <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">
                    Phone Numbers
                  </span>
                  <p className="font-semibold text-white mt-0.5">{info.phone_primary}</p>
                  <p className="text-slate-400 text-[11px]">{info.phone_support} (Student Hotline)</p>
                </div>
              </div>

              {/* Email */}
              <div className="flex items-start gap-3 text-slate-300">
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                  <Mail className="h-4 w-4" />
                </div>
                <div>
                  <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">
                    Email Desks
                  </span>
                  <a
                    href={`mailto:${info.support_email}`}
                    className="font-semibold text-emerald-300 hover:underline mt-0.5 block"
                  >
                    {info.support_email}
                  </a>
                  <span className="text-slate-400 text-[11px]">{info.admissions_email}</span>
                </div>
              </div>

              {/* Address */}
              <div className="flex items-start gap-3 text-slate-300">
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-amber-500/10 text-amber-400 border border-amber-500/20">
                  <Building className="h-4 w-4" />
                </div>
                <div>
                  <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">
                    Headquarters
                  </span>
                  <p className="text-slate-300 mt-0.5 leading-relaxed">
                    {info.office_address.street}, {info.office_address.city},{" "}
                    {info.office_address.state} {info.office_address.postal_code},{" "}
                    {info.office_address.country}
                  </p>
                </div>
              </div>

              {/* Hours */}
              <div className="flex items-start gap-3 text-slate-300">
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                  <Clock className="h-4 w-4" />
                </div>
                <div>
                  <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">
                    Office Hours
                  </span>
                  <p className="text-slate-300 mt-0.5">{info.office_hours}</p>
                </div>
              </div>
            </div>
          </Card>

          {/* Social Links Card */}
          <Card className="p-5 border-surface-800">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-1.5 mb-3">
              <Share2 className="h-3.5 w-3.5 text-brand-400" />
              Official Social Channels
            </h3>

            <div className="grid grid-cols-2 gap-2.5 text-xs">
              <a
                href={info.social_links.linkedin}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center justify-between p-2.5 rounded-xl bg-surface-900 border border-surface-800/80 hover:bg-surface-800/80 hover:border-surface-700 transition-colors text-slate-300"
              >
                <span>LinkedIn</span>
                <ExternalLink className="h-3.5 w-3.5 text-slate-500" />
              </a>
              <a
                href={info.social_links.github}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center justify-between p-2.5 rounded-xl bg-surface-900 border border-surface-800/80 hover:bg-surface-800/80 hover:border-surface-700 transition-colors text-slate-300"
              >
                <span>GitHub</span>
                <ExternalLink className="h-3.5 w-3.5 text-slate-500" />
              </a>
              <a
                href={info.social_links.youtube}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center justify-between p-2.5 rounded-xl bg-surface-900 border border-surface-800/80 hover:bg-surface-800/80 hover:border-surface-700 transition-colors text-slate-300"
              >
                <span>YouTube</span>
                <ExternalLink className="h-3.5 w-3.5 text-slate-500" />
              </a>
              <a
                href={info.social_links.twitter}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center justify-between p-2.5 rounded-xl bg-surface-900 border border-surface-800/80 hover:bg-surface-800/80 hover:border-surface-700 transition-colors text-slate-300"
              >
                <span>Twitter / X</span>
                <ExternalLink className="h-3.5 w-3.5 text-slate-500" />
              </a>
            </div>
          </Card>
        </div>

        {/* Right Column: Contact Inquiry Form (7 cols) */}
        <div className="lg:col-span-7">
          <Card className="p-6 sm:p-8 border-surface-800">
            {submittedSuccess ? (
              <div className="text-center py-10 space-y-4">
                <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                  <CheckCircle2 className="h-8 w-8" />
                </div>
                <div>
                  <h2 className="text-xl font-bold text-white">Inquiry Successfully Logged</h2>
                  <p className="text-xs text-slate-400 max-w-md mx-auto leading-relaxed mt-2">
                    Your inquiry has been submitted to the academic administration queue. Our instructors and support team will reply to your registered email address within 24 hours.
                  </p>
                </div>
                <div className="pt-4">
                  <Button variant="secondary" onClick={() => setSubmittedSuccess(false)}>
                    Submit Another Inquiry
                  </Button>
                </div>
              </div>
            ) : (
              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="border-b border-surface-800 pb-4">
                  <h3 className="text-lg font-bold text-white flex items-center gap-2">
                    <MessageSquare className="h-5 w-5 text-brand-400" />
                    Submit Support Inquiry
                  </h3>
                  <p className="text-xs text-slate-400 mt-0.5">
                    Fill in the details below. All tickets are assigned directly to academic support staff.
                  </p>
                </div>

                {/* Honeypot field for anti-spam (hidden from users) */}
                <input
                  type="text"
                  name="website"
                  value={formData.website}
                  onChange={(e) => setFormData({ ...formData, website: e.target.value })}
                  style={{ display: "none" }}
                  tabIndex={-1}
                  autoComplete="off"
                />

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <FormField label="Full Name" required error={errors.name}>
                    <Input
                      placeholder="Your full name"
                      value={formData.name}
                      onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                      required
                    />
                  </FormField>

                  <FormField label="Email Address" required error={errors.email}>
                    <Input
                      type="email"
                      placeholder="your.email@example.com"
                      value={formData.email}
                      onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                      required
                    />
                  </FormField>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <FormField label="Inquiry Category" required>
                    <Select
                      value={formData.category}
                      onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                    >
                      <option value="TECHNICAL_SUPPORT">Technical Support & Sandbox</option>
                      <option value="COURSE_DOUBT">Curriculum / Module Doubts</option>
                      <option value="ACCOUNT_ISSUE">Account & Login Access</option>
                      <option value="GENERAL_FEEDBACK">General Feedback & Suggestions</option>
                    </Select>
                  </FormField>

                  <FormField label="Subject" required error={errors.subject}>
                    <Input
                      placeholder="e.g. Question regarding Module #12 unlock"
                      value={formData.subject}
                      onChange={(e) => setFormData({ ...formData, subject: e.target.value })}
                      required
                    />
                  </FormField>
                </div>

                <FormField label="Detailed Message" required error={errors.message}>
                  <Textarea
                    rows={5}
                    placeholder="Provide full details, code snippet references, or question context..."
                    value={formData.message}
                    onChange={(e) => setFormData({ ...formData, message: e.target.value })}
                    required
                  />
                  <div className="flex justify-between text-[11px] text-slate-500 mt-1">
                    <span>Minimum 10 characters</span>
                    <span>{formData.message.length} / 2000</span>
                  </div>
                </FormField>

                <div className="pt-4 border-t border-surface-800 flex items-center justify-between">
                  <div className="text-[11px] text-slate-500">
                    Submissions are rate-limited to 5 inquiries per 10 minutes.
                  </div>
                  <Button
                    type="submit"
                    disabled={inquiryMutation.isPending}
                    className="flex items-center gap-1.5"
                  >
                    {inquiryMutation.isPending ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <Send className="h-4 w-4" />
                    )}
                    Submit Ticket
                  </Button>
                </div>
              </form>
            )}
          </Card>
        </div>
      </div>
    </div>
  );
};
