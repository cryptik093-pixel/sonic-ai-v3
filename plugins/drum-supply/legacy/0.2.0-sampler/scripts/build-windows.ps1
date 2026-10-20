param([switch]$CoreOnly, [ValidateRange(1,8)][int]$Jobs=1)
$ErrorActionPreference='Stop'
$drumRoot=Split-Path -Parent $PSScriptRoot
$drumCoreOnly=$CoreOnly
. "$PSScriptRoot/toolchain-windows.ps1" -Jobs $Jobs
$drumBuild=if($drumCoreOnly){"$drumRoot/build-core"}else{"$drumRoot/build"}
$drumOption=if($drumCoreOnly){'OFF'}else{'ON'}
$drumArgs=@('-DDRUM_JUCE_PACKAGE=')
$cachedJuce="$drumRoot/../sonic-pocket/build/deps/JUCE-8.0.16-security"
$cachedArchive="$drumRoot/../sonic-pocket/build/juce.zip"
if((Test-Path "$cachedJuce/CMakeLists.txt") -and (Test-Path $cachedArchive)) {
  if((Get-FileHash $cachedArchive).Hash -ne '7F75CEE28EA4DD216FC49BA6FB57F4BAA14729EF97529040D3A99DD04910F166'){throw 'JUCE cache archive mismatch'}
  $drumArgs+="-DFETCHCONTENT_SOURCE_DIR_JUCE=$cachedJuce"
  $cachedExport="$drumRoot/../sonic-pocket/build/_deps/juce-build/JUCEExportConfig.cmake"
  $cachedTool="$drumRoot/../sonic-pocket/build/_deps/juce-build/tools/extras/Build/juceaide/juceaide_artefacts/Custom/juceaide.exe"
  if(!$drumCoreOnly -and (Test-Path $cachedExport) -and (Test-Path $cachedTool)) {
    $toolVersion=& $cachedTool version
    if(!$LASTEXITCODE -and $toolVersion -match '^JUCE v8\.0\.16$'){$drumArgs+="-DDRUM_JUCE_PACKAGE=$cachedExport"}
  }
}
& cmake -S $drumRoot -B $drumBuild -G Ninja -DCMAKE_BUILD_TYPE=Release "-DCMAKE_C_COMPILER=$compilerDir/cl.exe" "-DCMAKE_CXX_COMPILER=$compilerDir/cl.exe" "-DDRUM_BUILD_PLUGIN=$drumOption" @drumArgs
if($LASTEXITCODE){throw 'Drum configure failed'}
& cmake --build $drumBuild --parallel $Jobs
if($LASTEXITCODE){throw 'Drum build failed'}
& ctest --test-dir $drumBuild --output-on-failure
if($LASTEXITCODE){throw 'Drum tests failed'}
