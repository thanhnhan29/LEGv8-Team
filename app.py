# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, jsonify
import traceback

# Import from our simulator package
from simulator.simulator_engine import SimulatorEngine
from simulator.assembler import Assembler

app = Flask(__name__)

# --- Global Simulation Instances ---
# These are created once when the Flask app starts.
simulator_engine = SimulatorEngine()
assembler = Assembler()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/load', methods=['POST'])
def api_load():
    print("\n>>> Received /api/load request <<<")
    try:
        data = request.get_json()
        if not data or 'code' not in data: raise ValueError("Missing 'code' field")
        code = data['code']
        if not isinstance(code, str): raise ValueError("'code' must be a string")

        # Use the Assembler to parse the code
        processed_instr, raw_instr, labels = assembler.parse(code)
        
        # Load the parsed data into the simulator engine
        instr_count = simulator_engine.load_program_data(processed_instr, raw_instr, labels)

        simulator_engine._save_state_snapshot()
        return jsonify({
            "status": "success",
            "message": f"{instr_count} instructions loaded. Ready to run.",
            "cpu_state": simulator_engine.get_cpu_state_for_api(),
            "initial_instr_addr": f"0x{simulator_engine.current_instr_addr_for_display:X}",
            "initial_instr_str": simulator_engine.current_instr_str_for_display,
            "can_return_back": simulator_engine.can_return_back()
        })

    except Exception as e:
        print(f"[ERROR] /api/load failed: {e}")
        traceback.print_exc()
        simulator_engine.initialize_state() # Reset simulator on load failure
        return jsonify({"status": "error", "message": f"Load failed: {e}"}), 400

@app.route('/api/micro_step', methods=['POST'])
def api_micro_step():
    global simulator_engine # We are interacting with the global instance
    print(f"\n>>> Received /api/micro_step (Current Sim PC=0x{simulator_engine.pc:X}) <<<")
    
    # The simulator_engine.step_micro() now handles most of the logic
    # that was previously in this API endpoint.
    response_data = simulator_engine.step_micro()
    
    # Determine HTTP status code based on simulator's response status
    http_status_code = 200
    if response_data.get("status") == "error":
        http_status_code = 500 # Internal Server Error for simulation runtime errors
    elif response_data.get("status") == "finished_program":
         http_status_code = 200 # Normal finish
    
    return jsonify(response_data), http_status_code


@app.route('/api/return_back', methods=['POST'])
def api_return_back():
    print(f"\n>>> Received /api/return_back (Current Sim PC=0x{simulator_engine.pc:X}) <<<")
    
    # Call the return_back method from simulator_engine
    response_data = simulator_engine.return_back()
    
    # Determine HTTP status code based on simulator's response status
    http_status_code = 200
    if response_data.get("status") == "error":
        http_status_code = 400  # Bad Request for return back errors
    
    return jsonify(response_data), http_status_code

@app.route('/api/reset', methods=['POST'])
def api_reset_state():
    print("\n>>> Received /api/reset request <<<")
    simulator_engine.initialize_state()
    assembler.label_table.clear() # Also clear assembler state if any
    assembler.instruction_memory.clear()
    assembler.raw_instruction_memory.clear()
    simulator_engine._save_state_snapshot()
    return jsonify({
        "status": "success",
        "message": "Simulator has been reset.",
        "cpu_state": simulator_engine.get_cpu_state_for_api(),
        "can_return_back": simulator_engine.can_return_back()
    })

if __name__ == '__main__':
    print("=================================================")
    print(" Starting LEGv8 Simulator Flask Web Server (Refactored)")
    print(" Access at: http://localhost:5010")
    print("=================================================")
    # Initialize state explicitly at startup, though constructor does it too.
    simulator_engine.initialize_state() 
    app.run(debug=True, host='0.0.0.0', port=5010, threaded=False)