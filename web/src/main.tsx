import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import { VoxeraProvider } from "./store/VoxeraContext";
import { ThemeProvider } from "./contexts/ThemeContext";
import "./index.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <ThemeProvider>
      <VoxeraProvider>
        <App />
      </VoxeraProvider>
    </ThemeProvider>
  </React.StrictMode>
);
