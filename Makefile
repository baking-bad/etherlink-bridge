LIGO_COMPILER = docker run --rm -v "${PWD}":"${PWD}" -w "${PWD}" ligolang/ligo:0.69.0

compile:
	@if [ ! -d ./build ]; then mkdir ./build ; fi
	${LIGO_COMPILER} compile contract contracts/proxy.mligo -m Proxy -o build/proxy.tz
	${LIGO_COMPILER} compile contract contracts/locker.mligo -m Locker -o build/locker.tz
	${LIGO_COMPILER} compile contract contracts/ticketer.mligo -m Ticketer -o build/ticketer.tz
