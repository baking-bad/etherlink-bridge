LIGO_COMPILER = docker run --rm -v "${PWD}":"${PWD}" -w "${PWD}" ligolang/ligo:0.68.0

compile:
	@if [ ! -d ./build ]; then mkdir ./build ; fi
	${LIGO_COMPILER} compile contract contracts/ticketer.mligo -m Ticketer -o build/ticketer.tz

