import React, { useState, useRef, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
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
  CalendarCheck,
  Calendar,
  Save,
  BookOpen,
  Camera,
  UploadCloud,
  Trash2,
} from "lucide-react";
import { useAuthStore } from "../../store/authStore";
import {
  studentApi,
  BadgeItem,
  StudentCertificateItem,
  CertificateVerificationResult,
  StudentAttendanceSummary,
  StudentProfileUpdatePayload,
} from "../../api/studentApi";
import { Card } from "../../components/ui/Card";
import { Badge } from "../../components/ui/Badge";
import { Button } from "../../components/ui/Button";
import { Input } from "../../components/ui/Form";
import { useToast } from "../../context/ToastContext";
import { UserAvatar } from "../../components/ui/UserAvatar";

export const StudentProfilePage: React.FC = () => {
  const { user, studentProfile, updateStudentProfile, updateUser } = useAuthStore();
  const queryClient = useQueryClient();
  const { success, error: toastError } = useToast();
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const [activeTab, setActiveTab] = useState<"profile" | "attendance" | "achievements" | "certificates" | "verify">("profile");

  // Editable Profile Form State
  const [formData, setFormData] = useState<StudentProfileUpdatePayload>({
    dob: (studentProfile as any)?.dob || "",
    avatar_url: studentProfile?.avatar_url || "",
    branch: (studentProfile as any)?.branch || "",
    college_name: studentProfile?.college_name || "",
    graduation_year: studentProfile?.graduation_year || 2027,
    bio: (studentProfile as any)?.bio || "",
    github_url: (studentProfile as any)?.github_url || "",
    linkedin_url: (studentProfile as any)?.linkedin_url || "",
  });

  // Verification lookup state
  const [lookupIdentifier, setLookupIdentifier] = useState("");
  const [lookupResult, setLookupResult] = useState<CertificateVerificationResult | null>(null);
  const [lookupLoading, setLookupLoading] = useState(false);
  const [lookupError, setLookupError] = useState<string | null>(null);

  // Queries
  const { data: attendanceData, isLoading: attendanceLoading } = useQuery<StudentAttendanceSummary>({
    queryKey: ["student-attendance"],
    queryFn: studentApi.getAttendance,
  });

  const { data: badges = [], isLoading: badgesLoading } = useQuery<BadgeItem[]>({
    queryKey: ["student-badges"],
    queryFn: studentApi.getAchievements,
  });

  const { data: certificates = [], isLoading: certsLoading } = useQuery<StudentCertificateItem[]>({
    queryKey: ["student-certificates"],
    queryFn: studentApi.getCertificates,
  });

  // Profile Update Mutation
  const updateProfileMutation = useMutation({
    mutationFn: (payload: StudentProfileUpdatePayload) => studentApi.updateProfile(payload),
    onSuccess: (updatedProfile) => {
      success("Profile Updated", "Your editable profile details have been saved successfully.");
      if (studentProfile) {
        updateStudentProfile({ ...studentProfile, ...updatedProfile });
      }
      queryClient.invalidateQueries({ queryKey: ["student"] });
    },
    onError: (err: any) => {
      const msg = err.response?.data?.error?.message || "Failed to update profile. Please try again.";
      toastError("Update Failed", msg);
    },
  });

  // Upload Avatar Mutation
  const uploadAvatarMutation = useMutation({
    mutationFn: (file: File) => studentApi.uploadAvatar(file),
    onSuccess: (data) => {
      success("Profile Photo Updated", "Your profile photo is now live across the portal and header.");
      setFormData((prev) => ({ ...prev, avatar_url: data.avatar_url }));
      if (data.student_profile) {
        updateStudentProfile(data.student_profile);
      } else if (studentProfile) {
        updateStudentProfile({ ...studentProfile, avatar_url: data.avatar_url });
      }
      if (data.user) {
        updateUser(data.user);
      }
      queryClient.invalidateQueries({ queryKey: ["student"] });
    },
    onError: (err: any) => {
      const msg = err.response?.data?.error?.message || err?.message || "Failed to upload photo.";
      toastError("Upload Failed", msg);
    },
  });

  const handleAvatarFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!file.type.startsWith("image/")) {
      toastError("Invalid File", "Please select a valid image file (PNG, JPG, JPEG, WEBP).");
      return;
    }

    if (file.size > 5 * 1024 * 1024) {
      toastError("File Too Large", "Profile photo size must be less than 5 MB.");
      return;
    }

    uploadAvatarMutation.mutate(file);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const handleRemoveAvatar = () => {
    setFormData((prev) => ({ ...prev, avatar_url: "" }));
    updateProfileMutation.mutate({ ...formData, avatar_url: "" });
  };

  useEffect(() => {
    if (studentProfile) {
      setFormData({
        dob: (studentProfile as any)?.dob || "",
        avatar_url: studentProfile?.avatar_url || "",
        branch: (studentProfile as any)?.branch || "",
        college_name: studentProfile?.college_name || "",
        graduation_year: studentProfile?.graduation_year || 2026,
        bio: (studentProfile as any)?.bio || "",
        github_url: (studentProfile as any)?.github_url || "",
        linkedin_url: (studentProfile as any)?.linkedin_url || "",
      });
    }
  }, [studentProfile]);

  const handleProfileSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const payload: StudentProfileUpdatePayload = {
      ...formData,
      dob: formData.dob ? formData.dob : undefined,
      graduation_year: formData.graduation_year ? Number(formData.graduation_year) : undefined,
      branch: formData.branch || "",
      college_name: formData.college_name || "",
      bio: formData.bio || "",
      github_url: formData.github_url || "",
      linkedin_url: formData.linkedin_url || "",
      avatar_url: formData.avatar_url || "",
    };
    updateProfileMutation.mutate(payload);
  };

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

  const pointsFormatted = (studentProfile?.total_points || 0).toLocaleString();
  const displayName = studentProfile?.full_name || user?.email || "Student";
  const courseOpted = (studentProfile as any)?.course_opted || studentProfile?.batch_code || "Full Stack Software & Assessment Track";
  const unlockedCount = badges.filter((b) => b.is_unlocked).length;

  return (
    <div className="space-y-8 max-w-5xl pb-12">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white flex items-center gap-2">
          <User className="h-6 w-6 text-brand-500" />
          Student Profile & Academic Portal
        </h1>
        <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
          Review your institutional enrollment, edit permitted personal info, and monitor session attendance.
        </p>
      </div>

      {/* Profile Overview Card */}
      <Card className="p-6 sm:p-8 bg-white dark:bg-gradient-to-br dark:from-surface-900 dark:via-surface-900 dark:to-surface-950 border-slate-200 dark:border-surface-800 shadow-sm">
        <div className="flex flex-col gap-6 sm:flex-row sm:items-center sm:justify-between border-b border-slate-100 dark:border-surface-800/80 pb-6">
          <div className="flex items-center gap-4">
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleAvatarFileChange}
              accept="image/png,image/jpeg,image/jpg,image/webp"
              className="hidden"
            />
            <div
              className="relative group cursor-pointer"
              onClick={() => fileInputRef.current?.click()}
              title="Click to upload profile photo"
            >
              <UserAvatar
                src={formData.avatar_url || studentProfile?.avatar_url}
                name={displayName}
                size="xl"
                className="!h-20 !w-20 ring-4 ring-brand-500/20 shadow-md group-hover:opacity-80 transition-opacity"
              />
              <div className="absolute inset-0 flex flex-col items-center justify-center rounded-2xl bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity text-white text-[10px] font-bold">
                {uploadAvatarMutation.isPending ? (
                  <Loader2 className="h-5 w-5 animate-spin text-white" />
                ) : (
                  <>
                    <Camera className="h-5 w-5 text-white mb-0.5" />
                    <span>Change</span>
                  </>
                )}
              </div>
            </div>

            <div>
              <div className="flex items-center gap-2 flex-wrap">
                <h2 className="text-xl font-bold text-slate-900 dark:text-white">{displayName}</h2>
                <Badge
                  variant={
                    user?.onboarding_status === "ACTIVE"
                      ? "emerald"
                      : user?.onboarding_status === "PENDING_ACTIVATION"
                        ? "amber"
                        : "rose"
                  }
                >
                  {user?.onboarding_status || "ACTIVE"}
                </Badge>
              </div>
              <div className="mt-1 flex items-center gap-2 text-xs text-slate-500 dark:text-slate-400">
                <span className="font-mono text-slate-700 dark:text-slate-300">ID: {studentProfile?.student_id_number || "—"}</span>
                <span>•</span>
                <Badge variant="indigo" size="sm">
                  {studentProfile?.batch_code || "General Cohort"}
                </Badge>
              </div>

              {/* Avatar Quick Action Buttons */}
              <div className="mt-2.5 flex items-center gap-2">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  disabled={uploadAvatarMutation.isPending}
                  onClick={() => fileInputRef.current?.click()}
                  className="h-7 text-[11px] px-2.5 flex items-center gap-1.5"
                >
                  {uploadAvatarMutation.isPending ? (
                    <Loader2 className="h-3.5 w-3.5 animate-spin" />
                  ) : (
                    <UploadCloud className="h-3.5 w-3.5 text-brand-500" />
                  )}
                  <span>{uploadAvatarMutation.isPending ? "Uploading..." : "Upload Photo"}</span>
                </Button>
                {(formData.avatar_url || studentProfile?.avatar_url) && (
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    onClick={handleRemoveAvatar}
                    className="h-7 text-[11px] px-2 text-rose-500 hover:text-rose-600 hover:bg-rose-500/10 flex items-center gap-1"
                  >
                    <Trash2 className="h-3 w-3" />
                    <span>Remove</span>
                  </Button>
                )}
              </div>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 rounded-xl bg-emerald-500/10 px-3.5 py-2 border border-emerald-500/20">
              <CalendarCheck className="h-4 w-4 text-emerald-500" />
              <div>
                <span className="text-[10px] uppercase font-semibold text-emerald-700 dark:text-emerald-300/80 block leading-tight">Attendance</span>
                <span className="text-sm font-bold text-emerald-600 dark:text-emerald-300">
                  {attendanceData ? `${attendanceData.attendance_percentage}%` : "100%"}
                </span>
              </div>
            </div>
            <div className="flex items-center gap-2 rounded-xl bg-amber-500/10 px-3.5 py-2 border border-amber-500/20">
              <Star className="h-4 w-4 text-amber-500 fill-amber-500" />
              <div>
                <span className="text-[10px] uppercase font-semibold text-amber-700 dark:text-amber-300/80 block leading-tight">Total Score</span>
                <span className="text-sm font-bold text-amber-600 dark:text-amber-300">{pointsFormatted} pts</span>
              </div>
            </div>
            <div className="flex items-center gap-2 rounded-xl bg-rose-500/10 px-3.5 py-2 border border-rose-500/20">
              <Flame className="h-4 w-4 text-rose-500 fill-rose-500" />
              <div>
                <span className="text-[10px] uppercase font-semibold text-rose-700 dark:text-rose-300/80 block leading-tight">Streak</span>
                <span className="text-sm font-bold text-rose-600 dark:text-rose-300">{studentProfile?.current_streak_days || 0} days</span>
              </div>
            </div>
          </div>
        </div>

        {/* Details Strip */}
        <div className="mt-6 grid grid-cols-1 gap-6 sm:grid-cols-2">
          <div className="space-y-4">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
              Enrolled Program & Standing
            </h3>
            <div className="space-y-2.5 text-xs">
              <div className="flex items-center gap-2 text-slate-700 dark:text-slate-300">
                <BookOpen className="h-4 w-4 text-brand-500 shrink-0" />
                <span>Track: <strong className="text-slate-900 dark:text-white">{courseOpted}</strong> (Fixed)</span>
              </div>
              <div className="flex items-center gap-2 text-slate-700 dark:text-slate-300">
                <Building className="h-4 w-4 text-slate-400 shrink-0" />
                <span>College: {formData.college_name || studentProfile?.college_name || "Institution Registered"}</span>
              </div>
              <div className="flex items-center gap-2 text-slate-700 dark:text-slate-300">
                <GraduationCap className="h-4 w-4 text-slate-400 shrink-0" />
                <span>Class: {formData.graduation_year || studentProfile?.graduation_year || "2026"} • Branch: {formData.branch || (studentProfile as any)?.branch || "CSE"}</span>
              </div>
            </div>
          </div>

          <div className="space-y-4">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
              Verified Institutional Account
            </h3>
            <div className="space-y-2.5 text-xs">
              <div className="flex items-center gap-2 text-slate-700 dark:text-slate-300">
                <Mail className="h-4 w-4 text-slate-400 shrink-0" />
                <span>{user?.email || "No email assigned"}</span>
              </div>
              <div className="flex items-center gap-2 text-slate-700 dark:text-slate-300">
                <Phone className="h-4 w-4 text-slate-400 shrink-0" />
                <span>{user?.mobile_number || "No mobile assigned"}</span>
              </div>
              <div className="flex items-center gap-2 text-slate-700 dark:text-slate-300">
                <ShieldCheck className="h-4 w-4 text-emerald-500 shrink-0" />
                <span>Authorization: {user?.onboarding_status === "ACTIVE" ? "Full Access Granted" : "Pending Approval"}</span>
              </div>
            </div>
          </div>
        </div>
      </Card>

      {/* Tabs Navigation */}
      <div className="flex border-b border-slate-200 dark:border-surface-800 gap-6 overflow-x-auto">
        <button
          onClick={() => setActiveTab("profile")}
          className={`pb-3 text-sm font-semibold transition-colors whitespace-nowrap relative ${activeTab === "profile"
            ? "text-brand-600 dark:text-brand-400 border-b-2 border-brand-500"
            : "text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white"
            }`}
        >
          <div className="flex items-center gap-2">
            <User className="h-4 w-4" />
            <span>Profile & Settings</span>
          </div>
        </button>

        <button
          onClick={() => setActiveTab("attendance")}
          className={`pb-3 text-sm font-semibold transition-colors whitespace-nowrap relative ${activeTab === "attendance"
            ? "text-brand-600 dark:text-brand-400 border-b-2 border-brand-500"
            : "text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white"
            }`}
        >
          <div className="flex items-center gap-2">
            <CalendarCheck className="h-4 w-4" />
            <span>Attendance Records</span>
            {attendanceData && (
              <Badge variant="emerald" size="sm">
                {attendanceData.attendance_percentage}%
              </Badge>
            )}
          </div>
        </button>

        <button
          onClick={() => setActiveTab("achievements")}
          className={`pb-3 text-sm font-semibold transition-colors whitespace-nowrap relative ${activeTab === "achievements"
            ? "text-brand-600 dark:text-brand-400 border-b-2 border-brand-500"
            : "text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white"
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
          className={`pb-3 text-sm font-semibold transition-colors whitespace-nowrap relative ${activeTab === "certificates"
            ? "text-brand-600 dark:text-brand-400 border-b-2 border-brand-500"
            : "text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white"
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
          className={`pb-3 text-sm font-semibold transition-colors whitespace-nowrap relative ${activeTab === "verify"
            ? "text-brand-600 dark:text-brand-400 border-b-2 border-brand-500"
            : "text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white"
            }`}
        >
          <div className="flex items-center gap-2">
            <ShieldCheck className="h-4 w-4" />
            <span>Public Verification</span>
          </div>
        </button>
      </div>

      {/* Tab 1: Profile & Edit Restrictions */}
      {activeTab === "profile" && (
        <div className="space-y-6">
          {/* Institutional Immutability Notice */}
          <div className="rounded-2xl border border-amber-500/20 bg-amber-500/10 p-4 text-xs text-amber-800 dark:text-amber-300/90 flex items-start gap-3">
            <Lock className="h-4 w-4 text-amber-500 shrink-0 mt-0.5" />
            <div>
              <span className="font-bold block mb-0.5">Strict Institutional Policy & Security Controls</span>
              To preserve academic integrity, your <strong>Full Name</strong>, <strong>Institutional Email</strong>, <strong>Student ID</strong>, and <strong>Course Track</strong> are locked by the administrator. You may update your Date of Birth, Profile Avatar, Branch/Major, College Name, Graduation Year, Bio, and Social URLs.
            </div>
          </div>

          <form onSubmit={handleProfileSubmit} className="space-y-6">
            <Card className="p-6 border-slate-200 dark:border-surface-800 space-y-6">
              <h3 className="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2 border-b border-slate-100 dark:border-surface-800 pb-3">
                <Lock className="h-4 w-4 text-slate-400" />
                Locked Institutional Identity (Read-Only)
              </h3>

              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <div>
                  <label className="text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1 block">
                    Full Legal Name
                  </label>
                  <div className="flex items-center justify-between rounded-xl bg-slate-100 dark:bg-surface-800/80 px-3.5 py-2.5 text-xs text-slate-700 dark:text-slate-300 font-medium border border-slate-200 dark:border-surface-700 cursor-not-allowed">
                    <span>{displayName}</span>
                    <Lock className="h-3.5 w-3.5 text-slate-400" />
                  </div>
                </div>

                <div>
                  <label className="text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1 block">
                    Institutional Email Address
                  </label>
                  <div className="flex items-center justify-between rounded-xl bg-slate-100 dark:bg-surface-800/80 px-3.5 py-2.5 text-xs text-slate-700 dark:text-slate-300 font-medium border border-slate-200 dark:border-surface-700 cursor-not-allowed">
                    <span>{user?.email || "—"}</span>
                    <Lock className="h-3.5 w-3.5 text-slate-400" />
                  </div>
                </div>

                <div>
                  <label className="text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1 block">
                    Student ID / USN
                  </label>
                  <div className="flex items-center justify-between rounded-xl bg-slate-100 dark:bg-surface-800/80 px-3.5 py-2.5 text-xs text-slate-700 dark:text-slate-300 font-mono border border-slate-200 dark:border-surface-700 cursor-not-allowed">
                    <span>{studentProfile?.student_id_number || "—"}</span>
                    <Lock className="h-3.5 w-3.5 text-slate-400" />
                  </div>
                </div>

                <div>
                  <label className="text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1 block">
                    Enrolled Course Track (Fixed)
                  </label>
                  <div className="flex items-center justify-between rounded-xl bg-slate-100 dark:bg-surface-800/80 px-3.5 py-2.5 text-xs text-slate-700 dark:text-slate-300 font-medium border border-slate-200 dark:border-surface-700 cursor-not-allowed">
                    <span>{courseOpted}</span>
                    <Lock className="h-3.5 w-3.5 text-slate-400" />
                  </div>
                </div>
              </div>
            </Card>

            <Card className="p-6 border-slate-200 dark:border-surface-800 space-y-6">
              <h3 className="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2 border-b border-slate-100 dark:border-surface-800 pb-3">
                <User className="h-4 w-4 text-brand-500" />
                Editable Personal Information
              </h3>

              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <div>
                  <label className="text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1 block">
                    Date of Birth (DOB)
                  </label>
                  <Input
                    type="date"
                    value={formData.dob || ""}
                    onChange={(e) => setFormData({ ...formData, dob: e.target.value })}
                    className="text-xs"
                  />
                </div>

                <div className="sm:col-span-2 rounded-2xl border border-slate-200 dark:border-surface-800 bg-slate-50 dark:bg-surface-900/40 p-4 space-y-3">
                  <div className="flex items-center justify-between">
                    <div>
                      <label className="text-xs font-bold text-slate-800 dark:text-slate-200 flex items-center gap-1.5">
                        <Camera className="h-4 w-4 text-brand-500" />
                        Profile Photo & Avatar Image
                      </label>
                      <p className="text-[11px] text-slate-500 dark:text-slate-400">
                        Upload an image file (PNG, JPG, WEBP, max 5MB) or enter an external image URL.
                      </p>
                    </div>
                    {formData.avatar_url && (
                      <button
                        type="button"
                        onClick={handleRemoveAvatar}
                        className="text-[11px] font-semibold text-rose-500 hover:text-rose-600 flex items-center gap-1 transition-colors"
                      >
                        <Trash2 className="h-3 w-3" />
                        Remove Photo
                      </button>
                    )}
                  </div>

                  <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4">
                    <UserAvatar
                      src={formData.avatar_url}
                      name={displayName}
                      size="lg"
                      className="ring-2 ring-brand-500/20 shadow"
                    />

                    <div className="flex-1 w-full space-y-2">
                      <div className="flex items-center gap-2">
                        <Button
                          type="button"
                          variant="outline"
                          size="sm"
                          disabled={uploadAvatarMutation.isPending}
                          onClick={() => fileInputRef.current?.click()}
                          className="text-xs font-semibold flex items-center gap-2"
                        >
                          {uploadAvatarMutation.isPending ? (
                            <Loader2 className="h-4 w-4 animate-spin text-brand-500" />
                          ) : (
                            <UploadCloud className="h-4 w-4 text-brand-500" />
                          )}
                          <span>{uploadAvatarMutation.isPending ? "Uploading File..." : "Upload Photo File"}</span>
                        </Button>
                        <span className="text-xs text-slate-400 font-medium">or paste direct image URL:</span>
                      </div>

                      <Input
                        type="url"
                        placeholder="https://images.unsplash.com/photo-..."
                        value={formData.avatar_url || ""}
                        onChange={(e) => setFormData({ ...formData, avatar_url: e.target.value })}
                        className="text-xs"
                      />
                    </div>
                  </div>
                </div>

                <div>
                  <label className="text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1 block">
                    Academic Branch / Discipline
                  </label>
                  <Input
                    type="text"
                    placeholder="e.g. Computer Science & Engineering"
                    value={formData.branch || ""}
                    onChange={(e) => setFormData({ ...formData, branch: e.target.value })}
                    className="text-xs"
                  />
                </div>

                <div>
                  <label className="text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1 block">
                    College / University Name
                  </label>
                  <Input
                    type="text"
                    placeholder="e.g. Global Institute of Technology"
                    value={formData.college_name || ""}
                    onChange={(e) => setFormData({ ...formData, college_name: e.target.value })}
                    className="text-xs"
                  />
                </div>

                <div>
                  <label className="text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1 block">
                    Graduation Year
                  </label>
                  <Input
                    type="number"
                    min="2020"
                    max="2035"
                    value={formData.graduation_year || 2026}
                    onChange={(e) => setFormData({ ...formData, graduation_year: parseInt(e.target.value) || 2026 })}
                    className="text-xs"
                  />
                </div>

                <div>
                  <label className="text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1 block">
                    GitHub Profile Link
                  </label>
                  <Input
                    type="url"
                    placeholder="https://github.com/username"
                    value={formData.github_url || ""}
                    onChange={(e) => setFormData({ ...formData, github_url: e.target.value })}
                    className="text-xs"
                  />
                </div>

                <div className="sm:col-span-2">
                  <label className="text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1 block">
                    LinkedIn Profile Link
                  </label>
                  <Input
                    type="url"
                    placeholder="https://linkedin.com/in/username"
                    value={formData.linkedin_url || ""}
                    onChange={(e) => setFormData({ ...formData, linkedin_url: e.target.value })}
                    className="text-xs"
                  />
                </div>

                <div className="sm:col-span-2">
                  <label className="text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1 block">
                    Short Bio / Focus Area
                  </label>
                  <textarea
                    rows={3}
                    placeholder="Briefly describe your programming focus and learning goals..."
                    value={formData.bio || ""}
                    onChange={(e) => setFormData({ ...formData, bio: e.target.value })}
                    className="w-full rounded-xl border border-slate-200 dark:border-surface-700 bg-white dark:bg-surface-900 p-3 text-xs text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-brand-500"
                  />
                </div>
              </div>

              <div className="flex justify-end pt-2">
                <Button
                  type="submit"
                  disabled={updateProfileMutation.isPending}
                  className="flex items-center gap-2 shadow-lg shadow-brand-500/20"
                >
                  {updateProfileMutation.isPending ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Save className="h-4 w-4" />
                  )}
                  Save Profile Changes
                </Button>
              </div>
            </Card>
          </form>
        </div>
      )}

      {/* Tab 2: Attendance Records */}
      {activeTab === "attendance" && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            <Card className="p-5 border-emerald-500/20 bg-emerald-50/50 dark:bg-emerald-950/10">
              <span className="text-xs font-semibold uppercase tracking-wider text-emerald-700 dark:text-emerald-300">
                Attendance Percentage
              </span>
              <div className="mt-2 flex items-baseline gap-2">
                <span className="text-3xl font-black text-emerald-600 dark:text-emerald-400">
                  {attendanceData ? `${attendanceData.attendance_percentage}%` : "100%"}
                </span>
                <span className="text-xs text-emerald-700/80 dark:text-emerald-400/80 font-medium">Compliance</span>
              </div>
            </Card>

            <Card className="p-5 border-slate-200 dark:border-surface-800">
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                Classes Attended
              </span>
              <div className="mt-2 flex items-baseline gap-2">
                <span className="text-3xl font-black text-slate-900 dark:text-white">
                  {attendanceData?.attended_classes || 0}
                </span>
                <span className="text-xs text-slate-500 dark:text-slate-400">Sessions</span>
              </div>
            </Card>

            <Card className="p-5 border-slate-200 dark:border-surface-800">
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                Total Scheduled Classes
              </span>
              <div className="mt-2 flex items-baseline gap-2">
                <span className="text-3xl font-black text-slate-900 dark:text-white">
                  {attendanceData?.total_classes || 0}
                </span>
                <span className="text-xs text-slate-500 dark:text-slate-400">Recorded</span>
              </div>
            </Card>
          </div>

          <Card className="p-6 border-slate-200 dark:border-surface-800 space-y-4">
            <h3 className="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
              <CalendarCheck className="h-5 w-5 text-brand-500" />
              Daily Attendance & Session Log
            </h3>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Admin-verified daily live classroom, mentor lab, and coding test attendance logs.
            </p>

            {attendanceLoading ? (
              <div className="py-8 text-center text-xs text-slate-500">
                <Loader2 className="mx-auto h-6 w-6 animate-spin text-brand-500 mb-2" />
                Loading attendance history...
              </div>
            ) : !attendanceData || attendanceData.records.length === 0 ? (
              <div className="py-8 text-center text-xs text-slate-500 dark:text-slate-400">
                <Calendar className="mx-auto h-8 w-8 text-slate-400 mb-2" />
                No individual session logs recorded yet. All enrolled students are marked present by default for general sessions.
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="border-b border-slate-100 dark:border-surface-800 text-slate-500 dark:text-slate-400">
                    <tr>
                      <th className="pb-3 font-semibold">Date</th>
                      <th className="pb-3 font-semibold">Session Title</th>
                      <th className="pb-3 font-semibold">Status</th>
                      <th className="pb-3 font-semibold">Remarks</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 dark:divide-surface-800/60">
                    {attendanceData.records.map((rec) => (
                      <tr key={rec.id} className="py-2.5">
                        <td className="py-3 font-medium text-slate-900 dark:text-white">
                          {new Date(rec.date).toLocaleDateString("en-US", {
                            month: "short",
                            day: "numeric",
                            year: "numeric",
                          })}
                        </td>
                        <td className="py-3 text-slate-700 dark:text-slate-300 font-medium">
                          {rec.session_title}
                        </td>
                        <td className="py-3">
                          <Badge
                            variant={
                              rec.status === "PRESENT"
                                ? "emerald"
                                : rec.status === "LATE"
                                  ? "amber"
                                  : rec.status === "EXCUSED"
                                    ? "indigo"
                                    : "rose"
                            }
                            size="sm"
                          >
                            {rec.status}
                          </Badge>
                        </td>
                        <td className="py-3 text-slate-500 dark:text-slate-400">
                          {rec.remarks || "—"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </Card>
        </div>
      )}

      {/* Tab 3: Achievement Badges */}
      {activeTab === "achievements" && (
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Milestone badges are awarded dynamically as you complete modules, maintain practice streaks, and score points.
            </p>
          </div>

          {badgesLoading ? (
            <div className="py-12 text-center text-slate-500 dark:text-slate-400">
              <Loader2 className="mx-auto h-8 w-8 animate-spin text-brand-500 mb-2" />
              Evaluating achievement telemetry...
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {badges.map((badge) => (
                <Card
                  key={badge.id}
                  className={`p-5 relative transition-all duration-200 ${badge.is_unlocked
                    ? "border-brand-500/30 bg-white dark:bg-gradient-to-br dark:from-surface-900 dark:to-brand-950/20 shadow-sm"
                    : "opacity-75 border-slate-200 dark:border-surface-800/60 bg-slate-50/50 dark:bg-surface-950/40"
                    }`}
                >
                  <div className="flex items-start gap-3.5">
                    <div
                      className={`flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl text-xl font-bold shadow-md ${badge.is_unlocked
                        ? "bg-gradient-to-br from-brand-500 to-amber-500 text-white shadow-brand-500/20"
                        : "bg-slate-100 dark:bg-surface-800 text-slate-400"
                        }`}
                    >
                      {badge.is_unlocked ? "🏆" : <Lock className="h-5 w-5" />}
                    </div>

                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between gap-1">
                        <h4 className="font-bold text-sm text-slate-900 dark:text-white truncate">{badge.name}</h4>
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

                      <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 line-clamp-2">
                        {badge.description}
                      </p>

                      <div className="mt-3">
                        <div className="flex items-center justify-between text-[11px] mb-1">
                          <span className="text-slate-500 dark:text-slate-400">Progress</span>
                          <span className="font-semibold text-slate-700 dark:text-slate-300">
                            {badge.progress_percentage}%
                          </span>
                        </div>
                        <div className="h-1.5 w-full rounded-full bg-slate-100 dark:bg-surface-800 overflow-hidden">
                          <div
                            className={`h-full rounded-full transition-all duration-500 ${badge.is_unlocked
                              ? "bg-gradient-to-r from-brand-500 to-emerald-400"
                              : "bg-indigo-600"
                              }`}
                            style={{ width: `${badge.progress_percentage}%` }}
                          />
                        </div>
                      </div>

                      <div className="mt-3 flex items-center justify-between pt-2 border-t border-slate-100 dark:border-surface-800/60 text-[11px] text-slate-500">
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

      {/* Tab 4: Verified Certificates */}
      {activeTab === "certificates" && (
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Certificates of completion are automatically generated once 100% of a course curriculum is mastered.
            </p>
          </div>

          {certsLoading ? (
            <div className="py-12 text-center text-slate-500 dark:text-slate-400">
              <Loader2 className="mx-auto h-8 w-8 animate-spin text-brand-500 mb-2" />
              Loading certificate credentials...
            </div>
          ) : certificates.length === 0 ? (
            <Card className="p-8 text-center border-slate-200 dark:border-surface-800">
              <Award className="mx-auto h-12 w-12 text-slate-400 dark:text-slate-600 mb-3" />
              <h3 className="text-base font-bold text-slate-900 dark:text-white">No Certificates Issued Yet</h3>
              <p className="text-xs text-slate-500 dark:text-slate-400 max-w-md mx-auto mt-1">
                Complete all modules and assignments in your enrolled courses to automatically earn official signed certificates.
              </p>
            </Card>
          ) : (
            <div className="grid grid-cols-1 gap-6">
              {certificates.map((cert) => (
                <Card
                  key={cert.id}
                  className="p-6 border-brand-500/20 bg-white dark:bg-gradient-to-br dark:from-surface-900 dark:to-brand-950/10 relative overflow-hidden shadow-sm"
                >
                  <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <Badge variant="emerald" size="sm" className="flex items-center gap-1">
                          <CheckCircle2 className="h-3 w-3" />
                          Officially Issued
                        </Badge>
                        <span className="font-mono text-xs font-bold text-brand-600 dark:text-brand-300">
                          {cert.certificate_id}
                        </span>
                      </div>
                      <h3 className="text-lg font-bold text-slate-900 dark:text-white">{cert.title}</h3>
                      <p className="text-xs text-slate-500 dark:text-slate-400">
                        Awarded to <span className="text-slate-800 dark:text-slate-200 font-semibold">{cert.student_name}</span> for completing {cert.course_title}.
                      </p>
                      <div className="pt-2 text-[11px] font-mono text-slate-400 dark:text-slate-500 truncate max-w-lg">
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

      {/* Tab 5: Public Verification Tool */}
      {activeTab === "verify" && (
        <div className="space-y-6">
          <Card className="p-6 border-slate-200 dark:border-surface-800">
            <h3 className="text-base font-bold text-slate-900 dark:text-white mb-1">
              Cryptographic Certificate Verification
            </h3>
            <p className="text-xs text-slate-500 dark:text-slate-400 mb-6">
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
              <div className="mt-4 rounded-xl border border-rose-500/20 bg-rose-50 dark:bg-rose-500/10 p-4 text-xs text-rose-700 dark:text-rose-300 flex items-center gap-2">
                <AlertTriangle className="h-4 w-4 shrink-0 text-rose-500 dark:text-rose-400" />
                <span>{lookupError}</span>
              </div>
            )}

            {lookupResult && (
              <div className="mt-6 rounded-2xl border border-emerald-500/30 bg-emerald-50/60 dark:bg-emerald-950/20 p-6 space-y-4">
                <div className="flex items-center justify-between border-b border-emerald-500/20 pb-4">
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="h-5 w-5 text-emerald-600 dark:text-emerald-400" />
                    <span className="font-bold text-emerald-800 dark:text-emerald-300">Verified Authentic Certificate</span>
                  </div>
                  <Badge variant="emerald">{lookupResult.status}</Badge>
                </div>

                <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 text-xs">
                  <div>
                    <span className="text-slate-500 dark:text-slate-400 block text-[11px]">Recipient</span>
                    <p className="font-semibold text-slate-900 dark:text-white mt-0.5">{lookupResult.student_name}</p>
                    <p className="text-slate-500 dark:text-slate-400 text-[11px]">ID: {lookupResult.student_id_number}</p>
                  </div>
                  <div>
                    <span className="text-slate-500 dark:text-slate-400 block text-[11px]">Program</span>
                    <p className="font-semibold text-slate-900 dark:text-white mt-0.5">{lookupResult.course_title}</p>
                  </div>
                  <div>
                    <span className="text-slate-500 dark:text-slate-400 block text-[11px]">Certificate Identifier</span>
                    <p className="font-mono font-semibold text-brand-600 dark:text-brand-300 mt-0.5">{lookupResult.certificate_id}</p>
                  </div>
                  <div>
                    <span className="text-slate-500 dark:text-slate-400 block text-[11px]">Issued Date</span>
                    <p className="text-slate-700 dark:text-slate-300 mt-0.5">
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
                      className="inline-flex items-center gap-1 text-xs font-semibold text-emerald-600 dark:text-emerald-300 hover:text-emerald-700 dark:hover:text-emerald-200"
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


