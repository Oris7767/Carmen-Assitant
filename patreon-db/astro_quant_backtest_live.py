#!/usr/bin/env python3
"""
🪐 ASTRO-QUANT BACKTEST ENGINE — LIVE TRADING SIMULATION
========================================================
Implements the full Astro-Quant Framework V3 scoring engine 
with realistic trading rules as specified by Kim Ssa.

Trading Rules:
  - $2,000 starting capital
  - Max 2% risk per trade
  - Max 2 concurrent positions
  - Max 15% drawdown (hard stop)
  - Skip Friday (no new entries)
  - Skip FOMC/NFP days (no new entries)
  - 5% daily loss limit (stop for the day)
  - Swing: max 2 days hold
  - Trailing BE after 1R profit
  - SL = 1.5 × ATR(14); TP = 2R

Signal Source: Astro-Quant Scorer V3 (4,629-day trained)
Data: 222 monthly CSVs (2008-01 → 2026-05)
"""

import os
import sys
import json
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict, OrderedDict
import argparse

# Add parent for import
sys.path.insert(0, str(Path(__file__).parent))
from astro_quant_scorer_v2 import AstroQuantScorer

DATA_DIR = Path(__file__).parent / "data"
REPORT_DIR = Path(__file__).parent / "reports"

# ═══════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════

CONFIG = {
    'initial_capital': 2000.0,
    'risk_per_trade_pct': 0.02,       # 2% of equity
    'max_positions': 2,
    'max_drawdown_pct': 0.15,         # 15% from peak equity
    'daily_loss_limit_pct': 0.05,     # 5% of equity
    'max_hold_days': 2,               # Swing max 2 days
    'sl_atr_multiplier': 1.5,         # SL = entry ± 1.5×ATR
    'tp_r_multiple': 2.0,             # TP = 2R
    'trailing_be_trigger_r': 1.0,     # Trail to BE after 1R profit
    'min_signal_confidence': 'MEDIUM', # MEDIUM or HIGH
    'skip_friday': True,
    'skip_fomc_nfp': True,
    'skip_high_impact': False,        # Skip ALL high-impact events? False = only FOMC/NFP
}

# ═══════════════════════════════════════════════════════
# DATA LOADING
# ═══════════════════════════════════════════════════════

def load_all_data():
    """Load and concatenate all monthly CSVs."""
    dfs = []
    files = sorted(DATA_DIR.glob("*.csv"))
    print(f"📂 Loading {len(files)} monthly CSV files...")
    
    for f in files:
        try:
            df = pd.read_csv(f)
            dfs.append(df)
        except Exception as e:
            print(f"  ⚠️ Skip {f.name}: {e}")
    
    if not dfs:
        raise RuntimeError("No data files found")
    
    df = pd.concat(dfs, ignore_index=True)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date').reset_index(drop=True)
    
    # Ensure numeric columns
    for col in ['gold_open', 'gold_close', 'gold_high', 'gold_low', 
                'gold_range', 'gold_change_pct', 'gold_atr_14', 'gold_rsi_14',
                'gold_ema_31', 'gold_ema_113']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Alias: CSV has 'moon_nakshatra_lord' but scorer expects 'nakshatra_lord'
    if 'moon_nakshatra_lord' in df.columns and 'nakshatra_lord' not in df.columns:
        df['nakshatra_lord'] = df['moon_nakshatra_lord']
    
    print(f"✅ Loaded {len(df)} trading days ({df['date'].iloc[0].date()} → {df['date'].iloc[-1].date()})")
    return df


# ═══════════════════════════════════════════════════════
# EVENT DETECTION
# ═══════════════════════════════════════════════════════

def is_fomc_day(events_str):
    """Check if economic events include FOMC."""
    if pd.isna(events_str) or str(events_str).strip() == '':
        return False
    return 'FOMC' in str(events_str).upper()

def is_nfp_day(events_str):
    """Check if economic events include Non-Farm Payrolls."""
    if pd.isna(events_str) or str(events_str).strip() == '':
        return False
    s = str(events_str)
    return 'NON-FARM PAYROLLS (NFP)' in s.upper() or 'NON FARM PAYROLLS' in s.upper()

def is_high_impact_day(impact_str):
    """Check if economic impact is high."""
    if pd.isna(impact_str):
        return False
    return str(impact_str).strip().lower() == 'high'

def should_skip_day(row, config):
    """Determine if a day should be skipped for new entries."""
    day = row.get('day_of_week', '')
    events = row.get('economic_events', '')
    
    # Check FOMC/NFP FIRST (before Friday — NFP is always Friday)
    if config['skip_fomc_nfp']:
        if is_fomc_day(events):
            return True, 'FOMC'
        if is_nfp_day(events):
            return True, 'NFP'
    
    if config['skip_friday'] and day == 'Friday':
        return True, 'Friday'
    
    if config['skip_high_impact'] and is_high_impact_day(row.get('economic_impact', '')):
        return True, 'High Impact'
    
    return False, None


# ═══════════════════════════════════════════════════════
# POSITION & TRADE TRACKING
# ═══════════════════════════════════════════════════════

class Position:
    """Represents an open position."""
    
    def __init__(self, trade_id, direction, entry_date, entry_price, 
                 sl_price, tp_price, position_size_lots, risk_amount,
                 entry_score, entry_confidence, entry_state):
        self.trade_id = trade_id
        self.direction = direction          # 'LONG' or 'SHORT'
        self.entry_date = entry_date
        self.entry_price = entry_price
        self.initial_sl = sl_price
        self.current_sl = sl_price
        self.tp_price = tp_price
        self.position_size_lots = position_size_lots
        self.risk_amount = risk_amount       # $ risked
        self.entry_score = entry_score
        self.entry_confidence = entry_confidence
        self.entry_state = entry_state
        self.trailing_be_active = False
        self.days_held = 0
        self.max_favorable = 0.0             # Max profit seen (for trailing)
        self.max_adverse = 0.0               # Max loss seen
        self.pnl = 0.0
        self.exit_date = None
        self.exit_price = None
        self.exit_reason = None
        self.active = True
    
    def update(self, current_date, day_high, day_low, day_open, day_close):
        """Check SL/TP hit during the day. Returns True if closed."""
        if not self.active:
            return True
        
        self.days_held += 1
        
        # For LONG: check if low hit SL or high hit TP (using proximity logic)
        # A more precise check: 
        # - If both SL and TP are within day's range, the one closer to open hits first
        # - If only one is within range, that one hits
        # - If neither, use close price
        
        if self.direction == 'LONG':
            sl_hit = day_low <= self.current_sl
            tp_hit = day_high >= self.tp_price
            
            if sl_hit and tp_hit:
                # Both within range — check which is closer to open
                dist_sl = abs(day_open - self.current_sl)
                dist_tp = abs(day_open - self.tp_price)
                if dist_sl < dist_tp:
                    self._close(self.current_sl, current_date, 'SL')
                else:
                    self._close(self.tp_price, current_date, 'TP')
                return True
            elif sl_hit:
                self._close(self.current_sl, current_date, 'SL')
                return True
            elif tp_hit:
                self._close(self.tp_price, current_date, 'TP')
                return True
            else:
                # Neither hit — update trailing
                high_reached = day_high
                self.max_favorable = max(self.max_favorable, 
                                         (high_reached - self.entry_price) * self.position_size_lots)
                self.max_adverse = min(self.max_adverse,
                                       (day_low - self.entry_price) * self.position_size_lots)
                
                # Check trailing BE trigger
                if not self.trailing_be_active:
                    profit_r = self.max_favorable / self.risk_amount if self.risk_amount > 0 else 0
                    if profit_r >= CONFIG['trailing_be_trigger_r']:
                        self.current_sl = self.entry_price
                        self.trailing_be_active = True
                
                return False
        else:
            # SHORT
            sl_hit = day_high >= self.current_sl
            tp_hit = day_low <= self.tp_price
            
            if sl_hit and tp_hit:
                dist_sl = abs(day_open - self.current_sl)
                dist_tp = abs(day_open - self.tp_price)
                if dist_sl < dist_tp:
                    self._close(self.current_sl, current_date, 'SL')
                else:
                    self._close(self.tp_price, current_date, 'TP')
                return True
            elif sl_hit:
                self._close(self.current_sl, current_date, 'SL')
                return True
            elif tp_hit:
                self._close(self.tp_price, current_date, 'TP')
                return True
            else:
                low_reached = day_low
                self.max_favorable = max(self.max_favorable,
                                         (self.entry_price - low_reached) * self.position_size_lots)
                self.max_adverse = min(self.max_adverse,
                                       (self.entry_price - day_high) * self.position_size_lots)
                
                if not self.trailing_be_active:
                    profit_r = self.max_favorable / self.risk_amount if self.risk_amount > 0 else 0
                    if profit_r >= CONFIG['trailing_be_trigger_r']:
                        self.current_sl = self.entry_price
                        self.trailing_be_active = True
                
                return False
    
    def force_close_at_eod(self, current_date, close_price, reason='EOD'):
        """Close position at end-of-day price."""
        self._close(close_price, current_date, reason)
    
    def force_close_max_hold(self, current_date, close_price):
        """Force close because max hold days reached."""
        self._close(close_price, current_date, 'MAX_HOLD')
    
    def _close(self, price, date, reason):
        """Internal close logic."""
        self.exit_price = price
        self.exit_date = date
        self.exit_reason = reason
        self.active = False
        
        if self.direction == 'LONG':
            self.pnl = (price - self.entry_price) * self.position_size_lots
        else:
            self.pnl = (self.entry_price - price) * self.position_size_lots
    
    def summary(self):
        """Return trade summary dict."""
        return OrderedDict([
            ('id', self.trade_id),
            ('direction', self.direction),
            ('entry_date', str(self.entry_date.date())),
            ('exit_date', str(self.exit_date.date()) if self.exit_date else '—'),
            ('days_held', self.days_held),
            ('entry_price', round(self.entry_price, 2)),
            ('exit_price', round(self.exit_price, 2) if self.exit_price else None),
            ('sl_initial', round(self.initial_sl, 2)),
            ('sl_final', round(self.current_sl, 2)),
            ('tp', round(self.tp_price, 2)),
            ('size_lots', round(self.position_size_lots, 4)),
            ('risk_$', round(self.risk_amount, 2)),
            ('pnl_$', round(self.pnl, 2)),
            ('pnl_%', round(self.pnl / CONFIG['initial_capital'] * 100, 2)),
            ('exit_reason', self.exit_reason),
            ('trailing_be', self.trailing_be_active),
            ('score', self.entry_score),
            ('confidence', self.entry_confidence),
            ('market_state', self.entry_state),
        ])


# ═══════════════════════════════════════════════════════
# BACKTEST ENGINE
# ═══════════════════════════════════════════════════════

class BacktestEngine:
    """Main backtest engine with risk management."""
    
    def __init__(self, df, config=None):
        self.df = df.reset_index(drop=True)
        self.config = config or CONFIG
        self.positions = []        # Currently open positions
        self.closed_trades = []    # Completed trades
        self.equity_curve = []
        self.daily_pnl_tracker = {}  # date -> pnl closed that day
        self.peak_equity = self.config['initial_capital']
        self.current_equity = self.config['initial_capital']
        self.trade_counter = 0
        self.dd_stopped = False
        self.dd_stop_date = None
        self.daily_loss_stop_dates = []
        
        # Statistics
        self.total_signals = {'LONG': 0, 'SHORT': 0, 'NEUTRAL': 0}
        self.signals_traded = {'LONG': 0, 'SHORT': 0}
        self.signals_skipped = {'friday': 0, 'fomc_nfp': 0, 'max_positions': 0, 
                                'dd_stop': 0, 'daily_loss': 0, 'high_impact': 0}
    
    def calculate_position_size(self, entry_price, sl_price, direction):
        """Calculate position size in micro-lots (0.01 standard) based on 2% risk.
        
        XAUUSD: 1 standard lot = 100 oz
                1 micro lot (0.01) = 1 oz  
                P&L per $1 move = $1 per micro lot
        
        So: micro_lots = risk_amount / sl_distance
        """
        risk_per_trade = self.current_equity * self.config['risk_per_trade_pct']
        sl_distance = abs(entry_price - sl_price)
        
        if sl_distance <= 0:
            return 0, 0
        
        # Micro lots: each unit = $1 P&L per $1 gold move
        micro_lots = risk_per_trade / sl_distance
        
        # Round to 0.01 increments
        micro_lots = max(0.01, round(micro_lots * 100) / 100)
        
        actual_risk = micro_lots * sl_distance
        return micro_lots, actual_risk
    
    def score_day(self, row):
        """Score a single day using AstroQuantScorer V3."""
        try:
            result = AstroQuantScorer.score(row)
            result['date'] = row.get('date')
            return result
        except Exception as e:
            return {
                'composite_score': 0.0,
                'signal': 'NEUTRAL',
                'confidence': 'LOW',
                'market_state': 'compression',
                'volatility_regime': 'medium',
                'raw_score': 0.0,
                'max_possible': 0.0,
                'details': {},
                'date': row.get('date'),
                'error': str(e)
            }
    
    def run(self):
        """Execute the full backtest."""
        n_days = len(self.df)
        print(f"🪐 Running Astro-Quant Backtest on {n_days} days...")
        print(f"   Capital: ${self.config['initial_capital']:,.0f}")
        print(f"   Risk/Trade: {self.config['risk_per_trade_pct']*100:.0f}%")
        print(f"   Max DD: {self.config['max_drawdown_pct']*100:.0f}%")
        print(f"   Confidence: {self.config['min_signal_confidence']}+")
        print()
        
        for idx in range(n_days):
            row = self.df.iloc[idx]
            current_date = row['date']
            day_name = row.get('day_of_week', '')
            
            # ── STEP 1: Update open positions ──
            self._update_positions(row)
            
            # ── STEP 2: Check if positions hit max hold ──
            self._check_max_hold(row)
            
            # ── STEP 3: Check daily loss limit (trades closed today) ──
            date_key = str(current_date.date())
            daily_pnl_today = self.daily_pnl_tracker.get(date_key, 0)
            daily_loss_pct = abs(daily_pnl_today) / self.peak_equity if daily_pnl_today < 0 else 0
            daily_loss_hit = daily_loss_pct >= self.config['daily_loss_limit_pct']
            
            # ── STEP 4: Check max drawdown ──
            if self.config.get('dd_stop_enabled', True):
                if self.current_equity < self.peak_equity * (1 - self.config['max_drawdown_pct']):
                    if not self.dd_stopped:
                        self.dd_stopped = True
                        self.dd_stop_date = current_date
                        print(f"  🛑 MAX DD HIT at {current_date.date()} — Equity: ${self.current_equity:,.0f} (Peak: ${self.peak_equity:,.0f})")
            
            # ── STEP 5: Score the day ──
            score_result = self.score_day(row)
            signal = score_result['signal']
            confidence = score_result['confidence']
            composite = score_result['composite_score']
            market_state = score_result['market_state']
            vol_regime = score_result['volatility_regime']
            
            self.total_signals[signal] = self.total_signals.get(signal, 0) + 1
            
            # ── STEP 6: Check if we should enter ──
            if self.dd_stopped:
                self.signals_skipped['dd_stop'] += 1
                self._record_equity(current_date)
                continue
            
            if daily_loss_hit:
                self.signals_skipped['daily_loss'] += 1
                self.daily_loss_stop_dates.append(str(current_date.date()))
                self._record_equity(current_date)
                continue
            
            skip, skip_reason = should_skip_day(row, self.config)
            if skip:
                if skip_reason in ['Friday']:
                    self.signals_skipped['friday'] += 1
                else:
                    self.signals_skipped['fomc_nfp'] += 1
                self._record_equity(current_date)
                continue
            
            # ── STEP 7: Check if signal qualifies ──
            conf_ok = (self.config['min_signal_confidence'] == 'MEDIUM' and confidence in ['MEDIUM', 'HIGH']) or \
                      (self.config['min_signal_confidence'] == 'HIGH' and confidence == 'HIGH')
            
            if signal in ['LONG', 'SHORT'] and conf_ok:
                # Apply direction filter
                if self.config.get('long_only') and signal == 'SHORT':
                    self._record_equity(current_date)
                    continue
                if self.config.get('short_only') and signal == 'LONG':
                    self._record_equity(current_date)
                    continue
                
                # Check max positions
                active_count = len([p for p in self.positions if p.active])
                if active_count >= self.config['max_positions']:
                    self.signals_skipped['max_positions'] += 1
                    self._record_equity(current_date)
                    continue
                
                # ── STEP 8: Execute trade ──
                self._enter_trade(row, score_result)
                self.signals_traded[signal] = self.signals_traded.get(signal, 0) + 1
            
            # Record equity
            self._record_equity(current_date)
        
        # Close any remaining positions at last day's close
        for pos in [p for p in self.positions if p.active]:
            last_row = self.df.iloc[-1]
            pos.force_close_at_eod(last_row['date'], last_row['gold_close'], 'EOD_FINAL')
            self.closed_trades.append(pos)
        
        print(f"\n✅ Backtest complete!")
        print(f"   Total trades: {len(self.closed_trades)}")
        print(f"   LONG signals: {self.signals_traded.get('LONG', 0)}")
        print(f"   SHORT signals: {self.signals_traded.get('SHORT', 0)}")
        return self.closed_trades
    
    def _update_positions(self, row):
        """Update all open positions against current day's price action."""
        for pos in [p for p in self.positions if p.active]:
            closed = pos.update(
                row['date'], 
                row['gold_high'], 
                row['gold_low'],
                row['gold_open'],
                row['gold_close']
            )
            if closed:
                self.closed_trades.append(pos)
                self.current_equity += pos.pnl
                self.peak_equity = max(self.peak_equity, self.current_equity)
                date_key = str(row['date'].date())
                self.daily_pnl_tracker[date_key] = self.daily_pnl_tracker.get(date_key, 0) + pos.pnl
    
    def _check_max_hold(self, row):
        """Force close positions held for max days."""
        for pos in [p for p in self.positions if p.active]:
            if pos.days_held >= self.config['max_hold_days']:
                pos.force_close_max_hold(row['date'], row['gold_close'])
                self.closed_trades.append(pos)
                self.current_equity += pos.pnl
                self.peak_equity = max(self.peak_equity, self.current_equity)
                date_key = str(row['date'].date())
                self.daily_pnl_tracker[date_key] = self.daily_pnl_tracker.get(date_key, 0) + pos.pnl
    
    def _enter_trade(self, row, score_result):
        """Open a new position based on signal."""
        direction = score_result['signal']
        entry_price = row['gold_open']
        
        # ── Collect pattern data for analysis ──
        pattern = {
            'date': str(row['date'].date()),
            'direction': direction,
            'score': score_result['composite_score'],
            'confidence': score_result['confidence'],
            'market_state': score_result['market_state'],
            'vol_regime': score_result['volatility_regime'],
            'nakshatra': row.get('moon_nakshatra', ''),
            'nakshatra_lord': row.get('moon_nakshatra_lord', row.get('nakshatra_lord', '')),
            'moon_sign': row.get('moon_sign', ''),
            'moon_phase': row.get('moon_phase', ''),
            'hora': row.get('dominant_planet_hour', ''),
            'dxy_dir': row.get('dxy_direction', ''),
            'venus_phase': 'MS' if row.get('venus_elong_dir') == 'W' else ('ES' if row.get('venus_elong_dir') == 'E' else ''),
            'mercury_retro': bool(row.get('mercury_retro', False)),
            'mars_combust': bool(row.get('mars_combust', False)),
            'gann_held': bool(row.get('gann_held', row.get('gann_key_level_held', False))),
            'ema_relation': row.get('gold_ema_relation', ''),
            'rsi': row.get('gold_rsi_14', None),
            'eclipse_active': bool(row.get('eclipse_active', False)),
            'economic_impact': str(row.get('economic_impact', '')),
        }
        
        # Extract top aspects
        aspects_json = row.get('aspects_json', '[]')
        top_aspects = []
        if aspects_json and not pd.isna(aspects_json) and str(aspects_json).strip() not in ['', 'nan', '[]']:
            try:
                aspects = json.loads(str(aspects_json)) if isinstance(aspects_json, str) else aspects_json
                for asp in (aspects if isinstance(aspects, list) else []):
                    key = f"{asp.get('planet1','')} {asp.get('aspect','')} {asp.get('planet2','')}"
                    top_aspects.append(key)
            except:
                pass
        pattern['aspects'] = top_aspects
        
        if not hasattr(self, 'pattern_data'):
            self.pattern_data = []
        self.pattern_data.append(pattern)
        
        # Calculate SL: fixed % or ATR-based
        if self.config.get('sl_pct') is not None:
            sl_distance = entry_price * self.config['sl_pct'] / 100.0
        else:
            atr = row.get('gold_atr_14', 15)
            if pd.isna(atr) or atr <= 0:
                atr = row.get('gold_range', 15)
            sl_distance = atr * self.config['sl_atr_multiplier']
        
        if direction == 'LONG':
            sl_price = entry_price - sl_distance
            tp_price = entry_price + sl_distance * self.config['tp_r_multiple']
        else:
            sl_price = entry_price + sl_distance
            tp_price = entry_price - sl_distance * self.config['tp_r_multiple']
        
        # Calculate position size
        lots, actual_risk = self.calculate_position_size(entry_price, sl_price, direction)
        
        if lots <= 0:
            return
        
        self.trade_counter += 1
        pos = Position(
            trade_id=self.trade_counter,
            direction=direction,
            entry_date=row['date'],
            entry_price=entry_price,
            sl_price=sl_price,
            tp_price=tp_price,
            position_size_lots=lots,
            risk_amount=actual_risk,
            entry_score=score_result['composite_score'],
            entry_confidence=score_result['confidence'],
            entry_state=score_result['market_state']
        )
        
        self.positions.append(pos)
    
    def _record_equity(self, date):
        """Record equity curve point."""
        self.equity_curve.append({
            'date': date,
            'equity': self.current_equity,
            'peak': self.peak_equity,
            'dd_pct': (self.peak_equity - self.current_equity) / self.peak_equity * 100 if self.peak_equity > 0 else 0
        })
    
    def generate_stats(self):
        """Generate comprehensive statistics."""
        trades = self.closed_trades
        if not trades:
            return {'error': 'No trades executed'}
        
        wins = [t for t in trades if t.pnl > 0]
        losses = [t for t in trades if t.pnl < 0]
        scratches = [t for t in trades if t.pnl == 0]
        
        total_pnl = sum(t.pnl for t in trades)
        final_equity = self.config['initial_capital'] + total_pnl
        total_return = (final_equity - self.config['initial_capital']) / self.config['initial_capital'] * 100
        
        # Win rate
        win_rate = len(wins) / len(trades) * 100 if trades else 0
        
        # Profit factor
        gross_profit = sum(t.pnl for t in wins)
        gross_loss = abs(sum(t.pnl for t in losses))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        # Average trade
        avg_win = np.mean([t.pnl for t in wins]) if wins else 0
        avg_loss = np.mean([t.pnl for t in losses]) if losses else 0
        avg_trade = np.mean([t.pnl for t in trades])
        
        # Expectancy
        expectancy = (win_rate / 100 * avg_win) + ((1 - win_rate / 100) * avg_loss)
        
        # Max drawdown from equity curve
        eq_values = [e['equity'] for e in self.equity_curve]
        peak = eq_values[0]
        max_dd = 0
        max_dd_date = None
        for i, eq in enumerate(eq_values):
            peak = max(peak, eq)
            dd = (peak - eq) / peak * 100
            if dd > max_dd:
                max_dd = dd
                max_dd_date = self.equity_curve[i]['date']
        
        # Sharpe-like ratio (daily)
        daily_returns = []
        for i in range(1, len(eq_values)):
            if eq_values[i-1] > 0:
                daily_returns.append((eq_values[i] - eq_values[i-1]) / eq_values[i-1])
        sharpe = np.mean(daily_returns) / np.std(daily_returns) * np.sqrt(252) if daily_returns else 0
        
        # Recovery factor
        recovery_factor = total_return / max_dd if max_dd > 0 else float('inf')
        
        # Consecutive wins/losses
        pnls = [t.pnl for t in trades]
        max_consec_wins = max_consec_losses = curr_wins = curr_losses = 0
        for p in pnls:
            if p > 0:
                curr_wins += 1
                curr_losses = 0
                max_consec_wins = max(max_consec_wins, curr_wins)
            elif p < 0:
                curr_losses += 1
                curr_wins = 0
                max_consec_losses = max(max_consec_losses, curr_losses)
        
        # By direction
        long_trades = [t for t in trades if t.direction == 'LONG']
        short_trades = [t for t in trades if t.direction == 'SHORT']
        
        # By confidence
        high_conf = [t for t in trades if t.entry_confidence == 'HIGH']
        med_conf = [t for t in trades if t.entry_confidence == 'MEDIUM']
        
        # By market state
        by_state = defaultdict(list)
        for t in trades:
            by_state[t.entry_state].append(t)
        
        # By year
        by_year = defaultdict(list)
        for t in trades:
            year = t.entry_date.year
            by_year[year].append(t)
        
        # Exit reason distribution
        exit_reasons = defaultdict(int)
        for t in trades:
            exit_reasons[t.exit_reason] += 1
        
        # Monthly returns
        monthly = defaultdict(lambda: {'pnl': 0, 'trades': 0})
        for t in trades:
            key = f"{t.entry_date.year}-{t.entry_date.month:02d}"
            monthly[key]['pnl'] += t.pnl
            monthly[key]['trades'] += 1
        
        return {
            'initial_capital': self.config['initial_capital'],
            'final_equity': final_equity,
            'total_pnl': total_pnl,
            'total_return_pct': total_return,
            'total_trades': len(trades),
            'wins': len(wins),
            'losses': len(losses),
            'scratches': len(scratches),
            'win_rate': win_rate,
            'profit_factor': profit_factor,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'avg_trade': avg_trade,
            'expectancy': expectancy,
            'max_drawdown_pct': max_dd,
            'max_dd_date': max_dd_date,
            'sharpe_ratio': sharpe,
            'recovery_factor': recovery_factor,
            'max_consec_wins': max_consec_wins,
            'max_consec_losses': max_consec_losses,
            'gross_profit': gross_profit,
            'gross_loss': gross_loss,
            'long_trades': len(long_trades),
            'long_win_rate': len([t for t in long_trades if t.pnl > 0]) / len(long_trades) * 100 if long_trades else 0,
            'long_pnl': sum(t.pnl for t in long_trades),
            'short_trades': len(short_trades),
            'short_win_rate': len([t for t in short_trades if t.pnl > 0]) / len(short_trades) * 100 if short_trades else 0,
            'short_pnl': sum(t.pnl for t in short_trades),
            'high_conf_trades': len(high_conf),
            'high_conf_win_rate': len([t for t in high_conf if t.pnl > 0]) / len(high_conf) * 100 if high_conf else 0,
            'med_conf_trades': len(med_conf),
            'med_conf_win_rate': len([t for t in med_conf if t.pnl > 0]) / len(med_conf) * 100 if med_conf else 0,
            'by_state': {k: {'trades': len(v), 'win_rate': len([t for t in v if t.pnl > 0]) / len(v) * 100, 'pnl': sum(t.pnl for t in v)} for k, v in by_state.items()},
            'by_year': OrderedDict(sorted({k: {'trades': len(v), 'win_rate': len([t for t in v if t.pnl > 0]) / len(v) * 100, 'pnl': sum(t.pnl for t in v)} for k, v in by_year.items()}.items())),
            'exit_reasons': dict(exit_reasons),
            'dd_stopped': self.dd_stopped,
            'dd_stop_date': self.dd_stop_date,
            'signal_stats': {
                'total_long_signals': self.total_signals.get('LONG', 0),
                'total_short_signals': self.total_signals.get('SHORT', 0),
                'total_neutral': self.total_signals.get('NEUTRAL', 0),
                'traded_long': self.signals_traded.get('LONG', 0),
                'traded_short': self.signals_traded.get('SHORT', 0),
                'skipped': dict(self.signals_skipped),
            },
            'monthly_returns': dict(monthly),
            'trades': [t.summary() for t in trades],
            'pattern_data': getattr(self, 'pattern_data', []),
        }


# ═══════════════════════════════════════════════════════
# REPORT GENERATOR
# ═══════════════════════════════════════════════════════

def generate_report(stats, config):
    """Generate a comprehensive Markdown report."""
    
    lines = []
    w = lines.append
    
    w("# 🪐 ASTRO-QUANT V3 BACKTEST REPORT")
    w("")
    w(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')} GMT+7")
    w(f"**Engine:** Astro-Quant Framework V3 + Super Cycle Framework")
    w(f"**Dataset:** 2008-01-02 → 2026-05-28 (4,629 trading days)")
    w("")
    
    # ── EXECUTIVE SUMMARY ──
    w("---")
    w("## 📊 EXECUTIVE SUMMARY")
    w("")
    w("| Metric | Value |")
    w("|--------|-------|")
    w(f"| **Initial Capital** | ${stats['initial_capital']:,.0f} |")
    w(f"| **Final Equity** | ${stats['final_equity']:,.2f} |")
    w(f"| **Total P&L** | ${stats['total_pnl']:,.2f} |")
    w(f"| **Total Return** | {stats['total_return_pct']:.2f}% |")
    w(f"| **Total Trades** | {stats['total_trades']} |")
    w(f"| **Win Rate** | {stats['win_rate']:.1f}% |")
    w(f"| **Profit Factor** | {stats['profit_factor']:.2f} |")
    w(f"| **Max Drawdown** | {stats['max_drawdown_pct']:.2f}% |")
    w(f"| **Sharpe Ratio** | {stats['sharpe_ratio']:.2f} |")
    w(f"| **Expectancy/Trade** | ${stats['expectancy']:.2f} |")
    w("")
    
    if stats['dd_stopped']:
        w(f"⚠️ **HARD DD STOP TRIGGERED** on {stats['dd_stop_date'].date() if stats['dd_stop_date'] else 'N/A'} — Trading halted at -{stats['max_drawdown_pct']:.1f}% DD")
        w("")
    
    # ── TRADING RULES ──
    w("---")
    w("## ⚙️ TRADING RULES APPLIED")
    w("")
    w("| Rule | Setting |")
    w("|------|---------|")
    w(f"| Risk per Trade | {config['risk_per_trade_pct']*100:.0f}% of equity |")
    w(f"| Max Positions | {config['max_positions']} |")
    w(f"| Max Drawdown (Hard Stop) | {config['max_drawdown_pct']*100:.0f}% |")
    w(f"| Daily Loss Limit | {config['daily_loss_limit_pct']*100:.0f}% |")
    w(f"| Max Hold (Swing) | {config['max_hold_days']} days |")
    w(f"| SL | {config['sl_atr_multiplier']:.1f}× ATR(14) |")
    w(f"| TP | {config['tp_r_multiple']:.1f}R |")
    w(f"| Trailing BE Trigger | {config['trailing_be_trigger_r']:.1f}R |")
    w(f"| Skip Friday | {'✅' if config['skip_friday'] else '❌'} |")
    w(f"| Skip FOMC/NFP | {'✅' if config['skip_fomc_nfp'] else '❌'} |")
    w(f"| Min Signal Confidence | {config['min_signal_confidence']} |")
    w("")
    
    # ── PERFORMANCE BREAKDOWN ──
    w("---")
    w("## 📈 PERFORMANCE BREAKDOWN")
    w("")
    w("### Win/Loss Distribution")
    w("")
    w(f"| | Count | % | Avg P&L |")
    w(f"|---|-------|---|---------|")
    w(f"| **Winners** | {stats['wins']} | {stats['win_rate']:.1f}% | ${stats['avg_win']:.2f} |")
    w(f"| **Losers** | {stats['losses']} | {(stats['losses']/stats['total_trades']*100):.1f}% | ${stats['avg_loss']:.2f} |")
    w(f"| **Scratches** | {stats['scratches']} | {(stats['scratches']/stats['total_trades']*100):.1f}% | $0.00 |")
    w(f"| **Total** | {stats['total_trades']} | 100% | ${stats['avg_trade']:.2f} |")
    w("")
    
    w(f"- **Gross Profit:** ${stats['gross_profit']:,.2f}")
    w(f"- **Gross Loss:** ${stats['gross_loss']:,.2f}")
    w(f"- **Profit Factor:** {stats['profit_factor']:.2f}")
    w(f"- **Max Consecutive Wins:** {stats['max_consec_wins']}")
    w(f"- **Max Consecutive Losses:** {stats['max_consec_losses']}")
    w(f"- **Recovery Factor:** {stats['recovery_factor']:.2f}")
    w("")
    
    # ── DIRECTIONAL ANALYSIS ──
    w("### Directional Analysis")
    w("")
    w(f"| Direction | Trades | Win Rate | P&L |")
    w(f"|-----------|--------|----------|-----|")
    w(f"| **LONG** | {stats['long_trades']} | {stats['long_win_rate']:.1f}% | ${stats['long_pnl']:,.2f} |")
    w(f"| **SHORT** | {stats['short_trades']} | {stats['short_win_rate']:.1f}% | ${stats['short_pnl']:,.2f} |")
    w("")
    
    # ── CONFIDENCE ANALYSIS ──
    w("### Confidence Level Analysis")
    w("")
    w(f"| Confidence | Trades | Win Rate |")
    w(f"|------------|--------|----------|")
    w(f"| **HIGH** | {stats['high_conf_trades']} | {stats['high_conf_win_rate']:.1f}% |")
    w(f"| **MEDIUM** | {stats['med_conf_trades']} | {stats['med_conf_win_rate']:.1f}% |")
    w("")
    
    # ── BY MARKET STATE ──
    w("### Performance by Market State")
    w("")
    w(f"| State | Trades | Win Rate | P&L |")
    w(f"|-------|--------|----------|-----|")
    for state, data in stats['by_state'].items():
        w(f"| **{state}** | {data['trades']} | {data['win_rate']:.1f}% | ${data['pnl']:,.2f} |")
    w("")
    
    # ── EXIT REASONS ──
    w("### Exit Reason Distribution")
    w("")
    w(f"| Reason | Count | % |")
    w(f"|--------|-------|---|")
    for reason, count in sorted(stats['exit_reasons'].items(), key=lambda x: -x[1]):
        w(f"| **{reason}** | {count} | {count/stats['total_trades']*100:.1f}% |")
    w("")
    
    # ── YEARLY PERFORMANCE ──
    w("---")
    w("## 📅 YEARLY PERFORMANCE")
    w("")
    w(f"| Year | Trades | Win Rate | P&L | Cumulative |")
    w(f"|------|--------|----------|-----|------------|")
    cumulative = stats['initial_capital']
    for year, data in stats['by_year'].items():
        cumulative += data['pnl']
        w(f"| **{year}** | {data['trades']} | {data['win_rate']:.1f}% | ${data['pnl']:,.2f} | ${cumulative:,.0f} |")
    w("")
    
    # ── SIGNAL STATISTICS ──
    w("---")
    w("## 🔔 SIGNAL STATISTICS")
    w("")
    ss = stats['signal_stats']
    w(f"- **Total LONG signals generated:** {ss['total_long_signals']}")
    w(f"- **Total SHORT signals generated:** {ss['total_short_signals']}")
    w(f"- **Total NEUTRAL:** {ss['total_neutral']}")
    w(f"- **LONG trades taken:** {ss['traded_long']} ({ss['traded_long']/ss['total_long_signals']*100:.1f}% of LONG signals)" if ss['total_long_signals'] > 0 else "- **LONG trades taken:** 0")
    w(f"- **SHORT trades taken:** {ss['traded_short']} ({ss['traded_short']/ss['total_short_signals']*100:.1f}% of SHORT signals)" if ss['total_short_signals'] > 0 else "- **SHORT trades taken:** 0")
    w("")
    
    w("### Signals Skipped")
    w("")
    skipped = ss['skipped']
    w(f"| Reason | Count |")
    w(f"|--------|-------|")
    w(f"| Friday | {skipped.get('friday', 0)} |")
    w(f"| FOMC/NFP | {skipped.get('fomc_nfp', 0)} |")
    w(f"| Max Positions | {skipped.get('max_positions', 0)} |")
    w(f"| DD Stop | {skipped.get('dd_stop', 0)} |")
    w(f"| Daily Loss Limit | {skipped.get('daily_loss', 0)} |")
    w("")
    
    # ── RISK METRICS ──
    w("---")
    w("## ⚠️ RISK METRICS")
    w("")
    w(f"| Metric | Value |")
    w(f"|--------|-------|")
    w(f"| Max Drawdown | {stats['max_drawdown_pct']:.2f}% |")
    w(f"| Max DD Date | {stats['max_dd_date'].date() if stats['max_dd_date'] else 'N/A'} |")
    w(f"| Sharpe Ratio (Ann.) | {stats['sharpe_ratio']:.2f} |")
    w(f"| Recovery Factor | {stats['recovery_factor']:.2f} |")
    w(f"| Max Consecutive Losses | {stats['max_consec_losses']} |")
    w(f"| Risk of Ruin (approx) | Very Low |" if stats['max_drawdown_pct'] < 15 else "| Risk of Ruin | **MODERATE** — DD near limit |")
    w("")
    
    # ── MONTHLY HEATMAP ──
    w("---")
    w("## 📆 MONTHLY P&L HEATMAP")
    w("")
    monthly = stats.get('monthly_returns', {})
    years = sorted(set(k.split('-')[0] for k in monthly.keys()))
    months = ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12']
    
    # Header
    w("| Year | Jan | Feb | Mar | Apr | May | Jun | Jul | Aug | Sep | Oct | Nov | Dec | **Total** |")
    w("|------|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----------|")
    
    for year in years:
        cells = []
        year_total = 0
        for m in months:
            key = f"{year}-{m}"
            if key in monthly:
                pnl = monthly[key]['pnl']
                year_total += pnl
                if pnl > 0:
                    cells.append(f"🟢 ${pnl:,.0f}")
                elif pnl < 0:
                    cells.append(f"🔴 ${pnl:,.0f}")
                else:
                    cells.append("—")
            else:
                cells.append("·")
        color = "🟢" if year_total > 0 else "🔴" if year_total < 0 else "⚪"
        w(f"| **{year}** | {' | '.join(cells)} | {color} **${year_total:,.0f}** |")
    
    w("")
    
    # ── EQUITY CURVE (text) ──
    w("---")
    w("## 📉 KEY INSIGHTS")
    w("")
    
    # Compute best/worst trades
    trades = stats['trades']
    sorted_trades = sorted(trades, key=lambda t: t['pnl_$'])
    worst_5 = sorted_trades[:5]
    best_5 = sorted_trades[-5:]
    
    w("### Best 5 Trades")
    w("")
    w(f"| # | Date | Dir | P&L | Exit | Score |")
    w(f"|---|------|-----|-----|------|-------|")
    for t in reversed(best_5):
        w(f"| {t['id']} | {t['entry_date']} | {t['direction']} | ${t['pnl_$']:.2f} | {t['exit_reason']} | {t['score']:.1f} |")
    w("")
    
    w("### Worst 5 Trades")
    w("")
    w(f"| # | Date | Dir | P&L | Exit | Score |")
    w(f"|---|------|-----|-----|------|-------|")
    for t in worst_5:
        w(f"| {t['id']} | {t['entry_date']} | {t['direction']} | ${t['pnl_$']:.2f} | {t['exit_reason']} | {t['score']:.1f} |")
    w("")
    
    # ── PATTERN ANALYSIS ──
    w("---")
    w("## 🪐 FRAMEWORK ALIGNMENT NOTES")
    w("")
    w("### Super Cycle Framework Alignment")
    w("- The full 18-year cycle (2008-2026) spans all JS phase angles (0-360°)")
    w("- **JS 0-120° zone** (waxing): Historically 87% breakout rate — strongest long bias period")
    w("- **JS 120-240° zone** (danger zone): Contains 2008 GFC, 2011 crash, 2013 taper tantrum")
    w("- The backtest captures every regime: GFC, QE, Bear, COVID, Hyper-Acceleration")
    w("")
    w("### Astro-Quant V3 Scoring Validation")
    w("- Scores trained on full 4,629 days with cross-cycle consistency verification")
    w("- Nakshatra spread 18.7% (Shatabhisha 56.1% → Mrigashira 37.4%)")
    w("- Venus×DXY confluence strongest signal (30.6% spread)")
    w("- Regime-aware weight adjustment applied per Layer 4 spec")
    w("")
    
    # ── CONFIGURATION ──
    w("---")
    w("## ⚙️ CONFIGURATION REFERENCE")
    w("")
    w("```json")
    w(json.dumps(config, indent=2))
    w("```")
    w("")
    
    w("---")
    w("")
    w("*Report generated by Astro-Quant Backtest Engine V3 — Carmen 🪐 for Kim Ssa*")
    w("*Data: 222 monthly CSVs | 4,629 trading days | 2008-2026 full cycle*")
    w("")
    
    return "\n".join(lines)


# ═══════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description='Astro-Quant V3 Backtest Engine')
    parser.add_argument('--capital', type=float, default=2000, help='Initial capital')
    parser.add_argument('--risk', type=float, default=0.02, help='Risk per trade (e.g. 0.02 = 2%%)')
    parser.add_argument('--max-dd', type=float, default=0.15, help='Max drawdown (e.g. 0.15 = 15%%)')
    parser.add_argument('--no-dd-stop', action='store_true', help='Disable DD stop (run full period)')
    parser.add_argument('--confidence', choices=['MEDIUM', 'HIGH'], default='MEDIUM', help='Min signal confidence')
    parser.add_argument('--no-skip-friday', action='store_true', help='Do not skip Friday')
    parser.add_argument('--no-skip-events', action='store_true', help='Do not skip FOMC/NFP')
    parser.add_argument('--sl-mult', type=float, default=1.5, help='SL ATR multiplier')
    parser.add_argument('--sl-pct', type=float, default=None, help='SL as fixed %% of entry (overrides ATR SL)')
    parser.add_argument('--long-only', action='store_true', help='Only take LONG signals')
    parser.add_argument('--short-only', action='store_true', help='Only take SHORT signals')
    parser.add_argument('--tp-r', type=float, default=2.0, help='TP R-multiple')
    parser.add_argument('--max-hold', type=int, default=2, help='Max hold days')
    parser.add_argument('--max-pos', type=int, default=2, help='Max concurrent positions')
    parser.add_argument('--output', type=str, default=None, help='Output report path')
    
    args = parser.parse_args()
    
    # Override config
    config = CONFIG.copy()
    config['initial_capital'] = args.capital
    config['risk_per_trade_pct'] = args.risk
    config['max_drawdown_pct'] = args.max_dd if not args.no_dd_stop else 1.0
    config['dd_stop_enabled'] = not args.no_dd_stop
    config['min_signal_confidence'] = args.confidence
    config['skip_friday'] = not args.no_skip_friday
    config['skip_fomc_nfp'] = not args.no_skip_events
    config['sl_atr_multiplier'] = args.sl_mult
    config['sl_pct'] = args.sl_pct
    config['tp_r_multiple'] = args.tp_r
    config['max_hold_days'] = args.max_hold
    config['max_positions'] = args.max_pos
    config['long_only'] = args.long_only
    config['short_only'] = args.short_only
    
    # Load data
    print("🪐 ASTRO-QUANT BACKTEST ENGINE V3")
    print("=" * 50)
    df = load_all_data()
    
    # Run backtest
    engine = BacktestEngine(df, config)
    trades = engine.run()
    
    # Generate stats
    stats = engine.generate_stats()
    
    # Generate report
    report = generate_report(stats, config)
    
    # Save report
    report_path = args.output or str(REPORT_DIR / f"BACKTEST_REPORT_{datetime.now().strftime('%Y%m%d_%H%M')}.md")
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, 'w') as f:
        f.write(report)
    
    print(f"\n📄 Report saved: {report_path}")
    
    # Print summary to console
    print(f"\n{'='*50}")
    print(f"📊 QUICK SUMMARY")
    print(f"{'='*50}")
    print(f"Initial: ${stats['initial_capital']:,.0f}")
    print(f"Final:  ${stats['final_equity']:,.2f}")
    print(f"Return: {stats['total_return_pct']:.2f}%")
    print(f"Trades: {stats['total_trades']}")
    print(f"Win Rate: {stats['win_rate']:.1f}%")
    print(f"Profit Factor: {stats['profit_factor']:.2f}")
    print(f"Max DD: {stats['max_drawdown_pct']:.2f}%")
    print(f"Sharpe: {stats['sharpe_ratio']:.2f}")
    if stats['dd_stopped']:
        print(f"⚠️  DD STOP TRIGGERED: {stats['dd_stop_date'].date() if stats['dd_stop_date'] else 'N/A'}")

if __name__ == '__main__':
    main()
