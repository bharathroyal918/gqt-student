import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Award,
  Search,
  CheckCircle2,
  AlertTriangle,
  Download,
  ShieldAlert,
  Loader2,
  RefreshCw,
} from "lucide-react";
import { adminApi, AdminCertificateItem } from "../../api/adminApi";
import { Card } from "../../components/ui/Card";
import { Badge } from "../../components/ui/Badge";
import { Button } from "../../components/ui/Button";
import { Input } from "../../components/ui/Form";

export const CertificatesPage: React.FC = () => {
  const queryClient = useQueryClient();
  const [searchTerm, setSearchTerm] = useState("");
  const [revokingCert, setRevokingCert] = useState<AdminCertificateItem | null>(null);
  const [revokeReason, setRevokeReason] = useState("");

  const {
    data: certData,
    isLoading,
    isFetching,
    refetch,
  } = useQuery({
    queryKey: ["admin-certificates", searchTerm],
    queryFn: () => adminApi.getCertificates({ search: searchTerm || undefined }),
  });

  const revokeMutation = useMutation({
    mutationFn: ({ id, reason }: { id: string; reason: string }) =>
      adminApi.revokeCertificate(id, reason),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-certificates"] });
      setRevokingCert(null);
      setRevokeReason("");
    },
  });

  const handleRevokeSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!revokingCert) return;
    revokeMutation.mutate({
      id: revokingCert.id,
      reason: revokeReason || "Administrative integrity revocation",
    });
  };

  const certificates = certData?.certificates || [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white flex items-center gap-2">
            <Award className="h-6 w-6 text-brand-500" />
            Certificates & Credentials
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
            Audit, verify, and manage officially issued student course completion certificates.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Button
            variant="outline"
            size="sm"
            onClick={() => refetch()}
            disabled={isFetching}
            className="flex items-center gap-2"
          >
            <RefreshCw className={`h-4 w-4 ${isFetching ? "animate-spin" : ""}`} />
            Refresh
          </Button>
        </div>
      </div>

      {/* Search Bar */}
      <Card className="p-4">
        <div className="relative">
          <Search className="absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
          <Input
            type="text"
            placeholder="Search by student name, ID number, certificate ID or course title..."
            value={searchTerm}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) => setSearchTerm(e.target.value)}
            className="pl-10"
          />
        </div>
      </Card>

      {/* Certificates Table */}
      <Card className="overflow-hidden border-slate-200 dark:border-surface-800">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-slate-700 dark:text-slate-300">
            <thead className="border-b border-slate-200 dark:border-surface-800 bg-slate-50 dark:bg-surface-900/80 text-xs uppercase tracking-wider text-slate-600 dark:text-slate-400">
              <tr>
                <th className="px-6 py-4 font-semibold">Certificate ID</th>
                <th className="px-6 py-4 font-semibold">Student</th>
                <th className="px-6 py-4 font-semibold">Course</th>
                <th className="px-6 py-4 font-semibold">Issued Date</th>
                <th className="px-6 py-4 font-semibold">Status</th>
                <th className="px-6 py-4 text-right font-semibold">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200/80 dark:divide-surface-800/60 bg-white dark:bg-surface-950/40">
              {isLoading ? (
                <tr>
                  <td colSpan={6} className="py-12 text-center text-slate-500">
                    <Loader2 className="mx-auto h-8 w-8 animate-spin text-brand-500 mb-2" />
                    Loading certificate records...
                  </td>
                </tr>
              ) : certificates.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-12 text-center text-slate-500">
                    <Award className="mx-auto h-10 w-10 text-slate-400 opacity-60 mb-2" />
                    No certificate records found matching the query.
                  </td>
                </tr>
              ) : (
                certificates.map((cert) => (
                  <tr key={cert.id} className="hover:bg-slate-50 dark:hover:bg-surface-900/40 transition-colors">
                    <td className="px-6 py-4">
                      <div className="font-mono text-xs font-semibold text-brand-600 dark:text-brand-300">
                        {cert.certificate_id}
                      </div>
                      <div className="text-[11px] text-slate-500 font-mono truncate max-w-[140px]" title={cert.verification_hash}>
                        Hash: {cert.verification_hash.slice(0, 12)}...
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="font-semibold text-slate-900 dark:text-white">{cert.student_name}</div>
                      <div className="text-xs text-slate-500 dark:text-slate-400">
                        {cert.student?.student_id_number} • {cert.student?.batch_code}
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="text-slate-800 dark:text-slate-200 font-medium">{cert.course_title}</div>
                      <div className="text-xs text-slate-500">100% Curriculum Completed</div>
                    </td>
                    <td className="px-6 py-4 text-xs text-slate-500 dark:text-slate-400">
                      {new Date(cert.issued_at).toLocaleDateString("en-US", {
                        year: "numeric",
                        month: "short",
                        day: "numeric",
                      })}
                    </td>
                    <td className="px-6 py-4">
                      {cert.is_revoked ? (
                        <Badge variant="rose" size="sm" className="flex w-fit items-center gap-1">
                          <AlertTriangle className="h-3 w-3" />
                          Revoked
                        </Badge>
                      ) : (
                        <Badge variant="emerald" size="sm" className="flex w-fit items-center gap-1">
                          <CheckCircle2 className="h-3 w-3" />
                          Verified
                        </Badge>
                      )}
                    </td>
                    <td className="px-6 py-4 text-right">
                      <div className="flex items-center justify-end gap-2">
                        {cert.pdf_file && (
                          <a
                            href={cert.pdf_file}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-1 rounded-lg bg-slate-100 dark:bg-surface-800 px-2.5 py-1.5 text-xs font-medium text-slate-700 dark:text-slate-200 hover:bg-slate-200 dark:hover:bg-surface-700 transition-colors"
                          >
                            <Download className="h-3.5 w-3.5" />
                            PDF
                          </a>
                        )}
                        {!cert.is_revoked && (
                          <Button
                            variant="danger"
                            size="sm"
                            onClick={() => setRevokingCert(cert)}
                            className="text-xs py-1 px-2.5"
                          >
                            <ShieldAlert className="h-3.5 w-3.5 mr-1" />
                            Revoke
                          </Button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </Card>

      {/* Revocation Modal */}
      {revokingCert && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 p-4 backdrop-blur-sm">
          <div className="w-full max-w-md rounded-2xl border border-slate-200 dark:border-surface-800 bg-white dark:bg-surface-900 p-6 shadow-2xl">
            <div className="flex items-center gap-3 text-rose-500 mb-4">
              <ShieldAlert className="h-6 w-6" />
              <h3 className="text-lg font-bold text-slate-900 dark:text-white">Revoke Certificate</h3>
            </div>
            <p className="text-xs text-slate-700 dark:text-slate-300 mb-4">
              Are you sure you want to revoke certificate{" "}
              <span className="font-mono font-bold text-rose-600 dark:text-rose-300">{revokingCert.certificate_id}</span>{" "}
              issued to <span className="font-semibold text-slate-900 dark:text-white">{revokingCert.student_name}</span>?
              This action flags the credential as invalid across all public verification endpoints.
            </p>

            <form onSubmit={handleRevokeSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-400 mb-1">
                  Revocation Reason (Audit Log)
                </label>
                <Input
                  type="text"
                  placeholder="e.g. Academic integrity violation, administrative cancellation"
                  value={revokeReason}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => setRevokeReason(e.target.value)}
                  required
                />
              </div>

              <div className="flex justify-end gap-3 pt-2">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => setRevokingCert(null)}
                  disabled={revokeMutation.isPending}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  variant="danger"
                  size="sm"
                  disabled={revokeMutation.isPending}
                  className="flex items-center gap-1.5"
                >
                  {revokeMutation.isPending && <Loader2 className="h-4 w-4 animate-spin" />}
                  Confirm Revocation
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
