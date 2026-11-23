"""btc-race-24h: a Donchian-breakout bot with a trailing stop for cbBTC/USDC.

Strategy (my own design, written for this bounty):
- hello: the harness sends one hello, then one batch per minute (a bar per
  batch), then done. This bot answers every batch with exactly one reply
  echoing its seq, carrying its orders for that bar.
- Entry: when flat, buy with all cash once the bar's close breaks above the
  highest close of the previous 10 bars (a fresh 10-bar high). No trade is
  taken while warming up.
- Exit: while holding, track the highest close seen since the entry bar. Sell
  the whole position when the close falls 1.75% below that peak (a trailing
  stop), so a sharp pullback gets out early and a slow grind up is ridden.
  Offline replay of the dev window picked 1.75% over 1.5%: +$27.13 net PnL
  in 3 trades at 2.54% max drawdown, against +$20.69 in 5 trades at 1.5%.
- Long only, one position, full-size buys, at most one order per reply.
- Deterministic: all decisions are integer comparisons on the bars' closes;
  no clock, no environment, no randomness, no files outside the repo.

A round trip costs about 26 bps (4 bps fee + 2 bps slippage + impact each
way), so the trailing stop is set wide enough that only a real pullback, not
minute noise, exits the trade.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "vendor"))

import makefun_bars

SYMBOL = "CBBTC"
LOOKBACK = 10
TRAIL_BPS = 175
MAX_SLIPPAGE_BPS = 150


class TrendBot:
    """Donchian breakout + trailing stop on one symbol's closes."""

    def __init__(self):
        # Closes seen so far, oldest first; only bars the harness sent.
        self.closes = []
        # Highest close seen since the entry bar (None while flat).
        self.peak = None

    def on_batch(self, state, batch):
        for bar in batch["bars"]:
            if bar["symbol"] != SYMBOL:
                continue
            close = int(bar["c"])
            self.closes.append(close)
            held = state.positions.get(SYMBOL)
            if held is not None:
                if self.peak is None or close > self.peak:
                    self.peak = close
                # Trailing stop: close 1.75% below the peak since entry.
                if close * 10000 < self.peak * (10000 - TRAIL_BPS):
                    self.peak = None
                    return [{
                        "side": "sell",
                        "symbol": SYMBOL,
                        "qty": held.qty,
                        "max_slippage_bps": MAX_SLIPPAGE_BPS,
                    }]
            else:
                self.peak = None
                if state.warming_up:
                    continue
                if len(self.closes) > LOOKBACK:
                    prev_high = max(self.closes[-LOOKBACK - 1:-1])
                    if close > prev_high:
                        notional = state.cash
                        if notional >= int(state.hello["fees"]["min_notional_quote_units"]):
                            return [{
                                "side": "buy",
                                "symbol": SYMBOL,
                                "notional_quote_units": notional,
                                "max_slippage_bps": MAX_SLIPPAGE_BPS,
                            }]
        return []


def main():
    bot = TrendBot()
    makefun_bars.run(bot.on_batch)


if __name__ == "__main__":
    main()
