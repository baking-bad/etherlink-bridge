LIGO_COMPILER = docker run --rm -v "${PWD}":"${PWD}" -w "${PWD}" ligolang/ligo:0.70.1

compile:
	@if [ ! -d ./build ]; then mkdir ./build ; fi
	@if [ ! -d ./build/route-lambdas ]; then mkdir ./build/route-lambdas ; fi
	${LIGO_COMPILER} compile contract contracts/router.mligo -m Router -o build/router.tz
	${LIGO_COMPILER} compile expression cameligo Router.route_to_sender_lambda --init-file contracts/router.mligo > build/route-lambdas/to_sender.tz
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
