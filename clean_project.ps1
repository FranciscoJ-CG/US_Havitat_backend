# Change to the script directory
Set-Location -Path (Split-Path -Parent $MyInvocation.MyCommand.Definition)

# Function to clean specified directory
function Clean-Directory($path) {
    # Delete cache files
    Get-ChildItem -Path $path -Recurse -Force -Include __pycache__ | Remove-Item -Recurse -Force

    # Delete all migration files except __init__.py
    Get-ChildItem -Path $path -Recurse -Force -Include *.py, *.pyc | Where-Object { 
        $_.FullName -match "\\migrations\\" -and $_.Name -ne "__init__.py" 
    } | Remove-Item -Force
}

# Get all directories except 'venv'
$directories = Get-ChildItem -Directory -Exclude 'venv'

foreach ($dir in $directories) {
    Clean-Directory $dir.FullName
}

# Delete SQLite database
$dbPath = "db.sqlite3"
if (Test-Path $dbPath) {
    Remove-Item $dbPath -Force
    Write-Output "$dbPath deleted"
} else {
    Write-Output "$dbPath not found"
}

Write-Output "Cleaning complete"
