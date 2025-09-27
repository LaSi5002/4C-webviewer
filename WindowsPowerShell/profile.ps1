
#region conda initialize
# !! Contents within this block are managed by 'conda init' !!
If (Test-Path "D:\Programs\anaconda3\Scripts\conda.exe") {
    (& "D:\Programs\anaconda3\Scripts\conda.exe" "shell.powershell" "hook") | Out-String | ?{$_} | Invoke-Expression
}
#endregion
