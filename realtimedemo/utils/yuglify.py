# Yuglify CSS/JS compression filters
# They require you to install yuglify:
#   npm -g install yuglify
# Omit the -g flag to install locally, into current directory.

from compressor.filters import CompilerFilter


class YuglifyCssFilter(CompilerFilter):
    command = "yuglify --terminal --type css"


class YuglifyJsFilter(CompilerFilter):
    command = "yuglify --terminal --type js"
