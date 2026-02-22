Write-Host "================================" -ForegroundColor Cyan
Write-Host "   ST3215 Servo Control" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Run application
python UI.py

# Pause if running from explorer
if (System.Management.Automation.Internal.Host.InternalHost.Name -eq "ConsoleHost") {
    Write-Host "
Press any key to exit..." -ForegroundColor Yellow
     = System.Management.Automation.Internal.Host.InternalHost.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}
