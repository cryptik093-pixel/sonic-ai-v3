cmake_minimum_required(VERSION 3.24)
project(OmegaDrumSupply VERSION 0.2.0 LANGUAGES C CXX)
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_MSVC_RUNTIME_LIBRARY "MultiThreaded$<$<CONFIG:Debug>:Debug>")
include(CTest)
option(DRUM_BUILD_PLUGIN "Build native JUCE VST3" ON)
add_executable(DrumDspTests Tests/DspTests.cpp)
target_include_directories(DrumDspTests PRIVATE Source)
add_test(NAME DrumDsp COMMAND DrumDspTests)
add_executable(DrumSampleTests Tests/SampleTests.cpp)
target_include_directories(DrumSampleTests PRIVATE Source)
add_test(NAME DrumSample COMMAND DrumSampleTests)
if(DRUM_BUILD_PLUGIN)
  set(DRUM_JUCE_PACKAGE "" CACHE FILEPATH "Optional existing JUCE build-tree package")
  if(DRUM_JUCE_PACKAGE)
    get_filename_component(drum_juce_export_dir "${DRUM_JUCE_PACKAGE}" DIRECTORY)
    file(READ "${DRUM_JUCE_PACKAGE}" drum_juce_package)
    # This pinned JUCE build export unconditionally imports a missing LV2 helper.
    # This instrument builds VST3 only. Adapt a generated LOCAL copy, preserving
    # the existing project/SDK; resolve its relative tool paths to the original.
    string(REPLACE "\${CMAKE_CURRENT_LIST_DIR}" "${drum_juce_export_dir}" drum_juce_package "${drum_juce_package}")
    string(REPLACE "include(\"${drum_juce_export_dir}/LV2_HELPER.cmake\")"
      "include(\"${drum_juce_export_dir}/LV2_HELPER.cmake\" OPTIONAL)" drum_juce_package "${drum_juce_package}")
    file(WRITE "${CMAKE_BINARY_DIR}/JUCE-local-package.cmake" "${drum_juce_package}")
    include("${CMAKE_BINARY_DIR}/JUCE-local-package.cmake")
    get_filename_component(juce_SOURCE_DIR "${JUCE_MODULES_DIR}/.." ABSOLUTE)
  else()
    include(FetchContent)
    FetchContent_Declare(JUCE URL https://github.com/juce-framework/JUCE/archive/refs/tags/8.0.16-security.zip
      URL_HASH SHA256=7f75cee28ea4dd216fc49ba6fb57f4baa14729ef97529040d3a99dd04910f166 DOWNLOAD_EXTRACT_TIMESTAMP FALSE)
    FetchContent_MakeAvailable(JUCE)
  endif()
  if(MSVC)
    file(GLOB ui_units "${juce_SOURCE_DIR}/modules/juce_gui_basics/*.cpp" "${juce_SOURCE_DIR}/modules/juce_graphics/*.cpp")
    set_source_files_properties(${ui_units} PROPERTIES COMPILE_OPTIONS "$<$<CONFIG:Release>:/O1>")
  endif()
  juce_add_plugin(OmegaDrumSupply COMPANY_NAME "Omega House Studio LLC" BUNDLE_ID "com.omegahousestudio.drumsupply"
    PLUGIN_MANUFACTURER_CODE OmHs PLUGIN_CODE OhDs FORMATS VST3
    PRODUCT_NAME "Omega Drum Supply" DESCRIPTION "Seven-slot sample drum instrument"
    VST3_CATEGORIES Instrument Synth IS_SYNTH TRUE NEEDS_MIDI_INPUT TRUE NEEDS_MIDI_OUTPUT FALSE
    IS_MIDI_EFFECT FALSE EDITOR_WANTS_KEYBOARD_FOCUS TRUE COPY_PLUGIN_AFTER_BUILD FALSE)
  juce_add_binary_data(DrumFactory SOURCES Assets/starter0.wav Assets/starter1.wav Assets/starter2.wav Assets/starter3.wav Assets/starter4.wav Assets/starter5.wav Assets/starter6.wav)
  target_sources(OmegaDrumSupply PRIVATE Source/PluginProcessor.cpp Source/PluginEditor.cpp Source/SampleLibrary.cpp)
  target_include_directories(OmegaDrumSupply PUBLIC Source)
  target_compile_definitions(OmegaDrumSupply PUBLIC JUCE_WEB_BROWSER=0 JUCE_USE_CURL=0 JUCE_VST3_CAN_REPLACE_VST2=0)
  target_link_libraries(OmegaDrumSupply PRIVATE DrumFactory juce::juce_audio_processors juce::juce_audio_formats juce::juce_cryptography
    PUBLIC juce::juce_recommended_config_flags juce::juce_recommended_warning_flags)
  add_executable(DrumProcessorTests Tests/ProcessorTests.cpp)
  target_link_libraries(DrumProcessorTests PRIVATE OmegaDrumSupply)
  target_include_directories(DrumProcessorTests PRIVATE $<TARGET_PROPERTY:OmegaDrumSupply,INCLUDE_DIRECTORIES>)
  target_compile_definitions(DrumProcessorTests PRIVATE $<TARGET_PROPERTY:OmegaDrumSupply,COMPILE_DEFINITIONS>)
  add_test(NAME DrumProcessor COMMAND DrumProcessorTests)
endif()
