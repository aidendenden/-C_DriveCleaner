Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
base = fso.GetParentFolderName(WScript.ScriptFullName)
args = ""
For Each arg In WScript.Arguments
  args = args & " " & Chr(34) & Replace(arg, Chr(34), Chr(34) & Chr(34)) & Chr(34)
Next
shell.CurrentDirectory = base
shell.Run "pyw """ & base & "\c_drive_cleaner.py""" & args, 0, False
