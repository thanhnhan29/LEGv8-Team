

class MicroStepState:
    """ Represents the state of the datapath at a specific micro-step for visualization. """
    def __init__(self, stage, micro_step_index, log_msg="", blocks=None, paths=None, signals=None, controls=None):
        self.stage = stage                    # Name of the pipeline stage (e.g., "Fetch")
        self.micro_step_index = micro_step_index # Index within the instruction (0-4)
        self.log_entry = log_msg              # Descriptive log message for this step
        self.active_blocks = blocks if blocks else [] # IDs of highlighted hardware blocks
        self.active_paths = paths if paths else []   # IDs of highlighted data paths
        self.animated_signals = signals if signals else [] # Details for animating signals on paths
        self.control_signals = controls if controls else {} # Values of control signals for this instr

    def to_dict(self):
        """ Returns a JSON-serializable dictionary representation. """
        return {
            "stage": self.stage,
            "micro_step_index": self.micro_step_index,
            "log_entry": self.log_entry,
            "active_blocks": self.active_blocks,
            "active_paths": self.active_paths,
            "animated_signals": self.animated_signals,
            "control_signals": self.control_signals,
            # current_instruction_address/string are added later in the API endpoint
        }