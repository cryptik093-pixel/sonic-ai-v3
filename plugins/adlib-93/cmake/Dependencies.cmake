include(FetchContent)
# Optional reuse of juceaide built from this same pinned JUCE revision. This
# avoids recompiling an unchanged host build tool on the recovery workstation.
# The default remains JUCE's normal self-contained bootstrap.
set(ADLIB93_JUCEAIDE_PATH "" CACHE FILEPATH "Existing juceaide from the pinned JUCE revision")
if(ADLIB93_JUCEAIDE_PATH)
    if(NOT EXISTS "${ADLIB93_JUCEAIDE_PATH}")
        message(FATAL_ERROR "The explicitly supplied juceaide does not exist")
    endif()
    execute_process(COMMAND "${ADLIB93_JUCEAIDE_PATH}" version
        RESULT_VARIABLE aide_result OUTPUT_VARIABLE aide_version ERROR_VARIABLE aide_error)
    if(NOT aide_result EQUAL 0)
        message(FATAL_ERROR "Existing juceaide failed: ${aide_error}")
    endif()
    message(STATUS "Reusing pinned JUCE host tool: ${ADLIB93_JUCEAIDE_PATH} ${aide_version}")
    set(JUCE_MODULES_ONLY ON CACHE BOOL "Import modules using an explicitly supplied host tool" FORCE)
else()
    set(JUCE_MODULES_ONLY OFF CACHE BOOL "Use standard JUCE build helpers" FORCE)
endif()
FetchContent_Declare(JUCE
    URL https://github.com/juce-framework/JUCE/archive/3fb5cbc0340758596dac39f7c8de47d562b4896e.zip
    URL_HASH SHA256=47722c9e64f5af35b99c6d5f9605a2213e41858ff6ef1f5b9a9747b1fd310de3
    DOWNLOAD_EXTRACT_TIMESTAMP FALSE)
FetchContent_MakeAvailable(JUCE)
if(ADLIB93_JUCEAIDE_PATH)
    # JUCE_MODULES_ONLY imports its unchanged modules; use the pinned framework's
    # own bundle/resource functions with the already compiled native helper.
    include("${juce_SOURCE_DIR}/extras/Build/CMake/JUCEUtils.cmake")
    add_executable(juce::juceaide IMPORTED GLOBAL)
    set_target_properties(juce::juceaide PROPERTIES IMPORTED_LOCATION "${ADLIB93_JUCEAIDE_PATH}")
    set_property(GLOBAL PROPERTY JUCE_COPY_PLUGIN_AFTER_BUILD OFF)
endif()
