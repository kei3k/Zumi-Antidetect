Set objShell = CreateObject("WScript.Shell")
Set objFSO = CreateObject("Scripting.FileSystemObject")

' Get the directory where this script is located
strScriptPath = WScript.ScriptFullName
strScriptDir = objFSO.GetParentFolderName(strScriptPath)

' Change to that directory
objShell.CurrentDirectory = strScriptDir

' Run Python script hidden (0 = hidden window)
' Use pythonw.exe instead of python.exe to avoid console window
objShell.Run "pythonw.exe run.py", 0, False
