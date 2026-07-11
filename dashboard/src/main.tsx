import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import { QueryClientProvider } from "@tanstack/react-query";
import App from "./App";
import { AgentsProvider } from "./contexts/AgentsContext";
import { DeveloperProvider } from "./contexts/DeveloperContext";
import { KnowledgeBaseProvider } from "./contexts/KnowledgeBaseContext";
import { NotificationProvider } from "./contexts/NotificationContext";
import { AuthProvider } from "./contexts/AuthContext";
import { BillingProvider } from "./contexts/BillingContext";
import { EnvProvider } from "./contexts/EnvContext";
import { OrgProvider } from "./contexts/OrgContext";
import { ThemeProvider } from "./contexts/ThemeContext";
import { ToastProvider } from "./components/ui/Toast";
import { queryClient } from "./lib/queryClient";
import "./index.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <ThemeProvider>
          <ToastProvider>
            <AuthProvider>
              <EnvProvider>
                <OrgProvider>
                  <BillingProvider>
                    <AgentsProvider>
                      <KnowledgeBaseProvider>
                        <DeveloperProvider>
                          <NotificationProvider>
                            <App />
                          </NotificationProvider>
                        </DeveloperProvider>
                      </KnowledgeBaseProvider>
                    </AgentsProvider>
                  </BillingProvider>
                </OrgProvider>
              </EnvProvider>
            </AuthProvider>
          </ToastProvider>
        </ThemeProvider>
      </BrowserRouter>
    </QueryClientProvider>
  </React.StrictMode>,
);
