# MillikanCVV1

# Requirements

Python 3.12.1

# Create Environment

python -m venv venv

# Source Virtual Environment

## Powershell 

.\venv\Scripts\Activate.ps1

## Mac 

source venv/bin/activate

# Install Requirements

pip install -r requirements.txt

# Run Tool

python annotationTool.py

# Building the Excutable

pyinstaller.exe --onefile --noconsole --icon=images\experiment_105162.ico --hidden-import=scipy._lib.messagestream --clean annotationTool.py
