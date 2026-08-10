import { createContext, useCallback, useContext, useState } from "react";

const EventLogContext = createContext(null);

export function EventLogProvider({ children }) {
  const [entries, setEntries] = useState([]);

  const log = useCallback((message, type = "info") => {
    setEntries((prev) => [
      { id: prev.length ? prev[prev.length - 1].id + 1 : 1, message, type, at: prev.length },
      ...prev,
    ]);
  }, []);

  const clear = useCallback(() => setEntries([]), []);

  return (
    <EventLogContext.Provider value={{ entries, log, clear }}>
      {children}
    </EventLogContext.Provider>
  );
}

export function useEventLog() {
  const ctx = useContext(EventLogContext);
  if (!ctx) throw new Error("useEventLog phai dung trong EventLogProvider");
  return ctx;
}
