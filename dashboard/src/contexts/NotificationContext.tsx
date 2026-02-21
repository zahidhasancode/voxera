import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from "react";

export interface NotificationItem {
  id: string;
  type: "info" | "success" | "warning" | "error";
  title: string;
  message?: string;
  read: boolean;
  createdAt: string;
}

type NotificationContextValue = {
  notifications: NotificationItem[];
  unreadCount: number;
  markAsRead: (id: string) => void;
  markAllRead: () => void;
  addNotification: (n: Omit<NotificationItem, "id" | "read" | "createdAt">) => void;
  removeNotification: (id: string) => void;
};

const MOCK_NOTIFICATIONS: NotificationItem[] = [
  {
    id: "n1",
    type: "success",
    title: "Agent deployed",
    message: "Support Agent is now live in production.",
    read: false,
    createdAt: new Date(Date.now() - 3600000).toISOString(),
  },
  {
    id: "n2",
    type: "info",
    title: "Scheduled maintenance",
    message: "Planned maintenance on March 28, 02:00–04:00 UTC.",
    read: true,
    createdAt: new Date(Date.now() - 86400000).toISOString(),
  },
];

const NotificationContext = createContext<NotificationContextValue | null>(null);

export function NotificationProvider({ children }: { children: ReactNode }) {
  const [notifications, setNotifications] = useState<NotificationItem[]>(MOCK_NOTIFICATIONS);

  const unreadCount = useMemo(
    () => notifications.filter((n) => !n.read).length,
    [notifications]
  );

  const markAsRead = useCallback((id: string) => {
    setNotifications((prev) =>
      prev.map((n) => (n.id === id ? { ...n, read: true } : n))
    );
  }, []);

  const markAllRead = useCallback(() => {
    setNotifications((prev) => prev.map((n) => ({ ...n, read: true })));
  }, []);

  const addNotification = useCallback(
    (n: Omit<NotificationItem, "id" | "read" | "createdAt">) => {
      setNotifications((prev) => [
        {
          ...n,
          id: `n_${Date.now()}`,
          read: false,
          createdAt: new Date().toISOString(),
        },
        ...prev,
      ]);
    },
    []
  );

  const removeNotification = useCallback((id: string) => {
    setNotifications((prev) => prev.filter((n) => n.id !== id));
  }, []);

  const value = useMemo<NotificationContextValue>(
    () => ({
      notifications,
      unreadCount,
      markAsRead,
      markAllRead,
      addNotification,
      removeNotification,
    }),
    [
      notifications,
      unreadCount,
      markAsRead,
      markAllRead,
      addNotification,
      removeNotification,
    ]
  );

  return (
    <NotificationContext.Provider value={value}>
      {children}
    </NotificationContext.Provider>
  );
}

export function useNotifications() {
  const ctx = useContext(NotificationContext);
  if (!ctx) throw new Error("useNotifications must be used within NotificationProvider");
  return ctx;
}
