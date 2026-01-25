import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import { VoxeraProvider } from "./store/VoxeraContext";
import "./index.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <VoxeraProvider>
      <App />
    </VoxeraProvider>
  </React.StrictMode>
);
