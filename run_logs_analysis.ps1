$pythonPath = "C:\Users\New\AppData\Local\Programs\Python\Python39\python.exe"
$scriptPath = "main.py"

& $pythonPath "$scriptPath"

$trigger = New-ScheduledTaskTrigger -Once -RepetitionInterval (New-TimeSpan -Minutes 1)
$action = New-ScheduledTaskAction -Execute "$pythonPath" -Argument "`"$scriptPath`""
Register-ScheduledTask -TaskName "LogsAnalysisTask" -Trigger $trigger -Action $action