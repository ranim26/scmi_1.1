' ================================================================
' SysMonAgent_XP.vbs - Lance l'agent XP sans fenetre visible
' Utilise par le demarrage automatique Windows
' ================================================================

Dim shell
Set shell = CreateObject("WScript.Shell")

' Chemin vers le batch (meme dossier que ce vbs)
Dim scriptDir
scriptDir = Left(WScript.ScriptFullName, InStrRev(WScript.ScriptFullName, "\"))

Dim batPath
batPath = scriptDir & "SysMonAgent_XP.bat"

' Lancer sans fenetre (0 = fenetre cachee)
shell.Run "cmd.exe /c """ & batPath & """", 0, False

Set shell = Nothing
