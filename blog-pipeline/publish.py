#!/usr/bin/env python3
"""
Blog Publishing Pipeline — Vedic VN (Supabase)
===============================================
3 content series:
  Tuyến 1: "Chiêm tinh giải quyết vấn đề" (pain points → chart creation)
  Tuyến 2: "Bản tin Thời không" (transit events)
  Tuyến 3: "Kiến thức nền tảng Vedic" (authority building)

Usage:
  python3 publish.py                    # Post next due article (dry-run)
  python3 publish.py --run              # Post for real
  python3 publish.py --series 1         # Force series 1
  python3 publish.py --status           # Show publishing calendar
  python3 publish.py --init             # First-run, publish initial batch
"""

import csv
import json
import os
import random
import re
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone, timedelta
from pathlib import Path

# === CONFIG ===
SUPABASE_URL = "https://qzyyiqzekduduoscdwjc.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InF6eXlpcXpla2R1ZHVvc2Nkd2pjIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0Mzk5OTQ1MSwiZXhwIjoyMDU5NTc1NDUxfQ.2MiRoY-nF-uUszqzeKlSjeKq9IN0QlFWU2U4cHf1kAY"
TABLE_NAME = "blog_posts"

BIRTH_CHART_CSV = os.path.join(os.path.dirname(__file__), "..", "birth-chart-bank-data", "birth_chart_clean.csv")
STATE_FILE = os.path.join(os.path.dirname(__file__), "publish_state.json")
VN_TZ = timezone(timedelta(hours=7))

# === TEMPLATES ===

# ---- TUYẾN 1: Chiêm tinh giải quyết vấn đề ----
SERIES1 = [
    {
        "title": "Tại sao nỗ lực mãi nhưng sự nghiệp chưa bứt phá? Góc nhìn từ Sao Thổ trong bản đồ sao",
        "tags": ["vedic", "chiemtinh", "dudoan"],
        "slug_prefix": "saturn-career-breakthrough",
        "content_template": """
<p>Bạn có cảm thấy mình đã làm việc chăm chỉ, cống hiến hết mình, nhưng sự nghiệp vẫn như "dậm chân tại chỗ"?</p>
<p>Trong Chiêm tinh Vệ Đà (Jyotish), <strong>Sao Thổ (Shani)</strong> được xem là "hành tinh của nghiệp quả" – vị thẩm phán công bằng nhất vũ trụ. Nó không chỉ đại diện cho kỷ luật, trách nhiệm mà còn cho những <strong>bài học cần vượt qua</strong> để đạt đến thành công thực sự.</p>
<h2>Sao Thổ nằm ở đâu trong bản đồ sao của bạn?</h2>
<p>Mỗi người có một vị trí Sao Thổ khác nhau trong bản đồ sao cá nhân. Vị trí này cho biết <strong>bạn đang gặp khó khăn ở lĩnh vực nào</strong> và cần làm gì để vượt qua.</p>
<p>Thông thường, nếu Sao Thổ nằm ở:</p>
<ul>
<li><strong>Nhà 10 (Sự nghiệp):</strong> Bạn có thể gặp trì hoãn trong thăng tiến, nhưng nếu kiên trì, bạn sẽ đạt được vị trí vững chắc sau tuổi 36.</li>
<li><strong>Nhà 6 (Công việc hàng ngày):</strong> Bạn phải đối mặt với đồng nghiệp khó tính hoặc công việc nặng nhọc, nhưng điều này rèn luyện bạn trở nên mạnh mẽ hơn.</li>
<li><strong>Nhà 2 (Tài chính):</strong> Tiền bạc đến chậm nhưng bền vững nếu bạn biết quản lý chi tiêu.</li>
</ul>
{case_study}
<h2>Khi nào sẽ khá hơn?</h2>
<p>Giai đoạn <strong>Sao Thổ quá cảnh (Saturn Transit)</strong> qua các cung hoàng đạo khác nhau sẽ mang đến những cơ hội thay đổi. Đặc biệt là <strong>Sade Sati</strong> – chu kỳ 7.5 năm của Sao Thổ – dù khó khăn nhưng là thời điểm vàng để tái cấu trúc sự nghiệp.</p>
<p>👉 <strong>Muốn biết Sao Thổ đang ảnh hưởng thế nào đến cuộc đời bạn?</strong> Hãy <a href="/vedic-chart"><strong>tạo bản đồ sao ngay</strong></a> để khám phá vị trí các hành tinh trong lá số của bạn.</p>
<p>Theo dõi thêm các dự báo chiêm tinh hàng tháng tại <a href="https://patreon.com/VotiveAstrology">Patreon Votive Academy</a> và kết nối với cộng đồng qua <a href="https://facebook.com/votive.edu">Facebook</a> | <a href="https://x.com/VotiveAstrology">X (Twitter)</a> | <a href="https://t.me/votiveacademy">Telegram</a>.</p>
"""
    },
    {
        "title": "Tình duyên lận đận: Liệu có phải do Rahu và Ketu trong bản đồ sao?",
        "tags": ["vedic", "chiemtinh", "dudoan", "healing"],
        "slug_prefix": "rahu-ketu-relationship",
        "content_template": """
<p>Chuyện tình cảm của bạn cứ lặp đi lặp lại một kịch bản: <strong>yêu rồi tan, đến rồi đi</strong>? Có người thì thu hút toàn mẫu người không phù hợp, có người lại sợ cam kết dù rất muốn ổn định.</p>
<p>Trong Chiêm tinh Vệ Đà, <strong>Rahu (La Hầu)</strong> và <strong>Ketu (Kế Đô)</strong> – hai điểm nút mặt trăng – được xem là những "điểm nghiệp" (karmic points) chi phối các mối quan hệ. Chúng không phải hành tinh vật lý, nhưng ảnh hưởng của chúng trong chuyện tình cảm là rất rõ rệt.</p>
{h2h_section}
<h2>Rahu ở Nhà 7: Thu hút người "lạ" nhưng khó bền</h2>
<p>Rahu (La Hầu) là ảo ảnh, là những điều ta khao khát nhưng không thuộc về mình. Khi Rahu ở Nhà 7 (hôn nhân và quan hệ đối tác), bạn có xu hướng bị thu hút bởi những người "khác biệt" – khác văn hóa, khác tầng lớp, hoặc những mối quan hệ không được xã hội công nhận.</p>
{case_study_rahu}
<h2>Ketu ở Nhà 7: Sợ cam kết, thích cô đơn</h2>
<p>Ketu (Kế Đô) đại diện cho sự tách rời và tâm linh. Nếu Ketu ở Nhà 7, bạn có xu hướng sợ hôn nhân, cảm thấy ngột ngạt trong các mối quan hệ cam kết. Bạn cần một người bạn đời tôn trọng không gian riêng và sự tự do của bạn.</p>
{case_study_ketu}
<h2>Làm sao để hóa giải?</h2>
<ul>
<li><strong>Nhận thức được mô hình nghiệp:</strong> Bước đầu tiên là hiểu rằng những khó khăn trong tình cảm không phải "số phận an bài" mà là bài học cần học.</li>
<li><strong>Cân bằng năng lượng:</strong> Thiền định, yoga và các hoạt động tâm linh giúp làm dịu ảnh hưởng của Rahu/Ketu.</li>
<li><strong>Chọn đúng thời điểm:</strong> Kết hôn vào các thời điểm có sao Mộc (Jupiter) thuận lợi sẽ giúp giảm thiểu tác động tiêu cực.</li>
</ul>
<p>👉 <strong>Muốn biết Rahu/Ketu đang ảnh hưởng thế nào đến đường tình duyên của bạn?</strong> Hãy <a href="/vedic-chart"><strong>tạo bản đồ sao ngay</strong></a> để khám phá.</p>
<p><em>Bài viết có tham khảo dữ liệu từ hơn 10,000 lá số thực tế của Votive Academy.</em></p>
"""
    },
    {
        "title": "Khủng hoảng tuổi 30 dưới góc nhìn Chiêm tinh Vệ Đà",
        "tags": ["vedic", "chiemtinh", "healing"],
        "slug_prefix": "quarter-life-crisis-vedic",
        "content_template": """
<p>Bước sang tuổi 30, nhiều người bắt đầu cảm thấy <strong>hoang mang, lo lắng và áp lực</strong>. Sự nghiệp chưa như mơ, tình duyên chưa ổn định, bạn bè xung quanh ai cũng "có vẻ" thành công hơn mình.</p>
<p>Trong Chiêm tinh Vệ Đà, giai đoạn này thường trùng với một loạt chuyển động quan trọng của các hành tinh, đặc biệt là <strong>chu kỳ Sade Sati của Sao Thổ (29-36 tuổi)</strong> và <strong>sự trở về của Sao Mộc (24 và 36 tuổi)</strong>.</p>
{age_stat_section}
<h2>Sade Sati: 7.5 năm thử thách</h2>
<p>Sade Sati là chu kỳ Sao Thổ quá cảnh qua cung hoàng đạo chứa Mặt Trăng của bạn. Nếu bạn sinh ra với Mặt Trăng ở cung Bạch Dương, khi Sao Thổ đi qua Bạch Dương, Kim Ngưu và Song Tử (khoảng 7.5 năm), bạn trải qua Sade Sati.</p>
<p>Các biểu hiện thường gặp:</p>
<ul>
<li><strong>Công việc:</strong> Áp lực tăng cao, trách nhiệm nặng nề, có thể mất việc hoặc thay đổi nghề nghiệp</li>
<li><strong>Tài chính:</strong> Chi tiêu tăng, khó tiết kiệm, các khoản nợ đến hạn</li>
<li><strong>Sức khỏe:</strong> Stress kéo dài, mất ngủ, các bệnh mãn tính bắt đầu xuất hiện</li>
<li><strong>Tinh thần:</strong> Cảm giác cô đơn, muốn sống chậm lại, suy tư về ý nghĩa cuộc sống</li>
</ul>
{case_study}
<h2>Sao Mộc trở về: Cơ hội vàng giữa thử thách</h2>
<p>Sao Mộc trở về vị trí gốc (Jupiter Return) ở tuổi 24 và 36 là những cột mốc quan trọng. Nếu Sade Sati là thử thách, Jupiter Return là <strong>cơ hội mở rộng</strong> – thời điểm để học thêm kỹ năng mới, du lịch, hoặc bắt đầu một dự án tâm linh.</p>
<p>👉 <strong>Bạn đang ở giai đoạn nào của chu kỳ này?</strong> Hãy <a href="/vedic-chart"><strong>tạo bản đồ sao ngay</strong></a> để biết vị trí các hành tinh trong cuộc đời bạn.</p>
<p>Theo dõi thêm tại <a href="https://patreon.com/VotiveAstrology">Patreon</a> và tham gia cộng đồng <a href="https://t.me/votiveacademy">Telegram</a>.</p>
"""
    },
]

# ---- TUYẾN 2: Bản tin Thời không ----
SERIES2 = [
    {
        "title": "Sao Mộc quá cảnh 2026: Cơ hội mở rộng tài chính cho 12 Cung Mọc",
        "tags": ["vedic", "chiemtinh", "dudoan", "taichinh"],
        "slug_prefix": "jupiter-transit-2026",
        "content_template": """
<p>Năm 2026 đánh dấu một giai đoạn quan trọng khi <strong>Sao Mộc (Jupiter)</strong> – hành tinh của sự mở rộng, may mắn và thịnh vượng – quá cảnh qua các cung hoàng đạo, mang đến những cơ hội tài chính khác nhau cho từng Cung Mọc (Lagna).</p>
<h2>Sao Mộc và Tài Chính – Mối liên hệ vũ trụ</h2>
<p>Trong chiêm tinh Vệ Đà, Sao Mộc là <strong>Karaka (đại diện) của tài sản, kiến thức và con cái</strong>. Nó cai quản Nhà 2 (tài chính) và Nhà 11 (thu nhập) trong bản đồ sao tự nhiên. Khi Sao Mộc quá cảnh thuận lợi, các cơ hội tài chính thường đến từ việc mở rộng kiến thức, đầu tư giáo dục, hoặc hợp tác với đối tác nước ngoài.</p>
<h2>Dự báo cho từng Cung Mọc</h2>
<ul>
<li><strong>Cung Mọc Bạch Dương (Mesha):</strong> Sao Mộc quá cảnh qua Nhà 9 – thời điểm tốt để đầu tư vào giáo dục, xuất bản, và quan hệ quốc tế. Cơ hội tài chính đến từ xa.</li>
<li><strong>Cung Mọc Kim Ngưu (Vrishabha):</strong> Sao Mộc ở Nhà 8 – có thể nhận được tài sản thừa kế, tiền từ bảo hiểm hoặc đầu tư tài chính. Cần thận trọng với các khoản vay.</li>
<li><strong>Cung Mọc Song Tử (Mithuna):</strong> Sao Mộc quá cảnh Nhà 7 – cơ hội hợp tác kinh doanh, đối tác mang lại tài lộc. Hôn nhân có thể mang đến lợi ích tài chính.</li>
<li><strong>Cung Mọc Cự Giải (Karka):</strong> Sao Mộc ở Nhà 6 – cạnh tranh lành mạnh giúp bạn kiếm tiền tốt hơn. Công việc liên quan đến dịch vụ, sức khỏe thuận lợi.</li>
<li><strong>Cung Mọc Sư Tử (Simha):</strong> Sao Mộc quá cảnh Nhà 5 – đầu tư mạo hiểm, chứng khoán, và các dự án sáng tạo mang lại lợi nhuận.</li>
<li><strong>Cung Mọc Xử Nữ (Kanya):</strong> Sao Mộc ở Nhà 4 – bất động sản, mua nhà, đầu tư vào đất đai là hướng đi tốt.</li>
<li><strong>Cung Mọc Thiên Bình (Tula):</strong> Sao Mộc quá cảnh Nhà 3 – truyền thông, viết lách, kinh doanh online mang lại thu nhập.</li>
<li><strong>Cung Mọc Bọ Cạp (Vrishchika):</strong> Sao Mộc ở Nhà 2 – tài chính gia tăng, gia đình hỗ trợ, cơ hội kinh doanh gia truyền.</li>
<li><strong>Cung Mọc Nhân Mã (Dhanus):</strong> Sao Mộc quá cảnh Nhà 1 – năm cá nhân mạnh mẽ, thu hút cơ hội nhờ sự tự tin.</li>
<li><strong>Cung Mọc Ma Kết (Makara):</strong> Sao Mộc ở Nhà 12 – chi tiêu cho du lịch, tâm linh, đầu tư vào bản thân sẽ sinh lời dài hạn.</li>
<li><strong>Cung Mọc Bảo Bình (Kumbha):</strong> Sao Mộc quá cảnh Nhà 11 – năm tài chính tốt nhất trong chu kỳ, thu nhập tăng vọt.</li>
<li><strong>Cung Mọc Song Ngư (Meena):</strong> Sao Mộc ở Nhà 10 – thăng tiến trong sự nghiệp, danh tiếng mang lại tiền bạc.</li>
</ul>
<h2>Thời điểm "vàng" trong năm</h2>
<p>Các giai đoạn nên chú ý trong năm 2026 bao gồm khi Mặt Trăng (Moon) quá cảnh qua cung của Sao Mộc, tạo thành <strong>Gaja Kesari Yoga</strong> – một trong những tổ hợp chiêm tinh may mắn nhất cho tài chính.</p>
<p>👉 <strong>Bạn thuộc Cung Mọc nào?</strong> Chưa biết Cung Mọc của mình? Hãy <a href="/vedic-chart"><strong>tạo bản đồ sao ngay</strong></a> để khám phá!</p>
<p>Đừng quên theo dõi <a href="https://www.facebook.com/votive.edu">Facebook Votive Academy</a> để cập nhật các dự báo hàng tuần!</p>
"""
    },
    {
        "title": "Nhật Thực 2026: Ảnh hưởng đến tài chính và sự nghiệp của bạn",
        "tags": ["vedic", "chiemtinh", "dudoan"],
        "slug_prefix": "solar-eclipse-2026",
        "content_template": """
<p>Nhật thực (Solar Eclipse) và Nguyệt thực (Lunar Eclipse) là những sự kiện thiên văn <strong>mang ảnh hưởng cực mạnh</strong> trong Chiêm tinh Vệ Đà. Không giống như các hiện tượng chiêm tinh thông thường, nhật thực có thể tạo ra những <strong>cột mốc thay đổi cuộc đời</strong> trong vòng 6 tháng sau khi xảy ra.</p>
<h2>Tại sao nhật thực quan trọng?</h2>
<p>Trong Jyotish, nhật thực xảy ra khi Mặt Trời và Mặt Trăng cùng hội tụ tại một điểm trên bầu trời, gần với <strong>Rahu hoặc Ketu</strong> – hai điểm nút mặt trăng. Đây là thời điểm năng lượng của ba thực thể (Mặt Trời, Mặt Trăng và Rahu/Ketu) kết hợp, tạo ra một "cơn bão năng lượng" có thể đảo lộn mọi kế hoạch.</p>
{case_study}
<h2>Nhật thực ảnh hưởng đến từng Cung Mọc thế nào?</h2>
<ul>
<li><strong>Bạch Dương/Thiên Bình:</strong> Các mối quan hệ đối tác và hôn nhân sẽ có biến động. Cẩn thận với các hợp đồng ký kết trong thời gian này.</li>
<li><strong>Kim Ngưu/Bọ Cạp:</strong> Tài chính và vấn đề nợ nần cần được xem xét kỹ. Có thể có tin vui từ tài sản thừa kế.</li>
<li><strong>Song Tử/Nhân Mã:</strong> Sức khỏe và công việc hàng ngày bị ảnh hưởng. Tránh các quyết định quan trọng về nghề nghiệp.</li>
<li><strong>Cự Giải/Ma Kết:</strong> Gia đình và sự nghiệp có biến chuyển. Có thể chuyển nhà hoặc thay đổi công việc.</li>
<li><strong>Sư Tử/Bảo Bình:</strong> Con cái và các dự án sáng tạo. Nhật thực có thể mang đến tin vui về con cái.</li>
<li><strong>Xử Nữ/Song Ngư:</strong> Sức khỏe tinh thần và giấc ngủ. Tránh các quyết định vội vàng.</li>
</ul>
<h2>Lời khuyên cho thời gian nhật thực</h2>
<ul>
<li>Tránh bắt đầu dự án mới hoặc ký hợp đồng quan trọng trong vòng 3 ngày trước và sau nhật thực</li>
<li>Thiền định và tụng chú (mantra) trong thời gian diễn ra nhật thực giúp giảm tác động tiêu cực</li>
<li>Ghi lại những giấc mơ trong giai đoạn này – chúng thường chứa thông điệp quan trọng</li>
<li>Thực hiện các nghi lễ thanh tẩy (tắm, nhịn ăn) trong thời gian nhật thực</li>
</ul>
<p>👉 <strong>Biết bản đồ sao của bạn sẽ giúp hiểu rõ nhật thực ảnh hưởng thế nào đến cuộc sống của riêng bạn.</strong> <a href="/vedic-chart"><strong>Tạo bản đồ sao ngay</strong></a> để khám phá!</p>
"""
    },
    {
        "title": "Sao Thủy nghịch hành: Sự thật và cách vượt qua từ góc nhìn Vệ Đà",
        "tags": ["vedic", "chiemtinh", "kienthuc"],
        "slug_prefix": "mercury-retrograde-vedic",
        "content_template": """
<p>"Sao Thủy nghịch hành" (Mercury Retrograde) là một trong những cụm từ được nhắc đến nhiều nhất trong giới chiêm tinh. Nhưng <strong>sự thật về nó là gì</strong> và Chiêm tinh Vệ Đà nhìn nhận hiện tượng này khác với chiêm tinh phương Tây ra sao?</p>
<h2>Sao Thủy nghịch hành là gì?</h2>
<p>Sao Thủy nghịch hành xảy ra khoảng <strong>3-4 lần mỗi năm</strong>, mỗi lần kéo dài khoảng 3 tuần. Đây là hiện tượng quang học khi Sao Thủy di chuyển chậm hơn Trái Đất trên quỹ đạo, khiến từ góc nhìn của chúng ta, nó dường như "đi lùi" trên bầu trời.</p>
<p>Trong Chiêm tinh Vệ Đà, Sao Thủy (Budha) là hành tinh của <strong>giao tiếp, thương mại và trí tuệ</strong>. Khi nghịch hành, năng lượng của nó chuyển vào nội tâm thay vì hướng ngoại.</p>
<h2>Tác động cụ thể</h2>
<ul>
<li><strong>Giao tiếp:</strong> Dễ hiểu lầm, email thất lạc, thiết bị điện tử trục trặc</li>
<li><strong>Đi lại:</strong> Chậm trễ, hủy chuyến, mất hành lý</li>
<li><strong>Hợp đồng:</strong> Các điều khoản bị bỏ sót, đàm phán kéo dài</li>
<li><strong>Công nghệ:</strong> Máy tính hỏng, mất dữ liệu, lỗi phần mềm</li>
<li><strong>Sức khỏe:</strong> Đau đầu, căng thẳng thần kinh, mất ngủ</li>
</ul>
{case_study}
<h2>Góc nhìn Vệ Đà vs Phương Tây</h2>
<p>Khác với chiêm tinh phương Tây thường coi sao Thủy nghịch hành là "thảm họa", chiêm tinh Vệ Đà xem đây là <strong>thời điểm để nhìn lại và điều chỉnh</strong>. Thay vì lo sợ, hãy xem đây là cơ hội để:</p>
<ul>
<li>Kiểm tra lại các kế hoạch đã đề ra</li>
<li>Liên lạc lại với bạn bè cũ, đối tác cũ</li>
<li>Hoàn thành các dự án dang dở</li>
<li>Thực hành thiền định và nội quan</li>
</ul>
<h2>Làm thế nào để giảm tác động?</h2>
<ul>
<li>Sao chép dữ liệu quan trọng trước khi sao Thủy nghịch hành bắt đầu</li>
<li>Đọc kỹ hợp đồng 3 lần trước khi ký</li>
<li>Tránh mua sắm thiết bị điện tử mới trong thời gian này</li>
<li>Dành thêm thời gian cho việc kiểm tra lại thông tin</li>
</ul>
<p>👉 <strong>Bí ẩn nào đang chờ bạn khám phá trong bản đồ sao của mình?</strong> <a href="/vedic-chart"><strong>Tạo bản đồ sao miễn phí ngay hôm nay</strong></a>.</p>
"""
    },
]

# ---- TUYẾN 3: Kiến thức nền tảng Vedic ----
SERIES3 = [
    {
        "title": "Cung Mọc (Lagna) là gì và tại sao nó lại định hình toàn bộ cuộc đời bạn?",
        "tags": ["vedic", "chiemtinh", "kienthuc"],
        "slug_prefix": "lagna-ascendant-guide",
        "content_template": """
<p>Nếu bạn từng xem bản đồ sao chiêm tinh, chắc hẳn bạn đã thấy cụm từ <strong>"Cung Mọc" (Lagna)</strong> xuất hiện. Nhưng Cung Mọc thực sự là gì? Và tại sao các nhà chiêm tinh Vệ Đà lại coi nó là yếu tố <strong>quan trọng nhất</strong> trong toàn bộ lá số?</p>
<h2>Cung Mọc (Lagna) không phải Cung Hoàng Đạo</h2>
<p>Nhiều người nhầm lẫn giữa Cung Mọc (Ascendant) và Cung Hoàng Đạo (Sun Sign). Trong Chiêm tinh Vệ Đà, <strong>Cung Mọc là cung hoàng đạo đang mọc lên ở đường chân trời phía Đông</strong> tại thời điểm bạn chào đời. Nó thay đổi khoảng 2 giờ một lần, khác với Cung Mặt Trời chỉ thay đổi mỗi tháng.</p>
<p>Ví dụ: Nếu bạn sinh lúc 6h sáng tại Hà Nội, Cung Mọc của bạn có thể là Song Tử hoặc Cự Giải, trong khi Cung Mặt Trời của bạn phụ thuộc vào ngày sinh.</p>
<h2>Tại sao Cung Mọc quan trọng?</h2>
<ul>
<li><strong>Nó là "mặt nạ" bạn đeo trước thế giới:</strong> Cung Mọc quyết định cách bạn xuất hiện, cách người khác nhìn nhận bạn lần đầu tiên.</li>
<li><strong>Nó định hình thể chất:</strong> Mỗi Cung Mọc có một kiểu hình thể và sức khỏe đặc trưng.</li>
<li><strong>Nó quyết định cách bố trí toàn bộ lá số:</strong> Lagna quyết định Nhà 1 ở đâu, và từ đó xác định tất cả các nhà khác.</li>
<li><strong>Nó ảnh hưởng đến tính cách cốt lõi:</strong> Dù bạn thuộc cung Mặt Trời nào, Cung Mọc sẽ "nhuộm màu" cách bạn thể hiện bản thân.</li>
</ul>
{case_study}
<h2>12 Cung Mọc và đặc điểm</h2>
<ul>
<li><strong>Bạch Dương:</strong> Mạnh mẽ, quyết đoán, dễ nóng vội. Dáng người cân đối, thường có sẹo trên đầu hoặc mặt.</li>
<li><strong>Kim Ngưu:</strong> Điềm tĩnh, kiên định, yêu cái đẹp. Khuôn mặt tròn, mắt to, cổ ngắn.</li>
<li><strong>Song Tử:</strong> Nhanh nhẹn, thông minh, hài hước. Dáng cao gầy, tay chân dài.</li>
<li><strong>Cự Giải:</strong> Nhạy cảm, dễ xúc động, yêu gia đình. Mặt tròn, mắt ướt, dáng mập mạp.</li>
<li><strong>Sư Tử:</strong> Hào phóng, tự tin, thích làm trung tâm. Dáng cao, xương lớn, tóc dày.</li>
<li><strong>Xử Nữ:</strong> Tỉ mỉ, phân tích, cầu toàn. Dáng thon, mặt thanh tú, ăn mặc gọn gàng.</li>
<li><strong>Thiên Bình:</strong> Lịch thiệp, cân bằng, yêu hòa bình. Mặt thanh, mũi thẳng, duyên dáng.</li>
<li><strong>Bọ Cạp:</strong> Bí ẩn, sâu sắc, ý chí mạnh. Mắt sâu, nhìn xuyên thấu, dáng nhỏ nhưng săn chắc.</li>
<li><strong>Nhân Mã:</strong> Lạc quan, yêu tự do, thích khám phá. Dáng cao, hông và đùi nở nang.</li>
<li><strong>Ma Kết:</strong> Thực tế, kỷ luật, có tham vọng. Xương nhỏ, dáng thấp, khuôn mặt góc cạnh.</li>
<li><strong>Bảo Bình:</strong> Độc đáo, nhân đạo, thích đổi mới. Dáng cao, đặc điểm khác thường, phong cách riêng.</li>
<li><strong>Song Ngư:</strong> Mơ mộng, nghệ thuật, đồng cảm. Mắt to, mơ màng, bàn chân nhỏ.</li>
</ul>
<p>👉 <strong>Bạn muốn biết Cung Mọc của mình là gì và nó ảnh hưởng ra sao?</strong> Hãy <a href="/vedic-chart"><strong>tạo bản đồ sao ngay</strong></a> – chỉ mất 2 phút để khám phá!</p>
<p>Tham gia <a href="https://t.me/votiveacademy">Telegram Votive Academy</a> để thảo luận cùng cộng đồng yêu thích chiêm tinh.</p>
"""
    },
    {
        "title": "Sự khác biệt giữa Chiêm tinh Vệ Đà và Chiêm tinh Phương Tây: Bạn nên chọn ai?",
        "tags": ["vedic", "chiemtinh", "kienthuc"],
        "slug_prefix": "vedic-vs-western-astrology",
        "content_template": """
<p>Có một câu hỏi mà bất kỳ ai mới tìm hiểu chiêm tinh đều từng đặt ra: <strong>"Chiêm tinh Vệ Đà và Chiêm tinh Phương Tây khác nhau thế nào? Tôi nên theo trường phái nào?"</strong></p>
<h2>Khác biệt 1: Hệ thống cung hoàng đạo</h2>
<p><strong>Đây là khác biệt lớn nhất và gây ra nhiều nhầm lẫn nhất.</strong> Chiêm tinh Phương Tây sử dụng <strong>cung nhiệt đới (Tropical)</strong>, dựa trên vị trí của Mặt Trời so với Trái Đất. Chiêm tinh Vệ Đà sử dụng <strong>cung thiên văn (Sidereal)</strong>, dựa trên vị trí thực tế của các chòm sao trên bầu trời.</p>
<p>Vì hiện tượng <strong>tuế sai (precession)</strong> của Trái Đất, hai hệ thống này hiện tại lệch nhau khoảng <strong>24 độ</strong> – tương đương gần một cung hoàng đạo! Điều này có nghĩa là nếu bạn là Song Tử theo chiêm tinh Phương Tây, bạn có thể là Kim Ngưu theo chiêm tinh Vệ Đà.</p>
<h2>Khác biệt 2: Hành tinh sử dụng</h2>
<p>Chiêm tinh Phương Tây sử dụng cả ba hành tinh ngoài: <strong>Thiên Vương, Hải Vương và Diêm Vương</strong> (được phát hiện sau thế kỷ 18). Chiêm tinh Vệ Đà chỉ sử dụng <strong>9 Graha (hành tinh)</strong> bao gồm: Mặt Trời, Mặt Trăng, Sao Hỏa, Sao Thủy, Sao Mộc, Sao Kim, Sao Thổ, Rahu (La Hầu) và Ketu (Kế Đô) – những hành tinh và điểm đã được biết đến từ thời cổ đại.</p>
{case_study}
<h2>Khác biệt 3: Phương pháp luận giải</h2>
<ul>
<li><strong>Chiêm tinh Vệ Đà:</strong> Sử dụng hệ thống Dasha (các chu kỳ hành tinh) chi tiết, đặc biệt là Vimshottari Dasha 120 năm, cho phép dự đoán chính xác thời điểm xảy ra sự kiện.</li>
<li><strong>Chiêm tinh Phương Tây:</strong> Tập trung vào các góc chiếu (aspects) và quá cảnh (transits), ít sử dụng các hệ thống dự đoán thời gian chi tiết.</li>
<li><strong>Vệ Đà:</strong> Chú trọng đến Nakshatra (27 chòm sao Mặt Trăng) – một hệ thống sao chi tiết không có trong chiêm tinh Phương Tây.</li>
<li><strong>Vệ Đà:</strong> Xem nặng vai trò của nghiệp (karma) và sự tái sinh, trong khi chiêm tinh Phương Tây tập trung vào tâm lý học và sự phát triển cá nhân.</li>
</ul>
<h2>Bạn nên chọn hệ thống nào?</h2>
<p>Câu trả lời là: <strong>cả hai đều có giá trị riêng</strong>. Chiêm tinh Phương Tây có thế mạnh về phân tích tâm lý, trong khi Vệ Đà có thế mạnh về dự đoán sự kiện và thời điểm. Nếu bạn muốn biết <strong>"chuyện gì sẽ xảy ra và khi nào"</strong> – Vệ Đà là lựa chọn tốt hơn. Nếu bạn muốn hiểu <strong>"tại sao tôi lại như thế này"</strong> – cả hai đều hữu ích.</p>
<p>👉 <strong>Khám phá bản đồ sao Vệ Đà của bạn ngay hôm nay!</strong> <a href="/vedic-chart"><strong>Tạo bản đồ sao miễn phí</strong></a> – bạn sẽ ngạc nhiên vì sự chính xác của nó.</p>
"""
    },
    {
        "title": "Nakshatra: 27 chòm sao Mặt Trăng và ảnh hưởng sâu sắc đến tính cách của bạn",
        "tags": ["vedic", "chiemtinh", "kienthuc", "numerology"],
        "slug_prefix": "nakshatra-guide",
        "content_template": """
<p>Một trong những điểm độc đáo nhất của Chiêm tinh Vệ Đà mà không có trong bất kỳ hệ thống chiêm tinh nào khác là <strong>Nakshatra – 27 chòm sao Mặt Trăng</strong>.</p>
<p>Trong khi chiêm tinh phương Tây chỉ dừng lại ở 12 cung hoàng đạo, Vệ Đà chia bầu trời thành 27 phần bằng nhau (mỗi phần 13°20'), mỗi phần là một Nakshatra với <strong>ý nghĩa tâm linh và biểu tượng riêng</strong>.</p>
<h2>Vị trí của Mặt Trăng quyết định Nakshatra của bạn</h2>
<p>Nakshatra được xác định bởi vị trí của <strong>Mặt Trăng (Chandra)</strong> tại thời điểm bạn sinh ra. Trong Vệ Đà, vị trí của Mặt Trăng quan trọng đến nỗi nhiều nhà chiêm tinh coi nó <strong>ngang hàng với Cung Mọc</strong> trong việc quyết định tính cách và số phận.</p>
<h2>27 Nakshatra và 4 Mục tiêu Cuộc đời (Purusharthas)</h2>
<p>27 Nakshatra được chia thành 4 nhóm lớn, mỗi nhóm tương ứng với một mục tiêu cuộc đời:</p>
<ul>
<li><strong>Dharma (sứ mệnh):</strong> Ashwini, Magha, Mula — Những người này sinh ra để dẫn dắt và bảo vệ</li>
<li><strong>Artha (vật chất):</strong> Bharani, Purva Phalguni, Purva Ashadha — Năng lượng hướng đến tài chính và thành tựu</li>
<li><strong>Kama (đam mê):</strong> Krittika, Uttara Phalguni, Uttara Ashadha — Sáng tạo, tình yêu và tận hưởng</li>
<li><strong>Moksha (giải thoát):</strong> Rohini, Hasta, Shravana — Tâm linh và tìm kiếm chân lý</li>
</ul>
{case_study}
<h2>Một số Nakshatra đặc biệt</h2>
<ul>
<li><strong>Ashwini (Kinh Độ 0°–13°20' Bạch Dương):</strong> Cai quản bởi Ketu. Nhanh nhẹn, chữa lành, khởi đầu mới. Những người nổi tiếng như các bác sĩ, nhà tiên phong.</li>
<li><strong>Rohini (10°–23°20' Kim Ngưu):</strong> Cai quản bởi Mặt Trăng. Sáng tạo, cuốn hút, nhưng dễ bị chi phối bởi vật chất.</li>
<li><strong>Mrigashira (23°20' Kim Ngưu – 6°40' Song Tử):</strong> Cai quản bởi Sao Hỏa. Tò mò, thích tìm kiếm, thường có cuộc sống phiêu lưu.</li>
<li><strong>Magha (0°–13°20' Sư Tử):</strong> Cai quản bởi Ketu. Uy nghi, quyền lực, gắn liền với tổ tiên và dòng dõi.</li>
<li><strong>Shravana (10°–23°20' Ma Kết):</strong> Cai quản bởi Mặt Trăng. Lắng nghe, học hỏi, kết nối tâm linh.</li>
</ul>
<p>👉 <strong>Bạn muốn biết Nakshatra của mình và nó ảnh hưởng thế nào đến cuộc sống của bạn?</strong> <a href="/vedic-chart"><strong>Tạo bản đồ sao ngay</strong></a> để khám phá! Và đừng quên theo dõi các dự báo theo Nakshatra trên kênh <a href="https://patreon.com/VotiveAstrology">Patreon</a> của chúng tôi.</p>
"""
    },
]

# ============================================================

class BlogPublisher:
    def __init__(self):
        self.birth_data = self._load_birth_chart_data()
        self.state = self._load_state()

    def _load_birth_chart_data(self):
        """Load birth chart data for case studies"""
        records = []
        try:
            with open(BIRTH_CHART_CSV, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    records.append(row)
        except FileNotFoundError:
            print(f"⚠️  Birth chart CSV not found at {BIRTH_CHART_CSV}")
            return []
        print(f"📊 Loaded {len(records)} birth chart records for case studies")
        return records

    def _load_state(self):
        """Load publishing state"""
        default = {
            "published_posts": [],
            "series_counter": [0, 0, 0],  # how many posts published per series
            "last_publish": None
        }
        try:
            with open(STATE_FILE, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return default

    def _save_state(self):
        with open(STATE_FILE, 'w') as f:
            json.dump(self.state, f, indent=2, ensure_ascii=False)

    def _random_case_study(self):
        """Pick random birth chart record for an anonymous case study"""
        if len(self.birth_data) < 10:
            return ""
        r = random.choice(self.birth_data)
        age = self._calc_age(r.get("birth_date", ""))
        name = r.get("name", "Một khách hàng")
        location = r.get("location", "Việt Nam")
        return f"""
<div style="background:#f9f6ff;padding:15px;border-radius:10px;margin:20px 0;border-left:4px solid #7c5cbf">
<p><strong>📖 Case Study từ Votive Academy:</strong></p>
<p>Một khách hàng của Votive Academy (sinh ngày {r.get("birth_date", "N/A")}), hiện {age} tuổi, sống tại {location}, đã đến với chúng tôi trong giai đoạn gặp nhiều khó khăn. Sau khi <a href="/vedic-chart">phân tích bản đồ sao</a>, chúng tôi phát hiện vị trí đặc biệt của các hành tinh trong lá số, và từ đó đưa ra những lời khuyên giúp khách hàng vượt qua giai đoạn khó khăn và tìm lại hướng đi đúng đắn.</p>
<p><em>(Thông tin đã được ẩn danh để bảo vệ quyền riêng tư)</em></p>
</div>"""

    def _case_study_from_data(self, planet_house=None):
        """Generate a case study referencing specific planetary position"""
        if len(self.birth_data) < 10:
            return ""
        r = random.choice(self.birth_data)
        name = r.get("name", "một khách hàng")
        age = self._calc_age(r.get("birth_date", ""))
        if not planet_house:
            return self._random_case_study()
        return f"""
<div style="background:#f9f6ff;padding:15px;border-radius:10px;margin:20px 0;border-left:4px solid #7c5cbf">
<p><strong>📖 Case Study từ Votive Academy:</strong></p>
<p>{name}, {age} tuổi, có {planet_house} trong bản đồ sao. Sau nhiều năm loay hoay không hiểu tại sao cuộc sống cứ lặp đi lặp lại một mô hình, {name} đã tìm đến Votive Academy để <a href="/vedic-chart">phân tích lá số</a>. Nhận ra bài học nghiệp quả, {name} đã thay đổi cách tiếp cận và dần dần vượt qua được những khó khăn kéo dài.</p>
<p><em>(Thông tin đã được ẩn danh)</em></p>
</div>"""

    def _calc_age(self, birth_str):
        if not birth_str:
            return "N/A"
        try:
            b = datetime.strptime(birth_str[:10], "%Y-%m-%d")
            return (datetime.now() - b).days // 365
        except:
            return "N/A"

    def _get_age_stat_section(self):
        """Return audience statistics section"""
        return f"""
<div style="background:#eef9ff;padding:15px;border-radius:10px;margin:20px 0;border-left:4px solid #3498db">
<p><strong>📊 Từ dữ liệu thực tế:</strong> Trong số hơn 10,000 lá số mà Votive Academy đã thu thập, nhóm tuổi 25-34 chiếm đến <strong>27.7%</strong> – đây cũng chính là độ tuổi thường trải qua khủng hoảng hiện sinh và tìm đến chiêm tinh như một công cụ để thấu hiểu bản thân. Điều này cho thấy nhu cầu về chiêm tinh ứng dụng để giải quyết các vấn đề thực tế là rất lớn.</p>
</div>"""

    def _get_slug(self, prefix, index):
        """Generate unique slug"""
        base = re.sub(r'[^a-z0-9-]', '', prefix.lower().replace(' ', '-'))
        return f"{base}-{index}"

    def _publish_post(self, post_data, dry_run=True):
        """Publish a single post to Supabase"""
        headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Prefer": "return=representation"
        }

        if dry_run:
            print(f"\n🔍 [DRY-RUN] Would publish:")
            print(f"   Title: {post_data['title']}")
            print(f"   Slug: {post_data['slug']}")
            print(f"   Tags: {post_data['tags']}")
            print(f"   Content length: {len(post_data['content'])} chars")
            return True

        try:
            data = json.dumps(post_data).encode('utf-8')
            req = urllib.request.Request(
                f"{SUPABASE_URL}/rest/v1/{TABLE_NAME}",
                data=data,
                headers=headers,
                method="POST"
            )
            with urllib.request.urlopen(req) as resp:
                result = json.loads(resp.read().decode())
                print(f"✅ Published: {post_data['title']}")
                print(f"   ID: {result[0]['id'] if isinstance(result, list) else 'N/A'}")
                return True
        except urllib.error.HTTPError as e:
            body = e.read().decode()
            print(f"❌ HTTP {e.code}: {body}")
            return False
        except Exception as e:
            print(f"❌ Error: {e}")
            return False

    def generate_post(self, series_num, index, template_data):
        """Generate a full blog post from template"""
        tpl = template_data.copy()
        content = tpl["content_template"]

        # Inject case studies / statistics
        content = content.replace("{case_study}", self._random_case_study())
        content = content.replace("{case_study_rahu}", self._case_study_from_data("Rahu ở Nhà 7"))
        content = content.replace("{case_study_ketu}", self._case_study_from_data("Ketu ở Nhà 7"))
        content = content.replace("{age_stat_section}", self._get_age_stat_section())
        content = content.replace("{h2h_section}", "")
        content = content.replace("{case_study_saturn}", self._case_study_from_data("Sao Thổ ở Nhà 10"))

        # Build excerpt (first ~150 chars of content, strip tags)
        excerpt_text = re.sub(r'<[^>]+>', '', content[:300]).strip()
        excerpt = excerpt_text[:150] + "..." if len(excerpt_text) > 150 else excerpt_text

        now = datetime.now(VN_TZ)
        slug = self._get_slug(tpl["slug_prefix"], index)

        # Cycle through a few default images based on series
        default_images = {
            1: [
                "https://qzyyiqzekduduoscdwjc.supabase.co/storage/v1/object/public/blog-images/vedic-saturn-career.png",
                "https://qzyyiqzekduduoscdwjc.supabase.co/storage/v1/object/public/blog-images/vedic-relationship.png",
            ],
            2: [
                "https://qzyyiqzekduduoscdwjc.supabase.co/storage/v1/object/public/blog-images/vedic-jupiter-transit.png",
                "https://qzyyiqzekduduoscdwjc.supabase.co/storage/v1/object/public/blog-images/vedic-eclipse.png",
            ],
            3: [
                "https://qzyyiqzekduduoscdwjc.supabase.co/storage/v1/object/public/blog-images/vedic-lagna.png",
                "https://qzyyiqzekduduoscdwjc.supabase.co/storage/v1/object/public/blog-images/vedic-nakshatra.png",
            ],
        }
        img_list = default_images.get(series_num, ["https://qzyyiqzekduduoscdwjc.supabase.co/storage/v1/object/public/blog-images/vedic-default.png"])
        image_url = img_list[index % len(img_list)]

        post = {
            "title": tpl["title"],
            "content": content,
            "excerpt": excerpt,
            "slug": slug,
            "author": "Votive Academy",
            "date": now.isoformat(),
            "image_url": image_url,
            "tags": tpl["tags"],
        }
        return post

    def publish_series_post(self, series_num, post_index, dry_run=True):
        """Publish the nth post in a series"""
        series_map = {1: SERIES1, 2: SERIES2, 3: SERIES3}
        series = series_map.get(series_num)
        if not series:
            print(f"❌ Invalid series: {series_num}")
            return False

        template = series[post_index % len(series)]
        post = self.generate_post(series_num, post_index, template)

        success = self._publish_post(post, dry_run)
        if success and not dry_run:
            self.state["published_posts"].append({
                "series": series_num,
                "title": post["title"],
                "slug": post["slug"],
                "published_at": datetime.now(VN_TZ).isoformat()
            })
            self.state["series_counter"][series_num - 1] += 1
            self.state["last_publish"] = datetime.now(VN_TZ).isoformat()
            self._save_state()
        return success

    def publish_next(self, dry_run=True):
        """Publish the next due post (round-robin across series)"""
        # Find which series is due (lowest count gets next post)
        counts = self.state["series_counter"]
        min_count = min(counts)
        candidates = [i for i, c in enumerate(counts) if c == min_count]
        series_num = random.choice(candidates) + 1  # 1-indexed

        post_index = counts[series_num - 1]
        print(f"\n{'='*60}")
        print(f"📝 Publishing Series {series_num} — Post #{post_index + 1}")
        print(f"{'='*60}")
        return self.publish_series_post(series_num, post_index, dry_run)

    def show_status(self):
        """Show publishing calendar and state"""
        print(f"\n{'='*60}")
        print(f"📋 BLOG PUBLISHING STATUS")
        print(f"{'='*60}")
        total_series_posts = sum(len(s) for s in [SERIES1, SERIES2, SERIES3])
        print(f"\n📦 Templates: {total_series_posts} post templates ({len(SERIES1)} S1 + {len(SERIES2)} S2 + {len(SERIES3)} S3)")

        series_names = [
            "Tuyến 1: Chiêm tinh giải quyết vấn đề",
            "Tuyến 2: Bản tin Thời không",
            "Tuyến 3: Kiến thức nền tảng Vedic"
        ]
        for i, (sn, tpls) in enumerate(zip(series_names, [SERIES1, SERIES2, SERIES3])):
            c = self.state["series_counter"][i]
            print(f"\n  {sn}")
            print(f"    Published: {c} | Remaining templates: {len(tpls)}")
            for j, t in enumerate(tpls):
                marker = "✅" if any(p["title"] == t["title"] for p in self.state["published_posts"]) else "⬜"
                print(f"    {marker} [{j+1}] {t['title'][:60]}...")

        total = sum(self.state["series_counter"])
        print(f"\n📊 Total published: {total}")
        print(f"📅 Last publish: {self.state.get('last_publish', 'Never')}")
        print(f"📁 Database: {len(self.birth_data)} birth chart records available for case studies")
        print()

    def publish_batch(self, count=3, dry_run=True):
        """Publish multiple posts in sequence"""
        success = 0
        for i in range(count):
            if self.publish_next(dry_run):
                success += 1
            if dry_run:
                break  # Only show one in dry-run
        print(f"\n📊 Batch complete: {success}/{count} posts {'would be published' if dry_run else 'published'}")
        return success

    def publish_series_complete(self, series_num, dry_run=True):
        """Publish all posts in a series"""
        series_map = {1: SERIES1, 2: SERIES2, 3: SERIES3}
        series = series_map.get(series_num)
        if not series:
            return False

        success = 0
        for i in range(len(series)):
            if self.publish_series_post(series_num, i, dry_run):
                success += 1
            if dry_run:
                break
        return success


def main():
    publisher = BlogPublisher()

    if "--status" in sys.argv:
        publisher.show_status()
        return

    dry_run = "--run" not in sys.argv

    if "--init" in sys.argv:
        print(f"\n🚀 INIT MODE: Publishing first batch of posts...")
        publisher.publish_batch(count=3, dry_run=dry_run)
        return

    if "--series" in sys.argv:
        idx = sys.argv.index("--series")
        series_num = int(sys.argv[idx + 1])
        publisher.publish_series_complete(series_num, dry_run=dry_run)
        return

    if "--all" in sys.argv:
        for s in [1, 2, 3]:
            publisher.publish_series_complete(s, dry_run=dry_run)
        return

    # Default: publish next due post
    publisher.publish_next(dry_run=dry_run)


if __name__ == "__main__":
    main()
