document.addEventListener("DOMContentLoaded", () => {
  function forceRightPanelVisible() {
    console.log("FORCING right panel visibility...");
    
    const rightColumn = document.getElementById('right-column');
    if (!rightColumn) {
      console.error("RIGHT COLUMN NOT FOUND IN DOM");
      return;
    }
    
    // Force CSS display
    rightColumn.setAttribute('style', 'display: flex !important; flex: 1 !important; min-width: 280px !important; max-width: 400px !important; flex-direction: column !important; border: 2px solid red !important;');
    
    // Check children
    const topPanel = document.getElementById('tabs-panel-top');
    const bottomPanel = document.getElementById('tabs-panel-bottom');
    
    if (topPanel) {
      topPanel.setAttribute('style', 'display: flex !important; flex: 1 !important; flex-direction: column !important; min-height: 200px !important; border: 1px solid blue !important;');
      console.log("Top panel found and styled");
    } else {
      console.error("Top panel missing!");
    }
    
    if (bottomPanel) {
      bottomPanel.setAttribute('style', 'display: flex !important; flex: 1 !important; flex-direction: column !important; min-height: 200px !important; border: 1px solid green !important;');
      console.log("Bottom panel found and styled");
    } else {
      console.log("Bottom panel missing - will try to create it");
    }
    
    console.log("Force styling applied to right panel");
  }
  
  // Call this function immediately
  forceRightPanelVisible();
  const emergencyStyles = document.createElement('style');
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
  
  #tabs-panel-top, #tabs-panel-bottom {
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
  // --- Constants (Unchanged) ---
  const BITS_64 = 64n;
  const SIGN_BIT_64_MASK = 1n << (BITS_64 - 1n);
  const MAX_UNSIGNED_64 = (1n << BITS_64) - 1n;
  const TWO_POW_64 = 1n << BITS_64;

  // --- Element References ---
  const loadProgramButton = document.getElementById("load-program-button");
  const microStepButton = document.getElementById("micro-step-button");
  const fullInstructionButton = document.getElementById("full-instruction-button");
  const resetButton = document.getElementById("reset-button");
  const runPauseButton = document.getElementById("run-pause-button");
  const codeEditor = document.getElementById("code-editor");
  const codeDisplay = document.getElementById("code-display");
  const currentInstrDisplay = document.getElementById("current-instr-display");
  const microStepDisplay = document.getElementById("micro-step-display");
  const showAnimationsToggle = document.getElementById("show-animations-toggle");
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
  const svgStatus = document.createElement('div');
  svgStatus.id = 'svg-status';
  svgStatus.style = 'position:fixed; bottom:10px; right:10px; padding:5px; background:rgba(0,0,0,0.7); color:white; z-index:1000;';
  svgStatus.textContent = "SVG: Not loaded";
  document.body.appendChild(svgStatus);

  function fixRightPanel() {
    console.log("Fixing right panel...");
    
    // Check if right column exists
    const rightColumn = document.getElementById('right-column');
    if (!rightColumn) {
      console.error("Right column not found in DOM");
      return;
    }
    ensureBottomPanel();
    // Force right column visibility
    rightColumn.style.display = 'flex';
    rightColumn.style.flex = '1';
    rightColumn.style.minWidth = '280px';
    rightColumn.style.flexDirection = 'column';
    
    // Check top panel and ensure it's visible
    const topPanel = document.getElementById('tabs-panel-top');
    if (topPanel) {
      topPanel.style.display = 'flex';
      topPanel.style.flex = '1';
      topPanel.style.flexDirection = 'column';
      topPanel.style.minHeight = '0';
      topPanel.style.overflow = 'auto';
    }
    
    // Check if bottom panel exists and make it visible
    const bottomPanel = document.getElementById('tabs-panel-bottom');
    if (bottomPanel) {
      bottomPanel.style.display = 'flex';
      bottomPanel.style.flex = '1';
      bottomPanel.style.flexDirection = 'column';
      bottomPanel.style.minHeight = '0';
      bottomPanel.style.overflow = 'auto';
    }
  
    // Fix for possibly missing tab content divs
    ensureTabContentExists();
    
    // Force display of active tabs
    document.querySelectorAll('.tab-content.active').forEach(tab => {
      if (tab) tab.style.display = 'block';
    });
    
    console.log("Right panel fix applied");
  }
  
  function ensureBottomPanel() {
    const rightColumn = document.getElementById('right-column');
    if (!rightColumn) return;
    
    // Check if bottom panel exists
    let bottomPanel = document.getElementById('tabs-panel-bottom');
    if (!bottomPanel) {
      // Create the bottom panel
      bottomPanel = document.createElement('div');
      bottomPanel.id = 'tabs-panel-bottom';
      bottomPanel.className = 'panel';
      
      // Add heading
      const heading = document.createElement('h2');
      heading.textContent = 'Log';
      bottomPanel.appendChild(heading);
      
      // Append to right column
      rightColumn.appendChild(bottomPanel);
      
      console.log("Created missing bottom panel");
    }
  }
  // Add this function to ensure all tab content divs exist
  function ensureTabContentExists() {
    // Check if tab content divs exist and create them if missing
    const tabIds = ['registers', 'memory', 'cpu-state', 'control-signals', 'log'];
    const topPanelTabs = ['registers', 'memory', 'cpu-state', 'control-signals'];
    const bottomPanelTabs = ['log'];
    
    const topPanel = document.getElementById('tabs-panel-top');
    const bottomPanel = document.getElementById('tabs-panel-bottom');
    
    // Create tab container in top panel if missing
    if (topPanel && !topPanel.querySelector('.tabs-container')) {
      const tabsContainer = document.createElement('div');
      tabsContainer.className = 'tabs-container';
      
      // Create tab buttons container
      const tabButtons = document.createElement('div');
      tabButtons.className = 'tab-buttons';
      
      // Create buttons for each top panel tab
      topPanelTabs.forEach((tabId, index) => {
        const button = document.createElement('button');
        button.className = 'tab-button' + (index === 0 ? ' active' : '');
        button.setAttribute('data-tab', tabId);
        button.setAttribute('data-panel', 'top');
        button.textContent = tabId.split('-').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ');
        tabButtons.appendChild(button);
      });
      
      tabsContainer.appendChild(tabButtons);
      
      // Create tab contents
      topPanelTabs.forEach((tabId, index) => {
        // Check if tab content already exists
        if (!document.getElementById(`tab-${tabId}`)) {
          const tabContent = document.createElement('div');
          tabContent.id = `tab-${tabId}`;
          tabContent.className = 'tab-content' + (index === 0 ? ' active' : '');
          tabContent.style.display = index === 0 ? 'block' : 'none';
          
          // Add specific content for each tab
          switch(tabId) {
            case 'registers':
              tabContent.innerHTML = '<div id="register-display-grid" class="register-grid"></div>';
              break;
            case 'memory':
              tabContent.innerHTML = '<pre id="tab-memory-content">(Load program to view memory)</pre>';
              break;
            case 'cpu-state':
              tabContent.innerHTML = '<div><strong>PC:</strong> <span id="pc-value-display">N/A</span></div>';
              break;
            case 'control-signals':
              tabContent.innerHTML = '<div id="control-signals-display"></div>';
              break;
          }
          
          tabsContainer.appendChild(tabContent);
        }
      });
      
      topPanel.appendChild(tabsContainer);
    }
    
    // If bottom panel exists but no tab container
    if (bottomPanel && !bottomPanel.querySelector('.tabs-container')) {
      const tabsContainer = document.createElement('div');
      tabsContainer.className = 'tabs-container';
      
      // Create tab buttons container
      const tabButtons = document.createElement('div');
      tabButtons.className = 'tab-buttons';
      
      // Create button for log tab
      const button = document.createElement('button');
      button.className = 'tab-button active';
      button.setAttribute('data-tab', 'log');
      button.setAttribute('data-panel', 'bottom');
      button.textContent = 'Log';
      tabButtons.appendChild(button);
      
      tabsContainer.appendChild(tabButtons);
      
      // Create log tab content if it doesn't exist
      if (!document.getElementById('tab-log')) {
        const tabContent = document.createElement('div');
        tabContent.id = 'tab-log';
        tabContent.className = 'tab-content active';
        tabContent.style.display = 'block';
        tabContent.style.whiteSpace = 'pre-wrap';
        tabContent.textContent = 'Load a program using the \'Compile Code\' button or \'Upload File\'.\n';
        
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
    const controlSignalsTabContent = document.getElementById("tab-control-signals");
    const logTabContent = document.getElementById("tab-log");
  
    // Update structured display references
    const registerDisplayGrid = document.getElementById("register-display-grid");
    const pcValueDisplay = document.getElementById("pc-value-display");
    const controlSignalsDisplay = document.getElementById("control-signals-display");
    
    return {
      registersTabContent,
      memoryTabContent,
      cpuStateTabContent, 
      controlSignalsTabContent,
      logTabContent,
      registerDisplayGrid,
      pcValueDisplay,
      controlSignalsDisplay
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
  codeEditor.value = `// Example program:\n// Or Upload a file (.S, .asm, .txt)\nADDI X1, XZR, #10    // X1 = 10\nADDI X2, XZR, #5     // X2 = 5\nloop:                // Example Label\nADD X3, X1, X2       // X3 = X1 + X2 = 15\nSTUR X3, [SP, #8]    // Store X3 to Mem[SP+8]\nSUBI X2, X2, #1      // X2 = X2 - 1\nCBZ X2, end          // Branch if X2 is zero\nB loop               // Unconditional branch to loop\nend:                 // End Label\nADD X6, X6, #1       // Executed after loop finishes\n// End`;

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

      Object.entries(state.registers).forEach(([name, valueStr]) => {
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
    /* Unchanged */
    if (!svgDoc) {
      console.warn("resetAllSvgStyles: No SVG document available");
      return;
    }
    
    try {
      highlightedElements.clear();
      const dots = svgDoc.querySelectorAll(".signal-dot");
      dots.forEach((dot) => dot.remove());
      const elements = svgDoc.querySelectorAll("path[id], line[id], rect[id]");
      
      if (elements.length === 0) {
        console.warn("No SVG elements found with IDs - verify SVG structure");
        updateLog("Warning: SVG visualization may not be properly loaded");
      }
      
      elements.forEach((el) => {
        el.classList.remove("path-highlight", "block-highlight");
        el.style.stroke =
          el.tagName.toLowerCase() === "rect" ? "#555555" : "#aaaaaa";
        el.style.strokeWidth = el.tagName.toLowerCase() === "rect" ? "1" : "1.5";
        el.style.fill =
          el.tagName.toLowerCase() === "rect"
            ? "rgba(200, 200, 200, 0.05)"
            : "none";
        el.style.transition = "none";
      });
      
      setTimeout(() => {
        elements.forEach((el) => {
          el.style.transition =
            "stroke 0.15s linear, stroke-width 0.15s linear, fill 0.15s linear";
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
          return parseFloat(a.getAttribute("x") || 0) - parseFloat(b.getAttribute("x") || 0);
        });
        
        // Assign IDs to first few rectangles as common components
        const commonIds = ["PC", "InstructionMemory", "Registers", "ALU", "DataMemory", "Control"];
        rectArray.slice(0, Math.min(rectArray.length, commonIds.length)).forEach((rect, i) => {
          rect.setAttribute("id", commonIds[i]);
          console.log(`Added ID "${commonIds[i]}" to rectangle at (${rect.getAttribute("x")}, ${rect.getAttribute("y")})`);
        });
        
        // Add IDs to paths
        const paths = svgDoc.querySelectorAll("path");
        paths.forEach((path, i) => {
          path.setAttribute("id", `path-${i+1}`);
        });
        
        // Add IDs to lines
        const lines = svgDoc.querySelectorAll("line");
        lines.forEach((line, i) => {
          line.setAttribute("id", `line-${i+1}`);
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
    // Map between expected backend IDs and actual SVG element IDs
    const idMappings = {
      // Core components
      "block-pc": "PC",
      "block-imem": "InstructionMemory", 
      "block-adder1": "Adder1",
      "block-control": "Control",
      "block-registers": "Registers",
      "block-alu": "ALU",
      "block-dmem": "DataMemory",
      
      // Paths
      "path-pc-imem": "pc-to-imem",
      "path-pc-adder1": "pc-to-adder1",
      "path-adder1-mux4-in0": "adder1-to-mux4",
      "path-instr-regwriteaddr": "instruction-to-registerwrite",
      "path-mux3-wb": "mux3-to-wb",
      "path-wb-regwrite": "wb-to-regwrite",
      "path-alu-mux3-in0": "alu-to-mux3",
      "path-mux4-pc": "mux4-to-pc",
      
      // Control lines
      "control-regwrite-enable": "control-regwrite",
      "mux-memtoreg-in0": "memtoreg-input0",
      "mux-pcsrc-in0": "pcsrc-input0"
    };
    
    return idMappings[id] || id; // Return mapped ID or original
  }


  function createSignalBit(svgDoc, value) {
    /* Unchanged */
    if (!svgDoc) return null;
    const bit = svgDoc.createElementNS("http://www.w3.org/2000/svg", "circle");
    bit.setAttribute("r", "4");
    bit.classList.add("signal-dot");
    bit.classList.add(value === 1 ? "signal-bit-1" : "signal-bit-0");
    bit.setAttribute("fill", value === 1 ? "#4CAF50" : "#f44336");
    return bit;
  }

  function animateSignalBits(pathElement, signal, svgDoc) {
    /* Unchanged */
    if (!svgDoc || !pathElement || !signal) return;
    const bitValues = signal.bits || [1];
    const duration = signal.duration || animationSpeed;
    const startDelay = signal.start_delay || 0;
    const spacingFactor = 0.1;

    bitValues.forEach((bitValue, index) => {
      const bit = createSignalBit(svgDoc, bitValue);
      if (!bit) return;
      svgDoc.documentElement.appendChild(bit);
      gsap
        .timeline({
          onComplete: () => {
            if (bit && bit.parentNode) {
              bit.remove();
            }
          },
        })
        .set(bit, {
          motionPath: {
            path: pathElement,
            align: pathElement,
            alignOrigin: [0.5, 0.5],
            start: 0,
            end: 0,
          },
          opacity: 0,
          immediateRender: true,
        })
        .to(bit, {
          delay: startDelay + index * spacingFactor * duration,
          opacity: 1,
          duration: duration,
          motionPath: {
            path: pathElement,
            align: pathElement,
            alignOrigin: [0.5, 0.5],
            start: 0,
            end: 1,
            autoRotate: false,
          },
          ease: "none",
        })
        .to(bit, { opacity: 0, duration: 0.05 }, ">-0.05");
    });
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
    
    resetAllSvgStyles();
    
    let foundElements = 0;
    let missingElements = 0;
  
    // Apply block highlights with mapping
    (stepData.active_blocks || []).forEach((id) => {
      const mappedId = mapSvgId(id);
      const el = svgDoc.getElementById(mappedId);
      if (el) {
        foundElements++;
        el.classList.add("block-highlight");
        el.style.fill = "rgba(233, 30, 99, 0.15)";
        el.style.stroke = "#e91e63";
        el.style.strokeWidth = "1.5";
        console.log(`Highlighting block: ${id} → ${mappedId}`);
      } else {
        missingElements++;
        console.warn(`SVG Block ID not found: ${id} (mapped to ${mappedId})`);
      }
    });
  
    // Apply path highlights with mapping
    (stepData.active_paths || []).forEach((id) => {
      const mappedId = mapSvgId(id);
      const el = svgDoc.getElementById(mappedId);
      if (el && el.tagName.toLowerCase() !== "rect") {
        foundElements++;
        el.classList.add("path-highlight");
        el.style.stroke = "#e91e63";
        el.style.strokeWidth = "2.5";
        console.log(`Highlighting path: ${id} → ${mappedId}`);
      } else if (!el) {
        missingElements++;
        console.warn(`SVG Path ID not found: ${id} (mapped to ${mappedId})`);
      }
    });
    
    // Log statistics about highlight application
    if (missingElements > 0) {
      console.warn(`Missing ${missingElements} SVG elements for this step. Found: ${foundElements}`);
      if (foundElements === 0) {
        updateLog("Warning: Visualization not updating - SVG element IDs may not match simulation");
        svgStatus.textContent = `SVG: 0/${missingElements + foundElements} elements found`;
        svgStatus.style.backgroundColor = "rgba(255,0,0,0.7)";
      } else {
        svgStatus.textContent = `SVG: ${foundElements}/${missingElements + foundElements} elements found`;
        svgStatus.style.backgroundColor = "rgba(255,165,0,0.7)";
      }
    } else if (foundElements > 0) {
      svgStatus.textContent = `SVG: All ${foundElements} elements found`;
      svgStatus.style.backgroundColor = "rgba(0,128,0,0.7)";
    }
  
    // Handle animations with mapping
    if (showAnimationsToggle.checked && stepData.animated_signals) {
      stepData.animated_signals.forEach((signal) => {
        const mappedId = mapSvgId(signal.path_id);
        const pathElement = svgDoc.getElementById(mappedId);
        if (pathElement) {
          animateSignalBits(pathElement, signal, svgDoc);
          console.log(`Animating signal: ${signal.path_id} → ${mappedId}`);
        } else {
          console.warn(`Animation path ID not found: ${signal.path_id} (mapped to ${mappedId})`);
        }
      });
    }
  
    // Control signals update
    const signals = stepData.control_signals || {};
    knownControlSignals.forEach((signalName) => {
      const valueSpan = document.getElementById(
        `signal-value-${signalName.toLowerCase()}`
      );
      if (valueSpan) {
        const value = signals[signalName];
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
          updateLog("Warning: Visualization not available - SVG document can't be accessed");
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
          resetAllSvgStyles();
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
    /* Unchanged */
    if (isRunning || !simulationLoaded) return;
    isRunning = true;
    setSimulationState(simulationLoaded, true);
    const baseInterval = showAnimationsToggle.checked ? 600 : 50;
    const instructionOverhead = showAnimationsToggle.checked ? 100 : 20;
    const intervalTime = baseInterval + instructionOverhead;
    console.log(`Starting auto-run with interval: ~${intervalTime}ms`);
    const runTick = async () => {
      if (!simulationLoaded || !isRunning) {
        console.log("Auto-run tick: Halting (state changed).");
        return;
      }
      updateStatus("Running... Executing instruction...");
      await executeFullInstruction();
      if (!simulationLoaded) {
        console.log("Auto-run tick: Halting (sim finished/errored).");
        stopAutoRun();
      } else if (!isRunning) {
        console.log("Auto-run tick: Halting (paused by user).");
        stopAutoRun();
      } else {
        console.log("Auto-run tick: Instruction completed, continuing run.");
        updateStatus("Running... Waiting for next tick");
        scheduleNextTick();
      }
    };
    const scheduleNextTick = () => {
      if (isRunning && simulationLoaded) {
        runIntervalId = setTimeout(runTick, intervalTime);
      } else {
        console.log("Auto-run: Not scheduling next tick.");
        stopAutoRun();
      }
    };
    updateStatus("Running... Starting execution");
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
  const debugSvgButton = document.createElement('button');
debugSvgButton.textContent = "Debug SVG";
debugSvgButton.style = "position:fixed; bottom:45px; right:10px; padding:5px; background:#2196F3; color:white; border:none; border-radius:3px; cursor:pointer; z-index:1001;";
document.body.appendChild(debugSvgButton);

// Debug SVG button handler
debugSvgButton.addEventListener('click', () => {
  try {
    console.log("SVG object:", svgObject);
    
    if (!svgObject) {
      alert("SVG object reference not found!");
      return;
    }
    
    const svgSrc = svgObject.getAttribute("data");
    console.log(`SVG source: ${svgSrc || "Not set!"}`);
    
    if (!svgDoc) {
      alert("SVG document not loaded! Attempting to load it now...");
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
    
    // Test SVG with a visual indicator
    try {
      // Add a test rect to see if SVG is accessible
      const testRect = svgDoc.createElementNS("http://www.w3.org/2000/svg", "rect");
      testRect.setAttribute("x", "10");
      testRect.setAttribute("y", "10");
      testRect.setAttribute("width", "50");
      testRect.setAttribute("height", "50");
      testRect.setAttribute("fill", "rgba(255,0,0,0.5)");
      testRect.setAttribute("id", "debug-test-rect");
      svgDoc.documentElement.appendChild(testRect);
      
      // Set a timeout to remove the rect after 3 seconds
      setTimeout(() => {
        const rect = svgDoc.getElementById("debug-test-rect");
        if (rect && rect.parentNode) {
          rect.parentNode.removeChild(rect);
        }
      }, 3000);
      
      alert("Added a red square to the SVG for 3 seconds. If you can see it, SVG manipulation is working.");
    } catch (e) {
      alert(`Failed to modify SVG: ${e.message}`);
    }
  } catch (e) {
    alert(`SVG debug error: ${e.message}`);
  }
});
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
        console.log(`Total SVG elements (with or without IDs): ${totalElements}`);
        
        if (totalElements < 5) {
          console.error("SVG appears to be empty or invalid");
        } else {
          console.warn("SVG has content but no IDs - attempting to add IDs");
          if (addMissingIds()) {  // Call our new function here
            svgStatus.textContent = "SVG: Added missing IDs";
            svgStatus.style.backgroundColor = "rgba(255,165,0,0.7)";
            // Now check again for IDs
            const newElementsWithId = svgDoc.querySelectorAll("[id]");
            console.log(`After adding, SVG has ${newElementsWithId.length} elements with IDs`);
          }
        }
      } else {
        // Log all available IDs
        console.log("Available SVG element IDs:");
        elementsWithId.forEach(el => {
          console.log(`${el.id} (${el.tagName.toLowerCase()})`);
        });
      }
    } catch (e) {
      console.error("Error accessing SVG document:", e);
    }
  });

  loadProgramButton.addEventListener("click", async () => {
    /* Unchanged */
    stopAutoRun();
    const code = codeEditor.value;
    updateStatus("Loading and Resetting...");
    clearLog();
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
    /* Unchanged */
    stopAutoRun();
    updateStatus("Resetting simulation...");
    clearLog();
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
      refs.registerDisplayGrid.innerHTML = "<div>(Load program or upload file to view registers)</div>";
    if (refs.pcValueDisplay) refs.pcValueDisplay.textContent = "N/A";
    initializeControlSignalsDisplay();
    if (refs.memoryTabContent)
      refs.memoryTabContent.textContent = "(Load program or upload file to view memory)";
    if (refs.logTabContent)
      refs.logTabContent.textContent = "Load a program using the 'Compile Code' button or 'Upload File'.\n";
  
    // Activate tab button click handlers
    document.querySelectorAll('.tab-button').forEach(button => {
      button.addEventListener('click', function() {
        const targetTabId = this.getAttribute('data-tab');
        const targetPanelId = this.getAttribute('data-panel');
        if (!targetTabId || !targetPanelId) return;
        
        const parentPanel = document.getElementById(`tabs-panel-${targetPanelId}`);
        if (!parentPanel) return;
        
        // Deactivate all buttons in this panel
        parentPanel.querySelectorAll('.tab-button').forEach(btn => {
          btn.classList.remove('active');
        });
        
        // Hide all content in this panel
        parentPanel.querySelectorAll('.tab-content').forEach(content => {
          content.style.display = 'none';
          content.classList.remove('active');
        });
        
        // Activate this button
        this.classList.add('active');
        
        // Show target content
        const targetContent = document.getElementById(`tab-${targetTabId}`);
        if (targetContent) {
          targetContent.style.display = 'block';
          targetContent.classList.add('active');
        }
      });
    });
    
    // Activate first tabs in each panel
    const firstTopTabButton = document.querySelector('#tabs-panel-top .tab-button');
    if (firstTopTabButton) firstTopTabButton.click();
    
    const firstBottomTabButton = document.querySelector('#tabs-panel-bottom .tab-button');
    if (firstBottomTabButton) firstBottomTabButton.click();
  }

  initializeUI(); // Call the initialization function

  setTimeout(() => {
    console.log("Applying final right panel fix...");
    
    // Force the right column to appear with very specific styles
    const rightColumn = document.getElementById('right-column');
    if (rightColumn) {
      Object.assign(rightColumn.style, {
        display: 'flex',
        flex: '0 0 350px',
        minWidth: '280px',
        maxWidth: '400px',
        flexDirection: 'column',
        overflow: 'hidden',
        border: '2px solid red' // Temporary visual indicator
      });
    }
    
    // Force display of panels
    const topPanel = document.getElementById('tabs-panel-top');
    const bottomPanel = document.getElementById('tabs-panel-bottom');
    
    if (topPanel) {
      Object.assign(topPanel.style, {
        display: 'flex',
        flex: '1',
        flexDirection: 'column',
        minHeight: '0',
        overflow: 'auto'
      });
    }
    
    if (bottomPanel) {
      Object.assign(bottomPanel.style, {
        display: 'flex',
        flex: '1',
        flexDirection: 'column',
        minHeight: '0',
        overflow: 'auto'
      });
    }
    
    // Force display of tab containers
    const topTabsContainer = document.getElementById('status-tabs-top');
    const bottomTabsContainer = document.getElementById('status-tabs-bottom');
    
    if (topTabsContainer) {
      Object.assign(topTabsContainer.style, {
        display: 'flex',
        flex: '1',
        flexDirection: 'column',
        overflow: 'hidden'
      });
    }
    
    if (bottomTabsContainer) {
      Object.assign(bottomTabsContainer.style, {
        display: 'flex',
        flex: '1',
        flexDirection: 'column',
        overflow: 'hidden'
      });
    }
    
    // Force active tab content to be visible
    const activeTabContents = document.querySelectorAll('.tab-content.active');
    activeTabContents.forEach(el => {
      el.style.display = 'block';
    });
    
    console.log("Final right panel fix applied");
    
    // Check if content is actually visible
    setTimeout(() => {
      const registerGrid = document.getElementById('register-display-grid');
      const logContent = document.getElementById('tab-log');
      
      console.log("Register grid visible:", registerGrid?.offsetHeight > 0 ? "Yes" : "No");
      console.log("Log content visible:", logContent?.offsetHeight > 0 ? "Yes" : "No");
    }, 100);
  }, 1000);
}); // End DOMContentLoaded
