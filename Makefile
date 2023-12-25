LIGO_COMPILER = docker run --rm -v "${PWD}":"${PWD}" -w "${PWD}" ligolang/ligo:0.70.1

compile:
	@if [ ! -d ./tezos/build ]; then mkdir ./build ; fi
	${LIGO_COMPILER} compile contract contracts/ticket-helper/ticket-helper.mligo -m TicketHelper -o build/ticket-helper.tz
	${LIGO_COMPILER} compile contract contracts/rollup-mock/rollup-mock.mligo -m RollupMock -o build/rollup-mock.tz
	${LIGO_COMPILER} compile contract contracts/ticketer/ticketer.mligo -m Ticketer -o build/ticketer.tz
	${LIGO_COMPILER} compile contract contracts/router.mligo -m Router -o build/router.tz

install:
	poetry install

mypy:
	poetry run mypy .

test:
	poetry run pytest

format:
	poetry run black --skip-string-normalization tests scripts

