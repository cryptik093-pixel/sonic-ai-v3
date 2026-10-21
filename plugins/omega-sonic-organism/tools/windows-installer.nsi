Unicode True
!include "MUI2.nsh"
!include "x64.nsh"
!include "FileFunc.nsh"
!ifndef PAYLOAD
  !error "Set PAYLOAD to the validated delivery directory"
!endif
!ifndef OUTFILE
  !error "Set OUTFILE to the installer path"
!endif
Name "OMEGA SONIC ORGANISM 1.0 RC1 - Unqualified"
OutFile "${OUTFILE}"
!ifdef USERTEST
RequestExecutionLevel user
!else
RequestExecutionLevel admin
!endif
InstallDir "$COMMONFILES64\VST3"
SetCompressor zlib
VIProductVersion "1.0.0.1"
VIAddVersionKey /LANG=1033 "ProductName" "OMEGA SONIC ORGANISM"
VIAddVersionKey /LANG=1033 "CompanyName" "Omega House Studio LLC"
VIAddVersionKey /LANG=1033 "FileDescription" "Windows x64 VST3 installer"
VIAddVersionKey /LANG=1033 "FileVersion" "1.0.0-rc.1"
VIAddVersionKey /LANG=1033 "LegalCopyright" "Omega House Studio LLC"
!define MUI_ABORTWARNING
!define MUI_WELCOMEPAGE_TEXT "Install the offline Windows x64 VST3 instrument and its 30 factory patches.$\r$\n$\r$\nThis is a preview build. Existing installations are preserved.$\r$\n$\r$\nAfter installation, open FL Studio > Options > Manage plugins. Enable Verify plugins and click Find installed plugins."
!define MUI_FINISHPAGE_TEXT "The VST3 bundle is installed.$\r$\n$\r$\nIn FL Studio: Options > Manage plugins > enable Verify plugins > Find installed plugins.$\r$\n$\r$\nAdd OMEGA SONIC ORGANISM as a Generator.$\r$\n$\r$\nInstallation and VST3 validation are separate from FL Studio session acceptance."
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_LANGUAGE "English"
Function .onInit
  ${IfNot} ${RunningX64}
    MessageBox MB_ICONSTOP "This instrument requires Windows x64."
    Abort
  ${EndIf}
FunctionEnd
Section "Windows x64 VST3 instrument"
  InitPluginsDir
  SetOutPath "$PLUGINSDIR\payload"
  File /r "${PAYLOAD}\*.*"
  WriteUninstaller "$PLUGINSDIR\payload\OmegaSonicOrganism.vst3\Uninstall.exe"
  SetOutPath "$PLUGINSDIR\payload\OmegaSonicOrganism.vst3"
  File "uninstall-user.ps1"
  ${DisableX64FSRedirection}
  nsExec::ExecToStack '"$SYSDIR\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -ExecutionPolicy Bypass -File "$PLUGINSDIR\payload\tools\install-user.ps1" -PackageRoot "$PLUGINSDIR\payload" -Directory "$INSTDIR"'
  Pop $0
  Pop $1
  ${EnableX64FSRedirection}
  DetailPrint "$1"
  ${If} $0 != 0
    FileOpen $2 "$INSTDIR\OmegaSonicOrganism-install-error.log" w
    FileWrite $2 "PowerShell exit: $0$\r$\n$1"
    FileClose $2
    MessageBox MB_ICONSTOP "Installation did not complete. Existing files were preserved.$\r$\n$\r$\n$1" /SD IDOK
    SetErrorLevel 1
    Abort
  ${EndIf}
!ifndef USERTEST
  SetRegView 64
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\OmegaSonicOrganism" "DisplayName" "OMEGA SONIC ORGANISM 1.0 RC1 - Unqualified"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\OmegaSonicOrganism" "DisplayVersion" "1.0.0-rc.1"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\OmegaSonicOrganism" "Publisher" "Omega House Studio LLC"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\OmegaSonicOrganism" "UninstallString" '$\"$INSTDIR\OmegaSonicOrganism.vst3\Uninstall.exe$\"'
  WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\OmegaSonicOrganism" "NoModify" 1
  WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\OmegaSonicOrganism" "NoRepair" 1
!endif
SectionEnd
Section "Uninstall"
  ${GetParent} "$EXEDIR" $0
  ${DisableX64FSRedirection}
  nsExec::ExecToStack '"$SYSDIR\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -ExecutionPolicy Bypass -File "$EXEDIR\uninstall-user.ps1" -Directory "$0"'
  Pop $1
  Pop $2
  ${EnableX64FSRedirection}
  DetailPrint "$2"
!ifdef USERTEST
  ; The NSIS bootstrap exits before the copied uninstaller. Record the actual
  ; child result in the owned fixture directory instead of trusting its parent.
  FileOpen $3 "$0\fixture-uninstall-result.log" w
  FileWrite $3 "$1$\r$\n$2"
  FileClose $3
!endif
  ${If} $1 != 0
    MessageBox MB_ICONSTOP "Modified or unfamiliar files were preserved. Nothing removed.$\r$\n$2" /SD IDOK
    SetErrorLevel 1
    Abort
  ${EndIf}
!ifndef USERTEST
  SetRegView 64
  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\OmegaSonicOrganism"
!endif
SectionEnd
