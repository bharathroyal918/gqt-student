import React, { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  MessageSquare,
  Search,
  Loader2,
  RefreshCw,
  Mail,
  User,
  Calendar,
  Clock,
  CheckCircle2,
  AlertCircle,
  HelpCircle,
  ShieldCheck,
  Send,
  ExternalLink,
  ChevronRight,
} from "lucide-react";
import { adminApi, AdminContactInquiryItem } from "../../api/adminApi";
import { Card } from "../../components/ui/Card";
import { Badge } from "../../components/ui/Badge";
import { Button } from "../../components/ui/Button";
import { Input, Select, Textarea } from "../../components/ui/Form";
import { useToast } from "../../context/ToastContext";

export const ContactInquiriesPage: React.FC = () => {
  const { id: routeInquiryId } = useParams<{ id?: string }>();
  const queryClient = useQueryClient();
  const { success, error: toastError } = useToast();

  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("ALL");
  const [categoryFilter, setCategoryFilter] = useState<string>("");
  const [selectedInquiry, setSelectedInquiry] = useState<AdminContactInquiryItem | null>(null);
  const [resolutionStatus, setResolutionStatus] = useState<string>("RESOLVED");
  const [adminNotes, setAdminNotes] = useState<string>("");

  // Fetch all inquiries
  const {
    data: inquiriesData,
    isLoading,
    isFetching,
    refetch,
  } = useQuery({
    queryKey: ["admin-contact-inquiries", statusFilter, categoryFilter, searchTerm],
    queryFn: () =>
      adminApi.getContactInquiries({
        status: statusFilter === "ALL" ? undefined : statusFilter,
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

  const inquiries = inquiriesData?.inquiries || [];

  // Auto select from route param or fallback to first
  useEffect(() => {
    if (inquiries.length > 0) {
      if (routeInquiryId) {
        const match = inquiries.find((i) => i.id === routeInquiryId);
        if (match) {
          setSelectedInquiry(match);
          setResolutionStatus(match.status);
          setAdminNotes(match.admin_notes || "");
          return;
        }
      }
      if (!selectedInquiry || !inquiries.some((i) => i.id === selectedInquiry.id)) {
        setSelectedInquiry(inquiries[0]);
        setResolutionStatus(inquiries[0].status);
        setAdminNotes(inquiries[0].admin_notes || "");
      }
    }
  }, [inquiries, routeInquiryId]);

  const handleSelectInquiry = (item: AdminContactInquiryItem) => {
    setSelectedInquiry(item);
    setResolutionStatus(item.status);
    setAdminNotes(item.admin_notes || "");
  };

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

  // Stats calculation
  const totalCount = inquiries.length;
  const pendingCount = inquiries.filter((i) => i.status === "PENDING").length;
  const investigatingCount = inquiries.filter((i) => i.status === "INVESTIGATING").length;
  const resolvedCount = inquiries.filter((i) => i.status === "RESOLVED").length;
  const closedCount = inquiries.filter((i) => i.status === "CLOSED").length;

  const filterTabs = [
    { key: "ALL", label: "All Tickets", count: totalCount },
    { key: "PENDING", label: "Pending", count: pendingCount },
    { key: "INVESTIGATING", label: "Investigating", count: investigatingCount },
    { key: "RESOLVED", label: "Resolved", count: resolvedCount },
    { key: "CLOSED", label: "Closed", count: closedCount },
  ];

  const getCategoryBadgeVariant = (cat: string) => {
    switch (cat) {
      case "TECHNICAL_SUPPORT":
        return "rose";
      case "COURSE_DOUBT":
        return "indigo";
      case "ACCOUNT_ISSUE":
        return "amber";
      case "GENERAL_FEEDBACK":
        return "emerald";
      default:
        return "slate";
    }
  };

  const getStatusBadgeVariant = (st: string) => {
    switch (st) {
      case "RESOLVED":
        return "emerald";
      case "INVESTIGATING":
        return "indigo";
      case "CLOSED":
        return "slate";
      default:
        return "amber";
    }
  };

  return (
    <div className="space-y-6 pb-12">
      {/* Top Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white flex items-center gap-2">
            <MessageSquare className="h-6 w-6 text-brand-500 dark:text-brand-400" />
            Support Inquiries & Helpdesk Tickets
          </h1>
          <p className="text-xs sm:text-sm text-slate-600 dark:text-slate-400 mt-1">
            Review and resolve student queries, technical assistance tickets, and academic feedback.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Button
            variant="outline"
            size="sm"
            onClick={() => refetch()}
            disabled={isFetching}
            className="flex items-center gap-2 text-xs"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${isFetching ? "animate-spin" : ""}`} />
            Refresh Queue
          </Button>
        </div>
      </div>

      {/* Metric Highlights */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 sm:gap-4">
        <div className="rounded-2xl border border-slate-200 dark:border-surface-800 bg-white dark:bg-surface-900/60 p-4 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Total Tickets</span>
            <HelpCircle className="h-4 w-4 text-brand-500" />
          </div>
          <p className="mt-2 text-2xl font-black text-slate-900 dark:text-white">{totalCount}</p>
          <span className="text-[11px] text-slate-400">All received student requests</span>
        </div>

        <div className="rounded-2xl border border-amber-500/20 bg-amber-500/5 p-4 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-amber-600 dark:text-amber-400 uppercase tracking-wider">Pending Action</span>
            <Clock className="h-4 w-4 text-amber-500" />
          </div>
          <p className="mt-2 text-2xl font-black text-amber-600 dark:text-amber-400">{pendingCount}</p>
          <span className="text-[11px] text-amber-600/70 dark:text-amber-400/70">Awaiting initial review</span>
        </div>

        <div className="rounded-2xl border border-indigo-500/20 bg-indigo-500/5 p-4 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-indigo-600 dark:text-indigo-400 uppercase tracking-wider">Investigating</span>
            <AlertCircle className="h-4 w-4 text-indigo-500" />
          </div>
          <p className="mt-2 text-2xl font-black text-indigo-600 dark:text-indigo-400">{investigatingCount}</p>
          <span className="text-[11px] text-indigo-600/70 dark:text-indigo-400/70">In active diagnosis</span>
        </div>

        <div className="rounded-2xl border border-emerald-500/20 bg-emerald-500/5 p-4 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-emerald-600 dark:text-emerald-400 uppercase tracking-wider">Resolved</span>
            <CheckCircle2 className="h-4 w-4 text-emerald-500" />
          </div>
          <p className="mt-2 text-2xl font-black text-emerald-600 dark:text-emerald-400">{resolvedCount}</p>
          <span className="text-[11px] text-emerald-600/70 dark:text-emerald-400/70">Successfully completed</span>
        </div>
      </div>

      {/* Filter Tabs Bar */}
      <div className="flex items-center gap-2 overflow-x-auto pb-1 border-b border-slate-200 dark:border-surface-800">
        {filterTabs.map((tab) => {
          const isActive = statusFilter === tab.key;
          return (
            <button
              key={tab.key}
              onClick={() => setStatusFilter(tab.key)}
              className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold whitespace-nowrap transition-all ${
                isActive
                  ? "bg-brand-600 text-white shadow-md shadow-brand-500/20"
                  : "bg-white dark:bg-surface-900/60 text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-surface-800"
              }`}
            >
              <span>{tab.label}</span>
              <span
                className={`px-1.5 py-0.5 rounded-full text-[10px] font-bold ${
                  isActive
                    ? "bg-white/20 text-white"
                    : "bg-slate-100 dark:bg-surface-800 text-slate-600 dark:text-slate-300"
                }`}
              >
                {tab.count}
              </span>
            </button>
          );
        })}
      </div>

      {/* Search & Category Filter */}
      <Card className="p-4 bg-white dark:bg-surface-900/60 border-slate-200 dark:border-surface-800">
        <div className="grid grid-cols-1 sm:grid-cols-12 gap-3 items-center">
          <div className="sm:col-span-8 relative">
            <Search className="absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
            <Input
              placeholder="Search by student name, email, subject, or message keywords..."
              value={searchTerm}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => setSearchTerm(e.target.value)}
              className="pl-10 text-xs sm:text-sm"
            />
          </div>

          <div className="sm:col-span-4">
            <Select
              value={categoryFilter}
              onChange={(e: React.ChangeEvent<HTMLSelectElement>) => setCategoryFilter(e.target.value)}
              className="text-xs sm:text-sm"
            >
              <option value="">All Inquiry Categories</option>
              <option value="TECHNICAL_SUPPORT">Technical Support</option>
              <option value="COURSE_DOUBT">Course / Curriculum Doubt</option>
              <option value="ACCOUNT_ISSUE">Account / Login Issue</option>
              <option value="GENERAL_FEEDBACK">General Feedback</option>
            </Select>
          </div>
        </div>
      </Card>

      {/* Master Detail Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Inquiries Queue List (7 cols) */}
        <div className="lg:col-span-7">
          <Card className="overflow-hidden border-slate-200 dark:border-surface-800">
            <div className="p-4 bg-slate-50 dark:bg-surface-900/80 border-b border-slate-200 dark:border-surface-800 flex items-center justify-between text-xs font-semibold text-slate-600 dark:text-slate-400 uppercase tracking-wider">
              <span>Support Inquiries Queue ({inquiries.length})</span>
            </div>

            <div className="divide-y divide-slate-200 dark:divide-surface-800/60 max-h-[680px] overflow-y-auto">
              {isLoading ? (
                <div className="py-16 text-center text-slate-500 dark:text-slate-400 text-xs">
                  <Loader2 className="mx-auto h-8 w-8 animate-spin text-brand-500 mb-2" />
                  Loading inquiries queue...
                </div>
              ) : inquiries.length === 0 ? (
                <div className="py-16 text-center text-slate-500 dark:text-slate-400 text-xs space-y-2">
                  <MessageSquare className="mx-auto h-10 w-10 text-slate-300 dark:text-slate-600" />
                  <p className="font-semibold text-slate-700 dark:text-slate-300">No Inquiries Found</p>
                  <p className="text-[11px]">No student inquiries match the active status or filters.</p>
                </div>
              ) : (
                inquiries.map((item) => {
                  const isSelected = selectedInquiry?.id === item.id;
                  return (
                    <div
                      key={item.id}
                      onClick={() => handleSelectInquiry(item)}
                      className={`p-4 cursor-pointer transition-all ${
                        isSelected
                          ? "bg-brand-500/10 border-l-4 border-l-brand-600 shadow-sm"
                          : "hover:bg-slate-50 dark:hover:bg-surface-900/40"
                      }`}
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div className="space-y-1.5 min-w-0 flex-1">
                          <div className="flex items-center gap-2 flex-wrap">
                            <span className="font-bold text-sm text-slate-900 dark:text-white truncate">
                              {item.subject}
                            </span>
                            <Badge variant={getStatusBadgeVariant(item.status) as any} size="sm">
                              {item.status}
                            </Badge>
                            <Badge variant={getCategoryBadgeVariant(item.category) as any} size="sm">
                              {item.category.replace(/_/g, " ")}
                            </Badge>
                          </div>

                          <p className="text-xs text-slate-600 dark:text-slate-400 line-clamp-2 leading-relaxed">
                            {item.message}
                          </p>

                          <div className="flex flex-wrap items-center gap-3 text-[11px] text-slate-500 dark:text-slate-400 pt-1">
                            <span className="font-medium text-slate-700 dark:text-slate-300">
                              {item.name}
                            </span>
                            <span>&bull;</span>
                            <span>{item.email}</span>
                            <span>&bull;</span>
                            <span>{new Date(item.created_at).toLocaleDateString()}</span>
                          </div>
                        </div>

                        <ChevronRight className={`h-4 w-4 shrink-0 transition-transform ${
                          isSelected ? "text-brand-500 translate-x-1" : "text-slate-400"
                        }`} />
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </Card>
        </div>

        {/* Inquiry Detail & Resolution Form (5 cols) */}
        <div className="lg:col-span-5">
          {selectedInquiry ? (
            <Card className="p-5 sm:p-6 border-slate-200 dark:border-surface-800 bg-white dark:bg-surface-900 space-y-5 sticky top-6">
              {/* Header Info */}
              <div className="border-b border-slate-200 dark:border-surface-800 pb-4">
                <div className="flex items-center justify-between gap-2 flex-wrap">
                  <Badge variant={getCategoryBadgeVariant(selectedInquiry.category) as any} size="sm">
                    {selectedInquiry.category.replace(/_/g, " ")}
                  </Badge>
                  <span className="font-mono text-xs text-slate-400">
                    Ticket #{selectedInquiry.id.slice(0, 8)}
                  </span>
                </div>
                <h3 className="text-base font-bold text-slate-900 dark:text-white mt-2 leading-snug">
                  {selectedInquiry.subject}
                </h3>
              </div>

              {/* Student Details Card */}
              <div className="space-y-3 text-xs">
                <div className="p-3.5 rounded-2xl bg-slate-50 dark:bg-surface-950/60 border border-slate-200 dark:border-surface-800/80 space-y-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2 text-slate-700 dark:text-slate-300">
                      <User className="h-3.5 w-3.5 text-brand-500" />
                      <span><strong>Student:</strong> {selectedInquiry.name}</span>
                    </div>
                    <Badge variant={getStatusBadgeVariant(selectedInquiry.status) as any} size="sm">
                      {selectedInquiry.status}
                    </Badge>
                  </div>

                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2 text-slate-700 dark:text-slate-300">
                      <Mail className="h-3.5 w-3.5 text-indigo-400" />
                      <span><strong>Email:</strong> {selectedInquiry.email}</span>
                    </div>
                    <a
                      href={`mailto:${selectedInquiry.email}?subject=Re: [Ticket %23${selectedInquiry.id.slice(0, 8)}] ${encodeURIComponent(selectedInquiry.subject)}&body=Hello ${encodeURIComponent(selectedInquiry.name)},%0D%0A%0D%0ARegarding your inquiry:%0D%0A"${encodeURIComponent(selectedInquiry.message)}"%0D%0A%0D%0A`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1 text-[11px] font-semibold text-brand-600 dark:text-brand-400 hover:underline"
                    >
                      <Send className="h-3 w-3" />
                      <span>Reply by Email</span>
                    </a>
                  </div>

                  <div className="flex items-center gap-2 text-slate-500 dark:text-slate-400 text-[11px]">
                    <Calendar className="h-3.5 w-3.5 text-slate-400" />
                    <span>Submitted on {new Date(selectedInquiry.created_at).toLocaleString()}</span>
                  </div>

                  {selectedInquiry.resolved_at && (
                    <div className="flex items-center gap-2 text-emerald-600 dark:text-emerald-400 text-[11px] pt-1 border-t border-slate-200 dark:border-surface-800">
                      <CheckCircle2 className="h-3.5 w-3.5" />
                      <span>
                        Resolved on {new Date(selectedInquiry.resolved_at).toLocaleString()}
                        {selectedInquiry.resolved_by_email && ` by ${selectedInquiry.resolved_by_email}`}
                      </span>
                    </div>
                  )}
                </div>

                {/* Inquiry Body Content */}
                <div>
                  <label className="text-[11px] font-bold uppercase tracking-wider text-slate-600 dark:text-slate-400 block mb-1">
                    Student Inquiry Query
                  </label>
                  <div className="p-3.5 rounded-2xl bg-slate-50 dark:bg-surface-950 border border-slate-200 dark:border-surface-800 text-slate-800 dark:text-slate-200 leading-relaxed whitespace-pre-wrap text-xs">
                    {selectedInquiry.message}
                  </div>
                </div>
              </div>

              {/* Resolution / Status Update Form */}
              <form onSubmit={handleUpdateSubmit} className="pt-4 border-t border-slate-200 dark:border-surface-800 space-y-3.5">
                <h4 className="text-xs font-bold text-slate-900 dark:text-white uppercase tracking-wider flex items-center gap-1.5">
                  <ShieldCheck className="h-4 w-4 text-brand-500" />
                  <span>Update Resolution & Status</span>
                </h4>

                <div>
                  <label className="block text-[11px] font-semibold text-slate-700 dark:text-slate-400 mb-1">
                    Ticket Status
                  </label>
                  <Select
                    value={resolutionStatus}
                    onChange={(e: React.ChangeEvent<HTMLSelectElement>) => setResolutionStatus(e.target.value)}
                  >
                    <option value="PENDING">Pending (Requires Action)</option>
                    <option value="INVESTIGATING">Investigating (In Progress)</option>
                    <option value="RESOLVED">Resolved (Action Taken)</option>
                    <option value="CLOSED">Closed (Archived)</option>
                  </Select>
                </div>

                <div>
                  <label className="block text-[11px] font-semibold text-slate-700 dark:text-slate-400 mb-1">
                    Internal Admin Notes & Actions Taken
                  </label>
                  <Textarea
                    rows={3}
                    placeholder="Document resolution steps, student communications, or internal actions..."
                    value={adminNotes}
                    onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setAdminNotes(e.target.value)}
                  />
                </div>

                <div className="flex items-center justify-between pt-2">
                  <a
                    href={`mailto:${selectedInquiry.email}?subject=Re: [Ticket %23${selectedInquiry.id.slice(0, 8)}] ${encodeURIComponent(selectedInquiry.subject)}`}
                    className="inline-flex items-center gap-1.5 text-xs text-slate-600 dark:text-slate-400 hover:text-brand-500 font-medium"
                  >
                    <ExternalLink className="h-3.5 w-3.5" />
                    <span>Email Direct</span>
                  </a>

                  <Button
                    type="submit"
                    disabled={updateMutation.isPending}
                    className="flex items-center gap-1.5 text-xs font-bold"
                  >
                    {updateMutation.isPending && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
                    Save Resolution
                  </Button>
                </div>
              </form>
            </Card>
          ) : (
            <Card className="p-12 text-center border-slate-200 dark:border-surface-800 text-slate-500 dark:text-slate-400 text-xs">
              <MessageSquare className="mx-auto h-12 w-12 text-slate-300 dark:text-slate-700 mb-3" />
              Select an inquiry from the queue to inspect details and resolve.
            </Card>
          )}
        </div>
      </div>
    </div>
  );
};
