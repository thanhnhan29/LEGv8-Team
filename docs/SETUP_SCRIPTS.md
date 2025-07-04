# Setup Scripts

The LEGv8 Simulator includes automated setup scripts to make installation easier:

## Windows Setup

Run the batch file:

```batch
run_simulator.bat
```

## Mac/Linux Setup

Make the script executable and run:

```bash
chmod +x run_simulator.sh
./run_simulator.sh
```

## What the Scripts Do

Both scripts automatically:

1. **Check Python installation** - Verifies Python 3.9+ is installed
2. **Install Python if needed** - Downloads and installs Python 3.9
3. **Install dependencies** - Runs `pip install -r requirements.txt`
4. **Start the simulator** - Launches the Flask application
5. **Open browser** - Navigate to `http://localhost:5010`

## Manual Installation

If you prefer manual setup:

1. **Install Python 3.9+** from https://python.org
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Run the simulator**:
   ```bash
   python app.py
   ```

## Requirements

The `requirements.txt` file includes:

- **Flask 2.3.3** - Web framework
- **flask-cors 4.0.0** - Cross-origin resource sharing

## Troubleshooting

If you encounter issues:

1. **Python not found**: Ensure Python 3.9+ is installed and in PATH
2. **Permission denied**: On Unix systems, run `chmod +x run_simulator.sh`
3. **Port 5010 busy**: The script will show an error, try stopping other services
4. **Dependencies fail**: Try upgrading pip with `pip install --upgrade pip`

The scripts are designed to be idempotent - you can run them multiple times safely.
