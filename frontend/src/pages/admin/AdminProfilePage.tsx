import React, { useState, useEffect, useRef } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  User,
  Shield,
  ShieldCheck,
  Mail,
  Phone,
  Key,
  Lock,
  Save,
  Loader2,
  CheckCircle2,
  AlertTriangle,
  History,
  Award,
  Layers,
  FileCheck,
  Cpu,
  Camera,
  UploadCloud,
  Trash2,
} from "lucide-react";
import { useAuthStore } from "../../store/authStore";
import {
  adminApi,
  AdminProfileData,
  AdminProfileUpdatePayload,
  ChangePasswordPayload,
} from "../../api/adminApi";
import { Card } from "../../components/ui/Card";
import { Badge } from "../../components/ui/Badge";
import { Button } from "../../components/ui/Button";
import { Input, Textarea } from "../../components/ui/Form";
import { useToast } from "../../context/ToastContext";
import { LoadingState } from "../../components/ui/LoadingState";
import { ErrorState } from "../../components/ui/ErrorState";
import { UserAvatar } from "../../components/ui/UserAvatar";

export const AdminProfilePage: React.FC = () => {
  const { user, updateUser } = useAuthStore();
  const queryClient = useQueryClient();
  const { success, error: toastError } = useToast();
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const [activeTab, setActiveTab] = useState<"profile" | "security" | "activity" | "permissions">("profile");

  // Profile Form State
  const [profileForm, setProfileForm] = useState<AdminProfileUpdatePayload>({
    full_name: "",
    designation: "",
    department: "",
    mobile_number: "",
    phone_number: "",
    bio: "",
    avatar_url: "",
    can_review_projects: true,
    can_manage_curriculum: true,
  });

  // Password Form State
  const [passwordForm, setPasswordForm] = useState({
    current_password: "",
    new_password: "",
    confirm_password: "",
  });
  const [passwordErrors, setPasswordErrors] = useState<Record<string, string>>({});

  // Fetch admin profile
  const {
    data: adminData,
    isLoading,
    isError,
    error,
    refetch,
  } = useQuery<AdminProfileData>({
    queryKey: ["admin-profile"],
    queryFn: adminApi.getAdminProfile,
  });

  useEffect(() => {
    if (adminData) {
      const p = adminData.profile || (adminData.user as any)?.admin_profile;
      setProfileForm({
        full_name: p?.full_name || "Administrator",
        designation: p?.designation || "Portal Administrator",
        department: p?.department || "Academic Operations",
        mobile_number: adminData.user.mobile_number || "",
        phone_number: p?.phone_number || "",
        bio: p?.bio || "",
        avatar_url: p?.avatar_url || "",
        can_review_projects: p?.can_review_projects ?? true,
        can_manage_curriculum: p?.can_manage_curriculum ?? true,
      });
    }
  }, [adminData]);

  // Mutation: Update Profile
  const updateProfileMutation = useMutation({
    mutationFn: (payload: AdminProfileUpdatePayload) => adminApi.updateAdminProfile(payload),
    onSuccess: (res) => {
      success("Profile Updated", "Your administrative profile details have been saved.");
      queryClient.invalidateQueries({ queryKey: ["admin-profile"] });
      if (user && res?.user) {
        updateUser({ ...user, ...res.user });
      }
    },
    onError: (err: any) => {
      const msg = err?.response?.data?.error?.message || err?.message || "Failed to update admin profile.";
      toastError("Update Failed", msg);
    },
  });

  // Upload Avatar Mutation
  const uploadAvatarMutation = useMutation({
    mutationFn: (file: File) => adminApi.uploadAvatar(file),
    onSuccess: (data) => {
      success("Profile Photo Updated", "Your profile photo is now active across the admin header and sidebar.");
      setProfileForm((prev) => ({ ...prev, avatar_url: data.avatar_url }));
      if (data.user) {
        updateUser(data.user);
      }
      queryClient.invalidateQueries({ queryKey: ["admin-profile"] });
    },
    onError: (err: any) => {
      const msg = err?.response?.data?.error?.message || err?.message || "Failed to upload photo.";
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
    setProfileForm((prev) => ({ ...prev, avatar_url: "" }));
    updateProfileMutation.mutate({ ...profileForm, avatar_url: "" });
  };

  // Mutation: Change Password
  const changePasswordMutation = useMutation({
    mutationFn: (payload: ChangePasswordPayload) => adminApi.changePassword(payload),
    onSuccess: () => {
      success("Password Changed", "Your password was changed successfully.");
      setPasswordForm({
        current_password: "",
        new_password: "",
        confirm_password: "",
      });
      setPasswordErrors({});
    },
    onError: (err: any) => {
      const msg = err?.response?.data?.error?.message || err?.message || "Failed to change password.";
      toastError("Password Change Failed", msg);
    },
  });

  const handleProfileSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    updateProfileMutation.mutate(profileForm);
  };

  const handlePasswordSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const errs: Record<string, string> = {};

    if (!passwordForm.current_password) {
      errs.current_password = "Current password is required.";
    }
    if (!passwordForm.new_password || passwordForm.new_password.length < 8) {
      errs.new_password = "New password must be at least 8 characters long.";
    }
    if (passwordForm.new_password !== passwordForm.confirm_password) {
      errs.confirm_password = "Passwords do not match.";
    }

    if (Object.keys(errs).length > 0) {
      setPasswordErrors(errs);
      return;
    }

    setPasswordErrors({});
    changePasswordMutation.mutate({
      current_password: passwordForm.current_password,
      new_password: passwordForm.new_password,
    });
  };

  if (isLoading) {
    return <LoadingState message="Loading administrative profile..." />;
  }

  if (isError) {
    return (
      <ErrorState
        title="Profile Unavailable"
        message={error instanceof Error ? error.message : "Failed to load administrative profile."}
        onRetry={refetch}
      />
    );
  }

  const recentLogins = adminData?.recent_logins || [];
  const initials = (profileForm.full_name || user?.email || "AD")
    .slice(0, 2)
    .toUpperCase();

  const tabs = [
    { id: "profile", label: "Profile Overview & Details", icon: User },
    { id: "security", label: "Security & Credentials", icon: Lock },
    { id: "activity", label: "Login & Audit History", icon: History },
    { id: "permissions", label: "System Permissions & Roles", icon: ShieldCheck },
  ];

  return (
    <div className="space-y-6 pb-16">
      {/* Top Banner & Identity Card */}
      <div className="relative overflow-hidden rounded-3xl bg-gradient-to-r from-slate-900 via-indigo-950 to-brand-950 p-6 sm:p-8 text-white shadow-xl border border-slate-800">
        <div className="absolute right-0 top-0 -mt-12 -mr-12 h-64 w-64 rounded-full bg-brand-500/10 blur-3xl pointer-events-none" />
        <div className="absolute left-1/3 bottom-0 -mb-12 h-48 w-48 rounded-full bg-indigo-500/10 blur-2xl pointer-events-none" />

        <div className="relative z-10 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-6">
          <div className="flex items-center gap-5">
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
                src={profileForm.avatar_url}
                name={profileForm.full_name || "Admin"}
                initials={initials}
                size="xl"
                className="ring-4 ring-white/10 shadow-lg group-hover:opacity-80 transition-opacity"
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

            <div className="space-y-1">
              <div className="flex items-center gap-2.5 flex-wrap">
                <h1 className="text-2xl font-black tracking-tight text-white">
                  {profileForm.full_name || "System Administrator"}
                </h1>
                <Badge variant="brand" size="sm">
                  Super Administrator
                </Badge>
                <Badge variant="emerald" size="sm">
                  Active
                </Badge>
              </div>

              <p className="text-xs sm:text-sm text-slate-300 font-medium flex items-center gap-2">
                <span>{profileForm.designation || "Platform Administrator"}</span>
                <span>&bull;</span>
                <span className="text-indigo-300">{profileForm.department || "Academic Operations"}</span>
              </p>

              <div className="flex flex-wrap items-center gap-4 text-xs text-slate-400 pt-1">
                <span className="flex items-center gap-1.5">
                  <Mail className="h-3.5 w-3.5 text-slate-400" />
                  {adminData?.user.email}
                </span>
                {adminData?.user.mobile_number && (
                  <span className="flex items-center gap-1.5">
                    <Phone className="h-3.5 w-3.5 text-slate-400" />
                    {adminData.user.mobile_number}
                  </span>
                )}
                <span className="flex items-center gap-1.5 text-slate-400">
                  <Shield className="h-3.5 w-3.5 text-amber-400" />
                  Full Privileges
                </span>
              </div>

              {/* Avatar Quick Action Buttons */}
              <div className="flex flex-wrap items-center gap-3 text-xs text-slate-400 pt-2">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  disabled={uploadAvatarMutation.isPending}
                  onClick={() => fileInputRef.current?.click()}
                  className="h-7 text-[11px] px-2.5 bg-white/10 text-white border-white/20 hover:bg-white/20 flex items-center gap-1.5"
                >
                  {uploadAvatarMutation.isPending ? (
                    <Loader2 className="h-3.5 w-3.5 animate-spin" />
                  ) : (
                    <UploadCloud className="h-3.5 w-3.5 text-brand-400" />
                  )}
                  <span>{uploadAvatarMutation.isPending ? "Uploading..." : "Upload Photo"}</span>
                </Button>
                {profileForm.avatar_url && (
                  <button
                    type="button"
                    onClick={handleRemoveAvatar}
                    className="text-[11px] text-rose-400 hover:text-rose-300 flex items-center gap-1 transition-colors"
                  >
                    <Trash2 className="h-3 w-3" />
                    Remove
                  </button>
                )}
              </div>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <Button
              variant="outline"
              size="sm"
              onClick={() => refetch()}
              className="border-white/20 bg-white/10 text-white hover:bg-white/20 text-xs backdrop-blur"
            >
              Refresh
            </Button>
          </div>
        </div>
      </div>

      {/* Tabs Bar */}
      <div className="flex items-center gap-2 overflow-x-auto pb-1 border-b border-slate-200 dark:border-surface-800">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs font-semibold whitespace-nowrap transition-all ${isActive
                ? "bg-brand-600 text-white shadow-md shadow-brand-500/25 font-bold"
                : "bg-white dark:bg-surface-900/60 text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-surface-800"
                }`}
            >
              <Icon className="h-4 w-4" />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      {/* Tab 1: Profile Details Form */}
      {activeTab === "profile" && (
        <form onSubmit={handleProfileSubmit} className="space-y-6">
          <Card className="p-6 border-slate-200 dark:border-surface-800 bg-white dark:bg-surface-900/60 space-y-6">
            <div className="border-b border-slate-200 dark:border-surface-800 pb-4">
              <h2 className="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
                <User className="h-5 w-5 text-brand-500" />
                Administrative Profile Details
              </h2>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                Update your identity details, department assignment, and public contact information.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5">
                  Full Name / Display Name *
                </label>
                <Input
                  required
                  placeholder="e.g. Dr. Jane Doe"
                  value={profileForm.full_name || ""}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                    setProfileForm((prev) => ({ ...prev, full_name: e.target.value }))
                  }
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5">
                  Designation / Role Title
                </label>
                <Input
                  placeholder="e.g. Head of Academic Operations & Placements"
                  value={profileForm.designation || ""}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                    setProfileForm((prev) => ({ ...prev, designation: e.target.value }))
                  }
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5">
                  Department / Unit
                </label>
                <Input
                  placeholder="e.g. Academic Operations & Curriculum Management"
                  value={profileForm.department || ""}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                    setProfileForm((prev) => ({ ...prev, department: e.target.value }))
                  }
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5">
                  Official Email Address (Primary Identity)
                </label>
                <Input
                  disabled
                  value={adminData?.user.email || ""}
                  className="bg-slate-100 dark:bg-surface-800 text-slate-500 cursor-not-allowed"
                />
                <span className="text-[11px] text-slate-400 mt-1 block">
                  Email changes require root system administrator provisioning.
                </span>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5">
                  Primary Mobile Number
                </label>
                <Input
                  placeholder="+91 9876543210"
                  value={profileForm.mobile_number || ""}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                    setProfileForm((prev) => ({ ...prev, mobile_number: e.target.value }))
                  }
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5">
                  Office Phone Extension / Direct Line
                </label>
                <Input
                  placeholder="+91 9448403469"
                  value={profileForm.phone_number || ""}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                    setProfileForm((prev) => ({ ...prev, phone_number: e.target.value }))
                  }
                />
              </div>

              <div className="md:col-span-2 rounded-2xl border border-slate-200 dark:border-surface-800 bg-slate-50 dark:bg-surface-900/40 p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <div>
                    <label className="text-xs font-bold text-slate-800 dark:text-slate-200 flex items-center gap-1.5">
                      <Camera className="h-4 w-4 text-brand-500" />
                      Administrator Profile Photo
                    </label>
                    <p className="text-[11px] text-slate-500 dark:text-slate-400">
                      Upload an image file (PNG, JPG, WEBP, max 5MB) or specify an image URL.
                    </p>
                  </div>
                  {profileForm.avatar_url && (
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
                    src={profileForm.avatar_url}
                    name={profileForm.full_name || "Admin"}
                    initials={initials}
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
                      <span className="text-xs text-slate-400 font-medium">or direct image URL:</span>
                    </div>

                    <Input
                      type="url"
                      placeholder="https://images.unsplash.com/... or hosted image URL"
                      value={profileForm.avatar_url || ""}
                      onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                        setProfileForm((prev) => ({ ...prev, avatar_url: e.target.value }))
                      }
                      className="text-xs"
                    />
                  </div>
                </div>
              </div>

              <div className="md:col-span-2">
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5">
                  Professional Bio & Responsibilities
                </label>
                <Textarea
                  rows={3}
                  placeholder="Brief overview of administrative responsibilities, office hours, or academic oversight focus..."
                  value={profileForm.bio || ""}
                  onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) =>
                    setProfileForm((prev) => ({ ...prev, bio: e.target.value }))
                  }
                />
              </div>
            </div>

            <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-200 dark:border-surface-800">
              <Button
                type="submit"
                disabled={updateProfileMutation.isPending}
                className="flex items-center gap-2 text-xs font-bold"
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
      )}

      {/* Tab 2: Security & Password */}
      {activeTab === "security" && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          <div className="lg:col-span-7 space-y-6">
            <Card className="p-6 border-slate-200 dark:border-surface-800 bg-white dark:bg-surface-900/60 space-y-5">
              <div className="border-b border-slate-200 dark:border-surface-800 pb-4">
                <h2 className="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
                  <Key className="h-5 w-5 text-indigo-500" />
                  Change Account Password
                </h2>
                <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                  Ensure your administrative credentials use a strong, unique password.
                </p>
              </div>

              <form onSubmit={handlePasswordSubmit} className="space-y-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5">
                    Current Password *
                  </label>
                  <Input
                    type="password"
                    placeholder="Enter your current password"
                    value={passwordForm.current_password}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                      setPasswordForm((prev) => ({ ...prev, current_password: e.target.value }))
                    }
                  />
                  {passwordErrors.current_password && (
                    <p className="text-xs text-rose-500 mt-1">{passwordErrors.current_password}</p>
                  )}
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5">
                    New Password (Min 8 Characters) *
                  </label>
                  <Input
                    type="password"
                    placeholder="Enter strong new password"
                    value={passwordForm.new_password}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                      setPasswordForm((prev) => ({ ...prev, new_password: e.target.value }))
                    }
                  />
                  {passwordErrors.new_password && (
                    <p className="text-xs text-rose-500 mt-1">{passwordErrors.new_password}</p>
                  )}
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5">
                    Confirm New Password *
                  </label>
                  <Input
                    type="password"
                    placeholder="Re-enter new password"
                    value={passwordForm.confirm_password}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                      setPasswordForm((prev) => ({ ...prev, confirm_password: e.target.value }))
                    }
                  />
                  {passwordErrors.confirm_password && (
                    <p className="text-xs text-rose-500 mt-1">{passwordErrors.confirm_password}</p>
                  )}
                </div>

                <div className="pt-3 border-t border-slate-200 dark:border-surface-800 flex justify-end">
                  <Button
                    type="submit"
                    disabled={changePasswordMutation.isPending}
                    className="flex items-center gap-2 text-xs font-bold"
                  >
                    {changePasswordMutation.isPending ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <Lock className="h-4 w-4" />
                    )}
                    Update Password
                  </Button>
                </div>
              </form>
            </Card>
          </div>

          <div className="lg:col-span-5 space-y-4">
            <Card className="p-5 border-slate-200 dark:border-surface-800 bg-slate-50 dark:bg-surface-900 space-y-4">
              <h3 className="text-xs font-bold text-slate-900 dark:text-white uppercase tracking-wider flex items-center gap-2">
                <ShieldCheck className="h-4 w-4 text-emerald-500" />
                Security Standards & Best Practices
              </h3>

              <div className="space-y-2.5 text-xs text-slate-600 dark:text-slate-400">
                <div className="flex items-start gap-2">
                  <CheckCircle2 className="h-4 w-4 text-emerald-500 shrink-0 mt-0.5" />
                  <span>Use at least 8 alphanumeric characters with mixed capitalization.</span>
                </div>
                <div className="flex items-start gap-2">
                  <CheckCircle2 className="h-4 w-4 text-emerald-500 shrink-0 mt-0.5" />
                  <span>Administrative actions and status updates are logged to the platform audit log.</span>
                </div>
                <div className="flex items-start gap-2">
                  <CheckCircle2 className="h-4 w-4 text-emerald-500 shrink-0 mt-0.5" />
                  <span>JWT session tokens rotate automatically to prevent token hijacking.</span>
                </div>
              </div>
            </Card>

            <Card className="p-5 border-indigo-500/20 bg-indigo-500/5 space-y-2">
              <span className="text-xs font-bold text-indigo-600 dark:text-indigo-400 uppercase tracking-wider">
                Session Lifecycle
              </span>
              <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
                Access tokens expire after 60 minutes of inactivity. Idle sessions will prompt for re-authentication.
              </p>
            </Card>
          </div>
        </div>
      )}

      {/* Tab 3: Login & Audit History */}
      {activeTab === "activity" && (
        <Card className="overflow-hidden border-slate-200 dark:border-surface-800">
          <div className="p-4 bg-slate-50 dark:bg-surface-900/80 border-b border-slate-200 dark:border-surface-800 flex items-center justify-between">
            <div>
              <h3 className="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2">
                <History className="h-4 w-4 text-brand-500" />
                Recent Authentication & Session History
              </h3>
              <p className="text-xs text-slate-500 mt-0.5">
                Audit trail of successful and attempted logins for this administrator account.
              </p>
            </div>
            <Badge variant="indigo" size="sm">
              {recentLogins.length} Events Logged
            </Badge>
          </div>

          <div className="divide-y divide-slate-200 dark:divide-surface-800/60 max-h-[550px] overflow-y-auto">
            {recentLogins.length === 0 ? (
              <div className="p-12 text-center text-xs text-slate-400">
                No recent login activity records found.
              </div>
            ) : (
              recentLogins.map((item) => (
                <div key={item.id} className="p-4 flex items-center justify-between gap-4 text-xs">
                  <div className="flex items-center gap-3">
                    <div
                      className={`flex h-8 w-8 items-center justify-center rounded-xl font-bold ${item.status === "SUCCESS"
                        ? "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400"
                        : "bg-rose-500/10 text-rose-500"
                        }`}
                    >
                      {item.status === "SUCCESS" ? (
                        <CheckCircle2 className="h-4 w-4" />
                      ) : (
                        <AlertTriangle className="h-4 w-4" />
                      )}
                    </div>

                    <div>
                      <p className="font-semibold text-slate-900 dark:text-white">
                        {item.login_type.replace(/_/g, " ")}
                      </p>
                      <p className="text-[11px] text-slate-500 dark:text-slate-400 truncate max-w-md">
                        IP: {item.ip_address || "127.0.0.1"} &bull; {item.user_agent || "Browser Session"}
                      </p>
                    </div>
                  </div>

                  <div className="text-right">
                    <Badge variant={item.status === "SUCCESS" ? "emerald" : "rose"} size="sm">
                      {item.status}
                    </Badge>
                    <p className="text-[11px] text-slate-400 mt-1">
                      {new Date(item.created_at).toLocaleString()}
                    </p>
                  </div>
                </div>
              ))
            )}
          </div>
        </Card>
      )}

      {/* Tab 4: System Permissions & Roles */}
      {activeTab === "permissions" && (
        <div className="space-y-6">
          <Card className="p-6 border-slate-200 dark:border-surface-800 bg-white dark:bg-surface-900/60 space-y-6">
            <div className="border-b border-slate-200 dark:border-surface-800 pb-4">
              <h2 className="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
                <ShieldCheck className="h-5 w-5 text-emerald-500" />
                Administrative Capabilities & Scope
              </h2>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                Overview of functional permissions assigned to your administrator account.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="p-4 rounded-2xl border border-slate-200 dark:border-surface-800 bg-slate-50 dark:bg-surface-950/60 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-xs text-slate-900 dark:text-white flex items-center gap-2">
                    <Layers className="h-4 w-4 text-brand-500" />
                    Curriculum & Course Management
                  </span>
                  <Badge variant="emerald" size="sm">
                    Granted
                  </Badge>
                </div>
                <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed">
                  Ability to publish courses, create modules, configure daily tasks, and set sandbox test cases.
                </p>
              </div>

              <div className="p-4 rounded-2xl border border-slate-200 dark:border-surface-800 bg-slate-50 dark:bg-surface-950/60 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-xs text-slate-900 dark:text-white flex items-center gap-2">
                    <FileCheck className="h-4 w-4 text-indigo-500" />
                    Project & Assignment Grading
                  </span>
                  <Badge variant="emerald" size="sm">
                    Granted
                  </Badge>
                </div>
                <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed">
                  Review student pull requests, project zip repositories, evaluate deliverables, and assign grades.
                </p>
              </div>

              <div className="p-4 rounded-2xl border border-slate-200 dark:border-surface-800 bg-slate-50 dark:bg-surface-950/60 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-xs text-slate-900 dark:text-white flex items-center gap-2">
                    <Award className="h-4 w-4 text-amber-500" />
                    Placements & Career Drives
                  </span>
                  <Badge variant="emerald" size="sm">
                    Granted
                  </Badge>
                </div>
                <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed">
                  Post new campus placement drives, review student resumes/applications, shortlist, and select candidates.
                </p>
              </div>

              <div className="p-4 rounded-2xl border border-slate-200 dark:border-surface-800 bg-slate-50 dark:bg-surface-950/60 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-xs text-slate-900 dark:text-white flex items-center gap-2">
                    <Cpu className="h-4 w-4 text-purple-500" />
                    Helpdesk & Support Inquiries
                  </span>
                  <Badge variant="emerald" size="sm">
                    Granted
                  </Badge>
                </div>
                <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed">
                  Triage incoming student help requests, reply via email, update investigation status, and log resolution notes.
                </p>
              </div>
            </div>
          </Card>
        </div>
      )}
    </div>
  );
};
