import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  MessageSquare,
  Search,
  Loader2,
  RefreshCw,
  Mail,
  User,
  Calendar,
} from "lucide-react";
import { adminApi, AdminContactInquiryItem } from "../../api/adminApi";
import { Card } from "../../components/ui/Card";
import { Badge } from "../../components/ui/Badge";
import { Button } from "../../components/ui/Button";
import { Input, Select, Textarea } from "../../components/ui/Form";
import { useToast } from "../../context/ToastContext";

export const ContactInquiriesPage: React.FC = () => {
  const queryClient = useQueryClient();
  const { success, error: toastError } = useToast();

  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("");
  const [selectedInquiry, setSelectedInquiry] = useState<AdminContactInquiryItem | null>(null);
  const [resolutionStatus, setResolutionStatus] = useState<string>("RESOLVED");
  const [adminNotes, setAdminNotes] = useState<string>("");

  const {
    data: inquiriesData,
    isLoading,
    isFetching,
    refetch,
  } = useQuery({
    queryKey: ["admin-contact-inquiries", statusFilter, categoryFilter, searchTerm],
    queryFn: () =>
      adminApi.getContactInquiries({
        status: statusFilter || undefined,
        category: categoryFilter || undefined,
        search: searchTerm || undefined,
      }),
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: { status: string; admin_notes?: string } }) =>
      adminApi.updateContactInquiry(id, payload),
    onSuccess: (updated) => {
      queryClient.invalidateQueries({ queryKey: ["admin-contact-inquiries"] });
      setSelectedInquiry(updated);
      success("Ticket Updated", `Inquiry #${updated.id.slice(0, 8)} updated to ${updated.status}.`);
    },
    onError: (err: any) => {
      toastError("Update Failed", err?.response?.data?.error?.message || "Could not update inquiry.");
    },
  });

  const handleUpdateSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedInquiry) return;
    updateMutation.mutate({
      id: selectedInquiry.id,
      payload: {
        status: resolutionStatus,
        admin_notes: adminNotes,
      },
    });
  };

  const inquiries = inquiriesData?.inquiries || [];

  return (
    <div className="space-y-6 pb-12">
      {/* Top Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white flex items-center gap-2">
            <MessageSquare className="h-6 w-6 text-brand-500 dark:text-brand-400" />
            Support Inquiries & Helpdesk Tickets
          </h1>
          <p className="text-sm text-slate-600 dark:text-slate-400 mt-1">
            Manage incoming student queries, curriculum doubts, and technical assistance requests.
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

      {/* Filters Bar */}
      <Card className="p-4 bg-white dark:bg-surface-900/60 border-slate-200 dark:border-surface-800">
        <div className="grid grid-cols-1 sm:grid-cols-12 gap-3 items-center">
          <div className="sm:col-span-6 relative">
            <Search className="absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
            <Input
              placeholder="Search by student name, email, subject, or keywords..."
              value={searchTerm}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => setSearchTerm(e.target.value)}
              className="pl-10"
            />
          </div>

          <div className="sm:col-span-3">
            <Select
              value={statusFilter}
              onChange={(e: React.ChangeEvent<HTMLSelectElement>) => setStatusFilter(e.target.value)}
            >
              <option value="">All Statuses</option>
              <option value="PENDING">Pending</option>
              <option value="INVESTIGATING">Investigating</option>
              <option value="RESOLVED">Resolved</option>
              <option value="CLOSED">Closed</option>
            </Select>
          </div>

          <div className="sm:col-span-3">
            <Select
              value={categoryFilter}
              onChange={(e: React.ChangeEvent<HTMLSelectElement>) => setCategoryFilter(e.target.value)}
            >
              <option value="">All Categories</option>
              <option value="TECHNICAL_SUPPORT">Technical Support</option>
              <option value="COURSE_DOUBT">Course Doubt</option>
              <option value="ACCOUNT_ISSUE">Account Issue</option>
              <option value="GENERAL_FEEDBACK">General Feedback</option>
            </Select>
          </div>
        </div>
      </Card>

      {/* Master Detail Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Inquiries List (7 cols) */}
        <div className="lg:col-span-7">
          <Card className="overflow-hidden border-slate-200 dark:border-surface-800">
            <div className="p-4 bg-slate-50 dark:bg-surface-900/80 border-b border-slate-200 dark:border-surface-800 flex items-center justify-between text-xs font-semibold text-slate-600 dark:text-slate-400 uppercase tracking-wider">
              <span>Support Tickets ({inquiries.length})</span>
            </div>

            <div className="divide-y divide-slate-200 dark:divide-surface-800/60 max-h-[650px] overflow-y-auto">
              {isLoading ? (
                <div className="py-12 text-center text-slate-500 dark:text-slate-400 text-xs">
                  <Loader2 className="mx-auto h-8 w-8 animate-spin text-brand-500 dark:text-brand-400 mb-2" />
                  Loading inquiries queue...
                </div>
              ) : inquiries.length === 0 ? (
                <div className="py-12 text-center text-slate-500 dark:text-slate-400 text-xs">
                  <MessageSquare className="mx-auto h-10 w-10 text-slate-400 dark:text-slate-600 mb-2" />
                  No inquiries found matching criteria.
                </div>
              ) : (
                inquiries.map((item) => (
                  <div
                    key={item.id}
                    onClick={() => {
                      setSelectedInquiry(item);
                      setResolutionStatus(item.status);
                      setAdminNotes(item.admin_notes || "");
                    }}
                    className={`p-4 cursor-pointer transition-colors ${
                      selectedInquiry?.id === item.id
                        ? "bg-brand-500/10 border-l-4 border-l-brand-500"
                        : "hover:bg-slate-50 dark:hover:bg-surface-900/40"
                    }`}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="space-y-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <span className="font-semibold text-sm text-slate-900 dark:text-white truncate">
                            {item.subject}
                          </span>
                          <Badge
                            variant={
                              item.status === "RESOLVED"
                                ? "emerald"
                                : item.status === "INVESTIGATING"
                                ? "indigo"
                                : item.status === "CLOSED"
                                ? "slate"
                                : "amber"
                            }
                            size="sm"
                          >
                            {item.status}
                          </Badge>
                        </div>
                        <p className="text-xs text-slate-600 dark:text-slate-400 line-clamp-1">{item.message}</p>
                        <div className="flex items-center gap-3 text-[11px] text-slate-500 dark:text-slate-400 pt-1">
                          <span>{item.name} ({item.email})</span>
                          <span>•</span>
                          <span>{new Date(item.created_at).toLocaleDateString()}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </Card>
        </div>

        {/* Inquiry Detail & Resolution Pane (5 cols) */}
        <div className="lg:col-span-5">
          {selectedInquiry ? (
            <Card className="p-6 border-slate-200 dark:border-surface-800 bg-white dark:bg-surface-900 space-y-5 sticky top-6">
              <div className="border-b border-slate-200 dark:border-surface-800 pb-4">
                <div className="flex items-center justify-between">
                  <Badge variant="indigo" size="sm">
                    {selectedInquiry.category.replace(/_/g, " ")}
                  </Badge>
                  <span className="font-mono text-xs text-slate-500">
                    ID: {selectedInquiry.id.slice(0, 8)}
                  </span>
                </div>
                <h3 className="text-base font-bold text-slate-900 dark:text-white mt-2">
                  {selectedInquiry.subject}
                </h3>
              </div>

              {/* Recipient & Message */}
              <div className="space-y-3 text-xs">
                <div className="p-3 rounded-xl bg-slate-50 dark:bg-surface-950/60 border border-slate-200 dark:border-surface-800/80 space-y-1.5">
                  <div className="flex items-center gap-2 text-slate-700 dark:text-slate-300">
                    <User className="h-3.5 w-3.5 text-slate-500 dark:text-slate-400" />
                    <span><strong>Student:</strong> {selectedInquiry.name}</span>
                  </div>
                  <div className="flex items-center gap-2 text-slate-700 dark:text-slate-300">
                    <Mail className="h-3.5 w-3.5 text-slate-500 dark:text-slate-400" />
                    <span><strong>Email:</strong> {selectedInquiry.email}</span>
                  </div>
                  <div className="flex items-center gap-2 text-slate-700 dark:text-slate-300">
                    <Calendar className="h-3.5 w-3.5 text-slate-500 dark:text-slate-400" />
                    <span><strong>Submitted:</strong> {new Date(selectedInquiry.created_at).toLocaleString()}</span>
                  </div>
                </div>

                <div>
                  <label className="text-[11px] font-semibold uppercase tracking-wider text-slate-600 dark:text-slate-400 block mb-1">
                    Inquiry Body
                  </label>
                  <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-surface-950 border border-slate-200 dark:border-surface-800 text-slate-800 dark:text-slate-200 leading-relaxed whitespace-pre-wrap">
                    {selectedInquiry.message}
                  </div>
                </div>
              </div>

              {/* Ticket Resolution Form */}
              <form onSubmit={handleUpdateSubmit} className="pt-4 border-t border-slate-200 dark:border-surface-800 space-y-3.5">
                <h4 className="text-xs font-semibold text-slate-800 dark:text-slate-300 uppercase tracking-wider">
                  Update Ticket Status
                </h4>

                <div>
                  <label className="block text-[11px] font-semibold text-slate-700 dark:text-slate-400 mb-1">
                    Status
                  </label>
                  <Select
                    value={resolutionStatus}
                    onChange={(e: React.ChangeEvent<HTMLSelectElement>) => setResolutionStatus(e.target.value)}
                  >
                    <option value="PENDING">Pending</option>
                    <option value="INVESTIGATING">Investigating</option>
                    <option value="RESOLVED">Resolved</option>
                    <option value="CLOSED">Closed</option>
                  </Select>
                </div>

                <div>
                  <label className="block text-[11px] font-semibold text-slate-700 dark:text-slate-400 mb-1">
                    Internal Admin Notes (Audit Record)
                  </label>
                  <Textarea
                    rows={3}
                    placeholder="Enter resolution notes, actions taken, or email reply summary..."
                    value={adminNotes}
                    onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setAdminNotes(e.target.value)}
                  />
                </div>

                <div className="flex justify-end pt-2">
                  <Button
                    type="submit"
                    disabled={updateMutation.isPending}
                    className="flex items-center gap-1.5"
                  >
                    {updateMutation.isPending && <Loader2 className="h-4 w-4 animate-spin" />}
                    Save Changes
                  </Button>
                </div>
              </form>
            </Card>
          ) : (
            <Card className="p-12 text-center border-slate-200 dark:border-surface-800 text-slate-500 dark:text-slate-400 text-xs">
              <MessageSquare className="mx-auto h-12 w-12 text-slate-300 dark:text-slate-700 mb-3" />
              Select an inquiry from the queue on the left to review and update status.
            </Card>
          )}
        </div>
      </div>
    </div>
  );
};
