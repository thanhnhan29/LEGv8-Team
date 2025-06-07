document.addEventListener("DOMContentLoaded", () => {
  function forceRightPanelVisible() {
    console.log("FORCING right panel visibility...");

    const rightColumn = document.getElementById("right-column");
    if (!rightColumn) {
      console.error("RIGHT COLUMN NOT FOUND IN DOM");
      return;
    }

    // Force CSS display
    rightColumn.setAttribute(
      "style",
      "display: flex !important; flex: 1 !important; min-width: 280px !important; max-width: 400px !important; flex-direction: column !important; border: 2px solid red !important;"
    );

    // Check children
    const topPanel = document.getElementById("tabs-panel-top");
    const bottomPanel = document.getElementById("tabs-panel-bottom");
    const toggleButtonForTopPanel = document.getElementById(
      "toggle-cpu-state-button"
    ); // Check for the toggle button

    if (topPanel) {
      if (!toggleButtonForTopPanel) {
        // Only apply these styles if the toggle button doesn't exist
        topPanel.setAttribute(
          "style",
          "display: flex !important; flex: 1 !important; flex-direction: column !important; min-height: 200px !important; border: 1px solid blue !important;"
        );
        console.log(
          "Top panel styled by forceRightPanelVisible (as part of right column legacy)"
        );
      } else {
        console.log(
          "Top panel's visibility is controlled by toggle-cpu-state-button, forceRightPanelVisible skipping display style."
        );
      }
    } else {
      console.error("Top panel missing in forceRightPanelVisible!");
    }

    if (bottomPanel) {
      bottomPanel.setAttribute(
        "style",
        "display: flex !important; flex: 1 !important; flex-direction: column !important; min-height: 200px !important; border: 1px solid green !important;"
      );
      console.log("Bottom panel found and styled");
    } else {
      console.log("Bottom panel missing - will try to create it");
    }

    console.log("Force styling applied to right panel");
  }

  // Call this function immediately
  forceRightPanelVisible();
  const emergencyStyles = document.createElement("style");
  emergencyStyles.textContent = `
  .main-container {
    display: flex !important;
    flex-direction: row !important;
    width: 100% !important;
    height: 100vh !important;
  }
  
  #right-column {
    display: flex !important;
    flex: 1 !important;
    min-width: 280px !important;
    max-width: 400px !important;
    flex-direction: column !important;
  }
  
  /* MODIFIED SELECTOR: Only apply to #tabs-panel-top when it's a direct child of #right-column */
  #right-column > #tabs-panel-top, 
  #right-column > #tabs-panel-bottom {
    display: flex !important;
    flex: 1 !important;
    flex-direction: column !important;
    overflow: auto !important;
  }
  
  .tabs-container {
    display: flex !important;
    flex: 1 !important;
    flex-direction: column !important;
    overflow: hidden !important;
  }
  
  .tab-content {
    flex: 1 !important;
    overflow: auto !important;
  }
  
  .tab-content.active {
    display: block !important;
  }
  
  #tab-registers, #tab-memory, #tab-cpu-state, #tab-control-signals, #tab-log {
    padding: 10px;
    box-sizing: border-box;
  }
  
  .register-grid {
    display: grid;
    grid-template-columns: auto 1fr 1fr;
    gap: 5px;
  }
`;
  document.head.appendChild(emergencyStyles);

  // Add CSS for better path highlighting
  const highlightStyles = document.createElement("style");
  highlightStyles.textContent = `
    /* Path highlighting styles */
    .path-highlight {
      z-index: 1000 !important;
      position: relative !important;
      stroke-dasharray: none !important;
      opacity: 1 !important;
      pointer-events: auto !important;
    }
    
    .block-highlight {
      z-index: 500 !important;
      position: relative !important;
      opacity: 0.9 !important;
    }
    
    /* Ensure highlighted elements are above normal elements */
    svg path.path-highlight,
    svg line.path-highlight {
      z-index: 1000 !important;
      position: relative !important;
    }
    
    svg rect.block-highlight,
    svg g.block-highlight {
      z-index: 500 !important;
      position: relative !important;
    }
    
    /* Text animation styles */
    .signal-text-group {
      z-index: 1500 !important;
      position: relative !important;
      pointer-events: none !important;
      user-select: none !important;
    }
    
    .signal-text {
      z-index: 1500 !important;
      position: relative !important;
      pointer-events: none !important;
      user-select: none !important;
      font-family: 'Arial', sans-serif !important;
      font-weight: 900 !important; /* Extra bold for better visibility */
    }
    
    .signal-text-background {
      z-index: 1499 !important;
      position: relative !important;
      pointer-events: none !important;
      filter: drop-shadow(2px 2px 4px rgba(0,0,0,0.3)) !important;
    }
    
    /* Different colors for different data types with enhanced contrast */
    .signal-text-group[data-path-id*="pc"] .signal-text {
      fill: #1976D2 !important;
    }
    
    .signal-text-group[data-path-id*="pc"] .signal-text-background {
      fill: rgba(255, 255, 255, 0.95) !important;
      stroke: #1976D2 !important;
    }
    
    .signal-text-group[data-path-id*="instr"] .signal-text {
      fill: #FF9800 !important;
    }
    
    .signal-text-group[data-path-id*="instr"] .signal-text-background {
      fill: rgba(255, 255, 255, 0.95) !important;
      stroke: #FF9800 !important;
    }
    
    .signal-text-group[data-path-id*="reg"] .signal-text {
      fill: #4CAF50 !important;
    }
    
    .signal-text-group[data-path-id*="reg"] .signal-text-background {
      fill: rgba(255, 255, 255, 0.95) !important;
      stroke: #4CAF50 !important;
    }
    
    .signal-text-group[data-path-id*="alu"] .signal-text {
      fill: #E91E63 !important;
    }
    
    .signal-text-group[data-path-id*="alu"] .signal-text-background {
      fill: rgba(255, 255, 255, 0.95) !important;
      stroke: #E91E63 !important;
    }
    
    .signal-text-group[data-path-id*="mem"] .signal-text {
      fill: #9C27B0 !important;
    }
    
    .signal-text-group[data-path-id*="mem"] .signal-text-background {
      fill: rgba(255, 255, 255, 0.95) !important;
      stroke: #9C27B0 !important;
    }
    
    .signal-text-group[data-path-id*="mux"] .signal-text {
      fill: #FF5722 !important;
    }
    
    .signal-text-group[data-path-id*="mux"] .signal-text-background {
      fill: rgba(255, 255, 255, 0.95) !important;
      stroke: #FF5722 !important;
    }
    
    .signal-text-group[data-path-id*="control"] .signal-text {
      fill: #1976D2 !important;
    }
    
    .signal-text-group[data-path-id*="control"] .signal-text-background {
      fill: rgba(227, 242, 253, 0.95) !important;
      stroke: #1976D2 !important;
    }
  `;
  document.head.appendChild(highlightStyles);

  // --- Constants (Unchanged) ---
  const BITS_64 = 64n;
  const SIGN_BIT_64_MASK = 1n << (BITS_64 - 1n);
  const MAX_UNSIGNED_64 = (1n << BITS_64) - 1n;
  const TWO_POW_64 = 1n << BITS_64;

  // --- Element References ---
  const loadProgramButton = document.getElementById("load-program-button");
  const microStepButton = document.getElementById("micro-step-button");
  const fullInstructionButton = document.getElementById(
    "full-instruction-button"
  );
  const resetButton = document.getElementById("reset-button");
  const runPauseButton = document.getElementById("run-pause-button");
  const codeEditor = document.getElementById("code-editor");
  const codeDisplay = document.getElementById("code-display");
  const currentInstrDisplay = document.getElementById("current-instr-display");
  const microStepDisplay = document.getElementById("micro-step-display");
  const showAnimationsToggle = document.getElementById(
    "show-animations-toggle"
  );
  const svgObject = document.getElementById("datapath-svg-object");
  if (!svgObject) {
    console.error("SVG object reference not found! Check the ID in HTML.");
  } else if (!svgObject.getAttribute("data")) {
    console.error("SVG object has no 'data' attribute set! Check HTML.");
  } else {
    console.log("SVG source path:", svgObject.getAttribute("data"));
  }
  const uploadFileButton = document.getElementById("upload-file-button");
  const fileInput = document.getElementById("file-input");

  // Now you can safely log these
  console.log("SVG object reference:", svgObject);
  console.log("SVG source:", svgObject?.getAttribute("data"));
  // Add SVG status indicator
  const svgStatus = document.createElement("div");
  svgStatus.id = "svg-status";
  svgStatus.style =
    "position:fixed; bottom:10px; right:10px; padding:5px; background:rgba(0,0,0,0.7); color:white; z-index:1000;";
  svgStatus.textContent = "SVG: Not loaded";
  document.body.appendChild(svgStatus);

  function fixRightPanel() {
    console.log("Fixing right panel...");

    // Check if right column exists
    const rightColumn = document.getElementById("right-column");
    if (!rightColumn) {
      console.error("Right column not found in DOM");
      return;
    }
    ensureBottomPanel();
    // Force right column visibility
    rightColumn.style.display = "flex";
    rightColumn.style.flex = "1";
    rightColumn.style.minWidth = "280px";
    rightColumn.style.flexDirection = "column";

    // Check top panel and ensure it's visible
    const topPanel = document.getElementById("tabs-panel-top");
    if (topPanel) {
      topPanel.style.display = "flex";
      topPanel.style.flex = "1";
      topPanel.style.flexDirection = "column";
      topPanel.style.minHeight = "0";
      topPanel.style.overflow = "auto";
    }

    // Check if bottom panel exists and make it visible
    const bottomPanel = document.getElementById("tabs-panel-bottom");
    if (bottomPanel) {
      bottomPanel.style.display = "flex";
      bottomPanel.style.flex = "1";
      bottomPanel.style.flexDirection = "column";
      bottomPanel.style.minHeight = "0";
      bottomPanel.style.overflow = "auto";
    }

    // Fix for possibly missing tab content divs
    ensureTabContentExists();

    // Force display of active tabs
    document.querySelectorAll(".tab-content.active").forEach((tab) => {
      if (tab) tab.style.display = "block";
    });

    console.log("Right panel fix applied");
  }

  function ensureBottomPanel() {
    const rightColumn = document.getElementById("right-column");
    if (!rightColumn) return;

    // Check if bottom panel exists
    let bottomPanel = document.getElementById("tabs-panel-bottom");
    if (!bottomPanel) {
      // Create the bottom panel
      bottomPanel = document.createElement("div");
      bottomPanel.id = "tabs-panel-bottom";
      bottomPanel.className = "panel";

      // Add heading
      const heading = document.createElement("h2");
      heading.textContent = "Log";
      bottomPanel.appendChild(heading);

      // Append to right column
      rightColumn.appendChild(bottomPanel);

      console.log("Created missing bottom panel");
    }
  }
  // Add this function to ensure all tab content divs exist
  function ensureTabContentExists() {
    // Check if tab content divs exist and create them if missing
    const tabIds = [
      "registers",
      "memory",
      "cpu-state",
      "control-signals",
      "log",
    ];
    const topPanelTabs = [
      "registers",
      "memory",
      "cpu-state",
      "control-signals",
    ];
    const bottomPanelTabs = ["log"];

    const topPanel = document.getElementById("tabs-panel-top");
    const bottomPanel = document.getElementById("tabs-panel-bottom");

    // Create tab container in top panel if missing
    if (topPanel && !topPanel.querySelector(".tabs-container")) {
      const tabsContainer = document.createElement("div");
      tabsContainer.className = "tabs-container";

      // Create tab buttons container
      const tabButtons = document.createElement("div");
      tabButtons.className = "tab-buttons";

      // Create buttons for each top panel tab
      topPanelTabs.forEach((tabId, index) => {
        const button = document.createElement("button");
        button.className = "tab-button" + (index === 0 ? " active" : "");
        button.setAttribute("data-tab", tabId);
        button.setAttribute("data-panel", "top");
        button.textContent = tabId
          .split("-")
          .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
          .join(" ");
        tabButtons.appendChild(button);
      });

      tabsContainer.appendChild(tabButtons);

      // Create tab contents
      topPanelTabs.forEach((tabId, index) => {
        // Check if tab content already exists
        if (!document.getElementById(`tab-${tabId}`)) {
          const tabContent = document.createElement("div");
          tabContent.id = `tab-${tabId}`;
          tabContent.className = "tab-content" + (index === 0 ? " active" : "");
          tabContent.style.display = index === 0 ? "block" : "none";

          // Add specific content for each tab
          switch (tabId) {
            case "registers":
              tabContent.innerHTML =
                '<div id="register-display-grid" class="register-grid"></div>';
              break;
            case "memory":
              tabContent.innerHTML =
                '<pre id="tab-memory-content">(Load program to view memory)</pre>';
              break;
            case "cpu-state":
              tabContent.innerHTML =
                '<div><strong>PC:</strong> <span id="pc-value-display">N/A</span></div>';
              break;
            case "control-signals":
              tabContent.innerHTML = '<div id="control-signals-display"></div>';
              break;
          }

          tabsContainer.appendChild(tabContent);
        }
      });

      topPanel.appendChild(tabsContainer);
    }

    // If bottom panel exists but no tab container
    if (bottomPanel && !bottomPanel.querySelector(".tabs-container")) {
      const tabsContainer = document.createElement("div");
      tabsContainer.className = "tabs-container";

      // Create tab buttons container
      const tabButtons = document.createElement("div");
      tabButtons.className = "tab-buttons";

      // Create button for log tab
      const button = document.createElement("button");
      button.className = "tab-button active";
      button.setAttribute("data-tab", "log");
      button.setAttribute("data-panel", "bottom");
      button.textContent = "Log";
      tabButtons.appendChild(button);

      tabsContainer.appendChild(tabButtons);

      // Create log tab content if it doesn't exist
      if (!document.getElementById("tab-log")) {
        const tabContent = document.createElement("div");
        tabContent.id = "tab-log";
        tabContent.className = "tab-content active";
        tabContent.style.display = "block";
        tabContent.style.whiteSpace = "pre-wrap";
        tabContent.textContent =
          "Load a program using the 'Compile Code' button or 'Upload File'.\n";

        tabsContainer.appendChild(tabContent);
      }

      bottomPanel.appendChild(tabsContainer);
    }
  }
  // --- Tab Elements (Specific IDs for content are key) ---
  // Content areas (IDs remain unique across panels)
  const registersTabContent = document.getElementById("tab-registers"); // In Top Panel
  const memoryTabContent = document.getElementById("tab-memory"); // In Top Panel
  const cpuStateTabContent = document.getElementById("tab-cpu-state"); // In Top Panel
  const controlSignalsTabContent = document.getElementById(
    "tab-control-signals"
  ); // In Top Panel

  function updateTabReferences() {
    // Update tab content references after ensuring they exist
    const registersTabContent = document.getElementById("tab-registers");
    const memoryTabContent = document.getElementById("tab-memory");
    const cpuStateTabContent = document.getElementById("tab-cpu-state");
    const controlSignalsTabContent = document.getElementById(
      "tab-control-signals"
    );
    const logTabContent = document.getElementById("tab-log");

    // Update structured display references
    const registerDisplayGrid = document.getElementById(
      "register-display-grid"
    );
    const pcValueDisplay = document.getElementById("pc-value-display");
    const controlSignalsDisplay = document.getElementById(
      "control-signals-display"
    );

    return {
      registersTabContent,
      memoryTabContent,
      cpuStateTabContent,
      controlSignalsTabContent,
      logTabContent,
      registerDisplayGrid,
      pcValueDisplay,
      controlSignalsDisplay,
    };
  }

  const logTabContent = document.getElementById("tab-log"); // In Bottom Panel

  // --- Element References for structured displays (IDs remain unique) ---
  const registerDisplayGrid = document.getElementById("register-display-grid");
  const pcValueDisplay = document.getElementById("pc-value-display");
  const controlSignalsDisplay = document.getElementById(
    "control-signals-display"
  );

  // --- Simulation State (Frontend - Unchanged) ---
  let svgDoc = null;
  let highlightedElements = new Set();
  let highlightedLineElement = null;
  let simulationLoaded = false;
  let isRunning = false;
  let runIntervalId = null;
  let currentMicroStepIndex = -1;
  let currentInstructionAddr = -1;
  let currentInstructionStr = "N/A";
  let animationSpeed = 0.3;
  const knownControlSignals = [
    "RegWrite",
    "ALUSrc",
    "MemRead",
    "MemWrite",
    "MemToReg",
    "Branch",
    "UncondBranch",
    "ALUOp",
  ];

  // --- Initial Code (Unchanged) ---
  codeEditor.value = `// Example program:\n// Or Upload a file (.S, .asm, .txt)\nADDI X1, XZR, #10    // X1 = 10\nADDI X2, XZR, #5     // X2 = 5\nloop:               \nADD X3, X1, X2       // X3 = X1 + X2 = 15\nSTUR X3, [SP, #8]    // Store X3 to Mem[SP+8]\nSUBI X2, X2, #1      // X2 = X2 - 1\nCBZ X2, end          // Branch if X2 is zero\nB loop               // Unconditional branch to loop\nend:                 \nADD X6, X6, #1       // Executed after loop finishes\n// End`;

  // --- GSAP Registration (Unchanged) ---
  gsap.registerPlugin(MotionPathPlugin);
  console.log("GSAP and MotionPathPlugin registered.");

  // --- Helper Functions (Most remain unchanged, except for tab initialization) ---
  function updateStatus(message, isError = false) {
    /* Unchanged */
    console.log(`Status: ${message}`);
    if (isError) console.error(message);
  }

  function updateLog(message) {
    /* Unchanged - targets specific logTabContent ID */
    if (logTabContent) {
      logTabContent.textContent += message + "\n";
      logTabContent.scrollTop = logTabContent.scrollHeight;
    }
  }

  function clearLog() {
    /* Unchanged */
    if (logTabContent) logTabContent.textContent = "";
  }

  function parseAddress(addr) {
    /* Unchanged */
    if (addr === null || addr === undefined) return NaN;
    if (typeof addr === "number") return addr;
    if (typeof addr === "string") {
      if (addr.toLowerCase().startsWith("0x")) {
        try {
          return Number(BigInt(addr));
        } catch (e) {
          return NaN;
        }
      } else {
        const num = parseInt(addr, 10);
        return isNaN(num) ? NaN : num;
      }
    }
    if (typeof addr === "bigint") {
      return Number(addr);
    }
    return NaN;
  }

  function updateCpuStateTabs(state) {
    /* Unchanged - targets specific element IDs */
    if (!state) {
      /* ... (rest of function is identical) ... */ return;
    }

    // --- Registers Tab ---
    if (state.registers && registerDisplayGrid) {
      registerDisplayGrid.innerHTML = ""; // Clear previous grid content
      const headerName = document.createElement("div");
      headerName.textContent = "Reg";
      headerName.style.fontWeight = "bold";
      const headerHex = document.createElement("div");
      headerHex.textContent = "Hex Value";
      headerHex.style.fontWeight = "bold";
      const headerDec = document.createElement("div");
      headerDec.textContent = "Decimal (Signed)";
      headerDec.style.fontWeight = "bold";
      registerDisplayGrid.append(headerName, headerHex, headerDec);

      // Define the desired display order
      const displayOrder = ["FP", "SP", "LR", "XZR"];
      for (let i = 0; i < 28; i++) {
        // X0 through X27
        displayOrder.push(`X${i}`);
      }

      displayOrder.forEach((name) => {
        if (state.registers.hasOwnProperty(name)) {
          const valueStr = state.registers[name];
          const nameDiv = document.createElement("div");
          nameDiv.textContent = name;
          nameDiv.classList.add("register-name");
          let hexVal = "N/A";
          const hexMatch = String(valueStr).match(/^(0x[0-9A-Fa-f]+)/i);
          if (hexMatch) {
            hexVal = hexMatch[1];
          } else if (String(valueStr).match(/^[0-9]+$/)) {
            try {
              hexVal = "0x" + BigInt(valueStr).toString(16).toUpperCase();
            } catch {
              hexVal = valueStr;
            }
          } else {
            hexVal = valueStr;
          }
          const hexDiv = document.createElement("div");
          hexDiv.textContent = hexVal;
          hexDiv.classList.add("register-hex");

          let signedDecVal = "";
          try {
            const hexStringForBigInt = hexVal.startsWith("0x")
              ? hexVal
              : "0x" + hexVal;
            if (
              hexStringForBigInt.toUpperCase() === "0XN/A" ||
              hexStringForBigInt === "0x"
            ) {
              signedDecVal = "N/A";
            } else {
              const bigIntValue = BigInt(hexStringForBigInt);
              if ((bigIntValue & SIGN_BIT_64_MASK) !== 0n) {
                signedDecVal = (bigIntValue - TWO_POW_64).toString();
              } else {
                signedDecVal = bigIntValue.toString();
              }
            }
          } catch (e) {
            console.error(
              `Error converting hex '${hexVal}' to signed decimal for register ${name}:`,
              e
            );
            signedDecVal = "Error";
          }
          const decDiv = document.createElement("div");
          decDiv.textContent = signedDecVal;
          decDiv.classList.add("register-dec");
          registerDisplayGrid.append(nameDiv, hexDiv, decDiv);
        }
      });
    } else if (registerDisplayGrid) {
      registerDisplayGrid.innerHTML = "<div>(No registers data)</div>";
    }

    // --- Memory Tab ---
    if (state.data_memory && memoryTabContent) {
      let memHtml = "";
      const memEntries = Object.entries(state.data_memory);
      if (memEntries.length === 0) {
        memHtml = "(Memory Empty)";
      } else {
        memEntries.sort((a, b) => parseAddress(a[0]) - parseAddress(b[0]));
        memEntries.forEach(([addrStr, valStr]) => {
          const addrNum = parseAddress(addrStr);
          const addrHex = isNaN(addrNum)
            ? addrStr
            : `0x${addrNum.toString(16).toUpperCase()}`;
          let displayMemContent = valStr;
          const memHexMatch = String(valStr).match(/^(0x[0-9A-Fa-f]+)/i);
          if (memHexMatch) {
            const memHexVal = memHexMatch[1];
            try {
              const memBigIntValue = BigInt(memHexVal);
              let memSignedDecVal;
              if ((memBigIntValue & SIGN_BIT_64_MASK) !== 0n) {
                memSignedDecVal = (memBigIntValue - TWO_POW_64).toString();
              } else {
                memSignedDecVal = memBigIntValue.toString();
              }
              displayMemContent = `${memHexVal} (${memSignedDecVal})`;
            } catch (e) {
              console.warn(
                `Error converting memory hex '${memHexVal}' to signed decimal:`,
                e
              );
              displayMemContent = memHexVal + " (Error)";
            }
          }
          memHtml += `Mem[${addrHex.padEnd(18)}]: ${displayMemContent}\n`;
        });
      }
      memoryTabContent.textContent = memHtml;
    } else if (memoryTabContent) {
      memoryTabContent.textContent = "(No memory data)";
    }

    // --- CPU State Tab (PC) ---
    if (pcValueDisplay) {
      const pcAddr = parseAddress(state.pc);
      pcValueDisplay.textContent = isNaN(pcAddr)
        ? state.pc || "N/A"
        : `0x${pcAddr.toString(16).toUpperCase()}`;
    }
  }

  function initializeControlSignalsDisplay() {
    /* Unchanged */
    if (!controlSignalsDisplay) return;
    controlSignalsDisplay.innerHTML = "";
    knownControlSignals.forEach((signalName) => {
      const div = document.createElement("div");
      div.classList.add("control-signal");
      const nameSpan = document.createElement("span");
      nameSpan.classList.add("control-signal-name");
      nameSpan.textContent = signalName + ":";
      const valueSpan = document.createElement("span");
      valueSpan.classList.add("control-signal-value");
      valueSpan.id = `signal-value-${signalName.toLowerCase()}`;
      valueSpan.textContent = "-";
      valueSpan.classList.add("inactive");
      div.appendChild(nameSpan);
      div.appendChild(valueSpan);
      controlSignalsDisplay.appendChild(div);
    });
  }

  function resetAllSvgStyles() {
    /* Reset highlights but keep persistent text animations */
    if (!svgDoc) {
      console.warn("resetAllSvgStyles: No SVG document available");
      return;
    }

    try {
      highlightedElements.clear();
      const dots = svgDoc.querySelectorAll(".signal-dot");
      dots.forEach((dot) => dot.remove());

      // DON'T remove persistent text elements here - only remove on full reset
      // const persistentTexts = svgDoc.querySelectorAll(".signal-text");
      // persistentTexts.forEach((text) => text.remove());

      const elements = svgDoc.querySelectorAll(
        "path[id], line[id], rect[id], g[id]"
      );

      if (elements.length === 0) {
        console.warn("No SVG elements found with IDs - verify SVG structure");
        updateLog("Warning: SVG visualization may not be properly loaded");
      }

      elements.forEach((el) => {
        // Remove highlight classes
        el.classList.remove("path-highlight", "block-highlight");

        // Handle group elements
        if (el.tagName.toLowerCase() === "g") {
          const children = el.querySelectorAll(
            "rect, path, circle, ellipse, line"
          );
          children.forEach((child) => {
            child.classList.remove("path-highlight", "block-highlight");
            // Reset to original styles by removing inline styles
            child.style.stroke = "";
            child.style.strokeWidth = "";
            child.style.fill = "";
            child.style.transition = "none";
          });
        } else {
          // Reset individual elements by removing inline styles
          el.style.stroke = "";
          el.style.strokeWidth = "";
          el.style.fill = "";
          el.style.transition = "none";
        }
      });

      // Re-enable transitions after reset
      setTimeout(() => {
        elements.forEach((el) => {
          if (el.tagName.toLowerCase() === "g") {
            const children = el.querySelectorAll(
              "rect, path, circle, ellipse, line"
            );
            children.forEach((child) => {
              child.style.transition =
                "stroke 0.15s linear, stroke-width 0.15s linear, fill 0.15s linear";
            });
          } else {
            el.style.transition =
              "stroke 0.15s linear, stroke-width 0.15s linear, fill 0.15s linear";
          }
        });
      }, 50);
    } catch (err) {
      console.error("Error in resetAllSvgStyles:", err);
    }
  }

  function addMissingIds() {
    if (!svgDoc || !svgDoc.documentElement) {
      console.warn("Cannot add missing IDs - SVG document not available");
      return false;
    }

    // Check if we already have elements with IDs
    const elementsWithId = svgDoc.querySelectorAll("[id]");
    if (elementsWithId.length > 0) {
      console.log("SVG already has elements with IDs, not modifying");
      return false;
    }

    try {
      // Find likely elements and add IDs
      const rects = svgDoc.querySelectorAll("rect");
      if (rects.length > 0) {
        // Sort rectangles by x position (left to right)
        const rectArray = Array.from(rects);
        rectArray.sort((a, b) => {
          return (
            parseFloat(a.getAttribute("x") || 0) -
            parseFloat(b.getAttribute("x") || 0)
          );
        });

        // Assign IDs to first few rectangles as common components
        const commonIds = [
          "PC",
          "InstructionMemory",
          "Registers",
          "ALU",
          "DataMemory",
          "Control",
        ];
        rectArray
          .slice(0, Math.min(rectArray.length, commonIds.length))
          .forEach((rect, i) => {
            rect.setAttribute("id", commonIds[i]);
            console.log(
              `Added ID "${commonIds[i]}" to rectangle at (${rect.getAttribute(
                "x"
              )}, ${rect.getAttribute("y")})`
            );
          });

        // Add IDs to paths
        const paths = svgDoc.querySelectorAll("path");
        paths.forEach((path, i) => {
          path.setAttribute("id", `path-${i + 1}`);
        });

        // Add IDs to lines
        const lines = svgDoc.querySelectorAll("line");
        lines.forEach((line, i) => {
          line.setAttribute("id", `line-${i + 1}`);
        });

        return true;
      }

      return false;
    } catch (e) {
      console.error("Error adding missing IDs:", e);
      return false;
    }
  }

  function mapSvgId(id) {
    // NO MAPPING NEEDED - Backend IDs already match SVG IDs exactly
    // Just return the original ID since they're designed to match
    return id;
  }

  // LEGv8-specific highlighting patterns based on instruction type and pipeline stage
  function detectInstructionType(instrStr) {
    if (!instrStr) return "UNKNOWN";

    const instr = instrStr.toUpperCase().trim();

    // R-Type instructions (register-register operations)
    if (/^(ADD|SUB|AND|ORR|EOR|LSL|LSR|ASR)\s+X/.test(instr)) return "R-TYPE";

    // I-Type instructions (immediate operations)
    if (/^(ADDI|SUBI|ANDI|ORRI|EORI)\s+X/.test(instr)) return "I-TYPE";

    // Load instructions
    if (/^LDUR\s+X/.test(instr)) return "LOAD";

    // Store instructions
    if (/^STUR\s+X/.test(instr)) return "STORE";

    // Branch instructions
    if (/^(CBZ|CBNZ|B\.EQ|B\.NE|B\.LT|B\.LE|B\.GT|B\.GE|B)\s/.test(instr))
      return "BRANCH";

    // Move instructions
    if (/^(MOVZ|MOVK)\s+X/.test(instr)) return "MOVE";

    return "UNKNOWN";
  }

  function getLegv8HighlightPattern(instructionType, stage) {
    const patterns = {
      // === R-TYPE INSTRUCTIONS (ADD, SUB, AND, OR) ===
      "R-TYPE": {
        fetch: {
          active_blocks: ["block-pc", "block-imem", "block-pcadder"],
          active_paths: ["path-pc-imem", "path-pc-pcadder"],
          description: "Fetch instruction from memory",
        },
        decode: {
          active_blocks: [
            "block-control",
            "block-registers",
            "block-reg2locmux",
          ],
          active_paths: [
            "path-instr-control",
            "path-instr-reg1",
            "path-instr-reg2mux",
          ],
          control_signals: ["RegWrite", "ALUSrc", "ALUOp"],
          description: "Decode instruction and read registers",
        },
        execute: {
          active_blocks: ["block-alu", "block-alucontrol", "block-alusrcmux"],
          active_paths: [
            "path-reg1-alu",
            "path-reg2-alumux",
            "path-alumux-alu",
          ],
          description: "Perform ALU operation",
        },
        memory: {
          // R-type doesn't use memory
          active_blocks: [],
          active_paths: [],
          description: "Memory stage (not used for R-type)",
        },
        writeback: {
          active_blocks: ["block-registers", "block-memtoregmux"],
          active_paths: ["path-alu-memtoregmux", "path-memtoregmux-writereg"],
          description: "Write result back to register",
        },
      },

      // === LOAD INSTRUCTIONS (LDUR) ===
      LOAD: {
        memory: {
          active_blocks: ["block-dmem"],
          active_paths: ["path-alu-dmem-addr", "path-dmem-memtoregmux"],
          control_signals: ["MemRead"],
        },
      },

      // === STORE INSTRUCTIONS (STUR) ===
      STORE: {
        memory: {
          active_blocks: ["block-dmem"],
          active_paths: ["path-alu-dmem-addr", "path-reg2-dmem-data"],
          control_signals: ["MemWrite"],
        },
        writeback: {
          // Store doesn't write back to register
          active_blocks: [],
          active_paths: [],
        },
      },

      // === BRANCH INSTRUCTIONS (CBZ, B) ===
      BRANCH: {
        execute: {
          active_blocks: [
            "block-alu",
            "block-shiftleft",
            "block-branchadder",
            "block-andgate",
          ],
          active_paths: [
            "path-signext-shiftleft",
            "path-shiftleft-branchadder",
          ],
          control_signals: ["Branch"],
        },
      },
    };

    return (
      patterns[instructionType]?.[stage] || {
        active_blocks: [],
        active_paths: [],
        control_signals: [],
        description: `${instructionType} ${stage} (pattern not defined)`,
      }
    );
  }

  // Animation error tracking
  let animationErrorCount = 0;
  const MAX_ANIMATION_ERRORS = 10000;

  function handleAnimationError(errorMessage) {
    animationErrorCount++;
    console.warn(
      `Animation error ${animationErrorCount}/${MAX_ANIMATION_ERRORS}: ${errorMessage}`
    );

    if (animationErrorCount >= MAX_ANIMATION_ERRORS) {
      console.warn("Too many animation errors, disabling animations");
      showAnimationsToggle.checked = false;
      updateLog("Warning: Animations disabled due to repeated errors");
      animationErrorCount = 0; // Reset counter
    }
  }

  function calculateTextOffset(pathElement) {
    // Calculate offset to position text above the path to avoid overlap
    try {
      const pathLength = pathElement.getTotalLength();
      const midPoint = pathElement.getPointAtLength(pathLength / 2);
      const startPoint = pathElement.getPointAtLength(0);
      const endPoint = pathElement.getPointAtLength(pathLength);

      // Calculate path direction and perpendicular offset
      const deltaX = endPoint.x - startPoint.x;
      const deltaY = endPoint.y - startPoint.y;
      const pathAngle = Math.atan2(deltaY, deltaX);

      // Offset perpendicular to path direction (above the path)
      const offsetDistance = 15; // Distance above path
      const offsetX = -Math.sin(pathAngle) * offsetDistance;
      const offsetY = Math.cos(pathAngle) * offsetDistance;

      return { x: offsetX, y: offsetY };
    } catch (e) {
      return { x: 0, y: -15 }; // Default offset above
    }
  }

  function createSignalText(svgDoc, text, pathId) {
    if (!svgDoc) return null;

    // Create a group to hold background and text
    const textGroup = svgDoc.createElementNS("http://www.w3.org/2000/svg", "g");
    textGroup.classList.add("signal-text-group");
    textGroup.setAttribute("data-path-id", pathId);

    // Create background rectangle
    const backgroundRect = svgDoc.createElementNS(
      "http://www.w3.org/2000/svg",
      "rect"
    );
    backgroundRect.classList.add("signal-text-background");
    backgroundRect.setAttribute("fill", "rgba(255, 255, 255, 0.9)");
    backgroundRect.setAttribute("stroke", "#333333");
    backgroundRect.setAttribute("stroke-width", "1");
    backgroundRect.setAttribute("rx", "3"); // Rounded corners
    backgroundRect.setAttribute("ry", "3");

    // Create text element with enhanced styling
    const textElement = svgDoc.createElementNS(
      "http://www.w3.org/2000/svg",
      "text"
    );
    textElement.classList.add("signal-text");
    textElement.setAttribute("font-family", "Arial, sans-serif");
    textElement.setAttribute("font-size", "12");
    textElement.setAttribute("font-weight", "bold");
    textElement.setAttribute("fill", "#FF5722");
    textElement.setAttribute("text-anchor", "middle");
    textElement.setAttribute("dominant-baseline", "middle");
    textElement.textContent = text || "DATA";

    // Add background first, then text (so text appears on top)
    textGroup.appendChild(backgroundRect);
    textGroup.appendChild(textElement);

    // Calculate background size based on text content
    setTimeout(() => {
      try {
        const bbox = textElement.getBBox();
        const padding = 4;
        backgroundRect.setAttribute("x", bbox.x - padding);
        backgroundRect.setAttribute("y", bbox.y - padding);
        backgroundRect.setAttribute("width", bbox.width + padding * 2);
        backgroundRect.setAttribute("height", bbox.height + padding * 2);
      } catch (e) {
        // Fallback if getBBox fails
        const textLength = (text || "DATA").length;
        const estimatedWidth = textLength * 8;
        const estimatedHeight = 16;
        backgroundRect.setAttribute("x", -estimatedWidth / 2 - 2);
        backgroundRect.setAttribute("y", -estimatedHeight / 2 - 2);
        backgroundRect.setAttribute("width", estimatedWidth + 4);
        backgroundRect.setAttribute("height", estimatedHeight + 4);
      }
    }, 10);

    return textGroup;
  }

  function animateSignalText(pathElement, signal, svgDoc) {
    if (!svgDoc || !pathElement || !signal) {
      console.warn("Missing parameters for signal animation");
      return;
    }

    // Reset animation error counter on successful starts
    if (animationErrorCount > 0) {
      animationErrorCount = Math.max(0, animationErrorCount - 1);
    }

    // Validate path element
    if (!pathElement.getTotalLength) {
      console.warn(
        "Path element does not support getTotalLength - skipping animation"
      );
      handleAnimationError("Path element doesn't support getTotalLength");
      return;
    }

    // Remove existing text animations on the same path
    const currentPathId = signal.path_id;
    const existingTexts = svgDoc.querySelectorAll(
      `.signal-text-group[data-path-id="${currentPathId}"]`
    );
    existingTexts.forEach((existingText) => {
      console.log(`🗑️ Removing existing text on path: ${currentPathId}`);
      existingText.remove();
    });

    try {
      const pathLength = pathElement.getTotalLength();
      if (pathLength <= 0) {
        console.warn("Path has zero length - skipping animation");
        handleAnimationError("Path has zero length");
        return;
      }
    } catch (e) {
      console.warn("Invalid path element for animation:", e.message);
      handleAnimationError(`Invalid path element: ${e.message}`);
      return;
    }

    // Determine text content based on path ID
    const pathId = signal.path_id;
    let animationText = "DATA";

    // Map path IDs to appropriate text labels
    const textMap = {
      "path-pc-imem": "PC",
      "path-pc-adder1": "PC",
      "path-imem-out": "INSTR",
      "path-instr-control": "OPCODE",
      "path-instr-regs": "REG_ADDR",
      "path-regs-rdata1": "REG1_DATA",
      "path-regs-rdata2": "REG2_DATA",
      "path-instr-signext": "IMM",
      "path-signext-out-mux2": "SIGN_EXT",
      "path-mux2-alu": "ALU_IN2",
      "path-rdata1-alu": "ALU_IN1",
      "path-alu-result": "ALU_OUT",
      "path-alu-zero": "ZERO",
      "path-mem-readdata": "MEM_DATA",
      "path-mux3-wb": "WB_DATA",
      "path-adder1-mux4-in0": "PC+4",
      "path-mux4-pc": "NEXT_PC",
      "path-rdata2-memwrite": "STORE_DATA",
      "path-signext-br-shift": "BR_OFFSET",
      "path-pc-adder2": "PC",
      "path-adder2-mux4-in1": "BR_TARGET",
    };

    animationText = signal.bits;

    // Slower, more cinematic animation speed
    const duration = 5 || 2.0; // Increased duration for slower movement
    const startDelay = signal.start_delay || 0;

    // Create text element
    const textElement = createSignalText(svgDoc, animationText, pathId);
    if (!textElement) return;

    try {
      svgDoc.documentElement.appendChild(textElement);
      console.log(`Created signal text "${animationText}" for path: ${pathId}`);

      // Get path start position with offset to avoid overlap
      const startPoint = pathElement.getPointAtLength(0);
      const offset = calculateTextOffset(pathElement);

      gsap
        .timeline({
          onComplete: () => {
            // Don't remove text element - keep it persistent
            console.log(
              `Text "${animationText}" animation completed, keeping persistent`
            );
          },
          onError: (error) => {
            console.warn("GSAP text animation error:", error);
            handleAnimationError(`GSAP error: ${error.message || error}`);
            if (textElement && textElement.parentNode) {
              textElement.remove();
            }
          },
        })
        .set(textElement, {
          x: startPoint.x + offset.x,
          y: startPoint.y + offset.y,
          opacity: 0,
          scale: 0.8,
          immediateRender: true,
        })
        .to(textElement, {
          delay: startDelay,
          opacity: 1,
          scale: 1,
          duration: 0.4,
          ease: "back.out(1.7)",
        })
        .to(
          textElement,
          {
            duration: duration,
            motionPath: {
              path: pathElement,
              autoRotate: false,
              alignOrigin: [0.5, 0.5],
            },
            ease: "power1.inOut", // Smoother, more linear easing
            onError: (error) => {
              console.warn("Motion path text animation error:", error);
              handleAnimationError(
                `Motion path error: ${error.message || error}`
              );
            },
          },
          "-=0.2"
        )
        .to(
          textElement,
          {
            // Keep text visible at the end position
            opacity: 0.8, // Slightly transparent to indicate completion
            scale: 0.9,
            duration: 0.3,
            ease: "power2.out",
          },
          ">-0.1"
        );
    } catch (e) {
      console.warn("Error creating GSAP text animation:", e.message);
      handleAnimationError(`GSAP creation error: ${e.message}`);
      if (textElement && textElement.parentNode) {
        textElement.remove();
      }
    }
  }

  function applyHighlightsAndAnimations(stepData) {
    if (!svgDoc) {
      console.warn("Cannot apply highlights - SVG document not available");
      return;
    }

    if (!stepData) {
      console.warn("Cannot apply highlights - Step data is missing");
      return;
    }

    // Reset all styles before applying new highlights
    resetAllSvgStyles();

    // *** LEGv8-SPECIFIC ENHANCEMENT ***
    // Determine instruction type and get LEGv8-specific patterns
    const instrType = detectInstructionType(
      stepData.current_instruction_string || currentInstructionStr
    );
    const stage = stepData.stage?.toLowerCase() || "fetch";
    const legv8Pattern = getLegv8HighlightPattern(instrType, stage);

    console.log(`LEGv8 Enhancement: ${instrType} - ${stage.toUpperCase()}`);
    console.log(`LEGv8 Pattern:`, legv8Pattern);

    let foundElements = 0;
    let missingElements = 0;

    // *** COMBINE BACKEND DATA + LEGv8 PATTERNS ***
    // Merge backend data with LEGv8-specific patterns for more accurate highlighting
    const allActiveBlocks = [
      ...(stepData.active_blocks || []),
      ...(legv8Pattern.active_blocks || []),
    ];

    const allActivePaths = [
      ...(stepData.active_paths || []),
      ...(legv8Pattern.active_paths || []),
    ];

    // Remove duplicates
    const uniqueActiveBlocks = [...new Set(allActiveBlocks)];
    const uniqueActivePaths = [...new Set(allActivePaths)];

    console.log(
      `Highlighting ${uniqueActiveBlocks.length} blocks and ${uniqueActivePaths.length} paths`
    );

    // Move highlighted paths to front (for better visibility)
    bringPathsToFront(uniqueActivePaths);

    // Apply block highlights with mapping
    uniqueActiveBlocks.forEach((id) => {
      const mappedId = mapSvgId(id);
      let el = svgDoc.getElementById(mappedId);
      console.log(mappedId);
      // If not found directly, try to find within groups
      if (!el) {
        // Look for the element within groups
        const groups = svgDoc.querySelectorAll("g");
        for (let group of groups) {
          if (group.id === mappedId) {
            el = group;
            break;
          }
          // Also check children within groups
          const childEl = group.querySelector(`#${mappedId}`);
          if (childEl) {
            el = childEl;
            break;
          }
        }
      }

      if (el) {
        foundElements++;

        // Handle group elements differently
        if (el.tagName.toLowerCase() === "g") {
          // Highlight all child elements in the group
          const children = el.querySelectorAll("rect, path, circle, ellipse");
          children.forEach((child) => {
            child.classList.add("block-highlight");
            child.style.fill = "rgba(233, 30, 99, 0.15)";
            child.style.stroke = "#e91e63";
            child.style.strokeWidth = "2";
          });
        } else {
          // Single element highlight
          el.classList.add("block-highlight");
          el.style.fill = "rgba(233, 30, 99, 0.15)";
          el.style.stroke = "#e91e63";
          el.style.strokeWidth = "2";
        }

        console.log(`Highlighting block: ${id} → ${mappedId}`);
      } else {
        missingElements++;
        console.warn(`SVG Block ID not found: ${id} (mapped to ${mappedId})`);
      }
    });

    // Apply path highlights with mapping
    uniqueActivePaths.forEach((id) => {
      const mappedId = mapSvgId(id); // Now actually uses mapping!
      let el = svgDoc.getElementById(mappedId);

      // If not found directly, try to find within groups
      if (!el) {
        const groups = svgDoc.querySelectorAll("g");
        for (let group of groups) {
          if (group.id === mappedId) {
            el = group;
            break;
          }
          const childEl = group.querySelector(`#${mappedId}`);
          if (childEl) {
            el = childEl;
            break;
          }
        }
      }

      if (el) {
        foundElements++;

        // Handle group elements differently for paths
        if (el.tagName.toLowerCase() === "g") {
          // Highlight all path elements in the group
          const paths = el.querySelectorAll("path, line");
          paths.forEach((path) => {
            if (path.tagName.toLowerCase() !== "rect") {
              path.classList.add("path-highlight");
              path.style.stroke = "#e91e63";
              path.style.strokeWidth = "3";
              path.style.zIndex = "1000"; // Bring highlighted paths to front
              path.style.position = "relative"; // Enable z-index
            }
          });
        } else if (el.tagName.toLowerCase() !== "rect") {
          // Single path element highlight
          el.classList.add("path-highlight");
          el.style.stroke = "#e91e63";
          el.style.strokeWidth = "3";
          el.style.zIndex = "1000"; // Bring highlighted paths to front
          el.style.position = "relative"; // Enable z-index
        }

        console.log(`Highlighting path: ${id} → ${mappedId}`);
      } else {
        missingElements++;
        console.warn(`SVG Path ID not found: ${id} (mapped to ${mappedId})`);
      }
    });

    // Log statistics about highlight application
    if (missingElements > 0) {
      console.warn(
        `Missing ${missingElements} SVG elements for this step. Found: ${foundElements}`
      );
      if (foundElements === 0) {
        updateLog(
          "Warning: Visualization not updating - SVG element IDs may not match simulation"
        );
        svgStatus.textContent = `SVG: 0/${
          missingElements + foundElements
        } elements found`;
        svgStatus.style.backgroundColor = "rgba(255,0,0,0.7)";
      } else {
        svgStatus.textContent = `SVG: ${foundElements}/${
          missingElements + foundElements
        } elements found`;
        svgStatus.style.backgroundColor = "rgba(255,165,0,0.7)";
      }
    } else if (foundElements > 0) {
      svgStatus.textContent = `SVG: All ${foundElements} elements found`;
      svgStatus.style.backgroundColor = "rgba(0,128,0,0.7)";
    }

    // Handle animations with mapping - Text animation handling
    if (showAnimationsToggle.checked) {
      // Reset animation error counter when animations are enabled
      animationErrorCount = 0;

      // Create animations for backend signals if available
      if (stepData.animated_signals && stepData.animated_signals.length > 0) {
        stepData.animated_signals.forEach((signal) => {
          const mappedId = mapSvgId(signal.path_id);
          let pathElement = svgDoc.getElementById(mappedId);

          // If not found directly, try to find within groups
          if (!pathElement) {
            const groups = svgDoc.querySelectorAll("g");
            for (let group of groups) {
              if (group.id === mappedId) {
                // Use first path in the group for animation
                pathElement = group.querySelector("path, line");
                break;
              }
              const childEl = group.querySelector(`#${mappedId}`);
              if (
                childEl &&
                (childEl.tagName.toLowerCase() === "path" ||
                  childEl.tagName.toLowerCase() === "line")
              ) {
                pathElement = childEl;
                break;
              }
            }
          }

          if (pathElement) {
            // Additional safety check for path validity
            try {
              if (
                pathElement.getTotalLength &&
                pathElement.getTotalLength() > 0
              ) {
                // Use new text animation instead of dots
                animateSignalText(pathElement, signal, svgDoc);
                console.log(
                  `Animating signal text: ${signal.path_id} → ${mappedId}`
                );
              } else {
                console.warn(
                  `Path element found but invalid for animation: ${mappedId}`
                );
              }
            } catch (pathError) {
              console.warn(
                `Path element error for ${mappedId}:`,
                pathError.message
              );
            }
          } else {
            console.warn(
              `Animation path ID not found: ${signal.path_id} (mapped to ${mappedId})`
            );
          }
        });
      } else {
        // No backend signals, create animations for highlighted paths
        console.log(
          "No backend animated_signals, creating animations for highlighted paths"
        );

        uniqueActivePaths.forEach((pathId) => {
          const mappedId = mapSvgId(pathId);
          let pathElement = svgDoc.getElementById(mappedId);

          // If not found directly, try to find within groups
          if (!pathElement) {
            const groups = svgDoc.querySelectorAll("g");
            for (let group of groups) {
              if (group.id === mappedId) {
                pathElement = group.querySelector("path, line");
                break;
              }
              const childEl = group.querySelector(`#${mappedId}`);
              if (
                childEl &&
                (childEl.tagName.toLowerCase() === "path" ||
                  childEl.tagName.toLowerCase() === "line")
              ) {
                pathElement = childEl;
                break;
              }
            }
          }

          if (pathElement) {
            try {
              if (
                pathElement.getTotalLength &&
                pathElement.getTotalLength() > 0
              ) {
                // Create synthetic signal for path animation
                const syntheticSignal = {
                  path_id: pathId,
                  duration: 2.0,
                  start_delay: Math.random() * 0.5, // Random delay for variety
                };

                animateSignalText(pathElement, syntheticSignal, svgDoc);
                console.log(
                  `Creating synthetic text animation for path: ${pathId}`
                );
              }
            } catch (pathError) {
              console.warn(
                `Path error for synthetic animation ${mappedId}:`,
                pathError.message
              );
            }
          }
        });
      }
    }

    // Control signals update with LEGv8 enhancement
    const backendSignals = stepData.control_signals || {};
    const legv8Signals = legv8Pattern.control_signals || [];

    knownControlSignals.forEach((signalName) => {
      const valueSpan = document.getElementById(
        `signal-value-${signalName.toLowerCase()}`
      );
      if (valueSpan) {
        // Use backend data if available, otherwise check LEGv8 pattern
        let value = backendSignals[signalName];

        // If not in backend data but in LEGv8 pattern, mark as active
        if (value === undefined && legv8Signals.includes(signalName)) {
          value = 1; // LEGv8 pattern indicates this signal should be active
        }

        const displayValue =
          typeof value === "bigint" ? value.toString() : value;
        valueSpan.textContent = displayValue !== undefined ? displayValue : "-";
        valueSpan.classList.remove("active", "inactive", "other");

        if (displayValue === 1 || displayValue === "1") {
          valueSpan.classList.add("active");
        } else if (displayValue === 0 || displayValue === "0") {
          valueSpan.classList.add("inactive");
        } else if (displayValue !== undefined) {
          valueSpan.classList.add("other");
        } else {
          valueSpan.classList.add("inactive");
        }
      } else {
        console.warn(
          `Control signal display span not found for: ${signalName}`
        );
      }
    });
  }

  function updateMicroStepDisplay(index, stageName) {
    /* Unchanged */
    const totalSteps = 5;
    const displayIndex = index >= 0 ? index + 1 : 0;
    microStepDisplay.textContent = `${
      stageName || "Idle"
    } (${displayIndex}/${totalSteps})`;
  }

  function populateCodeDisplay(code) {
    /* Unchanged */
    if (!codeDisplay) return;
    codeDisplay.innerHTML = "";
    highlightedLineElement = null;
    const lines = code.split("\n");
    let currentAddr = 0;
    let lineAddrMap = {};

    lines.forEach((lineText, index) => {
      const span = document.createElement("span");
      span.classList.add("code-line");
      span.textContent = lineText.length > 0 ? lineText : "\u00A0";
      span.dataset.lineNumber = index;
      const trimmedLine = lineText.trim();
      const isComment = trimmedLine.startsWith("//");
      const isLabel = /^[a-zA-Z_][a-zA-Z0-9_]*:$/.test(trimmedLine);
      const isEmpty = trimmedLine === "";
      const isDirective = trimmedLine.startsWith(".");

      if (isComment) {
        span.classList.add("is-comment");
      } else if (isLabel) {
        span.classList.add("is-label");
      } else if (!isEmpty && !isDirective) {
        span.dataset.address = currentAddr;
        lineAddrMap[currentAddr] = index;
        currentAddr += 4;
      }
      codeDisplay.appendChild(span);
    });
    codeEditor.style.display = "none";
    codeDisplay.style.display = "block";
    console.log("Code display populated. Frontend address map:", lineAddrMap);
  }

  function highlightLine(addr) {
    /* Unchanged */
    if (!codeDisplay) return;
    const numericAddr = parseAddress(addr);
    if (highlightedLineElement) {
      highlightedLineElement.classList.remove("highlighted");
      highlightedLineElement = null;
    }
    if (isNaN(numericAddr) || numericAddr < 0) {
      return;
    }
    const targetLine = codeDisplay.querySelector(
      `.code-line[data-address="${numericAddr}"]`
    );
    if (targetLine) {
      targetLine.classList.add("highlighted");
      highlightedLineElement = targetLine;
      targetLine.scrollIntoView({
        behavior: "smooth",
        block: "nearest",
        inline: "nearest",
      });
    } else {
      console.warn(
        `Could not find code line element for address: 0x${numericAddr.toString(
          16
        )}`
      );
    }
  }

  function updateCurrentInstructionDisplay(addr, text) {
    /* Unchanged */
    const numericAddr = parseAddress(addr);
    const displayAddr =
      isNaN(numericAddr) || numericAddr < 0
        ? "N/A"
        : `0x${numericAddr.toString(16).toUpperCase()}`;
    currentInstrDisplay.textContent = `${displayAddr}: ${text || "N/A"}`;
    highlightLine(numericAddr);
  }

  function setSimulationState(loaded, running = false, error = null) {
    /* Unchanged */
    simulationLoaded = loaded;
    isRunning = running;
    microStepButton.disabled = !loaded || running || !!error;
    fullInstructionButton.disabled = !loaded || running || !!error;
    runPauseButton.disabled = !loaded || !!error;
    resetButton.disabled = running;
    loadProgramButton.disabled = running;
    uploadFileButton.disabled = running;

    if (error) {
      runPauseButton.textContent = "Run";
      runPauseButton.classList.remove("paused");
      runPauseButton.disabled = true;
      updateStatus(`Error: ${error}`, true);
      highlightLine(-1);
    } else if (running) {
      runPauseButton.textContent = "Pause";
      runPauseButton.classList.add("paused");
      updateStatus("Running...");
    } else if (loaded) {
      runPauseButton.textContent = "Run";
      runPauseButton.classList.remove("paused");
      updateStatus("Paused/Ready. Press Step or Run.");
      codeEditor.style.display = "none";
      codeDisplay.style.display = "block";
    } else {
      runPauseButton.textContent = "Run";
      runPauseButton.classList.remove("paused");
      runPauseButton.disabled = true;
      updateStatus("Load program or upload file to start.");
      currentInstrDisplay.textContent = "N/A";
      microStepDisplay.textContent = "Idle (0/5)";
      highlightLine(-1);
      codeEditor.style.display = "block";
      codeDisplay.style.display = "none";
    }
  }

  function stopAutoRun() {
    /* Unchanged */
    if (runIntervalId) {
      clearTimeout(runIntervalId);
      runIntervalId = null;
    }
    if (isRunning && simulationLoaded) {
      isRunning = false;
      setSimulationState(simulationLoaded, false);
      updateStatus("Execution paused by user.");
    } else if (isRunning) {
      isRunning = false;
    }
  }

  async function handleSingleMicroStep() {
    /* Unchanged */

    if (!simulationLoaded) return "error";
    if (!svgDoc) {
      console.warn("SVG document not ready - attempting to reload");
      try {
        svgDoc = svgObject.contentDocument;
        if (!svgDoc) {
          console.error("Could not access SVG document");
          updateLog(
            "Warning: Visualization not available - SVG document can't be accessed"
          );
        }
      } catch (e) {
        console.error("Error accessing SVG document during step:", e);
      }
    }
    let stepStatus = "error";
    try {
      const response = await fetch("/api/micro_step", { method: "POST" });
      if (!response) throw new Error("No response from server");
      const data = await response.json();
      if (!data) throw new Error("Invalid JSON response from server");
      if (data.log_entry) updateLog(data.log_entry);
      if (data.cpu_state) {
        updateCpuStateTabs(data.cpu_state);
      }

      if (response.ok) {
        if (data.step_data) {
          const step = data.step_data;
          const stepAddr = parseAddress(step.current_instruction_address);
          const addrChanged =
            !isNaN(stepAddr) && stepAddr !== currentInstructionAddr;
          const strChanged =
            step.current_instruction_string &&
            step.current_instruction_string !== currentInstructionStr;
          if (addrChanged || strChanged) {
            if (!isNaN(stepAddr)) currentInstructionAddr = stepAddr;
            currentInstructionStr =
              step.current_instruction_string || "(Unknown)";
            updateCurrentInstructionDisplay(
              currentInstructionAddr,
              currentInstructionStr
            );
          }
          currentMicroStepIndex = step.micro_step_index;
          updateMicroStepDisplay(currentMicroStepIndex, step.stage);
          applyHighlightsAndAnimations(step);
        }
        if (data.status === "success") {
          stepStatus = "micro_step_ok";
        } else if (
          data.status === "instruction_completed" ||
          data.status === "finished_instruction"
        ) {
          updateLog(data.message || "Instruction completed.");
          currentMicroStepIndex = -1;

          const nextPC = parseAddress(data.cpu_state?.pc);
          if (!isNaN(nextPC)) {
            currentInstructionAddr = nextPC;
            currentInstructionStr =
              data.next_instruction || "(Next instruction pending)";
            updateCurrentInstructionDisplay(
              currentInstructionAddr,
              currentInstructionStr
            );
            updateMicroStepDisplay(-1, "Fetch");
          } else {
            console.error("Could not determine next PC.");
            setSimulationState(
              simulationLoaded,
              false,
              "Error getting next PC state."
            );
            return "error";
          }
          stepStatus = "instruction_completed";
        } else if (data.status === "finished_program") {
          updateLog(data.message || "Program finished.");

          setSimulationState(false, false, data.message || "End of program");
          highlightLine(-1);
          stepStatus = "finished_program";
        } else {
          setSimulationState(
            simulationLoaded,
            false,
            data.message || `Unknown backend status: ${data.status}`
          );
          stepStatus = "error";
        }
      } else {
        const errorMsg = data.message || `API Error: ${response.status}`;
        updateLog(`Error: ${errorMsg}`);
        setSimulationState(simulationLoaded, false, errorMsg);
        resetAllSvgStyles();
        highlightLine(-1);
        stepStatus = "error";
      }
    } catch (error) {
      console.error("MicroStep execution error:", error);
      const errorMsg = `Frontend error during step: ${error.message}`;
      updateLog(errorMsg);
      setSimulationState(simulationLoaded, false, errorMsg);
      resetAllSvgStyles();
      highlightLine(-1);
      stepStatus = "error";
    }
    if (stepStatus === "micro_step_ok" && simulationLoaded && !isRunning) {
      setSimulationState(true, false);
    } else if (
      stepStatus === "instruction_completed" &&
      simulationLoaded &&
      !isRunning
    ) {
      setSimulationState(true, false);
    }
    return stepStatus;
  }

  async function executeFullInstruction() {
    /* Unchanged */
    if (!simulationLoaded) return false;
    const startingInstructionAddr = currentInstructionAddr;
    let safetyBreak = 0;
    const MAX_MICRO_STEPS_PER_CLICK = 10;
    let instructionCompletedOrSimEnded = false;
    try {
      while (
        simulationLoaded &&
        currentInstructionAddr === startingInstructionAddr &&
        safetyBreak < MAX_MICRO_STEPS_PER_CLICK
      ) {
        safetyBreak++;
        const stepResult = await handleSingleMicroStep();
        if (
          stepResult === "instruction_completed" ||
          stepResult === "finished_program" ||
          stepResult === "error"
        ) {
          instructionCompletedOrSimEnded = true;
          break;
        } else if (stepResult === "micro_step_ok") {
          if (showAnimationsToggle.checked && !isRunning) {
            await new Promise((resolve) => setTimeout(resolve, 50));
          }
        } else {
          console.error(
            "executeFullInstruction: Unexpected result:",
            stepResult
          );
          instructionCompletedOrSimEnded = true;
          break;
        }
      }
      if (safetyBreak >= MAX_MICRO_STEPS_PER_CLICK) {
        console.warn("Max micro-steps limit reached.");
        updateLog("[Warning] Max micro-steps limit reached.");
        instructionCompletedOrSimEnded = true;
      }
    } catch (error) {
      console.error("Error during Full Instruction execution loop:", error);
      instructionCompletedOrSimEnded = true;
    }
    return instructionCompletedOrSimEnded;
  }

  function startAutoRun() {
    /* Enhanced auto-run with micro-step mode */
    if (isRunning || !simulationLoaded) return;
    isRunning = true;
    setSimulationState(simulationLoaded, true);

    // Slower intervals for better visualization
    const microStepInterval = showAnimationsToggle.checked ? 1200 : 400; // Slower for micro-steps
    const instructionInterval = showAnimationsToggle.checked ? 800 : 200; // Pause between instructions

    console.log(
      `Starting auto-run with micro-step interval: ${microStepInterval}ms`
    );

    const runTick = async () => {
      if (!simulationLoaded || !isRunning) {
        console.log("Auto-run tick: Halting (state changed).");
        return;
      }

      updateStatus("Running... Executing micro-step...");

      try {
        const stepResult = await handleSingleMicroStep();

        if (stepResult === "error") {
          console.log("Auto-run tick: Halting (error occurred).");
          stopAutoRun();
          return;
        } else if (stepResult === "finished_program") {
          console.log("Auto-run tick: Halting (program finished).");
          stopAutoRun();
          return;
        } else if (stepResult === "instruction_completed") {
          console.log(
            "Auto-run tick: Instruction completed, brief pause before next..."
          );
          updateStatus("Running... Instruction completed, continuing...");

          // Brief pause between instructions
          if (isRunning && simulationLoaded) {
            runIntervalId = setTimeout(runTick, instructionInterval);
          } else {
            stopAutoRun();
          }
        } else if (stepResult === "micro_step_ok") {
          console.log("Auto-run tick: Micro-step completed, continuing...");
          updateStatus("Running... Continuing micro-steps...");

          // Continue with next micro-step
          if (isRunning && simulationLoaded) {
            runIntervalId = setTimeout(runTick, microStepInterval);
          } else {
            stopAutoRun();
          }
        } else {
          console.warn("Auto-run tick: Unexpected result:", stepResult);
          stopAutoRun();
        }
      } catch (error) {
        console.error("Auto-run tick error:", error);
        updateLog(`Auto-run error: ${error.message}`);
        stopAutoRun();
      }
    };

    updateStatus("Running... Starting micro-step execution");
    runTick();
  }

  async function performMicroStep() {
    /* Unchanged */
    if (!simulationLoaded || isRunning) return;
    microStepButton.disabled = true;
    fullInstructionButton.disabled = true;
    runPauseButton.disabled = true;
    updateStatus("Executing micro-step...");
    await handleSingleMicroStep();
    if (simulationLoaded && !isRunning) {
      setSimulationState(true, false);
    }
  }
  // --- End Helper Functions ---
  const debugSvgButton = document.createElement("button");
  debugSvgButton.textContent = "Debug SVG";
  debugSvgButton.style =
    "position:fixed; bottom:45px; right:10px; padding:5px; background:#2196F3; color:white; border:none; border-radius:3px; cursor:pointer; z-index:1001;";
  document.body.appendChild(debugSvgButton);

  // Debug SVG button handler
  debugSvgButton.addEventListener("click", () => {
    try {
      console.log("=== SVG DEBUG INFO ===");
      console.log("SVG object:", svgObject);

      if (!svgObject) {
        alert("SVG object reference not found!");
        return;
      }

      const svgSrc = svgObject.getAttribute("data");
      console.log(`SVG source: ${svgSrc || "Not set!"}`);

      if (!svgDoc) {
        console.log("SVG document not loaded! Attempting to load it now...");
        try {
          svgDoc = svgObject.contentDocument;
        } catch (e) {
          alert(`Failed to load SVG document: ${e.message}`);
          return;
        }
      }

      if (!svgDoc || !svgDoc.documentElement) {
        alert("Could not access SVG document or it has no root element");
        return;
      }

      // List all elements with IDs
      const elementsWithId = svgDoc.querySelectorAll("[id]");
      console.log(
        `\n=== ALL SVG ELEMENTS WITH IDs (${elementsWithId.length}) ===`
      );

      const idList = [];
      elementsWithId.forEach((el) => {
        const info = `${el.id} (${el.tagName.toLowerCase()})`;
        idList.push(info);
        console.log(info);
      });

      // Show in alert for easy copying
      alert(
        `SVG Elements with IDs:\n\n${idList.join(
          "\n"
        )}\n\nCheck console for more details.`
      );

      // Test highlight functionality
      console.log("\n=== TESTING HIGHLIGHT ===");

      // Try to highlight a few common elements
      const testIds = [
        "pc-register",
        "control-unit",
        "alu",
        "data-memory",
        "instruction-memory",
        "register-file",
      ];
      testIds.forEach((testId) => {
        const el = svgDoc.getElementById(testId);
        if (el) {
          console.log(`✓ Found: ${testId}`);
          // Apply test highlight
          el.style.fill = "rgba(255,0,0,0.3)";
          el.style.stroke = "#ff0000";
          el.style.strokeWidth = "2";

          // Remove after 2 seconds
          setTimeout(() => {
            el.style.fill = "";
            el.style.stroke = "";
            el.style.strokeWidth = "";
          }, 2000);
        } else {
          console.log(`✗ Missing: ${testId}`);
        }
      });
    } catch (e) {
      alert(`SVG debug error: ${e.message}`);
      console.error("SVG debug error:", e);
    }
  });

  function bringPathsToFront(highlightedPaths) {
    if (!svgDoc) return;

    // Find the data-paths group
    const dataPathsGroup = svgDoc.getElementById("data-paths");
    if (!dataPathsGroup) return;

    // Move highlighted paths to the end of the group (renders last = on top)
    highlightedPaths.forEach((pathId) => {
      const pathElement = svgDoc.getElementById(pathId);
      if (pathElement && dataPathsGroup.contains(pathElement)) {
        // Remove and re-append to move to end (renders on top)
        pathElement.parentNode.appendChild(pathElement);
      }
    });
  }

  function clearPersistentTextAnimations() {
    /* Clear all persistent text elements - used only for reset/new program */
    if (!svgDoc) {
      console.warn("clearPersistentTextAnimations: No SVG document available");
      return;
    }

    try {
      const persistentTexts = svgDoc.querySelectorAll(".signal-text-group");
      persistentTexts.forEach((text) => text.remove());
      console.log(`Cleared ${persistentTexts.length} persistent text elements`);
    } catch (err) {
      console.error("Error clearing persistent text animations:", err);
    }
  }

  // --- Event Listeners ---

  svgObject.addEventListener("load", () => {
    console.log("SVG load event triggered");
    try {
      // Clear previous reference
      svgDoc = null;

      // Get fresh reference
      svgDoc = svgObject.contentDocument;
      const svgSrc = svgObject.getAttribute("data");
      console.log("SVG source:", svgSrc);

      if (!svgSrc) {
        svgStatus.textContent = "SVG: Missing source path";
        svgStatus.style.backgroundColor = "rgba(255,0,0,0.7)";
        throw new Error("SVG object has no 'data' attribute");
      }

      if (!svgDoc || !svgDoc.documentElement) {
        svgStatus.textContent = "SVG: Failed to load";
        svgStatus.style.backgroundColor = "rgba(255,0,0,0.7)";
        throw new Error("SVG document is null or has no documentElement");
      }

      // Successfully loaded
      svgStatus.textContent = "SVG: Loaded";
      svgStatus.style.backgroundColor = "rgba(0,128,0,0.7)";
      console.log("SVG document accessed successfully");

      // List all elements with IDs
      const elementsWithId = svgDoc.querySelectorAll("[id]");
      console.log(`Total SVG elements with IDs: ${elementsWithId.length}`);

      if (elementsWithId.length === 0) {
        svgStatus.textContent = "SVG: No elements with IDs";
        svgStatus.style.backgroundColor = "rgba(255,165,0,0.7)";

        // Try to check if SVG has any content at all
        const totalElements = svgDoc.querySelectorAll("*").length;
        console.log(
          `Total SVG elements (with or without IDs): ${totalElements}`
        );

        if (totalElements < 5) {
          console.error("SVG appears to be empty or invalid");
        } else {
          console.warn("SVG has content but no IDs - attempting to add IDs");
          if (addMissingIds()) {
            // Call our new function here
            svgStatus.textContent = "SVG: Added missing IDs";
            svgStatus.style.backgroundColor = "rgba(255,165,0,0.7)";
            // Now check again for IDs
            const newElementsWithId = svgDoc.querySelectorAll("[id]");
            console.log(
              `After adding, SVG has ${newElementsWithId.length} elements with IDs`
            );
          }
        }
      } else {
        // Log all available IDs
        console.log("Available SVG element IDs:");
        elementsWithId.forEach((el) => {
          console.log(`${el.id} (${el.tagName.toLowerCase()})`);
        });
      }
    } catch (e) {
      console.error("Error accessing SVG document:", e);
    }
  });

  loadProgramButton.addEventListener("click", async () => {
    /* Clear persistent text when loading new program */
    stopAutoRun();
    const code = codeEditor.value;
    updateStatus("Loading and Resetting...");
    clearLog();
    clearPersistentTextAnimations(); // Clear text before loading new program
    resetAllSvgStyles();
    highlightLine(-1);
    populateCodeDisplay(code);
    initializeControlSignalsDisplay();
    try {
      const response = await fetch("/api/load", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ code: code }),
      });
      const data = await response.json();
      if (response.ok && data.status === "success") {
        updateLog(data.message || "Program loaded successfully.");
        updateCpuStateTabs(data.cpu_state);
        currentMicroStepIndex = -1;
        const initialAddrNumeric = parseAddress(data.cpu_state?.pc);
        if (isNaN(initialAddrNumeric)) {
          throw new Error("Backend did not return a valid initial PC.");
        }
        currentInstructionAddr = initialAddrNumeric;
        currentInstructionStr =
          data.initial_instr_str || "(Instruction pending)";
        updateCurrentInstructionDisplay(
          currentInstructionAddr,
          currentInstructionStr
        );
        updateMicroStepDisplay(-1, "Fetch");
        setSimulationState(true, false);
      } else {
        updateLog(
          `Error: ${data.message || "Unknown load error from backend"}`
        );
        setSimulationState(false, false, data.message || "Load failed");
        codeEditor.style.display = "block";
        codeDisplay.style.display = "none";
      }
    } catch (error) {
      console.error("Load Program error:", error);
      const errorMsg = `Error during program load: ${error.message}`;
      updateLog(errorMsg);
      setSimulationState(false, false, errorMsg);
      codeEditor.style.display = "block";
      codeDisplay.style.display = "none";
    }
  });

  uploadFileButton.addEventListener("click", () => {
    /* Unchanged */
    stopAutoRun();
    fileInput.click();
  });

  fileInput.addEventListener("change", (event) => {
    /* Unchanged */
    stopAutoRun();
    if (event.target.files && event.target.files[0]) {
      const file = event.target.files[0];
      const reader = new FileReader();
      reader.onload = (e) => {
        codeEditor.value = e.target.result;
        updateStatus(`File '${file.name}' read. Click 'Compile Code' to load.`);
      };
      reader.onerror = (e) => {
        console.error("Error reading file:", e);
        updateStatus(`Error reading file: ${e.target.error}`, true);
      };
      reader.readAsText(file);
    }
    event.target.value = null;
  });

  microStepButton.addEventListener("click", performMicroStep); /* Unchanged */

  fullInstructionButton.addEventListener("click", async () => {
    /* Unchanged */
    if (!simulationLoaded || isRunning) return;
    stopAutoRun();
    updateStatus("Executing full instruction...");
    microStepButton.disabled = true;
    fullInstructionButton.disabled = true;
    runPauseButton.disabled = true;
    await executeFullInstruction();
    if (simulationLoaded && !isRunning) {
      setSimulationState(true, false);
    }
  });

  runPauseButton.addEventListener("click", () => {
    /* Unchanged */
    if (isRunning) {
      stopAutoRun();
    } else if (simulationLoaded) {
      startAutoRun();
    }
  });

  resetButton.addEventListener("click", async () => {
    /* Clear persistent text when resetting */
    stopAutoRun();
    updateStatus("Resetting simulation...");
    clearLog();
    clearPersistentTextAnimations(); // Clear text before reset
    resetAllSvgStyles();
    highlightLine(-1);
    codeEditor.style.display = "block";
    codeDisplay.style.display = "none";
    initializeControlSignalsDisplay();
    try {
      const response = await fetch("/api/reset", { method: "POST" });
      const data = await response.json();
      if (response.ok && data.status === "success") {
        updateCpuStateTabs(data.cpu_state);
        currentMicroStepIndex = -1;
        currentInstructionAddr = parseAddress(data.cpu_state?.pc);
        if (isNaN(currentInstructionAddr)) currentInstructionAddr = -1;
        currentInstructionStr = "(Program not loaded)";
        updateCurrentInstructionDisplay(
          currentInstructionAddr,
          currentInstructionStr
        );
        updateMicroStepDisplay(-1, "Idle");
        setSimulationState(false, false);
        updateLog(data.message || "Simulator reset successfully.");
      } else {
        updateLog(
          `Error resetting simulator: ${data.message || "Unknown reset error"}`
        );
        setSimulationState(false, false, data.message || "Reset failed");
      }
    } catch (error) {
      console.error("Reset fetch error:", error);
      const errorMsg = `Network error during reset: ${error.message}`;
      updateLog(errorMsg);
      setSimulationState(false, false, errorMsg);
    }
  });

  // --- MODIFIED Tab Switching Logic ---
  // Select ALL tab buttons from both panels
  const allTabButtons = document.querySelectorAll(".tab-button");

  allTabButtons.forEach((button) => {
    button.addEventListener("click", () => {
      const targetTabId = button.getAttribute("data-tab");
      const targetPanelId = button.getAttribute("data-panel"); // Get which panel this button belongs to ('top' or 'bottom')
      if (!targetTabId || !targetPanelId) return;

      // Find the parent panel based on the data-panel attribute or ID
      const parentPanel = document.getElementById(
        `tabs-panel-${targetPanelId}`
      );
      if (!parentPanel) {
        console.error("Could not find parent panel for tab button:", button);
        return;
      }

      // --- Scope selections to the PARENT PANEL ---
      const buttonsInPanel = parentPanel.querySelectorAll(".tab-button");
      const contentsInPanel = parentPanel.querySelectorAll(".tab-content");
      // --- End Scope ---

      // Deactivate all buttons *within this panel*
      buttonsInPanel.forEach((btn) => btn.classList.remove("active"));
      // Hide all content divs *within this panel*
      contentsInPanel.forEach((content) => (content.style.display = "none")); // More reliable than removing 'active' class for display

      // Activate the clicked button
      button.classList.add("active");

      // Show the target content *within this panel*
      // We still use the unique ID of the content div
      const targetContent = document.getElementById(`tab-${targetTabId}`);
      if (targetContent && parentPanel.contains(targetContent)) {
        // Ensure the content is actually inside this panel
        targetContent.style.display = "block"; // Show the content
        // Ensure the .active class is also on the content for potential CSS styling
        targetContent.classList.add("active");
      } else {
        console.warn(
          `Tab content not found or not in correct panel for ID: tab-${targetTabId} in panel ${targetPanelId}`
        );
      }
    });
  });

  // --- Initial Setup on Page Load ---
  function initializeUI() {
    // Fix the right panel first
    fixRightPanel();

    // Get updated references
    const refs = updateTabReferences();

    setSimulationState(false); // Start in non-loaded state
    updateMicroStepDisplay(-1, "Idle"); // Set initial micro-step display

    // Set initial placeholder text for structured displays
    if (refs.registerDisplayGrid)
      refs.registerDisplayGrid.innerHTML =
        "<div>(Load program or upload file to view registers)</div>";
    if (refs.pcValueDisplay) refs.pcValueDisplay.textContent = "N/A";
    initializeControlSignalsDisplay();
    if (refs.memoryTabContent)
      refs.memoryTabContent.textContent =
        "(Load program or upload file to view memory)";
    if (refs.logTabContent)
      refs.logTabContent.textContent =
        "Load a program using the 'Compile Code' button or 'Upload File'.\n";

    // Activate tab button click handlers
    document.querySelectorAll(".tab-button").forEach((button) => {
      button.addEventListener("click", function () {
        const targetTabId = this.getAttribute("data-tab");
        const targetPanelId = this.getAttribute("data-panel");
        if (!targetTabId || !targetPanelId) return;

        const parentPanel = document.getElementById(
          `tabs-panel-${targetPanelId}`
        );
        if (!parentPanel) return;

        // Deactivate all buttons in this panel
        parentPanel.querySelectorAll(".tab-button").forEach((btn) => {
          btn.classList.remove("active");
        });

        // Hide all content in this panel
        parentPanel.querySelectorAll(".tab-content").forEach((content) => {
          content.style.display = "none";
          content.classList.remove("active");
        });

        // Activate this button
        this.classList.add("active");

        // Show target content
        const targetContent = document.getElementById(`tab-${targetTabId}`);
        if (targetContent) {
          targetContent.style.display = "block";
          targetContent.classList.add("active");
        }
      });
    });

    // Activate first tabs in each panel
    const firstTopTabButton = document.querySelector(
      "#tabs-panel-top .tab-button"
    );
    if (firstTopTabButton) firstTopTabButton.click();

    const firstBottomTabButton = document.querySelector(
      "#tabs-panel-bottom .tab-button"
    );
    if (firstBottomTabButton) firstBottomTabButton.click();
  }

  initializeUI(); // Call the initialization function

  setTimeout(() => {
    console.log("Applying final right panel fix...");

    // Force the right column to appear with very specific styles
    const rightColumn = document.getElementById("right-column");
    if (rightColumn) {
      Object.assign(rightColumn.style, {
        display: "flex",
        flex: "0 0 350px",
        minWidth: "280px",
        maxWidth: "400px",
        flexDirection: "column",
        overflow: "hidden",
        border: "2px solid red", // Temporary visual indicator
      });
    }

    // Force display of panels
    const topPanel = document.getElementById("tabs-panel-top");
    const bottomPanel = document.getElementById("tabs-panel-bottom");
    const toggleButtonForTopPanelExists = document.getElementById(
      "toggle-cpu-state-button"
    ); // Check again

    if (topPanel) {
      if (!toggleButtonForTopPanelExists) {
        // Only apply these styles if the toggle button doesn't exist
        Object.assign(topPanel.style, {
          display: "flex",
          flex: "1",
          flexDirection: "column",
          minHeight: "0",
          overflow: "auto",
        });
        console.log(
          "Top panel styled by setTimeout (as part of right column legacy)"
        );
      } else {
        console.log(
          "Top panel's visibility is controlled by toggle-cpu-state-button, setTimeout skipping display style."
        );
      }
    }

    if (bottomPanel) {
      Object.assign(bottomPanel.style, {
        display: "flex",
        flex: "1",
        flexDirection: "column",
        minHeight: "0",
        overflow: "auto",
      });
    }

    // Force display of tab containers
    const topTabsContainer = document.getElementById("status-tabs-top");
    const bottomTabsContainer = document.getElementById("status-tabs-bottom");

    if (topTabsContainer) {
      Object.assign(topTabsContainer.style, {
        display: "flex",
        flex: "1",
        flexDirection: "column",
        overflow: "hidden",
      });
    }

    if (bottomTabsContainer) {
      Object.assign(bottomTabsContainer.style, {
        display: "flex",
        flex: "1",
        flexDirection: "column",
        overflow: "hidden",
      });
    }

    // Force active tab content to be visible
    const activeTabContents = document.querySelectorAll(".tab-content.active");
    activeTabContents.forEach((el) => {
      el.style.display = "block";
    });

    console.log("Final right panel fix applied");

    // Check if content is actually visible
    setTimeout(() => {
      const registerGrid = document.getElementById("register-display-grid");
      const logContent = document.getElementById("tab-log");

      console.log(
        "Register grid visible:",
        registerGrid?.offsetHeight > 0 ? "Yes" : "No"
      );
      console.log(
        "Log content visible:",
        logContent?.offsetHeight > 0 ? "Yes" : "No"
      );
    }, 100);
  }, 1000);
}); // End DOMContentLoaded
