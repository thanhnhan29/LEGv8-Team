document.addEventListener("DOMContentLoaded", () => {
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
  const uploadFileButton = document.getElementById("upload-file-button");
  const fileInput = document.getElementById("file-input");

  // --- Tab Elements (Specific IDs for content are key) ---
  // Content areas (IDs remain unique across panels)
  const registersTabContent = document.getElementById("tab-registers"); // In Top Panel
  const memoryTabContent = document.getElementById("tab-memory"); // In Top Panel
  const cpuStateTabContent = document.getElementById("tab-cpu-state"); // In Top Panel
  const controlSignalsTabContent = document.getElementById(
    "tab-control-signals"
  ); // In Top Panel
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
    if (!svgDoc) return;
    highlightedElements.clear();
    const dots = svgDoc.querySelectorAll(".signal-dot");
    dots.forEach((dot) => dot.remove());
    const elements = svgDoc.querySelectorAll("path[id], line[id], rect[id]");
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
    /* Unchanged - targets specific control signal value IDs */
    if (!svgDoc || !stepData) return;
    resetAllSvgStyles();

    (stepData.active_blocks || []).forEach((id) => {
      const el = svgDoc.getElementById(id);
      if (el) {
        el.classList.add("block-highlight");
        el.style.fill = "rgba(233, 30, 99, 0.15)";
        el.style.stroke = "#e91e63";
        el.style.strokeWidth = "1.5";
      } else console.warn(`SVG Block ID not found: ${id}`);
    });

    (stepData.active_paths || []).forEach((id) => {
      const el = svgDoc.getElementById(id);
      if (el && el.tagName.toLowerCase() !== "rect") {
        el.classList.add("path-highlight");
        el.style.stroke = "#e91e63";
        el.style.strokeWidth = "2.5";
      } else if (!el) console.warn(`SVG Path ID not found: ${id}`);
    });

    if (showAnimationsToggle.checked && stepData.animated_signals) {
      stepData.animated_signals.forEach((signal) => {
        const pathElement = svgDoc.getElementById(signal.path_id);
        if (pathElement) {
          animateSignalBits(pathElement, signal, svgDoc);
        } else {
          console.warn(`Animation path ID not found: ${signal.path_id}`);
        }
      });
    }

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

  // --- Event Listeners ---

  svgObject.addEventListener("load", () => {
    /* Unchanged */
    try {
      svgDoc = svgObject.contentDocument;
      if (svgDoc && svgDoc.documentElement) {
        console.log("SVG loaded successfully.");
        const svgElement = svgDoc.documentElement;
        svgElement.setAttribute("width", "100%");
        svgElement.setAttribute("height", "100%");
        svgElement.setAttribute("preserveAspectRatio", "xMidYMid meet");
        svgElement.style.maxWidth = "100%";
        svgElement.style.maxHeight = "100%";
        svgElement.style.display = "block";
        svgElement.style.margin = "auto";
        resetAllSvgStyles();
      } else {
        console.error("Could not get SVG Document from object.");
      }
    } catch (e) {
      console.error("Error accessing SVG contentDocument:", e);
      updateStatus("Error loading SVG content.", true);
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
    setSimulationState(false); // Start in non-loaded state
    updateMicroStepDisplay(-1, "Idle"); // Set initial micro-step display

    // Set initial placeholder text for structured displays
    if (registerDisplayGrid)
      registerDisplayGrid.innerHTML =
        "<div>(Load program or upload file to view registers)</div>";
    if (pcValueDisplay) pcValueDisplay.textContent = "N/A";
    initializeControlSignalsDisplay();
    if (memoryTabContent)
      memoryTabContent.textContent =
        "(Load program or upload file to view memory)";
    if (logTabContent)
      logTabContent.textContent =
        "Load a program using the 'Compile Code' button or 'Upload File'.\n";

    // --- MODIFIED Initial Tab Activation ---
    // Activate the first tab in the TOP panel
    const firstTopTabButton = document.querySelector(
      "#tabs-panel-top .tab-button"
    );
    const firstTopTabContent = document.querySelector(
      "#tabs-panel-top .tab-content"
    ); // Use the actual content ID if known, e.g., #tab-registers
    if (firstTopTabButton && firstTopTabContent) {
      const topButtons = document.querySelectorAll(
        "#tabs-panel-top .tab-button"
      );
      const topContents = document.querySelectorAll(
        "#tabs-panel-top .tab-content"
      );
      topButtons.forEach((btn) => btn.classList.remove("active"));
      topContents.forEach((content) => {
        content.style.display = "none";
        content.classList.remove("active");
      }); // Hide and remove class

      firstTopTabButton.classList.add("active");
      // Get the specific content ID from the button
      const topTargetId = firstTopTabButton.getAttribute("data-tab");
      const topTargetContent = document.getElementById(`tab-${topTargetId}`);
      if (topTargetContent) {
        topTargetContent.style.display = "block"; // Show
        topTargetContent.classList.add("active"); // Add class
      }
    }

    // Activate the first tab in the BOTTOM panel
    const firstBottomTabButton = document.querySelector(
      "#tabs-panel-bottom .tab-button"
    );
    // const firstBottomTabContent = document.querySelector('#tabs-panel-bottom .tab-content'); // Use the actual content ID if known, e.g., #tab-log
    if (firstBottomTabButton) {
      // Only need button to find target
      const bottomButtons = document.querySelectorAll(
        "#tabs-panel-bottom .tab-button"
      );
      const bottomContents = document.querySelectorAll(
        "#tabs-panel-bottom .tab-content"
      );
      bottomButtons.forEach((btn) => btn.classList.remove("active"));
      bottomContents.forEach((content) => {
        content.style.display = "none";
        content.classList.remove("active");
      }); // Hide and remove class

      firstBottomTabButton.classList.add("active");
      // Get the specific content ID from the button
      const bottomTargetId = firstBottomTabButton.getAttribute("data-tab");
      const bottomTargetContent = document.getElementById(
        `tab-${bottomTargetId}`
      );
      if (bottomTargetContent) {
        bottomTargetContent.style.display = "block"; // Show
        bottomTargetContent.classList.add("active"); // Add class
      }
    }
  }

  initializeUI(); // Call the initialization function
}); // End DOMContentLoaded
