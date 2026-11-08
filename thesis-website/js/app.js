// Main Application Coordinator & Routing
// Patriarchate Taxonomy Research Website (אתר מחקר שושלת הנשיאים)

import { initTabPrompts } from "./tab-prompts.js";
import { initTabViewer } from "./tab-viewer.js";
import { initTabFindings } from "./tab-findings.js";

document.addEventListener("DOMContentLoaded", () => {
  // Initialize Lucide icons
  if (window.lucide) {
    window.lucide.createIcons();
  }

  // Initialize Tab Modules
  initTabPrompts();
  initTabViewer();
  initTabFindings();

  // Setup Tab Navigation & Routing
  setupTabRouting();
});

function setupTabRouting() {
  const tabButtons = document.querySelectorAll(".tab-btn");
  const tabPanes = document.querySelectorAll(".tab-pane");

  function switchTab(tabId, updateHash = true) {
    // Update button states
    tabButtons.forEach((btn) => {
      const isTarget = btn.getAttribute("data-tab") === tabId;
      btn.classList.toggle("active", isTarget);
    });

    // Update pane visibility
    tabPanes.forEach((pane) => {
      const isTarget = pane.id === `pane-${tabId}`;
      pane.classList.toggle("active", isTarget);
    });

    // Re-render Lucide icons on newly visible elements
    if (window.lucide) {
      window.lucide.createIcons();
    }

    // Update URL hash
    if (updateHash) {
      window.location.hash = tabId.replace("tab-", "");
    }
  }

  // Attach click listeners
  tabButtons.forEach((btn) => {
    btn.addEventListener("click", () => {
      const tabId = btn.getAttribute("data-tab");
      switchTab(tabId, true);
    });
  });

  // Handle URL hash on initial load & popstate
  function handleHash() {
    const rawHash = (window.location.hash || "").replace("#", "").trim();
    if (rawHash === "prompts" || rawHash === "architecture") {
      switchTab("tab-prompts", false);
    } else if (rawHash === "viewer") {
      switchTab("tab-viewer", false);
    } else if (rawHash === "findings") {
      switchTab("tab-findings", false);
    } else {
      switchTab("tab-methodology", false);
    }
  }

  window.addEventListener("popstate", handleHash);
  handleHash();
}

