class TAEngine:
    FIB_LEVELS = [0, 0.2126, 0.5, 0.618, 0.7874, 1, 1.2126, 1.5, 1.618, 1.7874]
    
    @staticmethod
    def calculate_fib_retracement(swing_high: float, swing_low: float, trend: str = 'UP'):
        diff = swing_high - swing_low
        levels = {}
        for ratio in TAEngine.FIB_LEVELS:
            if trend == 'UP':
                price = swing_low + (diff * ratio)
            else:
                price = swing_high - (diff * ratio)
            levels[str(ratio)] = round(price, 2)
        return levels

    @staticmethod
    def analyze_price_fibo(current_price, fib_levels):
        sorted_fibs = sorted([(float(k), v) for k, v in fib_levels.items()], key=lambda x: x[1])
        below = None
        above = None
        for i in range(len(sorted_fibs)-1):
            if sorted_fibs[i][1] <= current_price <= sorted_fibs[i+1][1]:
                below = sorted_fibs[i]
                above = sorted_fibs[i+1]
                break
        
        if not below and len(sorted_fibs) > 0 and current_price < sorted_fibs[0][1]:
            above = sorted_fibs[0]
        if not above and len(sorted_fibs) > 0 and current_price > sorted_fibs[-1][1]:
            below = sorted_fibs[-1]
            
        return {"below": below, "above": above}
