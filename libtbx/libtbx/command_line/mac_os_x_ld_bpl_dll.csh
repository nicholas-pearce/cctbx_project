#! /bin/csh -f
set noglob
set dll=None
if ("$1" == "-o") then
  shift
  set dll="$1"
  shift
endif
set cpp="$1"
shift
set framework_path="$1"
shift
if ("$1" != "-framework") then
  echo "Expected -framework. Bailing out."
  exit 1
endif
shift
set framework="$1"
shift
if ("$dll" == "None") then
  if ("$1" != "-o") then
    echo "Expected -o. Bailing out."
    exit 1
  endif
  shift
  set dll="$1"
  shift
endif
set echo
ld -dynamic -m -r -d -bind_at_load -o libboost_python.lo $*
"$cpp" -nostartfiles -Wl,-dylib -ldylib1.o "$framework_path" -framework "$framework" -o $dll libboost_python.lo
rm -f libboost_python.lo
