<#
Configura un equipo Windows para trabajar en un proyecto tipográfico del pipeline común.

Instala Git, GitHub CLI, Mise, FontForge y Potrace; configura Git y la sesión
de GitHub; activa Mise en PowerShell; clona el repositorio de la fuente (con el
pipeline común como submódulo) y prepara el entorno.
Se puede correr varias veces: lo que ya está instalado se omite.

Uso (PowerShell normal, no hace falta administrador):
    powershell -ExecutionPolicy Bypass -File .\setup-windows.ps1 -Repo citlalli-hg/sterna
Se puede repetir con cada fuente (citlalli-hg/elocaso, citlalli-hg/sterna...).
Opcional:
    -Destino "D:\Proyectos"   carpeta donde clonar (por defecto Documentos\GitHub)
#>
param(
    [string]$Destino = (Join-Path ([Environment]::GetFolderPath("MyDocuments")) "GitHub"),
    [string]$Repo = ""
)
# "Continue": en Windows PowerShell 5.1, "Stop" convierte en error cualquier
# mensaje que un programa escriba en stderr. Los fallos se revisan con $LASTEXITCODE.
$ErrorActionPreference = "Continue"
if (-not $Repo) {
    $Repo = Read-Host "Repositorio de la fuente (por ejemplo citlalli-hg/sterna)"
    if (-not $Repo) { throw "Indica el repositorio con -Repo citlalli-hg/<fuente>" }
}

function Paso($texto) { Write-Host "`n==> $texto" -ForegroundColor Cyan }
function Refrescar-Path {
    $env:Path = [Environment]::GetEnvironmentVariable("Path", "Machine") + ";" +
                [Environment]::GetEnvironmentVariable("Path", "User")
}
function Instalar($id, $nombre) {
    winget list --id $id -e --accept-source-agreements *> $null
    if ($LASTEXITCODE -eq 0) { Write-Host "  $nombre ya está instalado"; return }
    Write-Host "  Instalando $nombre..."
    winget install --id $id -e --silent --accept-source-agreements --accept-package-agreements
    if ($LASTEXITCODE -ne 0) { throw "No se pudo instalar $nombre ($id)" }
}

# 1. Programas ----------------------------------------------------------------
Paso "Instalando programas con winget"
if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
    throw "No encontré winget. Instala 'App Installer' desde Microsoft Store y vuelve a correr el script."
}
Instalar "Git.Git" "Git"
Instalar "GitHub.cli" "GitHub CLI"
Instalar "jdx.mise" "Mise"
Instalar "FontForge.FontForge" "FontForge"
Refrescar-Path

# 2. Potrace (no está en winget: se descarga el binario oficial) -------------
Paso "Potrace"
if (Get-Command potrace -ErrorAction SilentlyContinue) {
    Write-Host "  Potrace ya está instalado"
} else {
    $base = Join-Path $env:LOCALAPPDATA "Programs\potrace"
    $zip = Join-Path $env:TEMP "potrace.zip"
    try {
        Invoke-WebRequest "https://potrace.sourceforge.net/download/1.16/potrace-1.16.win64.zip" -OutFile $zip -UseBasicParsing
        Expand-Archive $zip -DestinationPath $base -Force
        $bin = (Get-ChildItem $base -Recurse -Filter potrace.exe | Select-Object -First 1).DirectoryName
        $userPath = [Environment]::GetEnvironmentVariable("Path", "User")
        if ($userPath -notlike "*$bin*") {
            [Environment]::SetEnvironmentVariable("Path", "$userPath;$bin", "User")
        }
        Refrescar-Path
        Write-Host "  Potrace instalado en $bin"
    } catch {
        Write-Warning "No pude descargar Potrace. Bájalo de https://potrace.sourceforge.net (Windows 64-bit), descomprímelo y agrega la carpeta al PATH."
    }
}

# 3. Git ----------------------------------------------------------------------
Paso "Configurando Git"
if (-not (git config --global user.name)) {
    $n = Read-Host "Tu nombre para los commits [Citlalli HG]"
    if (-not $n) { $n = "Citlalli HG" }
    git config --global user.name $n
}
if (-not (git config --global user.email)) {
    $e = Read-Host "Tu correo de GitHub [citlallihg@gmail.com]"
    if (-not $e) { $e = "citlallihg@gmail.com" }
    git config --global user.email $e
}
git config --global init.defaultBranch main
git config --global pull.rebase false
# Al hacer pull o cambiar de rama, el submódulo pipeline/ se pone en la versión que fija el proyecto
git config --global submodule.recurse true
Write-Host "  $(git config --global user.name) <$(git config --global user.email)>"

# 4. GitHub ------------------------------------------------------------------
Paso "Sesión de GitHub"
gh auth status *> $null
if ($LASTEXITCODE -ne 0) {
    Write-Host "  Se abrirá el navegador: copia el código que aparece aquí y autoriza GitHub CLI."
    gh auth login --hostname github.com --git-protocol https --web
}
gh auth setup-git

# 5. Mise en PowerShell -------------------------------------------------------
Paso "Activando Mise en PowerShell"
$linea = '(&mise activate pwsh) | Out-String | Invoke-Expression'
if (-not (Test-Path $PROFILE)) { New-Item -ItemType File -Path $PROFILE -Force | Out-Null }
if (-not (Select-String -Path $PROFILE -SimpleMatch $linea -Quiet)) {
    Add-Content -Path $PROFILE -Value "`n# Mise`n$linea"
    Write-Host "  Agregado a $PROFILE"
} else { Write-Host "  Ya estaba activo" }
# Respaldo: los shims de Mise en el PATH del usuario
$shims = Join-Path $env:LOCALAPPDATA "mise\shims"
$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($userPath -notlike "*$shims*") {
    [Environment]::SetEnvironmentVariable("Path", "$userPath;$shims", "User")
}
Refrescar-Path

# 6. Repositorio -------------------------------------------------------------
Paso "Clonando $Repo"
New-Item -ItemType Directory -Path $Destino -Force | Out-Null
$carpeta = Join-Path $Destino ($Repo.Split("/")[1])
if (Test-Path (Join-Path $carpeta ".git")) {
    Write-Host "  Ya existe en $carpeta; actualizando"
    git -C $carpeta pull --ff-only
} else {
    gh repo clone $Repo $carpeta -- --recurse-submodules
    if ($LASTEXITCODE -ne 0) { throw "No se pudo clonar $Repo" }
}
Set-Location $carpeta
git submodule update --init
if (-not (Test-Path "pipeline\tareas.toml")) {
    throw "Falta el pipeline común en pipeline\. ¿El repo ya usa el submódulo? (ver pipeline/docs/proyectos.md)"
}

# 7. Entorno del proyecto -----------------------------------------------------
Paso "Preparando el entorno con Mise"
mise trust
mise install
mise run setup
mise run doctor

Write-Host "`nListo. Abre una nueva ventana de PowerShell en $carpeta y corre 'mise tasks' para ver las tareas." -ForegroundColor Green
