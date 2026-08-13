// Gop 1 map "{day}-{period}" -> true (o da click chon) thanh 1 danh sach
// slot int[] (slot = day*slotsPerDay+period) - dung gui thang cho
// updateManualTeacher(id, {availability}) (PATCH /api/manual/teacher/<id>),
// hoac cac endpoint khac nhan "danh sach slot phang" cung khuon.
// Khac ban goc AvailabilityGrid cua FE_SCHEDULE: khong gop thanh khung
// gio-bat-dau/gio-ket-thuc (backend nay khong can, chi can list slot roi rac).
export function submissionToWindowSlots(selectedCellsMap, slotsPerDay) {
  const slots = [];
  for (const key of Object.keys(selectedCellsMap)) {
    if (!selectedCellsMap[key]) continue;
    const [day, period] = key.split("-").map(Number);
    slots.push(day * slotsPerDay + period);
  }
  return slots.sort((a, b) => a - b);
}

export function windowSlotsToSelectedCellsMap(windowSlots = [], slotsPerDay) {
  const map = {};
  windowSlots.forEach((slot) => {
    const day = Math.floor(slot / slotsPerDay);
    const period = slot % slotsPerDay;
    map[`${day}-${period}`] = true;
  });
  return map;
}
