# Rebuild the PCB and run DRC.   .\run.ps1 [-NoRoute] [-Pads]
param([switch]$NoRoute, [switch]$Pads)
$k = "C:\Program Files\KiCad\9.0\bin"
$h = Join-Path $PSScriptRoot "..\handheld"
$a = @()
if ($NoRoute) { $a += "--noroute" }
if ($Pads) { $a += "--pads" }
& "$k\python.exe" "$PSScriptRoot\gen_pcb.py" @a
if ($LASTEXITCODE -ne 0) { exit 1 }
& "$k\kicad-cli.exe" pcb drc --severity-all --schematic-parity --format json -o "$h\drc.json" "$h\handheld.kicad_pcb"
& "$k\python.exe" "$PSScriptRoot\drc_sum.py" "$h\drc.json"
