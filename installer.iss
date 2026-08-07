[Setup]
AppName=DJ CamelTrack
AppVersion=3.0
DefaultDirName={pf}\DJ CamelTrack
DefaultGroupName=DJ CamelTrack
UninstallDisplayIcon={app}\DJ CamelTrack.exe
Compression=lzma2
SolidCompression=yes
OutputDir=userdocs:Inno Setup Examples Output
OutputBaseFilename=DJ_CamelTrack_Setup

[Files]
Source: "dist\DJ CamelTrack.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "genre_model.pkl"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\DJ CamelTrack"; Filename: "{app}\DJ CamelTrack.exe"
Name: "{group}\Uninstall DJ CamelTrack"; Filename: "{uninstallexe}"
Name: "{commondesktop}\DJ CamelTrack"; Filename: "{app}\DJ CamelTrack.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop icon"; GroupDescription: "Additional icons:"
