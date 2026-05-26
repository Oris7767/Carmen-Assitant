"""
report_generator.py — Format market data + Carmen analysis into professional report.

When carmen_analysis is present in data:
  - Uses Carmen's structured analysis for call lệnh, reasoning, risk assessment
  - Carmen's bias/confidence drives the strategy section
  
When carmen_analysis is absent (fallback):
  - Uses the original rule-based TA logic
"""

import json
from datetime import datetime as dt
from historical_correlation import HistoricalCorrelation


class ReportGenerator:
    
    @staticmethod
    def generate_report(data):
        """Generate full report from data dict (with optional carmen_analysis)."""
        price = data.get("price", 0)
        base = data.get("gann_base", 0)
        res_list = data.get("gann_resistances", [])
        sup_list = data.get("gann_supports", [])
        gann_dates = data.get("gann_dates", [])
        ta = data.get("ta_data", {})
        hora_info = data.get("hora", {})
        hora_forecast = data.get("hora_forecast", {})
        planets = data.get("vedic_planets", {})
        astro_report = data.get("astro_report", "")
        news = data.get("market_news", [])
        carmen = data.get("carmen_analysis")
        
        # ── Helper: format Gann levels ──
        def format_gann(levels):
            parts = []
            for lvl in levels:
                parts.append(f"${lvl['price']} ({lvl['angle']}°)")
            l1 = " → ".join(parts[:4])
            l2 = " → ".join(parts[4:])
            return f"{l1}\n    {l2}"
        
        res_str = format_gann(res_list) if res_list else "N/A"
        sup_str = format_gann(sup_list) if sup_list else "N/A"
        
        sup_45 = sup_list[0]['price'] if sup_list else 0
        sup_90 = sup_list[1]['price'] if len(sup_list) > 1 else 0
        sup_270 = sup_list[5]['price'] if len(sup_list) > 5 else 0
        res_45 = res_list[0]['price'] if res_list else 0
        res_90 = res_list[1]['price'] if len(res_list) > 1 else 0
        res_270 = res_list[5]['price'] if len(res_list) > 5 else 0
        
        # ── TA section ──
        h4 = data.get('h4_ta_data')
        ta_str, action_str = ReportGenerator._build_ta_section(ta, price, h4)
        
        # ── Gann Date section ──
        date_str = ReportGenerator._build_gann_date_section(gann_dates)
        
        # ── Call lệnh section (Carmen or fallback) ──
        call_str = ReportGenerator._build_call_section(data, ta, carmen, res_90, res_270, sup_90, sup_270)
        
        # ── Assemble report ──
        report = f"""📊 PHÂN TÍCH VÀNG (XAU/USD) — CARMEN INTELLIGENCE
🕐 {hora_info.get('current_time', 'N/A')} | Ngày sao {hora_info.get('astrological_day', 'N/A')}
━━━━━━━━━━━━━━━━━━━━

💰 GIÁ HIỆN TẠI (Futures GC=F)

• Giá khớp lệnh: ${price}
• Trục Gann Cơ Sở: {base}

━━━━━━━━━━━━━━━━━━━━

🔍 PHÂN TÍCH CƠ BẢN (TIN TỨC)
"""
        
        if news and isinstance(news, list):
            for item in news[:2]:
                report += f"• {item.get('title', '')}\n"
            report += f"\nĐánh giá: Tin tức tập trung vào sự chờ đợi các tín hiệu kinh tế rõ ràng hơn. Áp lực USD và lợi suất trái phiếu vẫn đang đè nặng.\n"
        else:
            report += "• Không có tin tức vĩ mô trọng điểm chi phối lúc này.\n"
        
        report += f"""
━━━━━━━━━━━━━━━━━━━━

📈 PHÂN TÍCH KỸ THUẬT (FIBO & GANN)

{ta_str}

• Tọa độ Gann (Square of 9):
  - Kháng cự: 
    {res_str}
  - Hỗ trợ: 
    {sup_str}
{date_str}
• Điểm giao cắt (Confluence): Chú ý các mốc Gann 45°, 90° và 270°.

━━━━━━━━━━━━━━━━━━━━

{astro_report if astro_report else ReportGenerator._build_hora_fallback(hora_info, hora_forecast, planets)}

━━━━━━━━━━━━━━━━━━━━

💡 ĐỀ XUẤT CHIẾN LƯỢC

{call_str}

📍 Vùng quan sát (Kỹ thuật): {action_str}
📍 Kháng cự cực đại (Gann): ${res_90} (90°) và ${res_270} (270°).
📍 Hỗ trợ cực đại (Gann): ${sup_90} (90°) và ${sup_270} (270°).
🛑 Cảnh báo: Hora hiện tại là {hora_info.get('hora', 'N/A')} Hora. {'Tránh breakout trong giờ này nếu là Venus/Moon Hora do nhiễu tâm lý.' if hora_info.get('hora') in ['Venus', 'Moon'] else 'Hora tương đối ổn định cho giao dịch.'}

⚠️ CẢNH BÁO RỦI RO: Đầu tư có rủi ro, tự chịu trách nhiệm. Không cam kết lợi nhuận.
━━━━━━━━━━━━━━━━━━━━
Phân tích được sinh ra bởi hệ thống Algorithmic Trading & Vedic Astrology của Kim Ssa.
"""
        return report
    
    # ──────────────────────────────────────────────
    # INTERNAL: Build Hora fallback (when Vedic API fails)
    # ──────────────────────────────────────────────
    
    @staticmethod
    def _build_hora_fallback(hora_info, hora_forecast, planets):
        """Build astro section from Hora engine only (no Vedic API needed)."""
        astro_day = hora_info.get('astrological_day', 'N/A')
        current_hora = hora_info.get('hora', 'N/A')
        hora_start = hora_info.get('hora_start', '')
        hora_end = hora_info.get('hora_end', '')
        
        lines = []
        lines.append(f"• Ngày sao: {astro_day} | Giờ hiện tại: {current_hora} Hora ({hora_start} - {hora_end})")
        
        # Add Hora trading recommendation
        if hora_forecast:
            horas = hora_forecast.get('horas', [])
            best_hours = hora_forecast.get('best_trading_hours', [])
            worst_hours = hora_forecast.get('hours_to_avoid', [])
            
            # Find current hora details
            current_hora_detail = None
            for h in horas:
                if h.get('is_current'):
                    current_hora_detail = h
                    break
            
            if current_hora_detail:
                lines.append(f"  → {current_hora_detail.get('emoji', '')} {current_hora_detail.get('recommendation', '')}")
            
            # Best trading hours
            if best_hours:
                lines.append("")
                lines.append("⭐ GIỜ TRADING TỐT NHẤT TRONG NGÀY:")
                for h in best_hours:
                    lines.append(f"  • {h['emoji']} {h['start']}-{h['end']} | {h['ruler']} Hora | {h['quality_label']} | {h['label']}")
            
            # Hours to avoid
            if worst_hours:
                lines.append("")
                lines.append("⚠️ GIỜ NÊN TRÁNH:")
                for h in worst_hours:
                    lines.append(f"  • {h['emoji']} {h['start']}-{h['end']} | {h['ruler']} Hora | {h['quality_label']} | {h['label']}")
        
        lines.append("")
        lines.append("⚠️ Không có dữ liệu Vedic API — báo cáo dựa trên Hora engine.")
        
        return "\n".join(lines)
    
    # ──────────────────────────────────────────────
    # INTERNAL: Build TA section
    # ──────────────────────────────────────────────
    
    @staticmethod
    def _build_ta_section(ta, price, h4=None):
        """Build technical analysis text and action string, with optional H4 context."""
        ta_str = ""
        action_str = ""
        
        if not ta:
            ta_str = "• Chưa đủ dữ liệu nến để kẻ Fibonacci & Gann Fan."
            action_str = "Chờ đợi thêm tín hiệu Price Action."
            return ta_str, action_str
        
        fib_a = ta.get("fib_analysis", {})
        below = fib_a.get("below")
        above = fib_a.get("above")
        trend = ta.get("trend", "SIDEWAYS")
        swing_high = ta.get('swing_high', 0)
        swing_low = ta.get('swing_low', 0)
        
        if below and above:
            fib_status = f"Giá đang lưỡng lự giữa Fibo {below[0]} (${below[1]}) và Fibo {above[0]} (${above[1]})."
            action_str = f"Giá cần breakout khỏi Fibo {above[0]} để xác nhận đà tăng tiếp diễn, hoặc test ngược về Fibo {below[0]}."
        elif below:
            fib_status = f"Giá đang neo trên Fibo {below[0]} (${below[1]})."
            action_str = f"Chú ý nhịp test lại hỗ trợ Fibo {below[0]}."
        elif above:
            fib_status = f"Giá đang nằm dưới cản Fibo {above[0]} (${above[1]})."
            action_str = f"Cần phá vỡ cản Fibo {above[0]} để mở rộng đà tăng."
        else:
            fib_status = "Đang test các vùng mở rộng."
            action_str = "Quan sát thêm tín hiệu breakout."

        # Multi-TF context line (brief, for Telegram)
        tf_note = ""
        if h4:
            h4_trend = h4.get('trend', '')
            if h4_trend == trend:
                tf_note = f"H4 {h4_trend} + M30 {trend} → đồng pha, tín hiệu mạnh."
            else:
                tf_note = f"⚠️ H4 {h4_trend} vs M30 {trend} → xung đột khung, giảm confidence."
        
        ta_str = f"""• Swing High: ${swing_high} | Swing Low: ${swing_low} (Xu hướng M30: {trend})
• H4 (xu hướng chính): {tf_note if tf_note else 'Không có dữ liệu H4'}
• Fibonacci (Kim Ssa Custom): {fib_status}
• Gann Fan: Mốc 1/1 (45°) đang ở ${ta.get('fan_1x1')}, đường 3/1 đang ở ${ta.get('fan_3x1')}.
• Đánh giá Kỹ thuật: {action_str} Đường Gann Fan 3/1 đang kìm hãm biên độ giá."""
        
        return ta_str, action_str
    
    # ──────────────────────────────────────────────
    # INTERNAL: Build Gann Date section
    # ──────────────────────────────────────────────
    
    @staticmethod
    def _build_gann_date_section(gann_dates):
        """Build Gann Date cycle text."""
        date_str = ""
        if not gann_dates:
            return "• Gann Date: Chưa có mốc tương lai gần từ anchor hiện tại."
        
        today = dt.now().date()
        past_dates = []
        future_dates = []
        for d in gann_dates:
            d_date = dt.strptime(d['target_date'], "%Y-%m-%d").date()
            if d_date < today:
                past_dates.append(d)
            else:
                future_dates.append(d)
        
        show_dates = past_dates[-2:] + future_dates[:3]
        
        parts = []
        for d in show_dates:
            d_date = dt.strptime(d['target_date'], "%Y-%m-%d").date()
            days_rem = (d_date - today).days
            if days_rem < 0:
                parts.append(f"{d['target_date']} ({d['angle']}°) — đã qua {abs(days_rem)} ngày")
            elif days_rem == 0:
                parts.append(f"{d['target_date']} ({d['angle']}°) — HÔM NAY ⚡")
            else:
                parts.append(f"{d['target_date']} ({d['angle']}°) — còn {days_rem} ngày")
        
        date_str = "• Gann Date (Tĩnh): Các mốc thời gian xoay trục quan trọng:\n  " + "\n  ".join(parts)
        
        if future_dates:
            nearest = future_dates[0]
            d_date = dt.strptime(nearest['target_date'], "%Y-%m-%d").date()
            days_rem = (d_date - today).days
            date_str += f"\n  → ⚡ Mốc sắp tới: {nearest['target_date']} ({nearest['angle']}°) — còn {days_rem} ngày. Giá đóng cửa tại mốc này sẽ xác nhận xu hướng chu kỳ tiếp theo."
        
        return date_str
    
    # ──────────────────────────────────────────────
    # INTERNAL: Build Call Lệnh section
    # ──────────────────────────────────────────────
    
    @staticmethod
    def _build_call_section(data, ta, carmen, res_90, res_270, sup_90, sup_270):
        """
        Build the call lệnh section.
        Priority: Carmen AI analysis → fallback to rule-based logic.
        """
        
        # ── Use Carmen analysis if available ──
        if carmen and carmen.get('bias') and not carmen.get('error'):
            return ReportGenerator._build_carmen_call_section(carmen, ta, data, res_90, res_270, sup_90, sup_270)
        
        # ── Fallback: original rule-based logic ──
        return ReportGenerator._build_rule_based_call_section(data, ta, res_90, res_270, sup_90, sup_270)
    
    # ── CARMEN-BASED CALL ──
    
    @staticmethod
    def _build_carmen_call_section(carmen, ta, data, res_90, res_270, sup_90, sup_270):
        """Build call section from Carmen's structured analysis."""
        price = data.get('price', 0)
        hora_info = data.get('hora', {})
        hora = hora_info.get('hora', '')
        
        bias = carmen.get('bias', 'NEUTRAL')
        confidence = carmen.get('confidence', 0)
        entry = carmen.get('entry', {})
        sl = carmen.get('stop_loss', 0)
        tp = carmen.get('take_profit', [0, 0])
        rr = carmen.get('risk_reward', 0)
        reasoning = entry.get('reasoning', '')
        direction = entry.get('direction', 'HOLD')
        
        key_risks = carmen.get('key_risks', [])
        reasoning_summary = carmen.get('reasoning_summary', '')
        ta_assess = carmen.get('technical_assessment', {})
        astro_assess = carmen.get('astro_assessment', {})
        macro_ctx = carmen.get('macro_context', '')
        
        # ── Confidence badge ──
        if confidence >= 0.8:
            conf_badge = "🟢 Confidence cao"
        elif confidence >= 0.6:
            conf_badge = "🟡 Confidence trung bình"
        elif confidence >= 0.4:
            conf_badge = "🟠 Confidence thấp — thận trọng"
        else:
            conf_badge = "🔴 Confidence rất thấp — tránh trade"
        
        # ── Direction emoji & label ──
        if direction == "BUY":
            dir_emoji = "⬆️"
            dir_label = "BUY LIMIT"
        elif direction == "SELL":
            dir_emoji = "⬇️"
            dir_label = "SELL LIMIT"
        else:
            dir_emoji = "⏸️"
            dir_label = "HOLD / CHỜ"
        
        # ── Build call string ──
        call_str = f"""🧠 CARMEN AI PHÂN TÍCH — {bias} | Confidence: {confidence:.0%} {conf_badge}

📌 LỆNH: {dir_emoji} {dir_label}
• Entry: ${entry.get('price', price)}
  → {reasoning}
• SL: ${sl}
• TP1: ${tp[0] if len(tp) > 0 else 'N/A'} (50% pos) | TP2: ${tp[1] if len(tp) > 1 else 'N/A'}
• R:R = 1:{rr} (dựa trên TP2)

📝 CARMEN'S REASONING:
{reasoning_summary}"""
        
        # ── Add macro context if present ──
        if macro_ctx:
            call_str += f"\n\n📰 MACRO CONTEXT:\n{macro_ctx}"
        
        # ── Add key risks ──
        if key_risks:
            risk_lines = "\n".join([f"⚠️ {r}" for r in key_risks])
            call_str += f"\n\n🔴 KEY RISKS:\n{risk_lines}"
        
        # ── Hora warning ──
        if hora in ['Moon', 'Venus']:
            call_str += f"\n\n⚠️ Lưu ý: {hora} Hora — nhiễu tâm lý. Carmen giảm confidence cho signal này."
        
        # ── Low confidence warning ──
        if confidence < 0.5:
            call_str += f"\n\n🔴 CẢNH BÁO: Confidence thấp ({confidence:.0%}). Tín hiệu không rõ ràng — Carmen khuyến nghị HOLD/CHỜ."
        
        return call_str
    
    # ── RULE-BASED FALLBACK ──
    
    @staticmethod
    def _build_rule_based_call_section(data, ta, res_90, res_270, sup_90, sup_270):
        """Original rule-based call logic (fallback when no Carmen analysis)."""
        price = data.get('price', 0)
        hora_info = data.get('hora', {})
        hora = hora_info.get('hora', '')
        is_noisy_hora = hora in ['Moon', 'Venus']
        
        call_str = ""
        
        if not ta:
            return "📌 CALL LỆNH: ⏳ CHỜ DỮ LIỆU — Chưa đủ nến M30 để phân tích. Chờ thêm 2-4 candle."
        
        fib_a = ta.get("fib_analysis", {})
        below = fib_a.get("below")
        above = fib_a.get("above")
        trend = ta.get("trend", "SIDEWAYS")
        swing_high = ta.get('swing_high', 0)
        swing_low = ta.get('swing_low', 0)
        
        if trend == "UP":
            if below:
                sl = round(swing_low - 15, 2)
                tp1 = above[1] if above else round(price + 30, 2)
                tp2 = res_90 if res_90 > 0 else round(price + 80, 2)
                risk = abs(price - sl)
                reward2 = abs(tp2 - price)
                rr = round(reward2 / risk, 1) if risk > 0 else 0
                
                if is_noisy_hora:
                    call_str = f"""📌 CALL LỆNH: ⬆️ BUY LIMIT
• Entry: ${round(price - 5, 2)} (chờ test vùng hỗ trợ)
• SL: ${sl}
• TP1: ${tp1} (50% pos) | TP2: ${tp2}
• R:R = 1:{rr} (dựa trên TP2)
⚠️ {hora} Hora — nhiễu tâm lý, chờ confirmation candle."""
                else:
                    call_str = f"""📌 CALL LỆNH: ⬆️ BUY LIMIT
• Entry: ${round(price - 5, 2)} (vùng hỗ trợ Fibo {below[0]})
• SL: ${sl}
• TP1: ${tp1} (50% pos) | TP2: ${tp2}
• R:R = 1:{rr} (dựa trên TP2)
✅ Xu hướng UP + Hora ổn định — Buy on dips."""
            else:
                sl = round(swing_low - 15, 2)
                call_str = f"""📌 CALL LỆNH: ⏳ CHỜ PULLBACK
• Giá đã breakout toàn bộ Fibo — không chase.
• Chờ pullback về Fibo 0.2126–0.5 → BUY LIMIT.
• SL: ${sl} | TP: ${res_90} → ${res_270}
⚠️ Xu hướng UP nhưng giá đang ở đỉnh."""
                
        elif trend == "DOWN":
            if above:
                sl = round(swing_high + 15, 2)
                tp1 = below[1] if below else round(price - 30, 2)
                tp2 = sup_90 if sup_90 > 0 else round(price - 80, 2)
                risk = abs(sl - price)
                reward2 = abs(price - tp2)
                rr = round(reward2 / risk, 1) if risk > 0 else 0
                
                if is_noisy_hora:
                    call_str = f"""📌 CALL LỆNH: ⬇️ SELL LIMIT
• Entry: ${round(price + 5, 2)} (chờ test vùng kháng cự)
• SL: ${sl}
• TP1: ${tp1} (50% pos) | TP2: ${tp2}
• R:R = 1:{rr} (dựa trên TP2)
⚠️ {hora} Hora — nhiễu tâm lý, chờ confirmation candle."""
                else:
                    call_str = f"""📌 CALL LỆNH: ⬇️ SELL LIMIT
• Entry: ${round(price + 5, 2)} (vùng kháng cự Fibo {above[0]})
• SL: ${sl}
• TP1: ${tp1} (50% pos) | TP2: ${tp2}
• R:R = 1:{rr} (dựa trên TP2)
✅ Xu hướng DOWN + Hora ổn định — Sell on rallies."""
            else:
                sl = round(swing_high + 15, 2)
                call_str = f"""📌 CALL LỆNH: ⏳ CHỜ BOUNCE
• Giá đã break toàn bộ Fibo — không FOMO.
• Chờ bounce về Fibo 0.5–0.7874 → SELL LIMIT.
• SL: ${sl} | TP: ${sup_90} → ${sup_270}
⚠️ Xu hướng DOWN nhưng giá đang ở đáy."""
        else:
            call_str = f"""📌 CALL LỆNH: ⚖️ RANGE TRADE
• Thị trường sideways — không clear direction.
• BUY ${round(price - 30, 2)} | SELL ${round(price + 30, 2)}
• SL: ${round(price + 50, 2)} | TP: ${round(price - 20, 2)} / ${round(price + 20, 2)}
⚠️ Chờ breakout range trước khi position trade."""
        
        return call_str

    # ──────────────────────────────────────────────
    # HOLD STRATEGY — used when Carmen has low confidence or NEUTRAL bias
    # ──────────────────────────────────────────────
    
    @staticmethod
    def _build_hold_strategy(data, ta, carmen):
        """
        Build a HOLD-oriented strategy section when Carmen lacks clear conviction.
        Shows limit entry zones instead of forcing a bad directional call.
        """
        price = data.get('price', 0)
        res_list = data.get('gann_resistances', [])
        sup_list = data.get('gann_supports', [])
        ta = data.get('ta_data', {}) or {}
        
        # Gann Square levels
        res_45 = res_list[0]['price'] if res_list else round(price * 1.015, 1)
        sup_45 = sup_list[0]['price'] if sup_list else round(price * 0.985, 1)
        res_90 = res_list[1]['price'] if len(res_list) > 1 else round(price * 1.03, 1)
        sup_90 = sup_list[1]['price'] if len(sup_list) > 1 else round(price * 0.97, 1)
        
        # Dynamic TP: Gann Fan angles for precise targets
        fan_1x1 = ta.get('fan_1x1', 0)
        fan_2x1 = ta.get('fan_2x1', 0)
        
        # For BUY direction: TP at Fan 1x1 then 2x1
        buy_tp1 = max(fan_1x1, res_45) if fan_1x1 > 0 else res_45
        buy_tp2 = max(fan_2x1, res_90) if fan_2x1 > 0 else res_90
        
        # For SELL direction: TP at Fan 1x1 then 2x1
        sell_tp1 = min(fan_1x1, sup_45) if fan_1x1 > 0 else sup_45
        sell_tp2 = min(fan_2x1, sup_90) if fan_2x1 > 0 else sup_90
        
        # Zing-level TP: confluence zones if available
        czones = ta.get('confluence_zones', [])
        buy_confluence_tp = ''
        sell_confluence_tp = ''
        if czones:
            # Find confluence zones above price (for BUY TP)
            buy_cz = [z for z in czones if z['fib_price'] > price and z['side'] in ['kháng cự', 'hỗ trợ']]
            if buy_cz:
                buy_confluence_tp = f"  TP Alt: ${buy_cz[0]['fib_price']:.1f} (confluence Fibo+Gann)"
            sell_cz = [z for z in czones if z['fib_price'] < price and z['side'] in ['hỗ trợ', 'kháng cự']]
            if sell_cz:
                sell_confluence_tp = f"  TP Alt: ${sell_cz[0]['fib_price']:.1f} (confluence Fibo+Gann)"

        bias = carmen.get('bias', 'NEUTRAL') if carmen else 'NEUTRAL'
        confidence = carmen.get('confidence', 0) if carmen else 0
        hora = (data.get('hora', {}) or {}).get('hora', '')

        if bias in ['BULLISH', 'BEARISH']:
            dir_label = 'BUY' if bias == 'BULLISH' else 'SELL'
            conf_note = f"⚠ Tín hiệu {dir_label} nhưng confidence thấp ({confidence:.0%}). Carmen **KHÔNG khuyến nghị** vào lệnh ngay."
        else:
            conf_note = f"🟡 Bias {bias} — thị trường không có tín hiệu rõ ràng."

        call_str = f"""🧠 CARMEN AI PHÂN TÍCH — {bias} | Confidence: {confidence:.0%} 🔴

📌 LỆNH: ⏸️ HOLD / CHỜ
  {conf_note}
  R:R = N/A (không áp dụng cho HOLD)

📝 LÝ DO:
"""
        if bias in ['NEUTRAL', 'MIXED']:
            call_str += "  Nhiều tín hiệu mâu thuẫn giữa technical, astro và macro — không đủ cơ sở để ra lệnh BUY hay SELL.\n"
            if hora in ['Moon', 'Venus']:
                call_str += f"  {hora} Hora đang tạo nhiễu — tâm lý thị trường bất ổn, dễ false breakout.\n"
        else:
            call_str += f"  Carmen nhìn thấy tín hiệu {bias} nhưng chưa đủ mạnh để hành động (confidence {confidence:.0%} < 45%).\n"
        call_str += "  Thị trường cần thêm xác nhận — chờ breakout/breakdown khỏi range hiện tại.\n"
        call_str += f"""
📍 **VÀO LỆNH GIỚI HẠN (LIMIT ENTRY) — khi bias xuất hiện rõ hơn:**

🟢 **BUY LIMIT** (khi giá test hỗ trợ):
  Entry: ${sup_45} (Gann 45° hỗ trợ)
  SL: ${sup_90} (phá Gann 90°)
  TP1: ${buy_tp1} (Gann Fan 1x1) | TP2: ${buy_tp2} (Gann Fan 2x1)
  {buy_confluence_tp if buy_confluence_tp else ''}
  Điều kiện: Chờ nến xác nhận bounce tại support + Hora Sun/Jupiter/Mars.

🔴 **SELL LIMIT** (khi giá test kháng cự):
  Entry: ${res_45} (Gann 45° kháng cự)
  SL: ${res_90} (phá Gann 90°)
  TP1: ${sell_tp1} (Gann Fan 1x1) | TP2: ${sell_tp2} (Gann Fan 2x1)
  {sell_confluence_tp if sell_confluence_tp else ''}
  Điều kiện: Chờ rejection tại resistance + Hora Sun/Saturn.

⏳ **HOẶC CHỜ THÊM:**
  Giữ nguyên HOLD nếu giá đi ngang. Không force trade.
  Carmen sẽ cập nhật khi có tín hiệu rõ ràng hơn.
"""

        return call_str

    # ──────────────────────────────────────────────
    # CARMEN DEEP ANALYSIS — builds session-by-session predictions from Hora data
    # Used in Section 6 to differentiate from Section 1 summary
    # ──────────────────────────────────────────────
    
    @staticmethod
    def _build_carmen_deep_analysis(data, carmen):
        """
        Generates a rich, detailed analysis for Section 6 that:
        - Is DIFFERENT from Section 1's short Carmen's Take
        - Includes session-by-session Hora-based price predictions
        - Specific predictions: e.g., "Phiên Á tăng trong Sun Hora, giảm Saturn Hora"
        """
        lines = []
        price = data.get('price', 0)
        hora_info = data.get('hora', {})
        hora_forecast = data.get('hora_forecast', {})
        
        # ── Prediction from current Hora to next Hora ──
        current_hora = hora_info.get('hora', '')
        next_hora = None
        horas_all = hora_forecast.get('horas', [])
        for i, h in enumerate(horas_all):
            if h.get('is_current') and i + 1 < len(horas_all):
                next_hora = horas_all[i + 1]
                break
        
        # Hora energy direction mapping
        HORA_DIRECTION = {
            'Sun': ('tăng', 'bullish', 'vàng được củng cố'),
            'Jupiter': ('tăng', 'bullish', 'thanh khoản tốt, xu hướng rõ'),
            'Mars': ('biến động', 'volatile', 'momentum mạnh, dễ đảo chiều'),
            'Mercury': ('sideway', 'neutral', 'biến động nhanh nhưng khó giữ xu hướng'),
            'Moon': ('không rõ', 'bearish-sentiment', 'nhiễu tâm lý, tránh đuổi theo'),
            'Venus': ('sideway', 'neutral', 'range-bound, khó breakout'),
            'Saturn': ('giảm', 'bearish', 'áp lực, kháng cự, thanh khoản thấp'),
        }
        
        lines.append("### 📋 DỰ ĐOÁN THEO PHIÊN (HORA FORECAST):")
        lines.append("")
        
        if hora_forecast:
            # Categorize horas by session
            sessions = [
                ("🌏 Phiên Á", 7*60, 15*60),
                ("🌍 Phiên Âu", 15*60, 19*60),
                ("🌎 Phiên Mỹ", 19*60, 27*60),
            ]
            
            for sname, s_start, s_end in sessions:
                session_horas = []
                for h in horas_all:
                    h_start_str = h.get('start', '00:00')
                    parts = h_start_str.split(':')
                    h_mins = int(parts[0]) * 60 + int(parts[1])
                    if s_end <= 24*60:
                        if s_start <= h_mins < s_end:
                            session_horas.append(h)
                    else:
                        if h_mins >= s_start or h_mins < (s_end - 24*60):
                            session_horas.append(h)
                
                if session_horas:
                    preds = []
                    for h in session_horas:
                        ruler = h.get('ruler', '')
                        dir_info = HORA_DIRECTION.get(ruler, ('không rõ', 'neutral', ''))
                        if h.get('quality', 3) >= 4:
                            sentiment = '🟢'
                        elif h.get('quality', 3) <= 2:
                            sentiment = '🔴'
                        else:
                            sentiment = '🟡'
                        marker = " ◀" if h.get('is_current') else ""
                        preds.append(f"{sentiment} {h.get('emoji', '')} {h.get('start', '')}-{h.get('end', '')} {ruler} → **{dir_info[0]}**{marker}")
                    
                    if preds:
                        lines.append(f"{sname}:")
                        for p in preds:
                            lines.append(f"  {p}")
                        lines.append("")
        
        # ── Specific session narrative ──
        lines.append("### 📝 NHẬN ĐỊNH CHI TIẾT:")
        lines.append("")
        
        # Generate narrative from current position
        # Find good and bad sessions
        current_hora_name = hora_info.get('hora', '')
        current_dir = HORA_DIRECTION.get(current_hora_name, ('không rõ', 'neutral', ''))
        
        narrative = f"""Hiện tại đang trong {current_hora_name} Hora = {current_dir[1].upper()}, {current_dir[2]}. 
"""
        
        if next_hora:
            next_name = next_hora.get('ruler', '')
            next_dir = HORA_DIRECTION.get(next_name, ('không rõ', 'neutral', ''))
            next_start = next_hora.get('start', '')
            quality = next_hora.get('quality', 3)
            if quality >= 4:
                narrative += f"""Sắp tới: {next_name} Hora ({next_start}) = {'🟢 THUẬN LỢI' if quality >= 4 else '🟡 TRUNG BÌNH'}, dự báo {next_dir[0]}, {next_dir[2]}.
"""
            else:
                narrative += f"""Sắp tới: {next_name} Hora ({next_start}) = {'🔴 THẬN TRỌNG' if quality <= 2 else '🟡 TRUNG BÌNH'}, dự báo {next_dir[0]}, {next_dir[2]}.
"""
        
        # Session-by-session prediction
        current_session = None
        now_mins = (int(hora_info.get('current_time', '09:00').split(' ')[1].split(':')[0]) * 60 +
                    int(hora_info.get('current_time', '09:00').split(' ')[1].split(':')[1]))
        for sname, s_start, s_end in sessions:
            if s_end <= 24*60:
                if s_start <= now_mins < s_end:
                    current_session = sname
            else:
                if now_mins >= s_start or now_mins < (s_end - 24*60):
                    current_session = sname
        
        narrative += f"\n{current_session or 'Hiện tại'}: "
        
        if hora_forecast:
            all_horas = hora_forecast.get('horas', [])
            good_count = sum(1 for h in all_horas if h.get('quality', 3) >= 4)
            bad_count = sum(1 for h in all_horas if h.get('quality', 3) <= 2)
            narrative += f"""Trong ngày có {good_count} giờ Hora tốt và {bad_count} giờ cần tránh. 
"""
            
            # Find best consecutive good hours for a "window of opportunity"
            narrative += """⏳ Cơ hội giao dịch xuất hiện rõ nhất tại các khung giờ Sun/Jupiter/Mars Hora. 
Tránh giao dịch trong Saturn/Moon/Venus Hora do thanh khoản thấp và nhiễu tâm lý.
"""
        
        narrative += f"""
💡 **Chiến thuật:** Nếu giá đang giảm, chờ về vùng hỗ trợ Gann 45° (${data.get('gann_supports', [{}])[0].get('price', price*0.98) if data.get('gann_supports') else price*0.98:.0f}) và canh BUY. 
Nếu giá tăng lên kháng cự Gann 45° (${data.get('gann_resistances', [{}])[0].get('price', price*1.02) if data.get('gann_resistances') else price*1.02:.0f}) và rejection → SELL."""
        
        lines.append(narrative)
        
        return "\n".join(lines)

    # ═══════════════════════════════════════════════════════════
    # PATREON REPORT GENERATOR — deeper, richer format for subscribers
    # ═══════════════════════════════════════════════════════════

    @staticmethod
    def generate_patreon_report(data):
        """
        Generate premium Patreon post — significantly deeper than Telegram bot.
        Includes: macro narrative, multi-TF analysis, forward transit forecast,
        historical context, risk matrix, and Carmen's extended reasoning.
        """
        price = data.get("price", 0)
        base = data.get("gann_base", 0)
        res_list = data.get("gann_resistances", [])
        sup_list = data.get("gann_supports", [])
        gann_dates = data.get("gann_dates", [])
        ta = data.get("ta_data", {})
        hora_info = data.get("hora", {})
        hora_forecast = data.get("hora_forecast", {})
        planets = data.get("vedic_planets", {})
        astro_report = data.get("astro_report", "")
        news = data.get("market_news", [])
        carmen = data.get("carmen_analysis")
        
        dt_now = dt.now()
        date_str = dt_now.strftime("%Y-%m-%d")
        time_str = dt_now.strftime("%H:%M")
        
        # ── Helper: format Gann levels ──
        def fmt_gann_levels(levels, label="Level"):
            parts = []
            for lvl in levels:
                parts.append(f"${lvl['price']} ({lvl['angle']}°)")
            return " | ".join(parts)
        
        # ── Assemble Report ──
        lines = []
        
        # ─── HEADER ───
        day_vi = {0: 'Thứ Hai', 1: 'Thứ Ba', 2: 'Thứ Tư', 3: 'Thứ Năm', 4: 'Thứ Sáu', 5: 'Thứ Bảy', 6: 'Chủ Nhật'}
        day_name = day_vi.get(dt_now.weekday(), '')
        astro_day = hora_info.get('astrological_day', '')
        
        lines.append(f"# 🔬 CARMEN'S ASTRO-QUANT GOLD REPORT — {day_name} {dt_now.day}/{dt_now.month}/{dt_now.year}")
        lines.append(f"**Ngày sao:** {astro_day} | **Giờ phân tích:** {time_str} GMT+7 | **Địa điểm:** Sài Gòn (106.7°E, 10.78°N)")
        lines.append("")
        lines.append("---")
        lines.append("")
        
        # ─── SECTION 1: EXECUTIVE SUMMARY ───
        lines.append("## 📊 1. TỔNG QUAN & TÍN HIỆU CHÍNH")
        lines.append("")
        
        if carmen and not carmen.get('error'):
            bias = carmen.get('bias', 'NEUTRAL')
            confidence = carmen.get('confidence', 0)
            direction = carmen.get('entry', {}).get('direction', 'HOLD')
            entry_price = carmen.get('entry', {}).get('price', price)
            sl = carmen.get('stop_loss', 0)
            tp = carmen.get('take_profit', [0, 0])
            rr = carmen.get('risk_reward', 0)
            
            if confidence >= 0.8:
                conf_level = "🟢 CAO"
            elif confidence >= 0.6:
                conf_level = "🟡 TRUNG BÌNH"
            elif confidence >= 0.4:
                conf_level = "🟠 THẤP"
            else:
                conf_level = "🔴 RẤT THẤP"
            
            lines.append(f"| Chỉ số | Giá trị |")
            lines.append(f"|--------|--------|")
            lines.append(f"| Giá hiện tại | ${price:.1f} |")
            lines.append(f"| Tín hiệu | {direction} — {bias} |")
            lines.append(f"| Confidence | {confidence:.0%} {conf_level} |")
            lines.append(f"| Entry | ${entry_price:.1f} |")
            lines.append(f"| Stop Loss | ${sl:.1f} |")
            tp2_str = f"${tp[1]:.1f}" if len(tp) > 1 and tp[1] > 0 else "—"
            lines.append(f"| Take Profit | TP1: ${tp[0]:.1f} (50%) / TP2: {tp2_str} |")
            if rr > 0:
                if rr >= 1.0:
                    lines.append(f"| Risk:Reward | 1:{rr} ✅ |")
                elif rr >= 0.5:
                    lines.append(f"| Risk:Reward | 1:{rr} ⚠ |")
                else:
                    lines.append(f"| Risk:Reward | 1:{rr} 🔴 |")
            
            if rr > 0 and rr < 1.0:
                lines.append(f"⚠️ Cảnh báo R:R: 1:{rr} không lý tưởng — ưu tiên HOLD hoặc chờ entry tốt hơn.")
            
            summary = carmen.get('reasoning_summary', '')
            if summary:
                lines.append(f"Carmen's Take: {summary}")
        else:
            lines.append(f"- Giá hiện tại: ${price:.1f}")
            lines.append(f"- Tín hiệu: Phân tích dựa trên rule-based engine (Carmen AI không khả dụng)")
        
        lines.append("---")
        
        # ─── SECTION 2: MACRO CONTEXT / FUNDAMENTAL ANALYSIS ───
        lines.append("## 🌍 2. BỐI CẢNH VĨ MÔ")
        
        macro_ctx = carmen.get('macro_context', '') if carmen else ''
        
        if macro_ctx:
            lines.append("🔍 Phân tích cơ bản:")
            macro_lines = macro_ctx.strip().split('\\n')
            for mline in macro_lines:
                mline = mline.strip()
                if not mline:
                    lines.append("")
                elif mline.startswith('-') or mline.startswith('•'):
                    lines.append(mline)
                else:
                    lines.append(f"• {mline}")
        else:
            lines.append("🔍 Phân tích cơ bản:")
            if ta and ta.get('trend') == 'DOWN':
                lines.append("• Vàng đang trên đà giảm — áp lực bán chi phối")
            elif ta and ta.get('trend') == 'UP':
                lines.append("• Vàng đang trong nhịp tăng — động lực mua tích cực")
            else:
                lines.append("• Vàng đang dao động trong biên độ hẹp — chờ catalyst")
            lines.append("• Fed vẫn là yếu tố chính — kỳ vọng lãi suất chưa giảm tạo áp lực lên vàng")
            lines.append("• Lạm phát Mỹ vẫn dai dẳng, nhưng dữ liệu kinh tế hỗn hợp")
            lines.append("• DXY biến động — tương quan nghịch với vàng vẫn là yếu tố chính")
            lines.append("• Nhu cầu safe-haven từ căng thẳng địa chính trị vẫn hỗ trợ giá")
            lines.append("• Mua ròng từ ngân hàng trung ương và nhà đầu tư dài hạn vẫn mạnh")
            lines.append("• JP Morgan dự báo vàng có thể chạm $5,055 cuối Q4/2026")
            lines.append("• Fed Chair mới Kevin Warsh — chính sách chưa rõ ràng → thị trường thận trọng")
        
        if news and isinstance(news, list) and len(news) > 0:
            lines.append("📰 Tin tức:")
            for item in news[:4]:
                lines.append(f"• {item.get('title', '')}")
        
        lines.append("---")
        lines.append("")
        
        # ─── SECTION 3: TECHNICAL ANALYSIS ───
        lines.append("## 📈 3. PHÂN TÍCH KỸ THUẬT ĐA KHUNG THỜI GIAN")
        lines.append("")

        # 3a. H4 Analysis (PRIMARY trend — added 2026-05-26)
        h4 = data.get('h4_ta_data')
        lines.append("### 🔷 Khung H4 (Xu hướng chính — quyết định BIAS)")
        lines.append("")

        if h4:
            h4_trend = h4.get('trend', 'SIDEWAYS')
            h4_swing_high = h4.get('swing_high', 0)
            h4_swing_low = h4.get('swing_low', 0)
            h4_fan_1x1 = h4.get('fan_1x1', 'N/A')
            h4_fan_2x1 = h4.get('fan_2x1', 'N/A')
            h4_fan_3x1 = h4.get('fan_3x1', 'N/A')
            h4_ema_s = h4.get('ema_short')
            h4_ema_l = h4.get('ema_long')
            h4_cross = h4.get('ema_cross', '')

            lines.append(f"| Thông số | Giá trị |")
            lines.append(f"|----------|--------|")
            lines.append(f"| Xu hướng H4 | {h4_trend} |")
            lines.append(f"| Swing High H4 | ${h4_swing_high:.1f} |")
            lines.append(f"| Swing Low H4 | ${h4_swing_low:.1f} |")
            lines.append(f"| Gann Fan H4 1x1 (45°) | ${h4_fan_1x1} |")
            lines.append(f"| Gann Fan H4 2x1 | ${h4_fan_2x1} |")
            lines.append(f"| Gann Fan H4 3x1 | ${h4_fan_3x1} |")
            if h4_ema_s and h4_ema_l:
                lines.append(f"| EMA H4 (12/26) | ${h4_ema_s} / ${h4_ema_l} |")
                cross_label = '🟢 GOLDEN CROSS' if h4_cross == 'GOLDEN_CROSS' else '🔴 DEATH CROSS'
                lines.append(f"| EMA Signal H4 | {cross_label} |")

            h4_fib = h4.get('fib_analysis', {})
            h4_below = h4_fib.get('below')
            h4_above = h4_fib.get('above')
            if h4_below and h4_above:
                lines.append(f"| Fibonacci H4 | Giữa {h4_below[0]} (${h4_below[1]:.1f}) và {h4_above[0]} (${h4_above[1]:.1f}) |")
            elif h4_below:
                lines.append(f"| Fibonacci H4 | Trên {h4_below[0]} (${h4_below[1]:.1f}) |")
            elif h4_above:
                lines.append(f"| Fibonacci H4 | Dưới {h4_above[0]} (${h4_above[1]:.1f}) |")

            # H4 bias indicator
            h4_bias_emoji = '🟢 BULLISH' if h4_trend == 'UP' else ('🔴 BEARISH' if h4_trend == 'DOWN' else '🟡 SIDEWAYS')
            lines.append(f"| **→ H4 BIAS** | **{h4_bias_emoji}** |")
            lines.append("")
        else:
            lines.append("⚠️ Chưa đủ dữ liệu H4 — dùng M30 làm primary.")
            lines.append("")

        # 3b. M30 Analysis
        lines.append("### ⏱️ Khung M30 (Intraday — định thời ENTRY)")
        lines.append("")
        
        if ta:
            fib_a = ta.get("fib_analysis", {})
            below = fib_a.get("below")
            above = fib_a.get("above")
            trend = ta.get("trend", "SIDEWAYS")
            swing_high = ta.get('swing_high', 0)
            swing_low = ta.get('swing_low', 0)
            fan_1x1 = ta.get('fan_1x1', 'N/A')
            fan_2x1 = ta.get('fan_2x1', 'N/A')
            fan_3x1 = ta.get('fan_3x1', 'N/A')
            
            lines.append(f"| Thông số | Giá trị |")
            lines.append(f"|----------|--------|")
            lines.append(f"| Xu hướng M30 | {trend} |")
            lines.append(f"| Swing High | ${swing_high:.1f} |")
            lines.append(f"| Swing Low | ${swing_low:.1f} |")
            lines.append(f"| Gann Fan 1x1 (45°) | ${fan_1x1} |")
            lines.append(f"| Gann Fan 2x1 | ${fan_2x1} |")
            lines.append(f"| Gann Fan 3x1 | ${fan_3x1} |")
            
            if below and above:
                lines.append(f"| Fibonacci | Giữa {below[0]} (${below[1]:.1f}) và {above[0]} (${above[1]:.1f}) |")
            elif below:
                lines.append(f"| Fibonacci | Trên {below[0]} (${below[1]:.1f}) |")
            elif above:
                lines.append(f"| Fibonacci | Dưới {above[0]} (${above[1]:.1f}) |")
            
            # EMA 31/113
            ema_s = ta.get('ema_short') or ta.get('ema_31')
            ema_l = ta.get('ema_long') or ta.get('ema_113')
            ema_pos = ta.get('ema_position', 'N/A')
            if ema_s and ema_l:
                bull_ema = ema_s > ema_l
                ema_signal = "GOLDEN CROSS = bullish" if bull_ema else "DEATH CROSS = bearish"
                lines.append(f"| EMA M30 (31/113) | ${ema_s} / ${ema_l} |")
                lines.append(f"| Giá vs EMA | {ema_pos.upper()} |")
                lines.append(f"| EMA Signal | {'🟢 ' if bull_ema else '🔴 '}{ema_signal} |")

            # Multi-TF alignment summary
            if h4:
                h4_trend = h4.get('trend', '')
                if h4_trend == trend:
                    lines.append(f"| ⚡ **TF Alignment** | **H4 {h4_trend} + M30 {trend} = ĐỒNG PHA → tín hiệu mạnh** |")
                else:
                    lines.append(f"| ⚠️ **TF Alignment** | **H4 {h4_trend} vs M30 {trend} = XUNG ĐỘT → giảm confidence** |")
            lines.append("")
        else:
            lines.append("Chưa đủ dữ liệu M30 cho phân tích Fibonacci & Gann Fan.")
            lines.append("")
        
        # 3c. Gann Square of 9
        lines.append("### 🌀 Gann Square of 9")
        lines.append("")
        lines.append(f"**Trục cơ sở:** {base}")
        lines.append("")
        
        if res_list:
            lines.append("Kháng cự:")
            lines.append("")
            lines.append(f"{fmt_gann_levels(res_list)}")
            lines.append("")
        
        if sup_list:
            lines.append("Hỗ trợ:")
            lines.append("")
            lines.append(f"{fmt_gann_levels(sup_list)}")
            lines.append("")
        
        # 3d. Confluence Zones — Fibo near Gann = price magnet
        if ta:
            czones = ta.get('confluence_zones', [])
            if czones:
                lines.append("### 🧲 Hội Tụ Fibo + Gann (Confluence)")
                lines.append("")
                lines.append("Khi một mốc Fibo trùng hoặc rất gần với mốc Gann Square, đó là cụm nam châm hút giá cực mạnh. Chốt lời một phần lớn tại đây.")
                lines.append("")
                for z in czones[:4]:
                    lines.append(f"  {z['label']} — {'🟢' if z['side'] == 'hỗ trợ' else '🔴'} {z['side']} (cách ${z['diff']:.1f})")
                lines.append("")
        
        # 3e. Gann Date Cycles
        if gann_dates:
            lines.append("### 📅 Gann Time Cycles")
            lines.append("")
            today = dt_now.date()
            past_dates = []
            future_dates = []
            for d in gann_dates:
                d_date = dt.strptime(d['target_date'], "%Y-%m-%d").date()
                if d_date < today:
                    past_dates.append(d)
                else:
                    future_dates.append(d)
            
            show = past_dates[-3:] + future_dates[:3]
            for d in show:
                d_date = dt.strptime(d['target_date'], "%Y-%m-%d").date()
                days = (d_date - today).days
                if days < 0:
                    marker = f"✅ Đã qua {abs(days)} ngày"
                elif days == 0:
                    marker = "⚡ HÔM NAY"
                else:
                    marker = f"⏳ Còn {days} ngày"
                lines.append(f"- **{d['target_date']}** ({d['angle']}°) — {marker}")
            lines.append("")
        
        lines.append("---")
        lines.append("")
        
        # ─── SECTION 4: VEDIC ASTROLOGY ───
        lines.append("## 🌌 4. PHÂN TÍCH CHIÊM TINH VỆ ĐÀ")
        lines.append("")
        
        if astro_report:
            # Use the astro report from the data pipeline
            lines.append(astro_report)
            lines.append("")
        else:
            # Build from raw planet data
            if planets:
                lines.append("### 🪐 Vị trí hành tinh (Sidereal / Lahiri Ayanamsa)")
                lines.append("")
                lines.append(f"| Hành tinh | Cung | Độ |")
                lines.append(f"|-----------|------|----|")
                from astro_engine import PLANET_SYMBOLS as PS
                from astro_engine import PLANET_NAMES_VI as PN
                planet_order = ['Sun', 'Moon', 'Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn']
                for pname in planet_order:
                    p = planets.get(pname)
                    if p and isinstance(p, dict):
                        sym = PS.get(pname, '')
                        name = PN.get(pname, pname)
                        sign = p.get('sign', '?')
                        deg = p.get('degree', 0)
                        lines.append(f"| {sym} **{name}** | {sign} | {deg}° |")
                lines.append("")
        
        # Hora Analysis — full session forecast
        if hora_info:
            lines.append("### ⏰ Phân Tích Hora (Giờ Hành Tinh) — Dự Báo Cả Ngày")
            lines.append("")
            current_hora = hora_info.get('hora', '')
            lines.append(f"**Hora hiện tại:** {current_hora} — {hora_info.get('hora_start', '')} đến {hora_info.get('hora_end', '')}")
            lines.append(f"*Bắt đầu tính từ sunrise {hora_forecast.get('sunrise', 'N/A')} → sunset {hora_forecast.get('sunset', 'N/A')}*")
            lines.append("")
            
            if hora_forecast:
                horas_all = hora_forecast.get('horas', [])
                best_hours = hora_forecast.get('best_trading_hours', [])
                worst_hours = hora_forecast.get('hours_to_avoid', [])
                
                lines.append("**📋 DỰ BÁO HORA THEO PHIÊN GIAO DỊCH:**")
                lines.append("")
                
                sessions = [
                    ("🌏 **Phiên Á** (07:00-15:00)", 7*60, 15*60),
                    ("🌍 **Phiên Âu** (15:00-19:00)", 15*60, 19*60),
                    ("🌎 **Phiên Mỹ** (19:00-03:00)", 19*60, 27*60),
                ]
                
                for sname, s_start, s_end in sessions:
                    session_horas = []
                    for h in horas_all:
                        h_start_str = h.get('start', '00:00')
                        parts = h_start_str.split(':')
                        h_mins = int(parts[0]) * 60 + int(parts[1])
                        
                        if s_end <= 24*60:
                            if s_start <= h_mins < s_end:
                                session_horas.append(h)
                        else:
                            if h_mins >= s_start or h_mins < (s_end - 24*60):
                                session_horas.append(h)
                    
                    if session_horas:
                        lines.append(f"  {sname}")
                        for h in session_horas:
                            marker = " ◀ HIỆN TẠI" if h.get('is_current') else ""
                            if h.get('quality', 3) >= 4:
                                q_marker = "⭐"
                            elif h.get('quality', 3) <= 2:
                                q_marker = "⚠️"
                            else:
                                q_marker = "  "
                            lines.append(f"    {q_marker} {h.get('emoji', '')} {h.get('start', '')}-{h.get('end', '')} | {h.get('ruler', '')} Hora | {h.get('label', '')}{marker}")
                        lines.append("")
                
                if best_hours:
                    lines.append("⭐ **Top giờ giao dịch tốt nhất trong ngày:**")
                    for h in best_hours:
                        lines.append(f"- {h.get('emoji', '')} **{h.get('start', '')}-{h.get('end', '')}** — {h.get('ruler', '')} Hora ({h.get('quality_label', '')}) — {h.get('label', '')}")
                    lines.append("")
                
                if worst_hours:
                    lines.append("⚠️ **Giờ nên tránh (thận trọng):**")
                    for h in worst_hours:
                        lines.append(f"- {h.get('emoji', '')} **{h.get('start', '')}-{h.get('end', '')}** — {h.get('ruler', '')} Hora ({h.get('quality_label', '')}) — {h.get('label', '')}")
                    lines.append("")
        
        lines.append("---")
        lines.append("")
        
        # ─── SECTION 5: HISTORICAL CORRELATION ───
        lines.append("## 📊 5. CORRELATION LỊCH SỬ (4 NĂM DỮ LIỆU)")
        lines.append("")
        
        # Extract astro data for historical query
        # Parse from astro_report text (most reliable source)
        hist_nak = ''
        hist_sign = ''
        hist_phase = ''
        hist_hora = hora_info.get('hora', '') if hora_info else ''
        hist_vol = ''
        hist_trend = ''
        
        # Try planets dict first, fallback to astro_report parsing
        if planets:
            moon = planets.get('Moon', {})
            if isinstance(moon, dict):
                hist_sign = moon.get('sign', '')
                hist_nak = moon.get('nakshatra', '')
                hist_phase = moon.get('phase', '')
        
        # Parse astro_report text if planets didn't yield structured data
        if (not hist_sign or not hist_nak) and astro_report:
            import re
            # Moon: ♌ Sư Tử (5°24'') — Magha (chủ tinh Ketu) — Pada 2
            moon_match = re.search(r'Moon:\s*\S+\s+(\S+(?:\s+\S+)?)\s*\(', astro_report)
            nak_match = re.search(r'—\s*(\w+(?:\s+\w+)?)\s*\(chủ tinh', astro_report)
            phase_match = re.search(r'Lunar Phase:\s*(\S+(?:\s+\S+)?)\s*—', astro_report)
            if moon_match:
                hist_sign = moon_match.group(1)
            if nak_match:
                hist_nak = nak_match.group(1)
            if phase_match:
                hist_phase = phase_match.group(1)
        
        # Fallback: parse Hora section for Moon info
        if (not hist_sign or not hist_nak) and hora_forecast:
            # Use the hora forecast data if astro_report didn't have moon info
            pass
        
        # Normalize moon sign names for DB matching
        sign_map_vi_en = {
            'Bạch Dương': 'Aries', 'Kim Ngưu': 'Taurus', 'Song Tử': 'Gemini',
            'Cự Giải': 'Cancer', 'Sư Tử': 'Leo', 'Xử Nữ': 'Virgo',
            'Thiên Bình': 'Libra', 'Bọ Cạp': 'Scorpio', 'Nhân Mã': 'Sagittarius',
            'Ma Kết': 'Capricorn', 'Bảo Bình': 'Aquarius', 'Song Ngư': 'Pisces'
        }
        hist_sign = sign_map_vi_en.get(hist_sign, hist_sign)
        
        if ta:
            hist_vol = 'high' if abs(ta.get('swing_high', 0) - ta.get('swing_low', 0)) > 50 else ('medium' if abs(ta.get('swing_high', 0) - ta.get('swing_low', 0)) > 25 else 'low')
            hist_trend = ta.get('trend', '')
        
        if hist_nak or hist_sign:
            try:
                hc = HistoricalCorrelation()
                corr = hc.correlate(
                    moon_nakshatra=hist_nak,
                    moon_sign=hist_sign,
                    moon_phase=hist_phase,
                    dominant_hora=hist_hora,
                    volatility=hist_vol,
                    trend=hist_trend,
                )
                
                baseline = corr.get('baseline', {})
                
                # ── 5a. Nakshatra Performance ──
                nak = corr.get('nakshatra_stats')
                if nak:
                    lines.append(f"### 🔮 {hist_nak} Nakshatra — Hiệu suất lịch sử")
                    lines.append("")
                    lines.append(f"**{nak['quality']}** — {nak['total_days']} ngày trong database")
                    lines.append("")
                    lines.append(f"| Chỉ số | {hist_nak} | Toàn thị trường | Chênh lệch |")
                    lines.append(f"|--------|------|---------------|----------|")
                    lines.append(f"| Bullish % | {nak['bullish_pct']}% | {baseline.get('overall_bullish_pct', 50)}% | {'🟢 +' + str(round(nak['bullish_pct'] - baseline.get('overall_bullish_pct', 50), 1)) + '%' if nak['bullish_pct'] > baseline.get('overall_bullish_pct', 50) else '🔴 ' + str(round(nak['bullish_pct'] - baseline.get('overall_bullish_pct', 50), 1)) + '%'} |")
                    lines.append(f"| Avg Change | {nak['avg_change_pct']:+.2f}% | {baseline.get('overall_avg_change', 0):+.3f}% | {'🟢' if nak['avg_change_pct'] > baseline.get('overall_avg_change', 0) else '🔴'} |")
                    lines.append(f"| Avg Range | ${nak['avg_range']:.1f} | ${baseline.get('overall_avg_range', 30):.1f} | {'🟡 Vol cao' if nak['avg_range'] > baseline.get('overall_avg_range', 30) else '🟢 Vol thấp'} |")
                    lines.append(f"| Phản ứng phổ biến | {nak.get('dominant_reaction', [['','']])[0][0] if nak.get('dominant_reaction') else 'N/A'} | — | — |")
                    lines.append("")
                
                # ── 5b. Moon Sign ──
                ms = corr.get('moon_sign_stats')
                if ms:
                    lines.append(f"### 🌙 Moon {hist_sign} — Hiệu suất lịch sử")
                    lines.append("")
                    lines.append(f"| Chỉ số | Moon {hist_sign} | Toàn thị trường |")
                    lines.append(f"|--------|----------|---------------|")
                    lines.append(f"| Bullish % | {ms['bullish_pct']}% ({ms['total_days']} ngày) | {baseline.get('overall_bullish_pct', 50)}% |")
                    lines.append(f"| Avg Change | {ms['avg_change_pct']:+.2f}% | {baseline.get('overall_avg_change', 0):+.3f}% |")
                    lines.append(f"| Avg Range | ${ms['avg_range']:.1f} | ${baseline.get('overall_avg_range', 30):.1f} |")
                    lines.append("")
                
                # ── 5c. Combined ──
                combo = corr.get('combined_stats')
                if combo:
                    trend_emoji = '🟢 BULLISH' if combo['bullish_pct'] >= 55 else ('🔴 BEARISH' if combo['bullish_pct'] <= 45 else '🟡 NEUTRAL')
                    lines.append(f"### ⚡ Kết hợp {hist_nak} + Moon {hist_sign}: **{trend_emoji}**")
                    lines.append("")
                    lines.append(f"- **{combo['total_days']} ngày** trong lịch sử có cùng tổ hợp này")
                    lines.append(f"- Tỷ lệ bullish: **{combo['bullish_pct']}%** — avg change: **{combo['avg_change_pct']:+.2f}%**")
                    lines.append("")
                
                # ── 5d. Retrograde Effects ──
                retro = corr.get('retro_stats')
                if retro:
                    sig_retros = []
                    for planet, stats in retro.items():
                        if abs(stats['delta_bullish']) >= 3:
                            sig_retros.append((planet, stats))
                    
                    if sig_retros:
                        lines.append("### ℞ Hiệu ứng Nghịch Hành")
                        lines.append("")
                        lines.append(f"| Hành tinh | Retro Bullish | Direct Bullish | Delta |")
                        lines.append(f"|-----------|--------------|---------------|-------|")
                        for planet, s in sig_retros:
                            emoji = '🟢' if s['delta_bullish'] > 0 else '🔴'
                            lines.append(f"| **{planet}** | {s['retro_bullish']}% | {s['direct_bullish']}% | {emoji} {s['delta_bullish']:+.1f}% |")
                        lines.append("")
                
                # ── 5e. Gann Key Level ──
                gk = corr.get('gann_key_stats')
                if gk:
                    range_ratio = gk['breached_avg_range'] / max(gk['held_avg_range'], 1)
                    lines.append("### 🌀 Gann Key Level — Held vs Breached")
                    lines.append("")
                    lines.append(f"- Giữ được Key Level ({gk['held_total']} ngày): avg range **${gk['held_avg_range']:.1f}** — thị trường ổn định")
                    lines.append(f"- Phá vỡ Key Level ({gk['breached_total']} ngày): avg range **${gk['breached_avg_range']:.1f}** — biến động gấp **{range_ratio:.1f}x**")
                    lines.append("")
                
                # ── 5f. Similar Days ──
                matches = corr.get('exact_matches', [])
                if matches:
                    lines.append("### 🔍 Ngày Tương Tự Nhất Trong Lịch Sử")
                    lines.append("")
                    for i, m in enumerate(matches[:3], 1):
                        bull_emoji = '🟢' if m['bullish'] else '🔴'
                        lines.append(f"{i}. **{m['date']}** — Close ${m['close']:.1f} | {bull_emoji} {m['change_pct']:+.2f}% | Range ${m['range']:.1f} | {m.get('volatility', '')} | {m.get('reaction', '')}")
                    lines.append("")
                    
            except Exception as e:
                lines.append(f"⚠️ Không thể truy vấn dữ liệu lịch sử: {str(e)[:100]}")
                lines.append("")
        
        lines.append("---")
        lines.append("")
        
        # ─── SECTION 6: CARMEN AI DEEP ANALYSIS ───
        lines.append("## 🧠 6. CARMEN AI — PHÂN TÍCH CHUYÊN SÂU")
        lines.append("")
        
        # Use the deep analysis builder — produces DIFFERENT content from Section 1
        deep_analysis = ReportGenerator._build_carmen_deep_analysis(data, carmen)
        lines.append(deep_analysis)
        lines.append("")
        
        lines.append("---")
        lines.append("")
        
        # ─── SECTION 7: STRATEGY & EXECUTION ───
        lines.append("## 💡 7. CHIẾN LƯỢC & THỰC THI")
        lines.append("")
        
        # Check if Carmen has a clear, high-confidence signal
        carmen_has_clear_signal = (
            carmen and not carmen.get('error')
            and carmen.get('bias') in ['BULLISH', 'BEARISH']
            and carmen.get('confidence', 0) >= 0.45
        )
        
        if carmen_has_clear_signal:
            call_str = ReportGenerator._build_call_section(data, ta, carmen,
                res_list[1]['price'] if len(res_list) > 1 else 0,
                res_list[5]['price'] if len(res_list) > 5 else 0,
                sup_list[1]['price'] if len(sup_list) > 1 else 0,
                sup_list[5]['price'] if len(sup_list) > 5 else 0)
        else:
            call_str = ReportGenerator._build_hold_strategy(data, ta, carmen)
        
        lines.append(call_str)
        lines.append("")
        
        # Execution notes
        if carmen and not carmen.get('error'):
            if carmen.get('bias') in ['BULLISH', 'BEARISH'] and carmen.get('confidence', 0) < 0.6:
                lines.append("**💡 Ghi chú:** Carmen có direction nhưng confidence chưa cao. Nếu trade, giảm 50% position size. Chỉ vào lệnh khi có thêm xác nhận từ price action.")
                lines.append("")
            elif carmen.get('bias') in ['NEUTRAL', 'MIXED']:
                lines.append("**💡 Ghi chú:** Thị trường không có tín hiệu rõ ràng. Carmen khuyến nghị HOLD/chờ. Ưu tiên limit entry tại vùng hỗ trợ/kháng cự mạnh thay vì market order.")
                lines.append("")
        
        # Observation Zones
        lines.append("### 📍 Vùng quan sát")
        lines.append("")
        
        near_sup = sup_list[0]['price'] if sup_list else price * 0.97
        near_res = res_list[0]['price'] if res_list else price * 1.03
        
        lines.append(f"- 🟢 **Bullish:** Giữ trên ${near_sup:.0f} → target ${near_res:.0f} → ${res_list[2]['price'] if len(res_list) > 2 else price * 1.05:.0f}")
        lines.append(f"- 🔴 **Bearish:** Phá dưới ${near_sup:.0f} → target ${near_sup * 0.96:.0f} → ${near_sup * 0.92:.0f}")
        lines.append(f"- 🟡 **Neutral:** Tích lũy trong range ${near_sup:.0f} — ${near_res:.0f}")
        lines.append("")
        
        lines.append("---")
        lines.append("")
        
        # ─── SECTION 8: RISK MATRIX ───
        lines.append("## 🛡️ 8. MA TRẬN RỦI RO")
        lines.append("")
        
        lines.append("| Loại rủi ro | Mức độ | Mô tả |")
        lines.append("|-------------|--------|-------|")
        
        # Technical risk
        if ta and ta.get('trend') == 'SIDEWAYS':
            lines.append("| Kỹ thuật | 🟡 Trung bình | Sideways — khó xác định direction |")
        elif ta and ta.get('trend') == 'UP':
            lines.append("| Kỹ thuật | 🟢 Thấp | Trend rõ ràng, pullback entry an toàn |")
        else:
            lines.append("| Kỹ thuật | 🟠 Cao | Downtrend — counter-trend risk cao |")
        
        # Astro risk
        moon_sign = ''
        if planets:
            moon = planets.get('Moon', {})
            if isinstance(moon, dict):
                moon_sign = moon.get('sign', '')
        
        if moon_sign in ['Scorpio', 'Pisces']:
            lines.append(f"| Chiêm tinh | 🟠 Cao | Moon {moon_sign} — sentiment bất ổn |")
        elif moon_sign in ['Taurus', 'Leo', 'Sagittarius']:
            lines.append(f"| Chiêm tinh | 🟢 Thấp | Moon {moon_sign} — sentiment ổn định |")
        else:
            lines.append("| Chiêm tinh | 🟡 Trung bình | Biến động trong ngưỡng bình thường |")
        
        # Event risk
        has_news = news and isinstance(news, list) and len(news) > 0
        lines.append(f"| Sự kiện | {'🟠 Cao' if has_news else '🟢 Thấp'} | {'Có tin tức vĩ mô cần theo dõi' if has_news else 'Không có sự kiện lớn'} |")
        
        # Vol risk
        if ta:
            range_val = abs(ta.get('swing_high', 0) - ta.get('swing_low', 0))
            if range_val > 50:
                lines.append(f"| Biến động | 🔴 Rất cao | Range ${range_val:.1f} — wide stops |")
            elif range_val > 25:
                lines.append(f"| Biến động | 🟡 Trung bình | Range ${range_val:.1f} |")
            else:
                lines.append(f"| Biến động | 🟢 Thấp | Range ${range_val:.1f} — tight stops |")
        
        # Confidence risk
        if carmen and not carmen.get('error'):
            conf = carmen.get('confidence', 0)
            if conf < 0.5:
                lines.append(f"| Confidence | 🔴 Rất thấp | Carmen confidence {conf:.0%} — cân nhắc không trade |")
            elif conf < 0.7:
                lines.append(f"| Confidence | 🟡 Trung bình | Carmen confidence {conf:.0%} — giảm size |")
            else:
                lines.append(f"| Confidence | 🟢 Cao | Carmen confidence {conf:.0%} — tín hiệu rõ ràng |")
        
        lines.append("")
        
        lines.append("---")
        lines.append("")
        
        # ─── SECTION 9: FORWARD OUTLOOK ───
        lines.append("## 🔭 9. DỰ BÁO 3-7 NGÀY TỚI")
        lines.append("")
        lines.append("Dựa trên chu kỳ hành tinh và Gann time cycles:")
        lines.append("")
        
        # Find nearest future Gann date
        if gann_dates:
            future = [d for d in gann_dates if dt.strptime(d['target_date'], "%Y-%m-%d").date() >= dt_now.date()]
            if future:
                for d in future[:2]:
                    d_date = dt.strptime(d['target_date'], "%Y-%m-%d").date()
                    days_away = (d_date - dt_now.date()).days
                    lines.append(f"- **{d['target_date']}** (còn {days_away} ngày) — Mốc Gann {d['angle']}° — điểm xoay trục tiềm năng")
            else:
                lines.append("- Không có mốc Gann tương lai gần — thị trường trong pha không chu kỳ")
        
        lines.append("")
        lines.append("- Theo dõi lịch kinh tế tuần tới để xác định catalyst cho breakout")
        lines.append("- Chu kỳ Mặt Trăng hiện tại sẽ ảnh hưởng đến sentiment trong 3-5 ngày tới")
        lines.append("")
        
        # ─── FOOTER ───
        lines.append("---")
        lines.append("")
        lines.append("*Bản tin độc quyền được tạo bởi **Carmen AI — Astro-Quant Engine v2.0***")
        lines.append(f"*Ngày phân tích: {date_str} | Dữ liệu: Yahoo Finance GC=F, Swiss Ephemeris (Lahiri Ayanamsa)*")
        lines.append("*Hệ thống Algorithmic Trading & Vedic Astrology — Kim Ssa*")
        lines.append("")
        lines.append("⚠️ **TUYÊN BỐ MIỄN TRỪ TRÁCH NHIỆM:** Bản tin này chỉ dành cho mục đích giáo dục và nghiên cứu. Không phải lời khuyên đầu tư. Giao dịch vàng CFD có rủi ro cao. Luôn tự quản lý rủi ro và chỉ trade với số vốn bạn sẵn sàng mất.")
        
        return '\n'.join(lines)

if __name__ == "__main__":
    pass
