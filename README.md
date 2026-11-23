# btc-race-24h

[![btc-race-24h](https://img.shields.io/badge/btc--race--24h-python%203.13-blue)](https://github.com/iwanr94/btc-race-24h)
[![btc-race-24h](https://img.shields.io/badge/btc--race--24h-stdlib%20only-brightgreen)](https://github.com/iwanr94/btc-race-24h)
[![btc-race-24h](https://img.shields.io/badge/btc--race--24h-MIT-yellow)](https://github.com/iwanr94/btc-race-24h/blob/main/LICENSE)

A bot that trades Coinbase Wrapped BTC (cbBTC) against USDC minute by minute
in the make.fun `btc-race-24h-20261123-0511` bounty, speaking
`agent-fun/bars-replay/v1` (NDJSON on stdin/stdout). Python 3.13, standard
library only, no network, no wall clock. Deterministic: every decision is an
integer comparison on the bars' closes.

## Strategy

- **Entry:** when flat, buy with all cash once a bar's close breaks above the
  highest close of the previous 10 bars (a fresh 10-bar high).
- **Exit:** while holding, track the highest close since the entry bar and
  sell the whole position when the close falls 1.75% below that peak (a
  trailing stop). A sharp pullback exits early; a slow grind up is ridden.
- Long only, one position, full-size buys, at most one order per reply.

## Dev window (offline replay)

- Net PnL **+$27.13**, 3 trades, max drawdown 2.54% (buy-and-hold on the same
  window: +$31.73 in 1 trade). The trailing stop is the difference: in a
  falling window it exits on the first 1.75% pullback instead of riding the
  drop to the end.

## Layout

- `main.py` — the bot (entrypoint).
- `vendor/makefun_bars.py` — byte-for-byte copy of the kit's Python SDK shim.
- `LICENSE` — MIT.

## Run

```sh
python3 -P -s main.py
```

The harness sends `hello`, then one `batch` per minute, then `done`; the bot
answers every batch with exactly one reply echoing its `seq`.
