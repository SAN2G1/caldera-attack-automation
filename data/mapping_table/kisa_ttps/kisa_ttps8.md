# MITRE ATT&CK TTPs

## Reconnaissance
- T1596.005 Search Open Technical Databases: Scan Databases

## Initial Access
- T1190 Exploit Public-Facing Application

## Execution
- T1569.002 System Services: Service Execution
- T1059.003 Command and Scripting Interpreter: Windows Command Shell
- T1059.006 Command and Scripting Interpreter: Python
- T1047 Windows Management Instrumentation

## Persistence
- T1547.001 Boot or Logon Autostart Execution: Registry Run Keys / Startup Folder
- T1543.004 Create or Modify System Process: Launch Daemon

## Defense Evasion
- T1140 Deobfuscate/Decode Files or Information
- T1036.005 Masquerading: Match Legitimate Name or Location
- T1055.003 Process Injection: Thread Execution Hijacking
- T1070 Indicator Removal on Host
- T1070.001 Indicator Removal on Host: Clear Windows Event Logs
- T1070.004 Indicator Removal on Host: File Deletion
- T1562.009 Impair Defenses: Safe Mode Boot
- T1218.007 System Binary Proxy Execution: Msiexec
- T1222.002 File and Directory Permissions Modification: Linux and Mac File and Directory Permissions Modification

## Credential Access
- T1003.001 OS Credential Dumping: LSASS Memory

## Discovery
- T1046 Network Service Discovery

## Lateral Movement
- T1021.002 Remote Services: SMB/Windows Admin Shares
- T1021.006 Remote Service: Windows Remote Management
- T1072 Software Deployment Tools
- T1570 Lateral Tool Transfer

## Command and Control
- T1071.001 Application Layer Protocol: Web Protocols
- T1090.001 Proxy: Internal Proxy

## Exfiltration
- T1048.003 Exfiltration Over Alternative Protocol: Exfiltration Over Unencrypted Non-C2 Protocol

## Impact
- T1485 Data Destruction
- T1489 Service Stop
- T1490 Inhibit System Recovery
- T1529 System Shutdown/Reboot