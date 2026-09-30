import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  User,
  Building,
  GraduationCap,
  Mail,
  Phone,
  ShieldCheck,
  Award,
  Lock,
  CheckCircle2,
  Download,
  Flame,
  Star,
  Search,
  Loader2,
  FileCheck,
  AlertTriangle,
} from "lucide-react";
import { useAuthStore } from "../../store/authStore";
import {
  studentApi,
  BadgeItem,
  StudentCertificateItem,
  CertificateVerificationResult,
} from "../../api/studentApi";
import { Card } from "../../components/ui/Card";
import { Badge } from "../../components/ui/Badge";
import { Button } from "../../components/ui/Button";
import { Input } from "../../components/ui/Form";

export const StudentProfilePage: React.FC = () => {
  const { user, studentProfile } = useAuthStore();
  const [activeTab, setActiveTab] = useState<"achievements" | "certificates" | "verify">("achievements");

  // Verification lookup state
  const [lookupIdentifier, setLookupIdentifier] = useState("");
  const [lookupResult, setLookupResult] = useState<CertificateVerificationResult | null>(null);
  const [lookupLoading, setLookupLoading] = useState(false);
  const [lookupError, setLookupError] = useState<string | null>(null);

  const { data: badges = [], isLoading: badgesLoading } = useQuery<BadgeItem[]>({
    queryKey: ["student-badges"],
    queryFn: studentApi.getAchievements,
  });

  const { data: certificates = [], isLoading: certsLoading } = useQuery<StudentCertificateItem[]>({
    queryKey: ["student-certificates"],
    queryFn: studentApi.getCertificates,
  });

  const pointsFormatted = (studentProfile?.total_points || 0).toLocaleString();
  const displayName = studentProfile?.full_name || user?.email || "Student";
  const unlockedCount = badges.filter((b) => b.is_unlocked).length;

  const handleVerifyLookup = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!lookupIdentifier.trim()) return;

    setLookupLoading(true);
    setLookupError(null);
    setLookupResult(null);

    try {
      const result = await studentApi.verifyCertificate(lookupIdentifier.trim());
      setLookupResult(result);
    } catch (err: any) {
      const errorMsg =
        err?.response?.data?.error?.message ||
        "Certificate could not be verified or record not found.";
      setLookupError(errorMsg);
    } finally {
      setLookupLoading(false);
    }
  };

  return (
    <div className="space-y-8 max-w-5xl pb-12">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
          <User className="h-6 w-6 text-brand-400" />
          Student Profile & Credentials
        </h1>
        <p className="text-sm text-slate-400 mt-1">
          Review your enrolled academic records, milestone achievement badges, and verified course certificates.
        </p>
      </div>

      {/* Profile Overview Card */}
      <Card className="p-6 sm:p-8 bg-gradient-to-br from-surface-900 via-surface-900 to-surface-950 border-surface-800">
        <div className="flex flex-col gap-6 sm:flex-row sm:items-center sm:justify-between border-b border-surface-800/80 pb-6">
          <div className="flex items-center gap-4">
            <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-brand-500 to-indigo-600 text-2xl font-black text-white shadow-xl shadow-brand-500/20">
              {displayName.slice(0, 2).toUpperCase()}
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-xl font-bold text-white">{displayName}</h2>
                <Badge variant="emerald">{user?.onboarding_status || "ACTIVE"}</Badge>
              </div>
              <div className="mt-1 flex items-center gap-2 text-xs text-slate-400">
                <span className="font-mono text-slate-300">ID: {studentProfile?.student_id_number || "—"}</span>
                <span>•</span>
                <Badge variant="indigo" size="sm">
                  {studentProfile?.batch_code || "General Batch"}
                </Badge>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 rounded-xl bg-amber-500/10 px-3.5 py-2 border border-amber-500/20">
              <Star className="h-4 w-4 text-amber-400 fill-amber-400" />
              <div>
                <span className="text-[10px] uppercase font-semibold text-amber-300/80 block leading-tight">Total Score</span>
                <span className="text-sm font-bold text-amber-300">{pointsFormatted} pts</span>
              </div>
            </div>
            <div className="flex items-center gap-2 rounded-xl bg-rose-500/10 px-3.5 py-2 border border-rose-500/20">
              <Flame className="h-4 w-4 text-rose-400 fill-rose-400" />
              <div>
                <span className="text-[10px] uppercase font-semibold text-rose-300/80 block leading-tight">Streak</span>
                <span className="text-sm font-bold text-rose-300">{studentProfile?.current_streak_days || 0} days</span>
              </div>
            </div>
          </div>
        </div>

        {/* Details Grid */}
        <div className="mt-6 grid grid-cols-1 gap-6 sm:grid-cols-2">
          <div className="space-y-4">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400">
              Academic Information
            </h3>
            <div className="space-y-2.5 text-xs">
              <div className="flex items-center gap-2 text-slate-300">
                <Building className="h-4 w-4 text-slate-400" />
                <span>College: {studentProfile?.college_name || "Institution Registered"}</span>
              </div>
              <div className="flex items-center gap-2 text-slate-300">
                <GraduationCap className="h-4 w-4 text-slate-400" />
                <span>Class Year: {studentProfile?.graduation_year || "2026"}</span>
              </div>
              <div className="flex items-center gap-2 text-slate-300">
                <ShieldCheck className="h-4 w-4 text-emerald-400" />
                <span>Status: Academic Standing Verified</span>
              </div>
            </div>
          </div>

          <div className="space-y-4">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400">
              Contact Details
            </h3>
            <div className="space-y-2.5 text-xs">
              <div className="flex items-center gap-2 text-slate-300">
                <Mail className="h-4 w-4 text-slate-400" />
                <span>{user?.email || "No email assigned"}</span>
              </div>
              <div className="flex items-center gap-2 text-slate-300">
                <Phone className="h-4 w-4 text-slate-400" />
                <span>{user?.mobile_number || "No mobile assigned"}</span>
              </div>
            </div>
          </div>
        </div>
      </Card>

      {/* Tabs Navigation */}
      <div className="flex border-b border-surface-800 gap-6">
        <button
          onClick={() => setActiveTab("achievements")}
          className={`pb-3 text-sm font-semibold transition-colors relative ${
            activeTab === "achievements"
              ? "text-brand-400 border-b-2 border-brand-500"
              : "text-slate-400 hover:text-white"
          }`}
        >
          <div className="flex items-center gap-2">
            <Award className="h-4 w-4" />
            <span>Achievement Badges</span>
            <Badge variant="indigo" size="sm">
              {unlockedCount}/{badges.length}
            </Badge>
          </div>
        </button>

        <button
          onClick={() => setActiveTab("certificates")}
          className={`pb-3 text-sm font-semibold transition-colors relative ${
            activeTab === "certificates"
              ? "text-brand-400 border-b-2 border-brand-500"
              : "text-slate-400 hover:text-white"
          }`}
        >
          <div className="flex items-center gap-2">
            <FileCheck className="h-4 w-4" />
            <span>Certificates</span>
            <Badge variant="emerald" size="sm">
              {certificates.length}
            </Badge>
          </div>
        </button>

        <button
          onClick={() => setActiveTab("verify")}
          className={`pb-3 text-sm font-semibold transition-colors relative ${
            activeTab === "verify"
              ? "text-brand-400 border-b-2 border-brand-500"
              : "text-slate-400 hover:text-white"
          }`}
        >
          <div className="flex items-center gap-2">
            <ShieldCheck className="h-4 w-4" />
            <span>Public Verification</span>
          </div>
        </button>
      </div>

      {/* Tab 1: Achievement Badges */}
      {activeTab === "achievements" && (
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <p className="text-xs text-slate-400">
              Milestone badges are awarded dynamically as you complete modules, maintain practice streaks, and score points.
            </p>
          </div>

          {badgesLoading ? (
            <div className="py-12 text-center text-slate-400">
              <Loader2 className="mx-auto h-8 w-8 animate-spin text-brand-400 mb-2" />
              Evaluating achievement telemetry...
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {badges.map((badge) => (
                <Card
                  key={badge.id}
                  className={`p-5 relative transition-all duration-200 ${
                    badge.is_unlocked
                      ? "border-brand-500/30 bg-gradient-to-br from-surface-900 to-brand-950/20 shadow-lg shadow-brand-500/5"
                      : "opacity-75 border-surface-800/60 bg-surface-950/40"
                  }`}
                >
                  <div className="flex items-start gap-3.5">
                    <div
                      className={`flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl text-xl font-bold shadow-md ${
                        badge.is_unlocked
                          ? "bg-gradient-to-br from-brand-500 to-amber-500 text-white shadow-brand-500/20"
                          : "bg-surface-800 text-slate-500"
                      }`}
                    >
                      {badge.is_unlocked ? "🏆" : <Lock className="h-5 w-5" />}
                    </div>

                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between gap-1">
                        <h4 className="font-bold text-sm text-white truncate">{badge.name}</h4>
                        {badge.is_unlocked ? (
                          <Badge variant="emerald" size="sm">
                            Unlocked
                          </Badge>
                        ) : (
                          <Badge variant="slate" size="sm">
                            Locked
                          </Badge>
                        )}
                      </div>

                      <p className="text-xs text-slate-400 mt-1 line-clamp-2">
                        {badge.description}
                      </p>

                      <div className="mt-3">
                        <div className="flex items-center justify-between text-[11px] mb-1">
                          <span className="text-slate-400">Progress</span>
                          <span className="font-semibold text-slate-300">
                            {badge.progress_percentage}%
                          </span>
                        </div>
                        <div className="h-1.5 w-full rounded-full bg-surface-800 overflow-hidden">
                          <div
                            className={`h-full rounded-full transition-all duration-500 ${
                              badge.is_unlocked
                                ? "bg-gradient-to-r from-brand-500 to-emerald-400"
                                : "bg-indigo-600"
                            }`}
                            style={{ width: `${badge.progress_percentage}%` }}
                          />
                        </div>
                      </div>

                      <div className="mt-3 flex items-center justify-between pt-2 border-t border-surface-800/60 text-[11px] text-slate-500">
                        <span>Reward: +{badge.points_reward} pts</span>
                        {badge.awarded_at && (
                          <span>
                            {new Date(badge.awarded_at).toLocaleDateString("en-US", {
                              month: "short",
                              day: "numeric",
                            })}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Tab 2: Verified Certificates */}
      {activeTab === "certificates" && (
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <p className="text-xs text-slate-400">
              Certificates of completion are automatically generated once 100% of a course curriculum is mastered.
            </p>
          </div>

          {certsLoading ? (
            <div className="py-12 text-center text-slate-400">
              <Loader2 className="mx-auto h-8 w-8 animate-spin text-brand-400 mb-2" />
              Loading certificate credentials...
            </div>
          ) : certificates.length === 0 ? (
            <Card className="p-8 text-center border-surface-800">
              <Award className="mx-auto h-12 w-12 text-slate-600 mb-3" />
              <h3 className="text-base font-bold text-white">No Certificates Issued Yet</h3>
              <p className="text-xs text-slate-400 max-w-md mx-auto mt-1">
                Complete all modules and assignments in your enrolled courses to automatically earn official signed certificates.
              </p>
            </Card>
          ) : (
            <div className="grid grid-cols-1 gap-6">
              {certificates.map((cert) => (
                <Card
                  key={cert.id}
                  className="p-6 border-brand-500/20 bg-gradient-to-br from-surface-900 to-brand-950/10 relative overflow-hidden"
                >
                  <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <Badge variant="emerald" size="sm" className="flex items-center gap-1">
                          <CheckCircle2 className="h-3 w-3" />
                          Officially Issued
                        </Badge>
                        <span className="font-mono text-xs font-bold text-brand-300">
                          {cert.certificate_id}
                        </span>
                      </div>
                      <h3 className="text-lg font-bold text-white">{cert.title}</h3>
                      <p className="text-xs text-slate-400">
                        Awarded to <span className="text-slate-200 font-semibold">{cert.student_name}</span> for completing {cert.course_title}.
                      </p>
                      <div className="pt-2 text-[11px] font-mono text-slate-500 truncate max-w-lg">
                        SHA-256: {cert.verification_hash}
                      </div>
                    </div>

                    <div className="flex items-center gap-3">
                      <a
                        href={`/api/v1/students/certificates/${cert.id}/download/`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-2 rounded-xl bg-brand-600 px-4 py-2.5 text-xs font-semibold text-white shadow-lg shadow-brand-500/20 hover:bg-brand-500 transition-colors"
                      >
                        <Download className="h-4 w-4" />
                        Download PDF
                      </a>
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Tab 3: Public Verification Tool */}
      {activeTab === "verify" && (
        <div className="space-y-6">
          <Card className="p-6 border-surface-800">
            <h3 className="text-base font-bold text-white mb-1">
              Cryptographic Certificate Verification
            </h3>
            <p className="text-xs text-slate-400 mb-6">
              Enter any Certificate ID (e.g. GQT-CERT-2026-XXXX) or SHA-256 hash to verify the institutional signature and authenticity.
            </p>

            <form onSubmit={handleVerifyLookup} className="flex gap-3">
              <Input
                type="text"
                placeholder="Enter Certificate ID or SHA-256 Hash..."
                value={lookupIdentifier}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setLookupIdentifier(e.target.value)}
                className="flex-1 font-mono text-xs"
                required
              />
              <Button type="submit" disabled={lookupLoading} className="flex items-center gap-2">
                {lookupLoading ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Search className="h-4 w-4" />
                )}
                Verify
              </Button>
            </form>

            {lookupError && (
              <div className="mt-4 rounded-xl border border-rose-500/20 bg-rose-500/10 p-4 text-xs text-rose-300 flex items-center gap-2">
                <AlertTriangle className="h-4 w-4 shrink-0 text-rose-400" />
                <span>{lookupError}</span>
              </div>
            )}

            {lookupResult && (
              <div className="mt-6 rounded-2xl border border-emerald-500/30 bg-emerald-950/20 p-6 space-y-4">
                <div className="flex items-center justify-between border-b border-emerald-500/20 pb-4">
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="h-5 w-5 text-emerald-400" />
                    <span className="font-bold text-emerald-300">Verified Authentic Certificate</span>
                  </div>
                  <Badge variant="emerald">{lookupResult.status}</Badge>
                </div>

                <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 text-xs">
                  <div>
                    <span className="text-slate-400 block text-[11px]">Recipient</span>
                    <p className="font-semibold text-white mt-0.5">{lookupResult.student_name}</p>
                    <p className="text-slate-400 text-[11px]">ID: {lookupResult.student_id_number}</p>
                  </div>
                  <div>
                    <span className="text-slate-400 block text-[11px]">Program</span>
                    <p className="font-semibold text-white mt-0.5">{lookupResult.course_title}</p>
                  </div>
                  <div>
                    <span className="text-slate-400 block text-[11px]">Certificate Identifier</span>
                    <p className="font-mono font-semibold text-brand-300 mt-0.5">{lookupResult.certificate_id}</p>
                  </div>
                  <div>
                    <span className="text-slate-400 block text-[11px]">Issued Date</span>
                    <p className="text-slate-300 mt-0.5">
                      {lookupResult.issued_at
                        ? new Date(lookupResult.issued_at).toLocaleDateString("en-US", {
                            year: "numeric",
                            month: "long",
                            day: "numeric",
                          })
                        : "—"}
                    </p>
                  </div>
                </div>

                {lookupResult.download_url && (
                  <div className="pt-2 border-t border-emerald-500/20 flex justify-end">
                    <a
                      href={lookupResult.download_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1 text-xs font-semibold text-emerald-300 hover:text-emerald-200"
                    >
                      <Download className="h-3.5 w-3.5 mr-1" />
                      Download PDF Document
                    </a>
                  </div>
                )}
              </div>
            )}
          </Card>
        </div>
      )}
    </div>
  );
};
