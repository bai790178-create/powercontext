$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$recordPath = Join-Path $projectRoot '.runtime\services.json'
$record = Get-Content -LiteralPath $recordPath -Raw | ConvertFrom-Json
if ($record.project -ne $projectRoot) { throw 'Service record does not belong to this project.' }
foreach ($serviceName in @('powercontext', 'seekdb')) {
    $processId = $record.($serviceName + '_pid')
    if (-not $processId) { continue }
    $serviceProcess = Get-CimInstance Win32_Process -Filter "ProcessId=$processId"
    if (-not $serviceProcess) { continue }
    if ($serviceName -eq 'seekdb') {
        $owned = $serviceProcess.ExecutablePath -eq $record.seekdb_exe -and
            $serviceProcess.CommandLine.Contains(($projectRoot + '\.runtime\seekdb').Replace('\', '/'))
    } else {
        $owned = $serviceProcess.ExecutablePath -eq (Join-Path $projectRoot '.venv\Scripts\python.exe') -and
            $serviceProcess.CommandLine.Contains('sdd_context.pc_server')
    }
    if (-not $owned) { throw "PID $processId no longer matches this project's $serviceName service." }
    if ($serviceName -eq 'powercontext') {
        # Windows venv python.exe may own a separate base-interpreter child.
        Get-CimInstance Win32_Process -Filter "ParentProcessId=$processId" |
            Where-Object { $_.Name -eq 'python.exe' -and $_.CommandLine.Contains('sdd_context.pc_server') } |
            ForEach-Object { Stop-Process -Id $_.ProcessId }
    }
    if (Get-Process -Id $processId -ErrorAction SilentlyContinue) { Stop-Process -Id $processId }
    Write-Output "Stopped $serviceName PID $processId. Data is retained."
}
