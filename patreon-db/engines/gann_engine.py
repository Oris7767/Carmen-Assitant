import math

class GannEngine:
    """
    W.D. Gann Square of 9 calculation engine for Financial Markets.
    """
    
    # Critical angles in the Square of 9 (in degrees)
    CRITICAL_ANGLES = [45, 90, 135, 180, 225, 270, 315, 360]
    
    @staticmethod
    def extract_base_number(price: float) -> int:
        """
        Convert real price to Gann base number (typically 3 digits).
        E.g., 2453.50 -> 245
              453.50 -> 453
        """
        price_str = str(int(price))
        if len(price_str) >= 3:
            return int(price_str[:3])
        return int(price)

    @staticmethod
    def calculate_gann_levels(base_number: int, scale_factor: float = 1.0) -> dict:
        """
        Calculate support and resistance levels based on Gann Square of 9.
        Formula: Target = (sqrt(Base) +/- (Angle/180))^2
        
        :param base_number: The integer base number on the Square of 9
        :param scale_factor: Multiplier to bring the base number back to real price scale (e.g., * 10)
        :return: Dict containing lists of Support and Resistance levels
        """
        if base_number <= 0:
            return {"supports": [], "resistances": []}

        root = math.sqrt(base_number)
        supports = []
        resistances = []
        
        for angle in GannEngine.CRITICAL_ANGLES:
            factor = angle / 180.0
            
            # Resistance (moving outwards/upwards in the spiral)
            res = (root + factor) ** 2
            resistances.append({
                "angle": angle,
                "base_val": round(res, 2),
                "price": round(res * scale_factor, 2)
            })
            
            # Support (moving inwards/downwards in the spiral)
            sup = (root - factor) ** 2
            supports.append({
                "angle": angle,
                "base_val": round(sup, 2),
                "price": round(sup * scale_factor, 2)
            })
            
        return {
            "base_number": base_number,
            "resistances": resistances,
            "supports": supports
        }

if __name__ == "__main__":
    # Test with Kim Ssa's example
    test_price = 2453.50
    base = GannEngine.extract_base_number(test_price)
    
    # Since we took first 3 digits (245) of a 4-digit number (2453), scale back by 10
    levels = GannEngine.calculate_gann_levels(base, scale_factor=10)
    
    print(f"--- GANN SQUARE OF 9 LEVELS ---")
    print(f"Original Price: {test_price}")
    print(f"Base Number: {base}")
    print("\n[RESISTANCES]")
    for r in levels['resistances']:
        print(f"{r['angle']:>3}° -> Base: {r['base_val']:>6.2f} | Price: {r['price']:>7.2f}")
        
    print("\n[SUPPORTS]")
    for s in levels['supports']:
        print(f"{s['angle']:>3}° -> Base: {s['base_val']:>6.2f} | Price: {s['price']:>7.2f}")

from datetime import datetime, timedelta

class GannDateEngine:
    """
    W.D. Gann Time cycles and Square of 9 on Date.
    
    Cycle: 630 ngày = 360° (1 vòng Gann Date đầy đủ)
    630 = 14 × 45° = 7 × 90°
    
    Công thức:
      angle = (days_from_anchor / 630) × 360°
      days  = (angle / 360) × 630
    """
    
    GANN_CYCLE_DAYS = 630  # 1 vòng = 360°
    
    # Standard time cycle angles
    CRITICAL_ANGLES = [45, 90, 135, 180, 225, 270, 315, 360]
    
    # Angle → days mapping (630-day cycle)
    ANGLE_TO_DAYS = {
        45:  79,    # 45/360 × 630 = 78.75
        90:  158,   # 90/360 × 630 = 157.5
        135: 236,   # 135/360 × 630 = 236.25
        180: 315,   # 180/360 × 630 = 315
        225: 394,   # 225/360 × 630 = 393.75
        270: 473,   # 270/360 × 630 = 472.5
        315: 551,   # 315/360 × 630 = 551.25
        360: 630,   # 360/360 × 630 = 630
    }
    
    # Important solar degrees
    SOLAR_ANGLES = {
        0: "March 21 (Equinox)",
        90: "June 21 (Solstice)",
        180: "September 23 (Equinox)",
        270: "December 22 (Solstice)"
    }

    @staticmethod
    def calculate_dates_from_anchor(anchor_date_str: str) -> list:
        """
        Calculate forward reversal dates based on 630-day Gann cycle.
        
        :param anchor_date_str: YYYY-MM-DD
        :return: List of potential reversal dates with angles.
        """
        anchor_date = datetime.strptime(anchor_date_str, "%Y-%m-%d")
        reversal_dates = []
        
        for angle in GannDateEngine.CRITICAL_ANGLES:
            days = GannDateEngine.ANGLE_TO_DAYS[angle]
            forward_date = anchor_date + timedelta(days=days)
            reversal_dates.append({
                "angle": angle,
                "days_added": days,
                "target_date": forward_date.strftime("%Y-%m-%d")
            })
            
        return reversal_dates

    @staticmethod
    def calculate_angle_from_anchor(anchor_date_str: str, target_date_str: str) -> float:
        """
        Calculate the Gann angle of a target date from an anchor.
        angle = (days / 630) × 360°
        
        :param anchor_date_str: YYYY-MM-DD
        :param target_date_str: YYYY-MM-DD
        :return: Angle in degrees (0-360)
        """
        anchor_date = datetime.strptime(anchor_date_str, "%Y-%m-%d")
        target_date = datetime.strptime(target_date_str, "%Y-%m-%d")
        days = (target_date - anchor_date).days
        return (days / GannDateEngine.GANN_CYCLE_DAYS) * 360

    @staticmethod
    def get_current_angle(anchor_date_str: str) -> dict:
        """
        Get current date's Gann angle from anchor.
        
        :param anchor_date_str: YYYY-MM-DD
        :return: Dict with days, angle, nearest critical angle.
        """
        from datetime import date
        anchor_date = datetime.strptime(anchor_date_str, "%Y-%m-%d").date()
        today = date.today()
        days = (today - anchor_date).days
        angle = (days / GannDateEngine.GANN_CYCLE_DAYS) * 360
        
        # Find nearest critical angle
        nearest = min(GannDateEngine.CRITICAL_ANGLES, key=lambda a: abs(angle - a))
        orb = abs(angle - nearest)
        
        return {
            "days_from_anchor": days,
            "current_angle": round(angle, 2),
            "nearest_critical_angle": nearest,
            "orb_to_nearest": round(orb, 2)
        }

    @staticmethod
    def find_nearest_future_date(future_dates: list) -> dict:
        """
        Find the nearest upcoming Gann date for emphasis in reports.
        
        :param future_dates: List from calculate_dates_from_anchor
        :return: Dict of nearest future date or None
        """
        from datetime import date
        if not future_dates:
            return None
        today = date.today()
        for d in future_dates:
            d_date = datetime.strptime(d["target_date"], "%Y-%m-%d").date()
            if d_date >= today:
                d["days_remaining"] = (d_date - today).days
                return d
        return None

    @staticmethod
    def date_to_gann_number(target_date_str: str, anchor_date_str: str) -> int:
        """
        Convert a date to a number on the Square of 9 by counting days 
        from a structural anchor (base = 1).
        """
        target_date = datetime.strptime(target_date_str, "%Y-%m-%d")
        anchor_date = datetime.strptime(anchor_date_str, "%Y-%m-%d")
        
        delta = target_date - anchor_date
        return max(1, delta.days)

if __name__ == "__main__":
    # Test Gann Date logic
    # Suppose a major gold bottom was on Feb 14, 2026
    anchor = "2026-02-14"
    print(f"\n--- GANN TIME REVERSALS ---")
    print(f"Anchor Date (Major Low/High): {anchor}")
    
    dates = GannDateEngine.calculate_dates_from_anchor(anchor)
    for d in dates:
        print(f"Angle {d['angle']:>3}° (+{d['days_added']:>3} days) -> Reversal Date: {d['target_date']}")
