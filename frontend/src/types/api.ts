export interface PaginationMeta {
  page: number;
  page_size: number;
  total_records: number;
  total_pages: number;
  has_next: boolean;
  has_prev: boolean;
}

export interface ApiSuccessResponse<T> {
  success: true;
  data: T;
  meta: {
    pagination?: PaginationMeta;
    timestamp: string;
  };
}

export interface PaginatedResponse<T> {
  success: true;
  data: T[];
  meta: {
    pagination: PaginationMeta;
    timestamp: string;
  };
}

export interface ApiErrorResponse {
  success: false;
  error: {
    code: string;
    message: string;
    details: Record<string, string[] | string>;
    request_id: string;
  };
  meta: {
    timestamp: string;
  };
}
