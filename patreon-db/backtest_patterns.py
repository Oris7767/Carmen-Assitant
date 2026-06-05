import pandas as pd
import numpy as np
from datetime import datetime
import json
import glob
import os

def load_all_data():
    """Load all CSV files from the patreon-db data directory"""
    csv_files = glob.glob("/Users/kimssa/.openclaw/workspace/patreon-db/data/*.csv")
    print(f"Found {len(csv_files)} CSV files")
    
    all_data = []
    for file in sorted(csv_files):
        try:
            df = pd.read_csv(file)
            all_data.append(df)
            print(f"Loaded {file}: {len(df)} rows")
        except Exception as e:
            print(f"Error loading {file}: {e}")
    
    if all_data:
        full_df = pd.concat(all_data, ignore_index=True)
        print(f"\nTotal data: {len(full_df)} rows from {full_df['date'].min()} to {full_df['date'].max()}")
        return full_df
    else:
        return pd.DataFrame()

def calculate_performance_metrics(df, condition_col, target_col='gold_bullish', change_col='gold_change_pct'):
    """Calculate performance metrics for a given condition"""
    subset = df[df[condition_col] == True]
    if len(subset) == 0:
        return None
    
    total_trades = len(subset)
    bullish_count = subset[target_col].sum()
    bearish_count = total_trades - bullish_count
    win_rate = bullish_count / total_trades if total_trades > 0 else 0
    avg_return = subset[change_col].mean()
    std_return = subset[change_col].std()
    total_return = subset[change_col].sum()
    
    # Calculate Sharpe ratio (risk-adjusted return)
    sharpe_ratio = avg_return / std_return if std_return != 0 else 0
    
    # Calculate maximum drawdown
    cumulative_returns = subset[change_col].cumsum()
    running_max = cumulative_returns.expanding().max()
    drawdown = cumulative_returns - running_max
    max_drawdown = drawdown.min()
    
    return {
        'total_trades': total_trades,
        'bullish_count': bullish_count,
        'bearish_count': bearish_count,
        'win_rate': win_rate,
        'avg_return': avg_return,
        'std_return': std_return,
        'sharpe_ratio': sharpe_ratio,
        'total_return': total_return,
        'max_drawdown': max_drawdown,
        'avg_magnitude': abs(subset[change_col]).mean()
    }

def analyze_patterns(df):
    """Analyze various astro-quant patterns in the data"""
    print("Analyzing patterns...")
    
    results = {}
    
    # Gann Level Patterns
    gann_conditions = {
        'gann_key_level_held_bullish': (df['gann_key_level_held'] == True) & (df['gold_bullish'] == True),
        'gann_key_level_held_bearish': (df['gann_key_level_held'] == True) & (df['gold_bullish'] == False),
        'gann_breached_level_bullish': (df['gann_breached_level'].notna()) & (df['gold_bullish'] == True),
        'gann_breached_level_bearish': (df['gann_breached_level'].notna()) & (df['gold_bullish'] == False),
        'gann_support_bounce': (df['gann_breached_level'].fillna('').str.contains('support', case=False, na=False)) & (df['gold_bullish'] == True),
        'gann_resistance_breakout': (df['gann_breached_level'].fillna('').str.contains('resistance', case=False, na=False)) & (df['gold_bullish'] == True)
    }
    
    # Astrological Patterns
    astro_conditions = {
        'mercury_retrograde_bullish': (df['mercury_retro'] == True) & (df['gold_bullish'] == True),
        'mercury_retrograde_bearish': (df['mercury_retro'] == True) & (df['gold_bullish'] == False),
        'venus_retrograde_bullish': (df['venus_retro'] == True) & (df['gold_bullish'] == True),
        'venus_retrograde_bearish': (df['venus_retro'] == True) & (df['gold_bullish'] == False),
        'mars_retrograde_bullish': (df['mars_retro'] == True) & (df['gold_bullish'] == True),
        'mars_retrograde_bearish': (df['mars_retro'] == True) & (df['gold_bullish'] == False),
        'jupiter_retrograde_bullish': (df['jupiter_retro'] == True) & (df['gold_bullish'] == True),
        'jupiter_retrograde_bearish': (df['jupiter_retro'] == True) & (df['gold_bullish'] == False),
        'saturn_retrograde_bullish': (df['saturn_retro'] == True) & (df['gold_bullish'] == True),
        'saturn_retrograde_bearish': (df['saturn_retro'] == True) & (df['gold_bullish'] == False),
        
        # Combust conditions
        'mercury_combust_bullish': (df['mercury_combust'] == True) & (df['gold_bullish'] == True),
        'mercury_combust_bearish': (df['mercury_combust'] == True) & (df['gold_bullish'] == False),
        'venus_combust_bullish': (df['venus_combust'] == True) & (df['gold_bullish'] == True),
        'venus_combust_bearish': (df['venus_combust'] == True) & (df['gold_bullish'] == False),
        'mars_combust_bullish': (df['mars_combust'] == True) & (df['gold_bullish'] == True),
        'mars_combust_bearish': (df['mars_combust'] == True) & (df['gold_bullish'] == False),
        
        # Moon Nakshatra patterns
        'nakshatra_purva_ashadha_bullish': (df['moon_nakshatra'] == 'Purva Ashadha') & (df['gold_bullish'] == True),
        'nakshatra_jyeshtha_bearish': (df['moon_nakshatra'] == 'Jyeshtha') & (df['gold_bullish'] == False),
        'nakshatra_ashwini_bullish': (df['moon_nakshatra'] == 'Ashwini') & (df['gold_bullish'] == True),
        'nakshatra_rohini_bearish': (df['moon_nakshatra'] == 'Rohini') & (df['gold_bullish'] == False),
        'nakshatra_mula_bullish': (df['moon_nakshatra'] == 'Mula') & (df['gold_bullish'] == True),
        'nakshatra_shatabhisha_bullish': (df['moon_nakshatra'] == 'Shatabhisha') & (df['gold_bullish'] == True),
        'nakshatra_mrigashira_bearish': (df['moon_nakshatra'] == 'Mrigashira') & (df['gold_bullish'] == False),
        
        # Moon Sign patterns
        'moon_sagittarius_bullish': (df['moon_sign'] == 'Sagittarius') & (df['gold_bullish'] == True),
        'moon_leo_bullish': (df['moon_sign'] == 'Leo') & (df['gold_bullish'] == True),
        'moon_scorpio_bearish': (df['moon_sign'] == 'Scorpio') & (df['gold_bullish'] == False),
        'moon_taurus_bearish': (df['moon_sign'] == 'Taurus') & (df['gold_bullish'] == False),
        
        # Planetary aspects - parsing JSON strings
        'sun_conj_saturn_bullish': df['aspects_json'].str.contains('Sun.*Saturn.*Conjunction', case=False, na=False) & (df['gold_bullish'] == True),
        'sun_conj_saturn_bearish': df['aspects_json'].str.contains('Sun.*Saturn.*Conjunction', case=False, na=False) & (df['gold_bullish'] == False),
        'moon_opposition_saturn_bullish': df['aspects_json'].str.contains('Moon.*Saturn.*Opposition', case=False, na=False) & (df['gold_bullish'] == True),
        'moon_sextile_saturn_bullish': df['aspects_json'].str.contains('Moon.*Saturn.*Sextile', case=False, na=False) & (df['gold_bullish'] == True),
        'mars_square_jupiter_bullish': df['aspects_json'].str.contains('Mars.*Jupiter.*Square', case=False, na=False) & (df['gold_bullish'] == True),
        'mars_square_jupiter_bearish': df['aspects_json'].str.contains('Mars.*Jupiter.*Square', case=False, na=False) & (df['gold_bullish'] == False),
        
        # Planetary hours
        'jupiter_hora_bullish': (df['dominant_planet_hour'] == 'Jupiter') & (df['gold_bullish'] == True),
        'moon_hora_bearish': (df['dominant_planet_hour'] == 'Moon') & (df['gold_bullish'] == False),
        'mars_hora_bearish': (df['dominant_planet_hour'] == 'Mars') & (df['gold_bullish'] == False),
        
        # Eclipse patterns
        'eclipse_active_bullish': (df['eclipse_active'] == True) & (df['gold_bullish'] == True),
        'eclipse_active_bearish': (df['eclipse_active'] == True) & (df['gold_bullish'] == False),
    }
    
    # Market reaction patterns
    market_conditions = {
        'reversal_signal_bullish': (df['market_reaction'] == 'reversal_signal') & (df['gold_bullish'] == True),
        'reversal_signal_bearish': (df['market_reaction'] == 'reversal_signal') & (df['gold_bullish'] == False),
        'strong_trend_bullish': (df['market_reaction'] == 'strong_trend') & (df['gold_bullish'] == True),
        'strong_trend_bearish': (df['market_reaction'] == 'strong_trend') & (df['gold_bullish'] == False),
        'consolidation_bullish': (df['market_reaction'] == 'consolidation') & (df['gold_bullish'] == True),
        'consolidation_bearish': (df['market_reaction'] == 'consolidation') & (df['gold_bullish'] == False),
    }
    
    # Combine all conditions
    all_conditions = {**gann_conditions, **astro_conditions, **market_conditions}
    
    # Calculate metrics for each condition
    for condition_name, condition_mask in all_conditions.items():
        try:
            # Create temporary column for this condition
            temp_col_name = f"temp_{condition_name}"
            df[temp_col_name] = condition_mask
            
            metrics = calculate_performance_metrics(df, temp_col_name, 
                                                  target_col='gold_bullish',
                                                  change_col='gold_change_pct')
            if metrics:
                # Adjust for bearish patterns
                if '_bearish' in condition_name:
                    # For bearish patterns, we're looking for when the market goes down
                    # So we invert the bullish count calculation
                    subset = df[condition_mask]
                    total_trades = len(subset)
                    bearish_count = len(subset[subset['gold_bullish'] == False])
                    win_rate = bearish_count / total_trades if total_trades > 0 else 0
                    avg_return = subset['gold_change_pct'].mean()
                    
                    metrics['bullish_count'] = len(subset[subset['gold_bullish'] == True])
                    metrics['bearish_count'] = bearish_count
                    metrics['win_rate'] = win_rate
                    # For bearish patterns, negative returns are "wins"
                    metrics['avg_return'] = -avg_return if avg_return < 0 else avg_return
                    metrics['total_return'] = -subset['gold_change_pct'].sum() if avg_return < 0 else subset['gold_change_pct'].sum()
                
                results[condition_name] = metrics
            
            # Clean up temporary column
            df.drop(columns=[temp_col_name], inplace=True)
        except Exception as e:
            print(f"Error processing condition {condition_name}: {e}")
            continue
    
    return results

def find_strongest_patterns(results, top_n=20):
    """Find the strongest buy and sell patterns based on multiple criteria"""
    # Convert results to DataFrame for easier sorting
    pattern_data = []
    for pattern, metrics in results.items():
        if metrics:
            pattern_type = 'BUY' if '_bullish' in pattern else 'SELL'
            pattern_data.append({
                'pattern': pattern,
                'type': pattern_type,
                'total_trades': metrics['total_trades'],
                'win_rate': metrics['win_rate'],
                'avg_return': metrics['avg_return'],
                'sharpe_ratio': metrics['sharpe_ratio'],
                'total_return': metrics['total_return'],
                'avg_magnitude': metrics['avg_magnitude']
            })
    
    df_patterns = pd.DataFrame(pattern_data)
    
    # Filter for patterns with minimum trade count for statistical significance
    df_filtered = df_patterns[df_patterns['total_trades'] >= 50].copy()
    
    if df_filtered.empty:
        df_filtered = df_patterns[df_patterns['total_trades'] >= 20].copy()
        if df_filtered.empty:
            df_filtered = df_patterns.copy()
    
    # Sort by multiple criteria
    # For BUY patterns: high win rate AND positive avg return AND good sharpe ratio
    # For SELL patterns: high win rate for bearish moves (negative returns)
    
    # Create composite scores
    df_filtered['composite_score'] = (
        df_filtered['win_rate'] * 0.4 +
        (df_filtered['avg_return'] / df_filtered['avg_return'].abs().max()) * 0.3 +
        (df_filtered['sharpe_ratio'] / df_filtered['sharpe_ratio'].abs().max()) * 0.3
    )
    
    # Separate BUY and SELL patterns
    buy_patterns = df_filtered[df_filtered['type'] == 'BUY'].sort_values('composite_score', ascending=False)
    sell_patterns = df_filtered[df_filtered['type'] == 'SELL'].sort_values('composite_score', ascending=False)
    
    return buy_patterns.head(top_n), sell_patterns.head(top_n)

def main():
    print("Loading 18 years of Aether database...")
    df = load_all_data()
    
    if df.empty:
        print("No data loaded!")
        return
    
    print(f"Analyzing {len(df)} trading days from {df['date'].min()} to {df['date'].max()}")
    
    # Perform pattern analysis
    results = analyze_patterns(df)
    
    # Find strongest patterns
    buy_patterns, sell_patterns = find_strongest_patterns(results)
    
    # Print results
    print("\n" + "="*80)
    print("STRONGEST BUY PATTERNS (18-Year Aether Database)")
    print("="*80)
    for idx, row in buy_patterns.head(15).iterrows():
        print(f"{row['pattern']:<40} | Trades: {row['total_trades']:>4} | Win Rate: {row['win_rate']*100:>5.1f}% | "
              f"Avg Return: {row['avg_return']*100:>5.2f}% | Sharpe: {row['sharpe_ratio']:>5.2f}")
    
    print("\n" + "="*80)
    print("STRONGEST SELL PATTERNS (18-Year Aether Database)")
    print("="*80)
    for idx, row in sell_patterns.head(15).iterrows():
        print(f"{row['pattern']:<40} | Trades: {row['total_trades']:>4} | Win Rate: {row['win_rate']*100:>5.1f}% | "
              f"Avg Return: {row['avg_return']*100:>5.2f}% | Sharpe: {row['sharpe_ratio']:>5.2f}")
    
    # Additional analysis: Most consistent patterns (high win rate + sufficient sample size)
    print("\n" + "="*80)
    print("MOST CONSISTENT PATTERNS (>60% Win Rate, >100 trades)")
    print("="*80)
    consistent_buy = buy_patterns[(buy_patterns['win_rate'] > 0.60) & (buy_patterns['total_trades'] > 100)]
    consistent_sell = sell_patterns[(sell_patterns['win_rate'] > 0.60) & (sell_patterns['total_trades'] > 100)]
    
    print("\nConsistent BUY patterns:")
    for idx, row in consistent_buy.iterrows():
        print(f"{row['pattern']:<40} | Trades: {row['total_trades']:>4} | Win Rate: {row['win_rate']*100:>5.1f}% | "
              f"Avg Return: {row['avg_return']*100:>5.2f}%")
    
    print("\nConsistent SELL patterns:")
    for idx, row in consistent_sell.iterrows():
        print(f"{row['pattern']:<40} | Trades: {row['total_trades']:>4} | Win Rate: {row['win_rate']*100:>5.1f}% | "
              f"Avg Return: {row['avg_return']*100:>5.2f}%")
    
    # Save detailed results to CSV
    all_patterns = pd.concat([buy_patterns, sell_patterns], ignore_index=True)
    all_patterns.to_csv('/Users/kimssa/.openclaw/workspace/18_year_backtest_results.csv', index=False)
    print(f"\nDetailed results saved to: /Users/kimssa/.openclaw/workspace/18_year_backtest_results.csv")

if __name__ == "__main__":
    main()