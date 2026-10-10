import React, { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Building2,
  Shield,
  Save,
  CheckCircle2,
  AlertCircle,
} from "lucide-react";
import { tpoApi } from "../../api/tpoApi";
import { useAuthStore } from "../../store/authStore";
import { Card } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";
import { FormField, Input } from "../../components/ui/Form";
import { LoadingState } from "../../components/ui/LoadingState";
import { ErrorState } from "../../components/ui/ErrorState";
import { UserAvatar } from "../../components/ui/UserAvatar";
import { UpdateTPOPayload } from "../../types/tpo";

export const TPOProfilePage: React.FC = () => {
  const queryClient = useQueryClient();
  const { user } = useAuthStore();

  const {
    data: profile,
    isLoading,
    isError,
    error,
    refetch,
  } = useQuery({
    queryKey: ["tpo-profile-me", user?.id],
    queryFn: tpoApi.getMe,
    staleTime: 60 * 1000,
  });

  const [formData, setFormData] = useState<UpdateTPOPayload>({
    full_name: "",
    designation: "",
    department: "",
    phone_number: "",
    bio: "",
    avatar_url: "",
  });

  const [saveSuccess, setSaveSuccess] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  useEffect(() => {
    if (profile) {
      setFormData({
        full_name: profile.full_name || "",
        designation: profile.designation || "",
        department: profile.department || "",
        phone_number: profile.phone_number || "",
        bio: profile.bio || "",
        avatar_url: profile.avatar_url || "",
      });
    }
  }, [profile]);

  const updateMutation = useMutation({
    mutationFn: (payload: UpdateTPOPayload) => tpoApi.updateMe(payload),
    onSuccess: (updated) => {
      queryClient.setQueryData(["tpo-profile-me", user?.id], updated);
      setSaveSuccess(true);
      setSaveError(null);
      setTimeout(() => setSaveSuccess(false), 4000);
    },
    onError: (err: any) => {
      setSaveError(
        err?.response?.data?.error?.message ||
          "Failed to update profile. Please review the inputs."
      );
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    updateMutation.mutate(formData);
  };

  if (isLoading) {
    return <LoadingState message="Loading officer profile..." />;
  }

  if (isError || !profile) {
    return (
      <ErrorState
        title="Profile Inaccessible"
        message={
          (error as any)?.response?.data?.error?.message ||
          "Could not retrieve your TPO profile."
        }
        onRetry={() => refetch()}
      />
    );
  }

  const college = profile.college;

  return (
    <div className="max-w-4xl mx-auto space-y-6 pb-12">
      {/* Header */}
      <div>
        <div className="flex items-center gap-2">
          <span className="text-xs font-bold uppercase tracking-wider text-brand-600 dark:text-brand-400">
            Account Preferences
          </span>
        </div>
        <h1 className="mt-1 text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
          Officer Profile
        </h1>
        <p className="mt-0.5 text-xs text-slate-500 dark:text-slate-400">
          Manage your personal placement officer contact information and view assigned institutional credentials.
        </p>
      </div>

      {saveSuccess && (
        <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-600 dark:text-emerald-400 text-xs font-semibold flex items-center gap-2">
          <CheckCircle2 className="h-4 w-4 shrink-0" />
          Profile updated successfully.
        </div>
      )}

      {saveError && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-600 dark:text-rose-400 text-xs font-semibold flex items-center gap-2">
          <AlertCircle className="h-4 w-4 shrink-0" />
          {saveError}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Left Column: Assigned Institution Badge */}
        <div className="space-y-6">
          {/* Avatar card */}
          <Card className="p-6 text-center">
            <UserAvatar
              src={formData.avatar_url || profile.avatar_url}
              name={formData.full_name || profile.full_name}
              initials={(formData.full_name || profile.full_name).slice(0, 2).toUpperCase()}
              size="xl"
              className="mx-auto mb-4"
            />
            <h2 className="text-base font-bold text-slate-900 dark:text-white">
              {profile.full_name}
            </h2>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
              {profile.designation || "Training & Placement Officer"}
            </p>
            <div className="mt-3">
              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-brand-500/10 text-brand-600 dark:text-brand-400">
                <Shield className="h-3 w-3" /> TPO Role
              </span>
            </div>
          </Card>

          {/* Assigned College Card */}
          <Card className="p-5">
            <div className="flex items-center gap-2 mb-3 text-brand-600 dark:text-brand-400 font-bold text-xs">
              <Building2 className="h-4 w-4" /> Assigned Institution
            </div>
            {college ? (
              <div className="space-y-2 text-xs">
                <p className="font-bold text-slate-900 dark:text-white">{college.name}</p>
                {college.code && (
                  <p className="text-slate-500 font-mono">Code: {college.code}</p>
                )}
                <p className="text-slate-500">
                  {college.city}, {college.state}
                </p>
                <div className="pt-2 border-t border-slate-100 dark:border-surface-800 text-[11px] text-slate-400">
                  Assigned by Admin on{" "}
                  {profile.assigned_at
                    ? new Date(profile.assigned_at).toLocaleDateString()
                    : "record"}
                </div>
              </div>
            ) : (
              <p className="text-xs text-amber-500">No active college assignment.</p>
            )}
          </Card>
        </div>

        {/* Right Column: Editable Form */}
        <div className="md:col-span-2">
          <Card className="p-6">
            <form onSubmit={handleSubmit} className="space-y-4">
              <h3 className="text-sm font-bold text-slate-900 dark:text-white border-b border-slate-100 dark:border-surface-800 pb-3">
                Edit Contact Details
              </h3>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <FormField label="Full Name" required>
                  <Input
                    type="text"
                    value={formData.full_name}
                    onChange={(e) =>
                      setFormData({ ...formData, full_name: e.target.value })
                    }
                    placeholder="Official Name"
                    required
                  />
                </FormField>

                <FormField label="Official Email (Fixed)">
                  <Input
                    type="email"
                    value={profile.email}
                    disabled
                    className="opacity-70 cursor-not-allowed bg-slate-100 dark:bg-surface-800"
                  />
                </FormField>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <FormField label="Designation">
                  <Input
                    type="text"
                    value={formData.designation}
                    onChange={(e) =>
                      setFormData({ ...formData, designation: e.target.value })
                    }
                    placeholder="e.g. Head of Placements"
                  />
                </FormField>

                <FormField label="Department">
                  <Input
                    type="text"
                    value={formData.department}
                    onChange={(e) =>
                      setFormData({ ...formData, department: e.target.value })
                    }
                    placeholder="e.g. Training & Placement Cell"
                  />
                </FormField>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <FormField label="Phone Number">
                  <Input
                    type="tel"
                    value={formData.phone_number}
                    onChange={(e) =>
                      setFormData({ ...formData, phone_number: e.target.value })
                    }
                    placeholder="+91 98765 43210"
                  />
                </FormField>

                <FormField label="Avatar URL">
                  <Input
                    type="url"
                    value={formData.avatar_url}
                    onChange={(e) =>
                      setFormData({ ...formData, avatar_url: e.target.value })
                    }
                    placeholder="https://example.com/photo.jpg"
                  />
                </FormField>
              </div>

              <FormField label="Bio / Notes">
                <textarea
                  value={formData.bio}
                  onChange={(e) =>
                    setFormData({ ...formData, bio: e.target.value })
                  }
                  rows={3}
                  className="w-full rounded-xl border border-slate-200 dark:border-surface-800 bg-white dark:bg-surface-900 p-3 text-xs text-slate-900 dark:text-white placeholder:text-slate-400 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
                  placeholder="Additional placement cell information..."
                />
              </FormField>

              <div className="flex justify-end pt-3">
                <Button
                  type="submit"
                  isLoading={updateMutation.isPending}
                  className="flex items-center gap-2"
                >
                  <Save className="h-4 w-4" /> Save Profile
                </Button>
              </div>
            </form>
          </Card>
        </div>
      </div>
    </div>
  );
};
