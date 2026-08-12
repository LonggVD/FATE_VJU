// HOC CHUNG: nhieu lop (nhieu ma mon) thuc chat la MOT buoi day - mot thay, mot
// phong, mot khung gio, sinh vien cac ma mon ngoi chung.
//
// Backend la NGUON DUY NHAT quyet dinh dieu do (xem webapp/domain/hoc_chung.py):
// solver ep ca nhom cung slot va chi tinh mot phong. Frontend chi viec DUNG lai
// ket luan do de khong bao "trung giang vien" cho dung cai cap ma giao vu da noi
// ro la hoc chung.
//
// Moi cho quet trung gio o frontend phai di qua day (problemInbox:
// scanTeacherClashes + scanPlacedClashes, unplacedAnalysis) - sot mot cho la hop
// thu van de vs luoi noi hai chuyen khac nhau ve cung mot cap lop.

/** (a, b) => true neu HAI LOP LA CUNG MOT BUOI (hoc chung). */
export function taoCungBuoi(data) {
  const theoNhom = new Map();
  for (const c of data?.classes ?? []) {
    if (c.hocChungId != null) theoNhom.set(c.sectionId, c.hocChungId);
  }
  if (theoNhom.size === 0) return () => false; // khong co nhom nao - khoi tra cuu
  return (a, b) => a !== b && theoNhom.has(a) && theoNhom.get(a) === theoNhom.get(b);
}

/** Cac lop cung buoi voi sid (KHONG gom sid). [] neu khong hoc chung. */
export function banCungBuoi(data, sid) {
  const c = (data?.classes ?? []).find((x) => x.sectionId === sid);
  return c?.hocChungWith ?? [];
}
