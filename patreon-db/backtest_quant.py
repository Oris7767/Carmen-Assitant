#!/usr/bin/env python3
"""
backtest_quant.py — Backtest Quant Filters trên 4 năm dữ liệu patreon-db

Kiểm thử bất kỳ tổ hợp bộ lọc nào (nakshatra, moon sign, Gann, Hora, retrograde...)
và tính toán tỷ lệ thắng, profit factor, max drawdown.

Usage:
    # Test 1 filter
    python3 backtest_quant.py --nakshatra "Purva Ashadha"

    # Test nhiều filter kết hợp
    python3 backtest_quant.py --moon-sign Sagittarius --gann-held --hora Jupiter

    # Test tất cả filter và so sánh
    python3 backtest_quant.py --compare-all

    # Test với R:R custom
    python3 backtest_quant.py --nakshatra Magha --rr 2.5 --direction BUY
"""

import os
import sys
import json
import argparse
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from collections import defaultdict

DATA_DIR = Path(os.path.dirname(os.path.abspath(__file__))) / "data"

# ── Load all data ──
def load_all_data():
    """Load and concatenate all monthly CSVs."""
    dfs = []
    for f in sorted(DATA_DIR.glob("*.csv")):
        try:
            df = pd.read_csv(f)
            dfs.append(df)
        except Exception as e:
            print(f"⚠️ Skip {f.name}: {e}")
    if not dfs:
        raise RuntimeError("No data files found")
    df = pd.concat(dfs, ignore_index=True)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date').reset_index(drop=True)
    return df


# ── Trade Simulator ──
class TradeSimulator:
    """
    Simulate trades on historical data with configurable entry conditions.
    
    For each day matching filters, simulate a trade on the NEXT trading day:
    - Entry: next day open
    - Risk: sl_pct% of entry (e.g., 0.005 = 0.5%)
    - SL: entry * (1 - sl_pct) for BUY | entry * (1 + sl_pct) for SELL  
    - TP: entry + risk_amount * rr for BUY | entry - risk_amount * rr for SELL
    
    Outcome (using daily OHLC with proximity heuristic):
    - If both SL and TP are within day's range, the closer one to open hits first
    - If only SL hit → LOSS; only TP hit → WIN; neither → EOD close
    """
    
    def __init__(self, df, sl_pct=0.005, rr=2.0, direction='BUY',
                 min_confidence=0, max_trades=None):
        self.df = df
        self.sl_pct = sl_pct
        self.rr = rr
        self.direction = direction.upper()
        self.min_confidence = min_confidence
        self.max_trades = max_trades
        self.trades = []
    
    def apply_filters(self, filters):
        """Apply filter dict to dataframe, return matching indices."""
        mask = pd.Series(True, index=self.df.index)
        
        for col, val in filters.items():
            if col not in self.df.columns:
                print(f"⚠️ Column '{col}' not in data, skipping filter")
                continue
            
            if isinstance(val, list):
                mask &= self.df[col].isin(val)
            elif isinstance(val, bool):
                mask &= self.df[col] == val
            elif val is None:
                mask &= self.df[col].isna()
            else:
                mask &= self.df[col] == val
        
        return self.df[mask].index.tolist()
    
    def run(self, filters, label=""):
        """
        Run backtest with given filters.
        
        Returns dict with trade log and performance metrics.
        """
        matching_idx = self.apply_filters(filters)
        
        if not matching_idx:
            return {
                'label': label,
                'filters': filters,
                'total_signals': 0,
                'trades': [],
                'error': 'No matching days found'
            }
        
        trades = []
        
        for idx in matching_idx:
            # Can't trade the last day (no next day)
            if idx >= len(self.df) - 1:
                continue
            
            if self.max_trades and len(trades) >= self.max_trades:
                break
            
            signal_day = self.df.iloc[idx]
            next_day = self.df.iloc[idx + 1]
            
            entry = next_day['gold_open']
            if pd.isna(entry) or entry <= 0:
                continue
            
            high = next_day['gold_high']
            low = next_day['gold_low']
            close = next_day['gold_close']
            
            if pd.isna(high) or pd.isna(low) or pd.isna(close):
                continue
            
            if self.direction == 'BUY':
                risk_amount = entry * self.sl_pct
                sl = entry - risk_amount
                tp = entry + risk_amount * self.rr
                
                # Simulate intraday outcome using proximity heuristic
                sl_hit = low <= sl
                tp_hit = high >= tp
                
                if sl_hit and tp_hit:
                    # Both hit — which is closer to open?
                    if (entry - sl) < (tp - entry):
                        outcome = 'LOSS'
                        exit_price = sl
                    else:
                        outcome = 'WIN'
                        exit_price = tp
                elif sl_hit:
                    outcome = 'LOSS'
                    exit_price = sl
                elif tp_hit:
                    outcome = 'WIN'
                    exit_price = tp
                else:
                    outcome = 'EOD'
                    exit_price = close
                
                pnl_pct = (exit_price - entry) / entry * 100
                
            else:  # SELL
                risk_amount = entry * self.sl_pct
                sl = entry + risk_amount
                tp = entry - risk_amount * self.rr
                
                sl_hit = high >= sl
                tp_hit = low <= tp
                
                if sl_hit and tp_hit:
                    if (sl - entry) < (entry - tp):
                        outcome = 'LOSS'
                        exit_price = sl
                    else:
                        outcome = 'WIN'
                        exit_price = tp
                elif sl_hit:
                    outcome = 'LOSS'
                    exit_price = sl
                elif tp_hit:
                    outcome = 'WIN'
                    exit_price = tp
                else:
                    outcome = 'EOD'
                    exit_price = close
                
                pnl_pct = (entry - exit_price) / entry * 100
            
            trades.append({
                'signal_date': signal_day['date'].strftime('%Y-%m-%d'),
                'trade_date': next_day['date'].strftime('%Y-%m-%d'),
                'direction': self.direction,
                'entry': round(entry, 2),
                'sl': round(sl, 2),
                'tp': round(tp, 2),
                'exit': round(exit_price, 2),
                'pnl_pct': round(pnl_pct, 3),
                'outcome': outcome,
                'nakshatra': signal_day.get('moon_nakshatra', ''),
                'moon_sign': signal_day.get('moon_sign', ''),
                'hora': signal_day.get('dominant_planet_hour', ''),
                'gann_held': bool(signal_day.get('gann_key_level_held', False)),
                'volatility': signal_day.get('volatility', ''),
                'trend': signal_day.get('trend_direction', ''),
            })
        
        total_signals = len(matching_idx)
        
        if not trades:
            return {
                'label': label,
                'filters': filters,
                'total_signals': total_signals,
                'trades': [],
                'error': 'No valid next-day data for trades'
            }
        
        return self._compute_metrics(trades, label, filters, total_signals)
    
    def _compute_metrics(self, trades, label, filters, total_signals):
        """Compute performance metrics from trade list."""
        wins = [t for t in trades if t['outcome'] == 'WIN']
        losses = [t for t in trades if t['outcome'] == 'LOSS']
        eods = [t for t in trades if t['outcome'] == 'EOD']
        
        n = len(trades)
        n_wins = len(wins)
        n_losses = len(losses)
        n_eod = len(eods)
        
        win_rate = n_wins / n * 100 if n > 0 else 0
        
        gross_win = sum(t['pnl_pct'] for t in wins) if wins else 0
        gross_loss = abs(sum(t['pnl_pct'] for t in losses)) if losses else 0
        profit_factor = gross_win / gross_loss if gross_loss > 0 else float('inf')
        
        avg_win = np.mean([t['pnl_pct'] for t in wins]) if wins else 0
        avg_loss = np.mean([t['pnl_pct'] for t in losses]) if losses else 0
        
        all_pnl = [t['pnl_pct'] for t in trades]
        total_return = sum(all_pnl)
        avg_trade = np.mean(all_pnl)
        std_trade = np.std(all_pnl) if len(all_pnl) > 1 else 0
        
        # Sharpe ratio (annualized, assuming 252 trading days)
        sharpe = (avg_trade / std_trade * np.sqrt(252)) if std_trade > 0 else 0
        
        # Max drawdown
        cumulative = np.cumsum(all_pnl)
        peak = np.maximum.accumulate(cumulative)
        drawdown = cumulative - peak
        max_dd = abs(min(drawdown)) if len(drawdown) > 0 else 0
        max_dd_pct = max_dd
        
        # Consecutive wins/losses
        cons_wins = cons_losses = cur_wins = cur_losses = 0
        for t in trades:
            if t['outcome'] == 'WIN':
                cur_wins += 1
                cur_losses = 0
                cons_wins = max(cons_wins, cur_wins)
            elif t['outcome'] == 'LOSS':
                cur_losses += 1
                cur_wins = 0
                cons_losses = max(cons_losses, cur_losses)
            # EOD breaks streaks
            else:
                cur_wins = cur_losses = 0
        
        # Monthly breakdown
        monthly = defaultdict(lambda: {'trades': 0, 'wins': 0, 'pnl': 0.0})
        for t in trades:
            m = t['trade_date'][:7]
            monthly[m]['trades'] += 1
            if t['outcome'] == 'WIN':
                monthly[m]['wins'] += 1
            monthly[m]['pnl'] += t['pnl_pct']
        
        monthly_table = []
        for m in sorted(monthly.keys()):
            d = monthly[m]
            wr = d['wins'] / d['trades'] * 100 if d['trades'] > 0 else 0
            monthly_table.append({
                'month': m,
                'trades': d['trades'],
                'win_rate': round(wr, 1),
                'pnl_pct': round(d['pnl'], 2),
            })
        
        return {
            'label': label,
            'filters': filters,
            'total_signals': total_signals,
            'total_trades': n,
            'wins': n_wins,
            'losses': n_losses,
            'eod_exits': n_eod,
            'win_rate': round(win_rate, 1),
            'profit_factor': round(profit_factor, 2) if profit_factor != float('inf') else '∞',
            'avg_win': round(avg_win, 3),
            'avg_loss': round(avg_loss, 3),
            'avg_trade': round(avg_trade, 3),
            'total_return_pct': round(total_return, 2),
            'sharpe': round(sharpe, 2),
            'max_drawdown_pct': round(max_dd_pct, 2),
            'std_dev': round(std_trade, 3),
            'max_consecutive_wins': cons_wins,
            'max_consecutive_losses': cons_losses,
            'monthly': monthly_table,
            'trades': trades,
        }


# ── Compare All Filters ──
def compare_all_filters(sim, direction='BUY', rr=2.0):
    """Test all major quant filters individually and report results."""
    
    filter_sets = {
        # Nakshatras (top performers from analysis)
        'Nak: Purva Ashadha (top bull)': {'moon_nakshatra': 'Purva Ashadha'},
        'Nak: Mula (top bull)': {'moon_nakshatra': 'Mula'},
        'Nak: Shatabhisha': {'moon_nakshatra': 'Shatabhisha'},
        'Nak: Ashwini': {'moon_nakshatra': 'Ashwini'},
        'Nak: Jyeshtha (bearish)': {'moon_nakshatra': 'Jyeshtha'},
        'Nak: Mrigashira (bearish)': {'moon_nakshatra': 'Mrigashira'},
        
        # Moon Signs
        'Moon: Sagittarius (top)': {'moon_sign': 'Sagittarius'},
        'Moon: Leo': {'moon_sign': 'Leo'},
        'Moon: Libra': {'moon_sign': 'Libra'},
        'Moon: Scorpio (worst)': {'moon_sign': 'Scorpio'},
        'Moon: Taurus (worst)': {'moon_sign': 'Taurus'},
        
        # Gann Key Level
        'Gann Key HELD': {'gann_key_level_held': True},
        'Gann Key BREACHED': {'gann_key_level_held': False},
        
        # Hora
        'Hora: Jupiter': {'dominant_planet_hour': 'Jupiter'},
        'Hora: Sun': {'dominant_planet_hour': 'Sun'},
        'Hora: Mars': {'dominant_planet_hour': 'Mars'},
        'Hora: Moon (worst)': {'dominant_planet_hour': 'Moon'},
        'Hora: Venus (noisy)': {'dominant_planet_hour': 'Venus'},
        
        # Volatility
        'Vol: LOW': {'volatility': 'low'},
        'Vol: HIGH': {'volatility': 'high'},
        
        # Trend
        'Trend: BULLISH': {'trend_direction': 'bullish'},
        'Trend: BEARISH': {'trend_direction': 'bearish'},
        
        # Retrograde effects
        'Mercury Retro': {'mercury_retro': True},
        'Venus Retro': {'venus_retro': True},
        'Mars Retro': {'mars_retro': True},
        
        # Combust
        'Mercury Combust': {'mercury_combust': True},
        'Venus Combust': {'venus_combust': True},
        
        # Market Reaction
        'Reaction: STRONG TREND': {'market_reaction': 'strong_trend'},
        'Reaction: REVERSAL': {'market_reaction': 'reversal_signal'},
        
        # Eclipse
        'Eclipse Active': {'eclipse_active': True},
        
        # Moon Phase
        'Moon Phase: New Moon': {'moon_phase': 'New Moon'},
        'Moon Phase: Full Moon': {'moon_phase': 'Full Moon'},
    }
    
    results = []
    for label, filters in filter_sets.items():
        result = sim.run(filters, label)
        if result.get('total_trades', 0) >= 5:  # Min 5 trades for significance
            results.append(result)
    
    # Sort by profit factor
    results.sort(key=lambda r: (
        r.get('profit_factor', 0) if isinstance(r.get('profit_factor'), (int, float)) else 0
    ), reverse=True)
    
    return results


# ── COMBO Test ──
def test_combos(sim, top_filters, direction='BUY', rr=2.0):
    """Test combinations of top-performing filters."""
    combos = []
    
    # Best moon sign + best nakshatra
    if 'Moon: Sagittarius (top)' in top_filters and 'Nak: Purva Ashadha (top bull)' in top_filters:
        for moon in ['Sagittarius', 'Leo', 'Libra']:
            for nak in ['Purva Ashadha', 'Mula', 'Ashwini']:
                combo = {'moon_sign': moon, 'moon_nakshatra': nak}
                r = sim.run(combo, f'Combo: {moon} + {nak}')
                if r.get('total_trades', 0) >= 5:
                    combos.append(r)
    
    # Gann held + best hora
    for hora in ['Jupiter', 'Sun', 'Mars']:
        combo = {'gann_key_level_held': True, 'dominant_planet_hour': hora}
        r = sim.run(combo, f'Combo: Gann Held + Hora {hora}')
        if r.get('total_trades', 0) >= 5:
            combos.append(r)
    
    # Trend + Gann
    for trend in ['bullish', 'bearish']:
        for held in [True, False]:
            combo = {'trend_direction': trend, 'gann_key_level_held': held}
            r = sim.run(combo, f'Combo: Trend {trend} + Gann Held={held}')
            if r.get('total_trades', 0) >= 5:
                combos.append(r)
    
    combos.sort(key=lambda r: (
        r.get('profit_factor', 0) if isinstance(r.get('profit_factor'), (int, float)) else 0
    ), reverse=True)
    return combos


# ── Report Formatter ──
def print_result(result, show_trades=False):
    """Pretty-print a single backtest result."""
    if result.get('error'):
        print(f"\n❌ {result.get('label', 'Unknown')}: {result['error']}")
        return
    
    print(f"\n{'='*60}")
    print(f"📊 {result['label']}")
    print(f"{'='*60}")
    print(f"Filters: {json.dumps(result['filters'])}")
    print(f"Trades: {result['total_trades']} | Wins: {result['wins']} | Losses: {result['losses']} | EOD: {result.get('eod_exits', 0)}")
    print(f"Win Rate: {result['win_rate']}%")
    print(f"Avg Win: {result['avg_win']:+.3f}% | Avg Loss: {result['avg_loss']:+.3f}% | Avg Trade: {result['avg_trade']:+.3f}%")
    print(f"Profit Factor: {result['profit_factor']}")
    print(f"Total Return: {result['total_return_pct']:+.2f}%")
    print(f"Sharpe: {result['sharpe']} | Max DD: {result['max_drawdown_pct']:.2f}%")
    print(f"Max Cons Wins: {result['max_consecutive_wins']} | Max Cons Losses: {result['max_consecutive_losses']}")
    
    # Monthly
    if result.get('monthly'):
        print(f"\n📅 Monthly Breakdown:")
        print(f"{'Month':<10} {'Trades':>6} {'Win%':>7} {'PnL%':>8}")
        print("-" * 35)
        for m in result['monthly']:
            emoji = '🟢' if m['pnl_pct'] > 0 else '🔴'
            print(f"{m['month']:<10} {m['trades']:>6} {m['win_rate']:>6.1f}% {m['pnl_pct']:>+7.2f}% {emoji}")
    
    if show_trades:
        print(f"\n📋 Trade Log:")
        for t in result['trades'][:10]:
            emoji = '🟢' if t['outcome'] == 'WIN' else ('🔴' if t['outcome'] == 'LOSS' else '🟡')
            print(f"  {t['signal_date']} → {t['trade_date']} | {t['direction']} @ ${t['entry']} | SL:${t['sl']} TP:${t['tp']} | {emoji} {t['pnl_pct']:+.3f}%")


def print_compare_table(results, top_n=15):
    """Print comparison table of top results."""
    print(f"\n{'='*80}")
    print(f"🏆 TOP {top_n} FILTERS — Backtest Results")
    print(f"{'='*80}")
    print(f"{'Rank':<5} {'Filter':<35} {'Trades':>6} {'Win%':>7} {'PF':>6} {'Return%':>8} {'Sharpe':>7} {'MaxDD%':>7}")
    print("-" * 85)
    
    for i, r in enumerate(results[:top_n], 1):
        pf = r.get('profit_factor', 0)
        pf_str = f"{pf:.2f}" if isinstance(pf, (int, float)) else str(pf)
        print(f"{i:<5} {r['label'][:35]:<35} {r['total_trades']:>6} {r['win_rate']:>6.1f}% {pf_str:>6} {r['total_return_pct']:>+7.2f}% {r['sharpe']:>7.2f} {r['max_drawdown_pct']:>7.2f}%")


# ── Walk-Forward Validation ──
def run_walk_forward(df, args):
    """
    Walk-forward validation: train on earlier years, test on later years.
    Shows if signals are stable across time periods or overfit.
    """
    years = sorted(df['date'].dt.year.unique())
    if len(years) < 3:
        print("Need at least 3 years for walk-forward")
        return
    
    # Define train/test splits: train on Y-1, test on Y
    print(f"\n{'Year':<8} {'Trades':>6} {'Win%':>7} {'PF':>6} {'Return%':>8} {'Sharpe':>7} {'MaxDD%':>7}")
    print("-" * 55)
    
    for i in range(1, len(years)):
        test_year = years[i]
        test_df = df[df['date'].dt.year == test_year]
        
        if len(test_df) < 10:
            continue
        
        sim = TradeSimulator(pd.concat([df[df['date'].dt.year < test_year], test_df]),
                            sl_pct=args.sl_pct, rr=args.rr, direction=args.direction)
        
        # Test the best 3 single filters + best combo across this year
        top_filters = [
            ("Nak: Mula", {'moon_nakshatra': 'Mula'}),
            ("Nak: Jyeshtha", {'moon_nakshatra': 'Jyeshtha'}),
            ("Mercury Combust", {'mercury_combust': True}),
            ("Moon: Libra", {'moon_sign': 'Libra'}),
            ("Mars Retro", {'mars_retro': True}),
        ]
        
        for label, filt in top_filters:
            r = sim.run(filt, label)
            n = r.get('total_trades', 0)
            if n > 0:
                # Only count trades in test_year
                test_trades = [t for t in r.get('trades', []) 
                              if t['trade_date'].startswith(str(test_year))]
                if len(test_trades) >= 3:
                    wins = sum(1 for t in test_trades if t['outcome'] == 'WIN')
                    losses = sum(1 for t in test_trades if t['outcome'] == 'LOSS')
                    wr = wins / len(test_trades) * 100
                    pnl = sum(t['pnl_pct'] for t in test_trades)
                    gross_win = sum(t['pnl_pct'] for t in test_trades if t['outcome'] == 'WIN')
                    gross_loss = abs(sum(t['pnl_pct'] for t in test_trades if t['outcome'] == 'LOSS'))
                    pf = round(gross_win / gross_loss, 2) if gross_loss > 0 else float('inf')
                    pf_str = f"{pf:.2f}" if isinstance(pf, float) else str(pf)
                    print(f"{test_year} {label:<30} {len(test_trades):>6} {wr:>6.1f}% {pf_str:>6} {pnl:>+8.2f}%")
    
    print()


# ── Main ──
def main():
    parser = argparse.ArgumentParser(description='Backtest Quant Filters trên patreon-db')
    parser.add_argument('--nakshatra', type=str, help='Nakshatra filter')
    parser.add_argument('--moon-sign', type=str, help='Moon sign filter')
    parser.add_argument('--moon-phase', type=str, help='Moon phase filter')
    parser.add_argument('--hora', type=str, help='Dominant planet hour')
    parser.add_argument('--gann-held', action='store_true', default=None, help='Gann key level held')
    parser.add_argument('--gann-breached', action='store_true', default=None, help='Gann key level breached')
    parser.add_argument('--trend', type=str, choices=['bullish', 'bearish', 'neutral'], help='Trend direction')
    parser.add_argument('--volatility', type=str, choices=['low', 'medium', 'high'], help='Volatility')
    parser.add_argument('--reaction', type=str, help='Market reaction type')
    parser.add_argument('--mercury-retro', action='store_true', default=None)
    parser.add_argument('--venus-retro', action='store_true', default=None)
    parser.add_argument('--mars-retro', action='store_true', default=None)
    parser.add_argument('--mercury-combust', action='store_true', default=None)
    parser.add_argument('--venus-combust', action='store_true', default=None)
    parser.add_argument('--eclipse', action='store_true', default=None)
    parser.add_argument('--direction', type=str, default='BUY', choices=['BUY', 'SELL'])
    parser.add_argument('--rr', type=float, default=2.0, help='Risk:Reward ratio')
    parser.add_argument('--sl-pct', type=float, default=0.005, help='SL as %% of entry (0.005 = 0.5%%)')
    parser.add_argument('--compare-all', action='store_true', help='Compare all major filters')
    parser.add_argument('--test-combos', action='store_true', help='Test combinations of top filters')
    parser.add_argument('--walk-forward', action='store_true', help='Walk-forward validation (split by year)')
    parser.add_argument('--show-trades', action='store_true', help='Show individual trades')
    parser.add_argument('--json', action='store_true', help='Output as JSON')
    
    args = parser.parse_args()
    
    print("🪐 Loading patreon-db...")
    df = load_all_data()
    print(f"✅ {len(df)} trading days loaded ({df['date'].min().date()} → {df['date'].max().date()})")
    
    sim = TradeSimulator(df, sl_pct=args.sl_pct, rr=args.rr, direction=args.direction)
    
    if args.compare_all:
        results = compare_all_filters(sim, direction=args.direction, rr=args.rr)
        
        if args.test_combos:
            combo_results = test_combos(sim, [r['label'] for r in results[:10]], 
                                        direction=args.direction, rr=args.rr)
            results = combo_results + results
        
        if args.walk_forward:
            print("\n" + "="*80)
            print("🔄 WALK-FORWARD VALIDATION (Train/Test split by year)")
            print("="*80)
            run_walk_forward(df, args)
            return
        
        if args.json:
            output = []
            for r in results:
                out = {k: v for k, v in r.items() if k != 'trades'}
                output.append(out)
            print(json.dumps(output, indent=2, ensure_ascii=False))
        else:
            print_compare_table(results, top_n=25)
            
            # Show top 3 details
            for r in results[:3]:
                print_result(r, show_trades=args.show_trades)
        
        # Overall stats
        total_trades = sum(r['total_trades'] for r in results)
        avg_win_rate = np.mean([r['win_rate'] for r in results])
        print(f"\n📊 Overall: {len(results)} filter sets tested, {total_trades} total trade signals")
        print(f"   Average win rate across all filters: {avg_win_rate:.1f}%")
    else:
        # Build custom filter
        filters = {}
        if args.nakshatra:
            filters['moon_nakshatra'] = args.nakshatra
        if args.moon_sign:
            filters['moon_sign'] = args.moon_sign
        if args.moon_phase:
            filters['moon_phase'] = args.moon_phase
        if args.hora:
            filters['dominant_planet_hour'] = args.hora
        if args.gann_held is not None:
            filters['gann_key_level_held'] = args.gann_held
        elif args.gann_breached is not None:
            filters['gann_key_level_held'] = not args.gann_breached
        if args.trend:
            filters['trend_direction'] = args.trend
        if args.volatility:
            filters['volatility'] = args.volatility
        if args.reaction:
            filters['market_reaction'] = args.reaction
        if args.mercury_retro is not None:
            filters['mercury_retro'] = args.mercury_retro
        if args.venus_retro is not None:
            filters['venus_retro'] = args.venus_retro
        if args.mars_retro is not None:
            filters['mars_retro'] = args.mars_retro
        if args.mercury_combust is not None:
            filters['mercury_combust'] = args.mercury_combust
        if args.venus_combust is not None:
            filters['venus_combust'] = args.venus_combust
        if args.eclipse is not None:
            filters['eclipse_active'] = args.eclipse
        
        if not filters:
            print("⚠️ No filters specified. Use --compare-all to test all filters, or specify filters.")
            print("Example: python3 backtest_quant.py --nakshatra 'Purva Ashadha' --moon-sign Sagittarius")
            return
        
        label = " + ".join(f"{k}={v}" for k, v in filters.items())
        result = sim.run(filters, label)
        
        if args.json:
            out = {k: v for k, v in result.items() if k != 'trades'}
            print(json.dumps(out, indent=2, ensure_ascii=False))
        else:
            print_result(result, show_trades=args.show_trades)


if __name__ == '__main__':
    main()
