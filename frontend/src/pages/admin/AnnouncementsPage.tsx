import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Megaphone,
  Plus,
  Edit2,
  Trash2,
} from "lucide-react";
import { adminApi } from "../../api/adminApi";
import { AnnouncementItem } from "../../types/admin";
import { Button } from "../../components/ui/Button";
import { Badge } from "../../components/ui/Badge";
import { StatusDot } from "../../components/ui/StatusDot";
import { DataTable, Column } from "../../components/ui/DataTable";
import { SearchInput } from "../../components/ui/SearchInput";
import { Modal } from "../../components/ui/Modal";
import { FormField, Input, Textarea, Select, Checkbox } from "../../components/ui/Form";
import { ConfirmDialog } from "../../components/ui/ConfirmDialog";
import { useToast } from "../../context/ToastContext";

export const AnnouncementsPage: React.FC = () => {
  const queryClient = useQueryClient();
  const { success, error: toastError } = useToast();

  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [search, setSearch] = useState("");

  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [editingItem, setEditingItem] = useState<AnnouncementItem | null>(null);
  const [deletingItem, setDeletingItem] = useState<AnnouncementItem | null>(null);

  const [formData, setFormData] = useState({
    title: "",
    content: "",
    target_batch: "",
    priority: "NORMAL" as "LOW" | "NORMAL" | "HIGH" | "URGENT",
    expires_at: "",
    is_active: true,
  });

  // Queries
  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ["admin-announcements", { page, pageSize, search }],
    queryFn: () =>
      adminApi.getAnnouncements({
        page,
        page_size: pageSize,
        search: search.trim() || undefined,
      }),
  });

  // Mutations
  const createMutation = useMutation({
    mutationFn: adminApi.createAnnouncement,
    onSuccess: (item) => {
      success("Announcement Broadcasted", `Notice '${item.title}' is published.`);
      setIsCreateModalOpen(false);
      resetForm();
      queryClient.invalidateQueries({ queryKey: ["admin-announcements"] });
    },
    onError: (err: any) => {
      const msg = err.response?.data?.message || err.response?.data?.error?.message || "Failed to create announcement";
      toastError("Creation Failed", msg);
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: Partial<AnnouncementItem> }) =>
      adminApi.updateAnnouncement(id, payload),
    onSuccess: () => {
      success("Announcement Updated", "Notice content updated.");
      setEditingItem(null);
      queryClient.invalidateQueries({ queryKey: ["admin-announcements"] });
    },
    onError: () => toastError("Update Failed", "Could not update notice."),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => adminApi.deleteAnnouncement(id),
    onSuccess: () => {
      success("Announcement Removed", "Notice deleted from feed.");
      setDeletingItem(null);
      queryClient.invalidateQueries({ queryKey: ["admin-announcements"] });
    },
    onError: () => toastError("Delete Failed", "Could not delete notice."),
  });

  const resetForm = () => {
    setFormData({
      title: "",
      content: "",
      target_batch: "",
      priority: "NORMAL",
      expires_at: "",
      is_active: true,
    });
  };

  const handleOpenEdit = (item: AnnouncementItem) => {
    setEditingItem(item);
    setFormData({
      title: item.title,
      content: item.content,
      target_batch: item.target_batch || "",
      priority: item.priority,
      expires_at: item.expires_at ? item.expires_at.split("T")[0] : "",
      is_active: item.is_active,
    });
  };

  const columns: Column<AnnouncementItem>[] = [
    {
      key: "title",
      header: "Announcement & Notice",
      cell: (row) => (
        <div className="flex items-start gap-3">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-brand-500/10 text-brand-400 border border-brand-500/20">
            <Megaphone className="h-5 w-5" />
          </div>
          <div>
            <div className="font-semibold text-white">{row.title}</div>
            <div className="text-xs text-slate-400 line-clamp-2 mt-0.5 leading-relaxed">{row.content}</div>
          </div>
        </div>
      ),
    },
    {
      key: "target",
      header: "Audience",
      cell: (row) => (
        <div className="text-xs">
          {row.target_batch ? (
            <Badge variant="indigo" size="sm">
              {row.target_batch}
            </Badge>
          ) : (
            <Badge variant="emerald" size="sm">
              All Batches
            </Badge>
          )}
        </div>
      ),
    },
    {
      key: "priority",
      header: "Priority",
      cell: (row) => {
        const variant =
          row.priority === "URGENT"
            ? "rose"
            : row.priority === "HIGH"
            ? "amber"
            : row.priority === "NORMAL"
            ? "indigo"
            : "slate";
        return (
          <Badge variant={variant} size="sm">
            {row.priority}
          </Badge>
        );
      },
    },
    {
      key: "date",
      header: "Created",
      cell: (row) => (
        <div className="text-xs text-slate-400">
          {new Date(row.created_at).toLocaleDateString()}
        </div>
      ),
    },
    {
      key: "status",
      header: "Status",
      cell: (row) => (
        <div className="flex items-center gap-1.5">
          <StatusDot status={row.is_active ? "online" : "offline"} pulse={row.is_active} />
          <span className="text-xs text-slate-300">{row.is_active ? "Active" : "Expired"}</span>
        </div>
      ),
    },
    {
      key: "actions",
      header: "Actions",
      align: "right",
      cell: (row) => (
        <div className="flex items-center justify-end gap-1.5">
          <Button size="sm" variant="ghost" onClick={() => handleOpenEdit(row)} title="Edit Notice">
            <Edit2 className="h-4 w-4 text-slate-400 hover:text-brand-400" />
          </Button>
          <Button size="sm" variant="ghost" onClick={() => setDeletingItem(row)} title="Delete Notice">
            <Trash2 className="h-4 w-4 text-rose-400 hover:text-rose-300" />
          </Button>
        </div>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            Announcements & Broadcasts
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Broadcast platform-wide updates, deadline extensions, or targeted notifications to specific cohorts.
          </p>
        </div>

        <Button
          onClick={() => {
            resetForm();
            setIsCreateModalOpen(true);
          }}
        >
          <Plus className="h-4 w-4 mr-2" />
          New Announcement
        </Button>
      </div>

      {/* Search Bar */}
      <div className="flex flex-col gap-3 rounded-2xl border border-surface-800 bg-surface-900/60 p-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="w-full sm:max-w-xs">
          <SearchInput
            value={search}
            onChange={(val) => {
              setSearch(val);
              setPage(1);
            }}
            placeholder="Search announcements..."
          />
        </div>
      </div>

      {/* Table */}
      <DataTable
        data={data?.data || []}
        columns={columns}
        isLoading={isLoading}
        isError={isError}
        errorMessage="Unable to load announcements."
        onRetry={() => refetch()}
        emptyTitle="No Announcements Found"
        emptyDescription="Broadcast notices to inform students about schedule updates and events."
        pagination={
          data?.meta?.pagination
            ? {
                page: data.meta.pagination.page,
                pageSize: data.meta.pagination.page_size,
                totalRecords: data.meta.pagination.total_records,
                totalPages: data.meta.pagination.total_pages,
                onPageChange: (newPage) => setPage(newPage),
                onPageSizeChange: (newSize) => {
                  setPageSize(newSize);
                  setPage(1);
                },
              }
            : undefined
        }
      />

      {/* Create Announcement Modal */}
      <Modal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        title="Broadcast Announcement"
        description="Publish a notice to all students or target a specific cohort batch."
        size="md"
      >
        <form
          onSubmit={(e) => {
            e.preventDefault();
            createMutation.mutate({
              title: formData.title,
              content: formData.content,
              target_batch: formData.target_batch || undefined,
              priority: formData.priority,
              expires_at: formData.expires_at ? new Date(formData.expires_at).toISOString() : null,
              is_active: formData.is_active,
            });
          }}
          className="space-y-4"
        >
          <FormField label="Announcement Title" required>
            <Input
              placeholder="e.g. Scheduled Maintenance & Hackathon Announcement"
              value={formData.title}
              onChange={(e) => setFormData({ ...formData, title: e.target.value })}
              required
            />
          </FormField>

          <div className="grid grid-cols-2 gap-4">
            <FormField label="Target Cohort Batch (Optional)">
              <Input
                placeholder="e.g. BATCH-2025-A (leave blank for all)"
                value={formData.target_batch}
                onChange={(e) => setFormData({ ...formData, target_batch: e.target.value })}
              />
            </FormField>

            <FormField label="Priority Level">
              <Select
                value={formData.priority}
                onChange={(e) => setFormData({ ...formData, priority: e.target.value as any })}
              >
                <option value="LOW">Low</option>
                <option value="NORMAL">Normal</option>
                <option value="HIGH">High</option>
                <option value="URGENT">Urgent</option>
              </Select>
            </FormField>
          </div>

          <FormField label="Expiry Date (Optional)">
            <Input
              type="date"
              value={formData.expires_at}
              onChange={(e) => setFormData({ ...formData, expires_at: e.target.value })}
            />
          </FormField>

          <FormField label="Message Content" required>
            <Textarea
              rows={5}
              placeholder="Detailed announcement text..."
              value={formData.content}
              onChange={(e) => setFormData({ ...formData, content: e.target.value })}
              required
            />
          </FormField>

          <Checkbox
            label="Active and Visible Immediately"
            checked={formData.is_active}
            onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
          />

          <div className="mt-6 flex justify-end gap-3 pt-4 border-t border-surface-800">
            <Button variant="secondary" type="button" onClick={() => setIsCreateModalOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" isLoading={createMutation.isPending}>
              Broadcast Notice
            </Button>
          </div>
        </form>
      </Modal>

      {/* Edit Announcement Modal */}
      <Modal
        isOpen={Boolean(editingItem)}
        onClose={() => setEditingItem(null)}
        title="Edit Announcement"
        description="Modify notice message or target cohort."
        size="md"
      >
        <form
          onSubmit={(e) => {
            e.preventDefault();
            if (!editingItem) return;
            updateMutation.mutate({
              id: editingItem.id,
              payload: {
                title: formData.title,
                content: formData.content,
                target_batch: formData.target_batch || undefined,
                priority: formData.priority,
                expires_at: formData.expires_at ? new Date(formData.expires_at).toISOString() : null,
                is_active: formData.is_active,
              },
            });
          }}
          className="space-y-4"
        >
          <FormField label="Announcement Title" required>
            <Input
              value={formData.title}
              onChange={(e) => setFormData({ ...formData, title: e.target.value })}
              required
            />
          </FormField>

          <div className="grid grid-cols-2 gap-4">
            <FormField label="Target Cohort Batch">
              <Input
                placeholder="Leave blank for all"
                value={formData.target_batch}
                onChange={(e) => setFormData({ ...formData, target_batch: e.target.value })}
              />
            </FormField>

            <FormField label="Priority Level">
              <Select
                value={formData.priority}
                onChange={(e) => setFormData({ ...formData, priority: e.target.value as any })}
              >
                <option value="LOW">Low</option>
                <option value="NORMAL">Normal</option>
                <option value="HIGH">High</option>
                <option value="URGENT">Urgent</option>
              </Select>
            </FormField>
          </div>

          <FormField label="Expiry Date">
            <Input
              type="date"
              value={formData.expires_at}
              onChange={(e) => setFormData({ ...formData, expires_at: e.target.value })}
            />
          </FormField>

          <FormField label="Message Content" required>
            <Textarea
              rows={5}
              value={formData.content}
              onChange={(e) => setFormData({ ...formData, content: e.target.value })}
              required
            />
          </FormField>

          <Checkbox
            label="Active"
            checked={formData.is_active}
            onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
          />

          <div className="mt-6 flex justify-end gap-3 pt-4 border-t border-surface-800">
            <Button variant="secondary" type="button" onClick={() => setEditingItem(null)}>
              Cancel
            </Button>
            <Button type="submit" isLoading={updateMutation.isPending}>
              Save Changes
            </Button>
          </div>
        </form>
      </Modal>

      {/* Delete Confirmation */}
      <ConfirmDialog
        isOpen={Boolean(deletingItem)}
        onClose={() => setDeletingItem(null)}
        onConfirm={() => deletingItem && deleteMutation.mutate(deletingItem.id)}
        isLoading={deleteMutation.isPending}
        title="Delete Announcement?"
        message={`Are you sure you want to remove '${deletingItem?.title}' from the student bulletin?`}
        confirmText="Delete Notice"
        variant="danger"
      />
    </div>
  );
};
