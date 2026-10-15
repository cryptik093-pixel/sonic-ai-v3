include(FetchContent)
FetchContent_Declare(JUCE
    URL https://github.com/juce-framework/JUCE/archive/3fb5cbc0340758596dac39f7c8de47d562b4896e.zip
    URL_HASH SHA256=47722c9e64f5af35b99c6d5f9605a2213e41858ff6ef1f5b9a9747b1fd310de3
    DOWNLOAD_EXTRACT_TIMESTAMP FALSE)
FetchContent_MakeAvailable(JUCE)
