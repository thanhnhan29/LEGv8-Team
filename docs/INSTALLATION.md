# Installation Guide

## Prerequisites

- **Python 3.9 or higher**
- **Modern web browser** (Chrome, Firefox, Safari, Edge)
- **Git** (for cloning the repository)

## Installation Steps

### 1. Clone the Repository

```bash
git clone https://github.com/thanhnhan29/LEGv8-Team.git
cd LEGv8-Team
```

### 2. Set Up Python Environment (Optional but Recommended)

Create a virtual environment:

```bash
# Create virtual environment
python -m venv legv8-env

# Activate virtual environment
# On Windows:
legv8-env\Scripts\activate
# On macOS/Linux:
source legv8-env/bin/activate
```

### 3. Install Dependencies

```bash
pip install flask
```

Or if you have a requirements.txt file:

```bash
pip install -r requirements.txt
```

### 4. Run the Simulator

```bash
python app.py
```

### 5. Open in Browser

Navigate to: `http://localhost:5010`

## Troubleshooting

### Python Version Issues

Check your Python version:

```bash
python --version
```

If using Python 2, try:

```bash
python3 app.py
```

### Missing Dependencies

Install Flask manually:

```bash
pip install Flask==2.3.3
```



```
