# Watches the Claude desktop app's Chat view (it has no hooks) through Windows UI Automation and
# writes what Claude is doing as a Molina session file. Started by Molina; exits when Molina exits.
# shortcut: matches the app's accessibility labels ("Stop response", "<step> running"); an app update may rename them.
param([string]$Out, [int]$ParentPid)
Add-Type -AssemblyName UIAutomationClient, UIAutomationTypes
$AE = [Windows.Automation.AutomationElement]
$All = [Windows.Automation.TreeScope]::Descendants
$StopCond = New-Object Windows.Automation.PropertyCondition($AE::NameProperty, 'Stop response')
$BtnCond = New-Object Windows.Automation.PropertyCondition($AE::ControlTypeProperty, [Windows.Automation.ControlType]::Button)
$Utf8 = New-Object Text.UTF8Encoding $false   # no BOM: Python's json reader rejects it
$started = $null; $last = ''; $recent = @(); $title = 'Claude chat'
$Thinking = 'Thinking' + [char]0x2026   # this file is read as ANSI, so keep it ASCII
$ErrLog = Join-Path (Split-Path (Split-Path $Out)) 'hook_errors.log'
Remove-Item $Out -ErrorAction SilentlyContinue

function Now { (Get-Date).ToString('yyyy-MM-ddTHH:mm:sszzz') }

function Save($state, $action) {
    $t = Now
    $script:recent = @(@($script:recent) + @{ time = $t; action = $action } | Select-Object -Last 5)  # @() keeps it a list
    $s = [ordered]@{ session_id = 'claude-chat'; project = $script:title; cwd = ''; state = $state; action = $action
        started = $script:started; last_event = $t; recent = @($script:recent); ended = $false }
    [IO.File]::WriteAllText("$Out.tmp", ($s | ConvertTo-Json -Depth 4), $Utf8)
    Move-Item "$Out.tmp" $Out -Force
}

function StepState($step) {
    if ($step -match 'web|search|fetch|brows') { return 'browsing' }
    if ($step -match 'command|code|script|run|execut|analy') { return 'running' }
    if ($step -match 'read|review|look') { return 'reading' }
    if ($step -match 'writ|edit|creat|draft') { return 'writing' }
    return 'thinking'
}

while (Get-Process -Id $ParentPid -ErrorAction SilentlyContinue) {
    try {
        $p = Get-Process claude -ErrorAction SilentlyContinue | Where-Object MainWindowHandle -ne 0 | Select-Object -First 1
        $busy = $false
        if ($p) {
            $root = $AE::FromHandle($p.MainWindowHandle)
            $busy = [bool]$root.FindFirst($All, $StopCond)
        }
        if ($busy) {
            if (-not $started) { $started = Now; $recent = @() }
            $names = @($root.FindAll($All, $BtnCond) | ForEach-Object { $_.Current.Name })
            $t = $names | Where-Object { $_ -cmatch ' Running$' } | Select-Object -First 1   # the chat in the sidebar
            if ($t) { $title = $t -creplace ' Running$', '' }
            $step = $names | Where-Object { $_ -cmatch ' running$' } | Select-Object -First 1  # the live step
            if ($step) { $step = $step -creplace ' running$', ''; $now = @((StepState $step), $step) }
            else { $now = @('thinking', $Thinking) }
        } elseif ($started) {
            $now = @('done', 'Done')
        } else { $now = $null }
        if ($now -and "$now" -ne $last) { Save $now[0] $now[1]; $last = "$now" }
        if ($now -and $now[0] -eq 'done') { $started = $null }
    } catch { Add-Content $ErrLog "$(Now) chat_watch: $($_.Exception.Message)" -ErrorAction SilentlyContinue }
    Start-Sleep -Milliseconds 1000
}
