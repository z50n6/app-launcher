' AppLauncher 静默启动脚本（修正版，防止800a0408错误）
Option Explicit

Dim currentDir, pythonCmd, launcherPath, shell, fso, cmd, result
Set fso = CreateObject("Scripting.FileSystemObject")
Set shell = CreateObject("WScript.Shell")
currentDir = fso.GetParentFolderName(WScript.ScriptFullName)
launcherPath = currentDir & "\\launcher.py"

' 检查 launcher.py 是否存在
If Not fso.FileExists(launcherPath) Then
    MsgBox "错误：找不到 launcher.py 文件！" & vbCrLf & launcherPath, 16, "启动失败"
    WScript.Quit 1
End If

' 检查 python/python3
pythonCmd = ""
On Error Resume Next
result = shell.Run("python --version", 0, True)
If result = 0 Then
    pythonCmd = "python"
Else
    result = shell.Run("python3 --version", 0, True)
    If result = 0 Then
        pythonCmd = "python3"
    Else
        MsgBox "错误：找不到Python环境！", 16, "启动失败"
        WScript.Quit 1
    End If
End If
On Error GoTo 0

' 拼接命令，静默启动
cmd = "cmd /c cd /d """ & currentDir & """ && " & pythonCmd & " launcher.py"
shell.Run cmd, 0, False  ' 0=隐藏窗口, False=不等待

Set shell = Nothing
Set fso = Nothing