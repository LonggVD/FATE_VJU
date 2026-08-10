import EventLogPage from "./EventLogPage";
import SavedSchedulesStubPage from "./SavedSchedulesStubPage";

// "Nhat ky & ban luu" - gop hai tab von gan nhu rong (EventLogPage 26 dong,
// SavedSchedulesStubPage 11 dong) nhung truoc day van chiem 2 cho ngang hang
// voi cac man that trong thanh dieu huong 10 muc.
//
// Thanh tab rieng da bi go - xem ghi chu trong DataPage. `key` khop voi children
// cua nhom "history" trong nav.js.
const PANES = {
  log: EventLogPage,
  saved: SavedSchedulesStubPage,
};

export default function HistoryPage({ role, sub }) {
  const Current = PANES[sub] ?? PANES.log;
  return <Current role={role} />;
}
