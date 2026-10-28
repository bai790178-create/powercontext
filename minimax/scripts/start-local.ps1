param([Parameter(Mandatory = $true)][string]$SeekdbExe)
$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$seekdbBinary = (Resolve-Path -LiteralPath $SeekdbExe).Path
$projectPython = Join-Path $projectRoot '.venv\Scripts\python.exe'
$runtimeDirectory = Join-Path $projectRoot '.runtime'
$databaseDirectory = Join-Path $runtimeDirectory 'seekdb'
if (-not (Test-Path -LiteralPath $projectPython)) { throw 'Install requirements in .venv first.' }
foreach ($servicePort in @(2882, 8910)) {
    if (Get-NetTCPConnection -State Listen -LocalPort $servicePort -ErrorAction SilentlyContinue) {
        throw "Port $servicePort is already in use. Inspect the existing process before starting."
    }
}
New-Item -ItemType Directory -Path $databaseDirectory -Force | Out-Null
$env:TELEMETRY_ENABLED = 'false'
$databaseArguments = @('--nodaemon', ('--base-dir="' + $databaseDirectory.Replace('\', '/') + '"'), '--port=2882',
    '--parameter', 'memory_budget=2G', '--parameter', 'cpu_count=2',
    '--parameter', 'datafile_size=64M', '--parameter', 'datafile_maxsize=2G',
    '--parameter', 'log_disk_size=2G', '--parameter', 'max_syslog_file_count=3',
    '--parameter', 'enable_rpc_service=false', '--log-level=WARN')
$databaseProcess = Start-Process -FilePath $seekdbBinary -ArgumentList $databaseArguments `
    -WorkingDirectory $databaseDirectory -WindowStyle Hidden -PassThru `
    -RedirectStandardOutput (Join-Path $runtimeDirectory 'seekdb-stdout.log') `
    -RedirectStandardError (Join-Path $runtimeDirectory 'seekdb-stderr.log')
$serviceRecord = @{ project = $projectRoot; seekdb_pid = $databaseProcess.Id; seekdb_exe = $seekdbBinary }
$serviceRecord | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $runtimeDirectory 'services.json') -Encoding utf8
$contextProcess = Start-Process -FilePath $projectPython -ArgumentList @('-X', 'utf8', '-m', 'sdd_context.pc_server') `
    -WorkingDirectory $projectRoot -WindowStyle Hidden -PassThru `
    -RedirectStandardOutput (Join-Path $runtimeDirectory 'powercontext-stdout.log') `
    -RedirectStandardError (Join-Path $runtimeDirectory 'powercontext-stderr.log')
$serviceRecord.powercontext_pid = $contextProcess.Id
$serviceRecord | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $runtimeDirectory 'services.json') -Encoding utf8
Write-Output "seekdb PID $($databaseProcess.Id), SQL port 2882; PowerContext PID $($contextProcess.Id), HTTP port 8910."
Write-Output 'Use python scripts/check-services.py to check readiness; initial database startup takes time.'
