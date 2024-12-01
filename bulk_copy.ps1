param(
  [string]$src,
  [string]$dest)
  

if(!(Test-Path -Path $src)) {
  throw "invalid source '$src'"
  exit 1
}
if(!(Test-Path -Path $dest)) {
  New-Item -ItemType Directory -Force -Path $dest
  if(!(Test-Path -Path $dest)) {
    throw "invalid destination '$dest'"
  }
}
robocopy $src $dest /e /z /j /move /mt:24 /log:"./logs/$(Get-Date -Format yyyy-MM-dd-mm-ss)-robocopy.log"

Write-Output "Completed copy from: '$src' to: '$dest"
