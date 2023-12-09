LIGO_COMPILER = docker run --rm -v "${PWD}":"${PWD}" -w "${PWD}" ligolang/ligo:0.70.1

compile:
	@if [ ! -d ./build ]; then mkdir ./build ; fi
	@if [ ! -d ./build/route-lambdas ]; then mkdir ./build/route-lambdas ; fi
	@if [ ! -d ./build/proxies ]; then mkdir ./build/proxies ; fi
	${LIGO_COMPILER} compile contract contracts/rollup-mock/rollup-mock.mligo -m RollupMock -o build/rollup-mock.tz
	${LIGO_COMPILER} compile contract contracts/ticketer/ticketer.mligo -m Ticketer -o build/ticketer.tz
	${LIGO_COMPILER} compile contract contracts/proxies/router.mligo -o build/proxies/router.tz
	${LIGO_COMPILER} compile contract contracts/proxies/ticketer.mligo -o build/proxies/ticketer.tz
	${LIGO_COMPILER} compile contract contracts/router.mligo -m Router -o build/router.tz

install:
	poetry install

mypy:
	poetry run mypy .

test:
	poetry run pytest
