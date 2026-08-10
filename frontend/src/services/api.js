// fetch wrapper mong - goi cung-origin qua Vite dev proxy (vite.config.js
// chuyen tiep /api/* sang Flask tren 127.0.0.1:5055), khong can CORS.
async function request(path, { method = "GET", body } = {}) {
  const res = await fetch(path, {
    method,
    headers: body ? { "Content-Type": "application/json" } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  });
  const json = await res.json().catch(() => null);
  if (!res.ok) {
    const message = json?.error || `Loi HTTP ${res.status}`;
    const err = new Error(message);
    // Gan status + body tren Error - /api/move-lesson tra ve 409 kem
    // {conflict: {...}} khi o do co van de va chua ghi ly do. Caller (drag-drop
    // handler) can doc duoc conflict de mo hop thoai, khong chi thay thong bao loi.
    err.status = res.status;
    err.body = json;
    throw err;
  }
  return json;
}

/** Tai file len (multipart). KHONG dat Content-Type - de trinh duyet tu sinh
 *  kem boundary; dat tay se lam Flask khong tach duoc phan file. */
export async function apiUpload(path, file, field = "file") {
  const form = new FormData();
  form.append(field, file);
  const res = await fetch(path, { method: "POST", body: form });
  const json = await res.json().catch(() => null);
  if (!res.ok) {
    const err = new Error(json?.error || `Loi HTTP ${res.status}`);
    err.status = res.status;
    err.body = json;
    throw err;
  }
  return json;
}

export const apiGet = (path) => request(path);
export const apiPost = (path, body) => request(path, { method: "POST", body });
export const apiPatch = (path, body) => request(path, { method: "PATCH", body });
export const apiDelete = (path) => request(path, { method: "DELETE" });
