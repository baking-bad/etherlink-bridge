LIGO_COMPILER = docker run --rm -v "${PWD}":"${PWD}" -w "${PWD}" ligolang/ligo:0.70.1

compile:
	@if [ ! -d ./build ]; then mkdir ./build ; fi
	${LIGO_COMPILER} compile contract contracts/proxy/proxy-router.mligo -o build/proxy-router.tz
	${LIGO_COMPILER} compile contract contracts/proxy/proxy-ticketer.mligo -o build/proxy-ticketer.tz
	${LIGO_COMPILER} compile contract contracts/rollup-mock.mligo -m RollupMock -o build/rollup-mock.tz
	${LIGO_COMPILER} compile contract contracts/ticketer.mligo -m Ticketer -o build/ticketer.tz

install:
	poetry install

mypy:
	poetry run mypy .

test:
	poetry run pytest
