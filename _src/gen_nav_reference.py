#!/usr/bin/env python3
"""Paket referans sayfalarını üretir: AMCL/move_base, costmap_2d, gmapping/map_server, twist_mux/ira_laser_tools.

Veri kaynağı: _src/data/nav_stack_verified.json (ROS Noetic kaynak kodundan ve kurulu
paketlerin dynamic_reconfigure tanımlarından çıkarıldı; bkz. dosyanın "_kaynak" alanı).
Bu dosyadaki GROUPS listeleri açıklamaları taşır; parametre var mı/adı doğru mu diye
JSON'a karşı denetlenir (table() bunu doğrular, eksik/fazlayı hata olarak keser).

Kullanım:  python3 _src/gen_nav_reference.py && python3 _src/build.py
"""
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = json.loads((ROOT / "_src" / "data" / "nav_stack_verified.json").read_text(encoding="utf-8"))
PAGES = ROOT / "_src" / "pages"

INF = float("inf")


def fmt(v):
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, str):
        return v if v.startswith('"') or " " in v or "(" in v else f'"{v}"'
    if v is None:
        return "—"
    if isinstance(v, (int, float)):
        return "%g" % v
    return str(v)


def rng(row):
    typ, lo, hi = row[1], row[3], row[4]
    if typ in ("bool", "string", "list"):
        return "—"
    if lo is None and hi is None:
        return "—"
    return f"{fmt(lo) if lo is not None else '−∞'} … {fmt(hi) if hi is not None else '∞'}"


def md_code(text):
    """`kod` → <code>, **kalın** → <strong>."""
    out, parts = [], html.escape(text).split("`")
    for i, part in enumerate(parts):
        out.append(f"<code>{part}</code>" if i % 2 else part)
    return re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", "".join(out))


def table(prefix, key, groups, extra_names=()):
    """groups: [(başlık, giriş, [(ad, açıklama), ...]), ...]. JSON'daki her satır kullanılmalı."""
    rows = {r[0]: r for r in DATA[key]}
    used = set()
    parts = []
    for gname, gintro, items in groups:
        trs = []
        for name, desc in items:
            used.add(name)
            if name not in rows:
                raise SystemExit(f"JSON'da yok: {key}/{name}")
            r = rows[name]
            trs.append(
                f'<tr id="{prefix}-{name}"><td><code>{html.escape(name)}</code></td>'
                f'<td>{html.escape(r[1])}</td><td class="n"><code>{html.escape(fmt(r[2]))}</code></td>'
                f'<td class="n">{html.escape(rng(r))}</td><td>{md_code(desc)}</td></tr>'
            )
        parts.append(
            f"<h3>{html.escape(gname)}</h3>\n<p>{md_code(gintro)}</p>\n"
            '<div class="tw ptab"><table><thead><tr><th>Parametre</th><th>Tür</th><th class="n">Varsayılan</th>'
            '<th class="n">Aralık</th><th>Açıklama</th></tr></thead><tbody>\n' + "\n".join(trs) + "\n</tbody></table></div>"
        )
    missing = set(rows) - used - set(extra_names)
    if missing:
        raise SystemExit(f"Açıklaması yazılmamış: {key}/{sorted(missing)}")
    return "\n".join(parts), len(used)


# ============================================================= AMCL
AMCL_GROUPS = [
    ("Genel ve çerçeveler", "AMCL'in hangi çerçeveleri kullandığı ve haritayı nasıl aldığı.", [
        ("odom_frame_id", "Odometri çerçevesinin adı."),
        ("base_frame_id", "Robot gövdesinin çerçeve adı."),
        ("global_frame_id", "AMCL'in yayınladığı konum çerçevesinin adı (genelde `map`)."),
        ("use_map_topic", "true ise harita `/map` topic'inden dinlenir; false ise `static_map` servisiyle bir kez istenir."),
        ("first_map_only", "true ise yalnızca ilk gelen harita kullanılır, sonraki `/map` güncellemeleri yok sayılır."),
        ("tf_broadcast", "false yaparsan AMCL `map→odom` dönüşümünü yayınlamaz; bunu başka bir node'un yapması gerekir."),
    ]),
    ("Başlangıç konumu", "Parçacık filtresinin ilk dağılımı bu konum etrafında (Gauss dağılımıyla) kurulur.", [
        ("initial_pose_x", "Başlangıç konumu, x (m)."),
        ("initial_pose_y", "Başlangıç konumu, y (m)."),
        ("initial_pose_a", "Başlangıç yönü, yaw (rad)."),
        ("initial_cov_xx", "Başlangıç konumunun x yönündeki belirsizliği (varyans, m²)."),
        ("initial_cov_yy", "Başlangıç konumunun y yönündeki belirsizliği (varyans, m²)."),
        ("initial_cov_aa", "Başlangıç yönünün belirsizliği (varyans, rad²)."),
    ]),
    ("Parçacık filtresi (KLD örnekleme)", "AMCL, konumu sabit sayıda değil, \"yeterince iyi temsil edene kadar\" değişen sayıda parçacıkla arar (KLD örnekleme).", [
        ("min_particles", "En az parçacık sayısı."),
        ("max_particles", "En çok parçacık sayısı. Büyütmek daha güvenilir ama daha yavaş."),
        ("kld_err", "Gerçek dağılımla örneklenen dağılım arasına izin verilen maksimum hata."),
        ("kld_z", "1 − p için üst standart normal kuantili; p, örneklenen dağılımın hatasının `kld_err`'ün altında kalma olasılığıdır."),
        ("resample_interval", "Kaç filtre güncellemesinde bir yeniden örnekleme (resampling) yapılacağı."),
        ("selective_resampling", "true ise etkin örnek büyüklüğü (ESS) düşük olmadıkça yeniden örnekleme atlanır; parçacık çeşitliliğini korur."),
        ("recovery_alpha_slow", "Yavaş hareketli ortalama ağırlık filtresinin üstel azalma oranı. `recovery_alpha_fast` ile birlikte, ölçüm uyumu ani düştüğünde (robot kaçırıldığında ya da kaybolduğunda) rastgele parçacık ekleyip eklemeyeceğine karar verir. Kurtarmayı kapatmak için ikisini de 0 yap; yalnızca birini 0 yapmak kapatmaz. Node başlarken bu kaynak kod varsayılanı geçerlidir; dinamik ayar tanımındaki varsayılan ise 0'dır, bu yüzden `rqt_reconfigure`'da Restore defaults kurtarmayı kapatır."),
        ("recovery_alpha_fast", "Hızlı hareketli ortalama ağırlık filtresinin üstel azalma oranı; `recovery_alpha_slow`'dan büyük olmalı. Kısa vadeli ortalama uzun vadeliden düştükçe o oranda rastgele parçacık eklenir. Kurtarmayı kapatmak için ikisini de 0 yap. Node başlarken bu kaynak kod varsayılanı geçerlidir; dinamik ayar tanımındaki varsayılan ise 0'dır, bu yüzden `rqt_reconfigure`'da Restore defaults kurtarmayı kapatır."),
    ]),
    ("Hareket (odometri) modeli", "Robot hareket ettikçe parçacıkların nasıl \"yayılacağını\" (belirsizleşeceğini) tanımlar.", [
        ("odom_model_type", "Sürüş modeli: `diff`, `omni`, `diff-corrected`, `omni-corrected`. `-corrected` türleri eski modellerdeki bir hatanın düzeltilmiş halidir; `odom_alphaN` varsayılanları eski modele göredir, düzeltilmiş modelde genelde daha küçük değerler gerekir."),
        ("odom_alpha1", "Dönüş hareketinden kaynaklanan dönüş gürültüsü tahmini."),
        ("odom_alpha2", "Öteleme hareketinden kaynaklanan dönüş gürültüsü tahmini."),
        ("odom_alpha3", "Öteleme hareketinden kaynaklanan öteleme gürültüsü tahmini."),
        ("odom_alpha4", "Dönüş hareketinden kaynaklanan öteleme gürültüsü tahmini."),
        ("odom_alpha5", "Yalnızca `omni` modelinde: hareket yönüne dik öteleme eğilimi gürültüsü."),
        ("update_min_d", "Bir filtre güncellemesi için robotun kat etmesi gereken en az mesafe (m)."),
        ("update_min_a", "Bir filtre güncellemesi için robotun dönmesi gereken en az açı (rad)."),
        ("transform_tolerance", "Yayınlanan `map→odom` dönüşümünün ne kadar ileri bir zamana \"damgalanacağı\" (sn); TF sorgularının küçük gecikmelerde başarısız olmamasını sağlar."),
    ]),
    ("Lazer (algı) modeli", "Bir parçacığın ne kadar \"doğru\" olduğu, o parçacığın konumundan beklenen taramayla gerçek taramanın ne kadar örtüştüğüne bakılarak puanlanır.", [
        ("laser_model_type", "Model: `beam`, `likelihood_field` (varsayılan, daha hızlı) ya da `likelihood_field_prob`."),
        ("laser_min_range", "Dikkate alınacak en küçük tarama mesafesi; −1,0 lazerin kendi bildirdiği minimumu kullanır."),
        ("laser_max_range", "Dikkate alınacak en büyük tarama mesafesi; −1,0 lazerin kendi bildirdiği maksimumu kullanır."),
        ("laser_max_beams", "Her taramadan puanlama için kaç ışının kullanılacağı (eşit aralıklı örnekleme). Azaltmak hesap yükünü düşürür."),
        ("laser_z_hit", "Ölçümün haritadaki gerçek bir engele isabet etmesini temsil eden bileşenin karışım ağırlığı (üç modelde de kullanılır)."),
        ("laser_z_short", "Ölçümün beklenenden daha kısa çıkma (beklenmeyen engel) olasılığının ağırlığı; yalnızca `beam` modelinde kullanılır."),
        ("laser_z_max", "Ölçümün menzil sonuna takılma (maksimum mesafe) olasılığının ağırlığı; yalnızca `beam` modelinde kullanılır."),
        ("laser_z_rand", "Rastgele/açıklanamayan ölçüm olasılığının ağırlığı."),
        ("laser_sigma_hit", "`z_hit` bileşeni için Gauss modelinin standart sapması (m)."),
        ("laser_lambda_short", "`z_short` bileşeni için üstel dağılımın parametresi; yalnızca `beam` modelinde kullanılır."),
        ("laser_likelihood_max_dist", "`likelihood_field` modelinde, harita üzerinde önceden hesaplanacak en büyük engel mesafesi (m)."),
        ("do_beamskip", "Yalnızca `likelihood_field_prob` modelinde ve filtre yakınsadıktan sonra: parçacıkların çoğunda haritayla uyuşmayan ışınlar (ör. dinamik engeller) puanlamadan atlanır."),
        ("beam_skip_distance", "Bir ışının bir parçacık için haritayla \"uyuşuyor\" sayılması için, ölçülen noktanın haritadaki en yakın engele olan uzaklığı bundan (m) küçük olmalı."),
        ("beam_skip_threshold", "Bir ışının kullanılması için, o ışının haritayla uyuştuğu parçacıkların oranı bu değerden büyük olmalı; değilse ışın atlanır."),
        ("beam_skip_error_threshold", "Atlanan ışınların oranı bu değere ulaşırsa filtre muhtemelen yanlış konuma yakınsamıştır: AMCL bir uyarı basar ve o taramada ışın atlamadan tüm ışınları kullanır."),
    ]),
    ("Yayın ve tanılama", "Görselleştirme, kayıt ve uyarı hızları.", [
        ("gui_publish_rate", "Görselleştirme mesajlarının yayın hızı (Hz); −1,0 kapalı demektir."),
        ("save_pose_rate", "Son tahmini konumun parametre sunucusuna kaydedilme hızı (Hz); sonraki açılışta başlangıç konumu olarak kullanılabilir. −1,0 kapalı demektir."),
        ("std_warn_level_x", "Konum belirsizliğinin (std sapma, m) x'te bu değeri aşması durumda uyarı loglanır."),
        ("std_warn_level_y", "Konum belirsizliğinin (std sapma, m) y'de bu değeri aşması durumda uyarı loglanır."),
        ("std_warn_level_yaw", "Yön belirsizliğinin (std sapma, rad) bu değeri aşması durumda uyarı loglanır."),
        ("force_update_after_initialpose", "true ise `initialpose` mesajı gelir gelmez (hareket beklemeden) bir filtre güncellemesi zorlanır."),
        ("force_update_after_set_map", "true ise yeni harita geldiğinde (hareket beklemeden) bir filtre güncellemesi zorlanır."),
        ("bag_scan_period", "Yalnızca bag oynatırken: art arda taramalar arasına eklenecek gecikme (sn); −1,0 kapalı demektir."),
    ]),
]

# ============================================================= move_base
MOVEBASE_GROUPS = [
    ("Planlayıcı seçimi", "move_base kendisi bir planlayıcı içermez; global ve yerel planlayıcıyı eklenti (plugin) olarak yükler.", [
        ("base_global_planner", "Global planlayıcı eklentisinin adı. Alternatifler: `global_planner/GlobalPlanner`, `carrot_planner/CarrotPlanner`."),
        ("base_local_planner", "Yerel planlayıcı eklentisinin adı (ör. `dwa_local_planner/DWAPlannerROS`, `teb_local_planner/TebLocalPlannerROS`). Varsayılan, eski ve artık önerilmeyen `TrajectoryPlannerROS`'tur."),
        ("recovery_behaviors", "Sırayla denenecek toparlanma eklentileri. Verilmezse 4 adımlı varsayılan liste kullanılır: hafif costmap temizliği (kenarı `conservative_reset_dist` olan karenin dışı) → yerinde dönme → agresif costmap temizliği (kenarı çevrelenmiş yarıçapın 4 katı olan karenin dışı) → tekrar yerinde dönme. `clearing_rotation_allowed: false` iken iki dönme adımı atlanır."),
        ("recovery_behavior_enabled", "Toparlanma davranışlarını tamamen açar/kapatır."),
        ("clearing_rotation_allowed", "Yalnızca varsayılan toparlanma listesi kullanılıyorken: takılınca yerinde dönme denenip denenmeyeceği."),
    ]),
    ("Döngü hızları ve sabır", "Planlayıcıların ne sıklıkla çalıştığı ve ne kadar \"sabırlı\" olunacağı.", [
        ("planner_frequency", "Global planın yenilenme hızı (Hz). 0 ise yalnızca yeni hedef geldiğinde ya da yerel planlayıcı yolun tıkandığını bildirdiğinde çalışır."),
        ("controller_frequency", "Yerel planlayıcının çalışma ve `/cmd_vel` üretme hızı (Hz)."),
        ("planner_patience", "Global planlayıcı geçerli bir plan bulamazsa, toparlanma davranışlarına geçmeden önce ne kadar (sn) denemeye devam edileceği."),
        ("controller_patience", "Yerel planlayıcı geçerli bir kontrol bulamazsa, toparlanma davranışlarına geçmeden önce ne kadar (sn) denemeye devam edileceği. Node başlarken bu kaynak kod varsayılanı (15) geçerlidir; dinamik ayar tanımındaki varsayılan ise 5'tir, `rqt_reconfigure`'da \"Restore defaults\" değeri 5'e çeker."),
        ("max_planning_retries", "Toparlanma davranışlarına geçmeden önce global planlayıcının kaç kez yeniden çağrılacağı; −1 sınırsız demektir."),
    ]),
    ("Salınım algılama", "Robot aynı bölgede ileri geri gidip geliyorsa (salınım) bunu algılayıp toparlanmaya geçer.", [
        ("oscillation_timeout", "Salınım sayılmadan önce izin verilen süre (sn); 0 bu denetimi kapatır."),
        ("oscillation_distance", "Salınım sayaçlarının sıfırlanması için robotun kat etmesi gereken en az mesafe (m)."),
    ]),
    ("Costmap ve plan servisleri", "`~make_plan` servisi ve costmap temizleme davranışıyla ilgili ayarlar.", [
        ("shutdown_costmaps", "true ise move_base etkin olmadığı sürelerde costmap'leri kapatıp kaynak tasarrufu yapar."),
        ("conservative_reset_dist", "Varsayılan \"hafif\" toparlanma davranışının `reset_distance`'ı: robot merkezli, kenarı bu uzunlukta (m) bir karenin dışındaki engeller temizlenir (varsayılanla robottan ±1,5 m ötesi)."),
        ("make_plan_clear_costmap", "`~make_plan` servisi çağrıldığında global costmap'i temizleyip temizlemeyeceği."),
        ("make_plan_add_unreachable_goal", "Hedefe ulaşılamıyorsa, `~make_plan` servisinin döndürdüğü plana en azından orijinal hedefi ekleyip eklemeyeceği."),
        ("clearing_radius", "Yalnızca varsayılan toparlanma davranışında: robotun etrafında engellerin zorla temizleneceği yarıçap (m); varsayılanı costmap'in \"çevrelenmiş yarıçapı\"dır (footprint'i tamamen kapsayan daire)."),
    ]),
]

TEB_LINK = '<p>Yerel planlayıcıların (DWA, TEB) tüm parametreleri için ayrı sayfaya bak: <a href="planlayici-parametreleri.html">DWA ve TEB parametreleri</a>.</p>'

ROTATE_GROUPS = [
    ("rotate_recovery", "Robot takıldığında yerinde 360° dönerek costmap'i temizlemeye çalışan varsayılan toparlanma davranışı. Dönüş sırasında her açıda çarpışma denetimi yapılır; bir açıda takılırsa oraya kadar döner ve durur. İlk iki parametre davranışın kendi isim alanından (`~/<davranış_adı>/`, varsayılan listede `~/rotate_recovery/`) okunur. Diğer dördü ise, hangi yerel planlayıcıyı kullanırsan kullan, **`~/TrajectoryPlannerROS/`** isim alanından okunur: DWA ya da TEB kullanırken `DWAPlannerROS/max_vel_theta` vermek toparlanma dönüşünü sınırlamaz; ağır bir robotta bu değerleri `TrajectoryPlannerROS:` altında ayrıca yazmalısın.", [
        ("sim_granularity", "Dönüş sırasında çarpışma denetiminin açısal adım aralığı (rad)."),
        ("frequency", "Dönüş sırasında hız komutu üretme hızı (Hz)."),
        ("TrajectoryPlannerROS/yaw_goal_tolerance", "Dönüşün \"tamamlandı\" sayılması için izin verilen açı hatası (rad)."),
        ("TrajectoryPlannerROS/max_vel_theta", "Toparlanma dönüşünün en yüksek açısal hızı (rad/s). Eski adı `max_rotational_vel` da kabul edilir."),
        ("TrajectoryPlannerROS/min_in_place_vel_theta", "Toparlanma dönüşünün en düşük açısal hızı (rad/s). Eski adı `min_in_place_rotational_vel` da kabul edilir."),
        ("TrajectoryPlannerROS/acc_lim_theta", "Toparlanma dönüşünde açısal ivme sınırı (rad/s²); yavaşlamaya ne zaman başlanacağını belirler. Eski adı `acc_lim_th` da kabul edilir."),
    ]),
]
CLEAR_GROUPS = [
    ("clear_costmap_recovery", "Robottan uzaktaki costmap engellerini zorla temizleyen varsayılan toparlanma davranışı (\"hafif\" ve \"agresif\" sıfırlama bu davranışın iki farklı `reset_distance` ile örneğidir).", [
        ("reset_distance", "Robot merkezli, kenar uzunluğu bu değer (m) olan bir karenin dışındaki engeller temizlenir; yani robottan her eksende bu değerin yarısından uzak olanlar. `invert_area_to_clear: true` ise karenin içi temizlenir."),
        ("layer_names", "Temizlenecek costmap katmanlarının adları. Katman adı (`plugins` listesindeki `name`) bu listedeki bir adla **birebir** aynı olmalıdır. Varsayılan `obstacles` olduğundan, engel katmanını `obstacle_layer` gibi başka bir adla tanımladıysan varsayılan toparlanma davranışları **hiçbir şeyi temizlemez**; bu durumda `conservative_reset/layer_names` ve `aggressive_reset/layer_names`'i kendi katman adınla ver."),
        ("force_updating", "true ise temizlemeden sonra costmap güncellemesi beklenmeden devam edilir."),
        ("affected_maps", "Hangi costmap'in etkileneceği: `local`, `global` ya da `both`."),
        ("invert_area_to_clear", "true ise belirtilen alanın *dışı* temizlenir, içi değil."),
    ]),
]

amcl_html, amcl_n = table("amcl", "amcl", AMCL_GROUPS)
mb_html, mb_n = table("mb", "move_base", MOVEBASE_GROUPS)
rot_html, rot_n = table("rotr", "rotate_recovery", ROTATE_GROUPS)
clr_html, clr_n = table("clrr", "clear_costmap_recovery", CLEAR_GROUPS)

PAGE1 = f"""<section id="amcl-ref">
<h2>AMCL</h2>
<p><code>amcl</code>, bilinen bir harita üzerinde robotun konumunu bulan lokalizasyon node'udur (Adaptive Monte Carlo Localization). Kavramsal anlatımı için <a href="harita-ve-navigasyon.html#lokalizasyon">Lokalizasyon (AMCL)</a> bölümüne bak; burada <strong>{amcl_n} parametrenin tamamı</strong> var.</p>
<div class="call"><b>Bu sayfadaki değerler nereden geliyor?</b>
<p>Parametre adları ve varsayılanlar ROS Noetic'in <code>amcl</code> kaynak kodundan (<code>ros-planning/navigation</code>, bu makinede kurulu olan <code>1.17.3</code> sürümünün etiketi, <code>amcl_node.cpp</code>) çıkarıldı: her parametre, kodda okunduğu <code>nh.param(...)</code> çağrısından ve o çağrının varsayılan değerinden alındı. Bazı parametreler (belirtilenler) ayrıca çalışırken <code>rqt_reconfigure</code> ile değiştirilebilir.</p></div>
<h4>Abone olunan topic'ler</h4>
<div class="tw"><table><thead><tr><th>Ad</th><th>Tür</th></tr></thead><tbody>
<tr><td><code>scan</code></td><td><code>sensor_msgs/LaserScan</code></td></tr>
<tr><td><code>tf</code></td><td><code>tf2_msgs/TFMessage</code></td></tr>
<tr><td><code>initialpose</code></td><td><code>geometry_msgs/PoseWithCovarianceStamped</code></td></tr>
<tr><td><code>map</code></td><td><code>nav_msgs/OccupancyGrid</code> (yalnızca <code>use_map_topic: true</code> ise)</td></tr>
</tbody></table></div>
<h4>Yayınlanan topic'ler</h4>
<div class="tw"><table><thead><tr><th>Ad</th><th>Tür</th></tr></thead><tbody>
<tr><td><code>amcl_pose</code></td><td><code>geometry_msgs/PoseWithCovarianceStamped</code> — robotun harita üzerindeki tahmini konumu</td></tr>
<tr><td><code>particlecloud</code></td><td><code>geometry_msgs/PoseArray</code> — parçacık filtresinin o anki tüm konum tahminleri</td></tr>
<tr><td><code>tf</code> (<code>map→odom</code>)</td><td><code>tf2_msgs/TFMessage</code> — <code>tf_broadcast: true</code> iken</td></tr>
</tbody></table></div>
<h4>Sunulan servisler</h4>
<div class="tw"><table><thead><tr><th>Ad</th><th>Tür</th></tr></thead><tbody>
<tr><td><code>global_localization</code></td><td><code>std_srvs/Empty</code> — parçacıkları haritaya rastgele yeniden dağıtır (konumu tamamen bilmiyorsan)</td></tr>
<tr><td><code>request_nomotion_update</code></td><td><code>std_srvs/Empty</code> — robot hareket etmeden bir filtre güncellemesi zorlar</td></tr>
<tr><td><code>set_map</code></td><td><code>nav_msgs/SetMap</code> — haritayı ve başlangıç konumunu tek çağrıda ayarlar</td></tr>
</tbody></table></div>

{amcl_html}
</section>

<section id="move-base-ref">
<h2>move_base</h2>
<p><code>move_base</code>, global ve yerel planlayıcıları, costmap'leri ve toparlanma davranışlarını bir araya getiren üst düzey navigasyon action sunucusudur. Kavramsal anlatım için <a href="harita-ve-navigasyon.html#navigasyon">Navigasyon (move_base)</a> bölümüne bak; burada <strong>{mb_n} parametrenin tamamı</strong> ve iki varsayılan toparlanma davranışının parametreleri var.</p>
<h4>Action arayüzü</h4>
<div class="tw"><table><thead><tr><th>Ad</th><th>Tür</th></tr></thead><tbody>
<tr><td><code>move_base</code></td><td><code>move_base_msgs/MoveBaseAction</code> — goal: <code>geometry_msgs/PoseStamped</code>, result: boş, feedback: o anki konum</td></tr>
</tbody></table></div>
<h4>Diğer topic ve servisler</h4>
<div class="tw"><table><thead><tr><th>Ad</th><th>Tür</th></tr></thead><tbody>
<tr><td><code>move_base_simple/goal</code></td><td>abone, <code>geometry_msgs/PoseStamped</code> — sonucu izlemeden hızlıca hedef göndermek için (RViz'in <em>2D Nav Goal</em>'ı bunu kullanır)</td></tr>
<tr><td><code>~clear_costmaps</code></td><td>servis, <code>std_srvs/Empty</code> — costmap'lerdeki tüm engelleri temizler</td></tr>
<tr><td><code>~make_plan</code></td><td>servis, <code>nav_msgs/GetPlan</code> — robotu hareket ettirmeden bir plan hesaplar</td></tr>
</tbody></table></div>

{mb_html}
{TEB_LINK}

<h3>Toparlanma (recovery) davranışları</h3>
<p>Varsayılan <code>recovery_behaviors</code> listesi bu iki eklentiyi kullanır. Kendi listeni tanımlarsan farklı sırayla, farklı parametrelerle kullanabilirsin.</p>
{rot_html}
{clr_html}
</section>
"""

# ============================================================= costmap_2d
CM_GROUPS = [
    ("Çerçeve ve zamanlama", "", [
        ("global_frame", "Costmap'in çalıştığı global çerçeve (global costmap için `map`, yerel için genelde `odom`)."),
        ("robot_base_frame", "Robot gövdesinin çerçeve adı."),
        ("transform_tolerance", "TF verisinin tolere edilebilir gecikmesi (sn)."),
        ("update_frequency", "Costmap'in güncellenme hızı (Hz)."),
        ("publish_frequency", "Görselleştirme için costmap'in yayınlanma hızı (Hz); 0 yayınlamaz."),
    ]),
    ("Boyut ve ayak izi", "", [
        ("width", "Costmap genişliği (m)."),
        ("height", "Costmap yüksekliği (m)."),
        ("resolution", "Hücre boyutu (m)."),
        ("origin_x", "Costmap'in sol-alt köşesinin global çerçevedeki x konumu (m)."),
        ("origin_y", "Costmap'in sol-alt köşesinin global çerçevedeki y konumu (m)."),
        ("rolling_window", "true ise costmap robotla birlikte kayan bir pencere olur (yerel costmap için tipiktir)."),
        ("footprint", "Robotun gövde çokgeni, `[[x1,y1],[x2,y2],…]` biçiminde, robot merkezine göre. Verilirse `robot_radius`'u geçersiz kılar."),
        ("robot_radius", "Dairesel robotlar için yarıçap (m); yalnızca `footprint` boşsa kullanılır."),
        ("footprint_padding", "Ayak izine her yönde eklenecek pay (m)."),
    ]),
    ("Genel davranış", "", [
        ("plugins", "Sırayla uygulanacak katman eklentileri listesi (ör. `static_layer`, `obstacle_layer`, `inflation_layer`). Verilmezse costmap eski (Hydro öncesi) düzene döner ve bir uyarı basar: `static_map: true` ise `static_layer`, her durumda `obstacle_layer` (`map_type: voxel` ise voxel katmanı) ve `inflation_layer` kurulur; eski üst düzey parametreler bu katmanlara taşınır."),
        ("always_send_full_costmap", "true ise her güncellemede costmap'in tamamı yayınlanır; false ise yalnızca değişen kısım (`~costmap_updates`)."),
        ("track_unknown_space", "true ise \"bilinmiyor\" bölgeler ayrı bir durum olarak tutulur (yalnızca hiçbir katman ezmemişse); katmanların çoğu bunu kendi ayarıyla ezer."),
        ("observation_sources", "Eski (Hydro öncesi) stil engel kaynağı tanımı; katman tabanlı costmap'lerde bunun yerine her katmanın kendi `observation_sources`'u kullanılır."),
    ]),
]
SL_GROUPS = [
    ("static_layer", "Haritayı (`map_server`'dan ya da bir topic'ten) costmap'e işleyen katman. Genelde yalnızca global costmap'te kullanılır.", [
        ("map_topic", "Haritanın alınacağı topic."),
        ("first_map_only", "true ise yalnızca ilk haritayı işler, sonraki güncellemeleri yok sayar."),
        ("subscribe_to_updates", "true ise haritanın yalnızca değişen kısımlarını taşıyan `~<topic>_updates` topic'ine de abone olur."),
        ("track_unknown_space", "true ise haritadaki bilinmeyen hücreler costmap'te de bilinmeyen kalır; false ise boş sayılır."),
        ("use_maximum", "false (varsayılan) ise bu katman kendi değerlerini ana costmap'e doğrudan yazar; true ise mevcut değerle maksimumunu alır (static katman ilk katman değilse kullanışlıdır)."),
        ("trinary_costmap", "true ise hücreler yalnızca boş/dolu/bilinmiyor (üçlü) olarak işlenir; false ise ara maliyet değerleri de taşınır."),
        ("lethal_cost_threshold", "Harita değeri bu eşik ya da üstündeyse hücre \"ölümcül\" (kesin engel) sayılır."),
        ("unknown_cost_value", "Haritada bu değere sahip hücreler \"bilinmiyor\" sayılır."),
    ]),
]
OB_GROUPS = [
    ("obstacle_layer: genel", "Lidar/nokta bulutu gibi canlı sensör verisinden engel işleyen katman.", [
        ("observation_sources", "Bu katmanın kullanacağı gözlem kaynaklarının (topic grupları) adları, boşlukla ayrılmış."),
        ("track_unknown_space", "Genelde ana costmap ayarından miras alınır."),
        ("transform_tolerance", "TF verisinin tolere edilebilir gecikmesi (sn)."),
        ("obstacle_range", "Bu mesafeden (m) yakın algılanan noktalar engel olarak işaretlenir. Kaynak bazında da ezilebilir."),
        ("raytrace_range", "Bu mesafeye (m) kadar, ölçümle sensör arasındaki boşluk temizlenir (ışın izleme). Kaynak bazında da ezilebilir."),
        ("max_obstacle_height", "Bu yükseklikten (m) yüksek noktalar yok sayılır."),
        ("min_obstacle_height", "Bu yükseklikten (m) alçak noktalar yok sayılır."),
        ("combination_method", "Bu katmanın ana costmap'e nasıl yazacağı: 0 üzerine yazar, 1 (varsayılan) mevcut değerle maksimumu alır; başka bir değer (ör. 99) katmanın hiçbir şey yazmamasını sağlar."),
        ("enabled", "Katmanı açar/kapatır."),
        ("footprint_clearing_enabled", "true ise robotun kendi ayak izinin içine düşen ölçümler engel sayılmaz."),
    ]),
    ("obstacle_layer: her gözlem kaynağı için", "`observation_sources`'ta adı geçen her kaynağın (ör. `scan`) kendi alt parametre grubu vardır: `<obstacle_layer_adı>/<kaynak_adı>/<parametre>`.", [
        ("topic", "Kaynağın dinleyeceği topic; verilmezse kaynak adıyla aynı kabul edilir."),
        ("sensor_frame", "Sensörün çerçevesi; boşsa mesajın kendi `frame_id`'si kullanılır."),
        ("observation_persistence", "Gözlemlerin ne kadar süre (sn) saklanacağı; 0 yalnızca en son gözlemi tutar."),
        ("expected_update_rate", "Kaynağın beklenen güncelleme hızı (Hz); 0 denetim yapılmaz demektir."),
        ("data_type", "Mesaj türü: `PointCloud`, `PointCloud2` ya da `LaserScan`."),
        ("min_obstacle_height", "Bu kaynak için minimum yükseklik (m); genel ayarı ezer."),
        ("max_obstacle_height", "Bu kaynak için maksimum yükseklik (m); genel ayarı ezer."),
        ("inf_is_valid", "true ise `LaserScan`'deki `inf` (sonsuz) ölçümler menzil sonuna kadar boş alan olarak işlenir; false ise atılır."),
        ("clearing", "true ise bu kaynağın ölçümleri, aralarındaki boşluğu temizlemek için kullanılır."),
        ("marking", "true ise bu kaynağın ölçümleri engel işaretlemek için kullanılır."),
    ]),
]
INF_GROUPS = [
    ("inflation_layer", "Engellerin çevresine, robotun ona ne kadar yaklaşabileceğini gösteren bir \"ceza\" bulutu (şişirme) ekler.", [
        ("inflation_radius", "Engel çevresinde sıfırdan büyük ceza uygulanacak yarıçap (m)."),
        ("cost_scaling_factor", "Şu formülle uzaklaştıkça maliyeti düşürür: `252 × exp(-1,0 × cost_scaling_factor × (mesafe − iç_yarıçap))` (iç yarıçap: footprint'in içine sığan en büyük daire). Büyük değer maliyeti hızlı düşürür (robot engele daha yakın gidebilir), küçük değer geniş bir tampon bırakır."),
        ("inflate_unknown", "true ise bilinmeyen hücreler de şişirilir (engelmiş gibi ceza alır)."),
        ("enabled", "Katmanı açar/kapatır."),
    ]),
]
VX_GROUPS = [
    ("voxel_layer", "3B nokta bulutu verisini bir voksel (hacim öğesi) ızgarasında tutan, sonra 2B costmap'e izdüşüren katman; `obstacle_layer`'ın 3B hâlidir.", [
        ("origin_z", "Voksel ızgarasının taban yüksekliği (m)."),
        ("z_resolution", "Dikey yöndeki hücre boyutu (m)."),
        ("z_voxels", "Dikey sütun başına voksel sayısı; ızgaranın toplam yüksekliği `z_resolution × z_voxels`'tir."),
        ("unknown_threshold", "Bir sütunun \"bilinen\" sayılması için içinde izin verilen en çok bilinmeyen voksel sayısı; daha fazlası varsa sütun bilinmiyor sayılır."),
        ("mark_threshold", "Bir sütunun \"boş\" sayılması için içinde izin verilen en çok dolu voksel sayısı; daha fazlası varsa sütun engel sayılır (varsayılan 0: tek dolu voksel yeter)."),
        ("combination_method", "Bu katmanın ana costmap'e nasıl yazacağı: 0 üzerine yazar, 1 (varsayılan) mevcut değerle maksimumu alır; başka bir değer (ör. 99) katmanın hiçbir şey yazmamasını sağlar."),
        ("max_obstacle_height", "Bu yükseklikten (m) yüksek noktalar yok sayılır; ızgaranın tepesi (`origin_z + z_resolution × z_voxels`) bundan alçaksa ızgara sınırı geçerlidir."),
        ("publish_voxel_map", "true ise 3B voksel ızgarasını da (görselleştirme için) yayınlar."),
        ("enabled", "Katmanı açar/kapatır."),
        ("footprint_clearing_enabled", "true ise robotun kendi ayak izinin içine düşen ölçümler engel sayılmaz."),
    ]),
]

cm_html, cm_n = table("cm", "costmap_2d_common", CM_GROUPS)
sl_html, sl_n = table("sl", "static_layer", SL_GROUPS)
ob_html, ob_n = table("ob", "obstacle_layer", [OB_GROUPS[0]])
obs_html, obs_n = table("obs", "obstacle_layer_source", [OB_GROUPS[1]])
inf_html, inf_n = table("inf", "inflation_layer", INF_GROUPS)
vx_html, vx_n = table("vx", "voxel_layer", VX_GROUPS)

PAGE2 = f"""<section id="costmap-ref">
<h2>costmap_2d</h2>
<p><code>costmap_2d</code>, "buradan geçmek ne kadar tehlikeli" haritasını (costmap) katman katman kurar: harita, canlı sensör verisi, güvenlik payı (inflation) her biri ayrı bir eklentidir ve üst üste bindirilir. Kavramsal anlatım için <a href="harita-ve-navigasyon.html#navigasyon">Navigasyon (move_base)</a> bölümüne bak; burada costmap'in kendisi ve <strong>4 katmanın tamamı</strong> için gerçek parametre listesi var.</p>
<div class="call"><b>Bu sayfadaki değerler nereden geliyor?</b>
<p>ROS Noetic'in <code>costmap_2d</code> kaynak kodundan (<code>ros-planning/navigation</code>, bu makinede kurulu olan <code>1.17.3</code> sürümünün etiketi: <code>costmap_2d_ros.cpp</code> ve <code>plugins/*.cpp</code>) ve kurulu paketin dynamic_reconfigure tanımlarından. Adı geçmeyen her parametre kaynaktaki varsayılanı alır.</p></div>

{cm_html}

<h3 id="static-layer">Katman: static_layer</h3>
{sl_html}

<h3 id="obstacle-layer">Katman: obstacle_layer</h3>
{ob_html}
{obs_html}
<pre><code># örnek: iki gözlem kaynağı
obstacle_layer:
  observation_sources: scan bumper
  scan:
    topic: /scan
    data_type: LaserScan
    marking: true
    clearing: true
  bumper:
    topic: /bumper_points
    data_type: PointCloud2
    marking: true
    clearing: false</code></pre>

<h3 id="inflation-layer">Katman: inflation_layer</h3>
{inf_html}

<h3 id="voxel-layer">Katman: voxel_layer (isteğe bağlı, 3B)</h3>
{vx_html}
</section>
"""

PAGES.joinpath("ref-amcl-move-base.html").write_text(PAGE1, encoding="utf-8")
PAGES.joinpath("ref-costmap.html").write_text(PAGE2, encoding="utf-8")

# ============================================================= gmapping / map_server
GM_GROUPS = [
    ("Çerçeveler ve zaman", "", [
        ("base_frame", "Robot gövdesinin çerçeve adı."),
        ("map_frame", "Üretilecek haritanın çerçeve adı."),
        ("odom_frame", "Odometri çerçevesinin adı."),
        ("transform_publish_period", "`map→odom` dönüşümünün yayınlanma periyodu (sn); 0 yayınlamaz."),
        ("tf_delay", "Yayınlanan dönüşümün ne kadar ileri damgalanacağı (sn); genelde `transform_publish_period` ile aynı tutulur."),
        ("throttle_scans", "Kaç taramada birinin işleneceği; 1 = her tarama."),
    ]),
    ("Harita boyutu ve güncelleme", "gmapping, haritayı önceden ayrılmış sabit boyutlu bir ızgarada tutar. Küçük bir alan için varsayılan (200×200 m) gereğinden büyük ve yavaştır; `xmin…ymax` ile daralt.", [
        ("xmin", "Harita sınırı, x ekseni alt uç (m)."),
        ("ymin", "Harita sınırı, y ekseni alt uç (m)."),
        ("xmax", "Harita sınırı, x ekseni üst uç (m)."),
        ("ymax", "Harita sınırı, y ekseni üst uç (m)."),
        ("delta", "Harita çözünürlüğü (m/hücre)."),
        ("map_update_interval", "Haritanın yeniden hesaplanma periyodu (sn); küçültmek daha güncel ama daha ağır bir harita verir."),
        ("occ_thresh", "Bir hücrenin \"dolu\" (engel) sayılması için gereken doluluk oranı eşiği."),
    ]),
    ("Ne zaman güncellensin", "Robot bu kadar hareket etmeden yeni bir tarama işlenmez; gereksiz işlem yükünü azaltır.", [
        ("linearUpdate", "Bir güncelleme için robotun kat etmesi gereken en az mesafe (m)."),
        ("angularUpdate", "Bir güncelleme için robotun dönmesi gereken en az açı (rad)."),
        ("temporalUpdate", "Konum değişmese bile bu süre (sn) geçince yine de güncelle; negatifse kapalı."),
        ("resampleThreshold", "Parçacık filtresinin yeniden örnekleneceği etkin örnek büyüklüğü eşiği."),
        ("particles", "Parçacık filtresindeki parçacık sayısı. Büyütmek daha güvenilir ama daha yavaş."),
    ]),
    ("Lazer menzili", "", [
        ("maxUrange", "Haritalamada kullanılacak en büyük \"kullanılabilir\" menzil (m); verilmezse `maxRange` ile aynı olur."),
        ("maxRange", "Lazerin geçerli sayılacak en büyük menzili (m); verilmezse taramanın kendi `range_max − 0,01` değeri kullanılır."),
        ("minimumScore", "Bir taramanın haritayla eşleşmesi için gereken en düşük puan; 0 bu denetimi etkisiz kılar. Simetrik/az özellikli ortamlarda ani sıçramaları önlemek için artırılabilir."),
    ]),
    ("Tarama eşleme (scan matching)", "gmapping, her taramayı önce ham odometri etrafında küçük bir pencerede arayarak haritayla en iyi eşleşen konumu bulur (scan matching); bu parametreler o aramayı ayarlar.", [
        ("sigma", "Bir ölçümün \"isabetli\" sayılması için haritadaki en yakın engelden izin verilen sapma (m)."),
        ("kernelSize", "Eşleşen nokta arama penceresinin hücre cinsinden yarıçapı."),
        ("lstep", "Öteleme yönünde arama adımı (m)."),
        ("astep", "Dönüş yönünde arama adımı (rad)."),
        ("iterations", "Tarama eşleme aramasının yineleme sayısı."),
        ("lsigma", "Puanlama sırasında (olabilirlik hesabında) kullanılan uyum standart sapması (m)."),
        ("ogain", "Yeniden örneklemede kullanılan ağırlıkların olabilirliğe göre \"keskinliği\"; büyütmek en iyi eşleşmenin ağırlığını artırır."),
        ("lskip", "Tarama eşlemede her ışından kaçının atlanacağı; 0 = hiçbiri atlanmaz (tüm ışınlar kullanılır)."),
    ]),
    ("Hareket modeli gürültüsü", "Tekerlek odometrisinin öteleme/dönüş hareketlerinden kaynaklanan gürültü tahminleri (AMCL'deki `odom_alphaN`'e benzer amaç).", [
        ("srr", "Öteleme hareketinden kaynaklanan öteleme gürültüsü."),
        ("srt", "Öteleme hareketinden kaynaklanan dönüş gürültüsü."),
        ("str", "Dönüş hareketinden kaynaklanan öteleme gürültüsü."),
        ("stt", "Dönüş hareketinden kaynaklanan dönüş gürültüsü."),
        ("llsamplerange", "Konum (doğrusal) örnekleme aralığı; olabilirlik hesabı için kullanılır."),
        ("llsamplestep", "Konum (doğrusal) örnekleme adımı."),
        ("lasamplerange", "Açı örnekleme aralığı."),
        ("lasamplestep", "Açı örnekleme adımı."),
    ]),
]
MS_GROUPS = [
    ("map_server node parametresi", "", [
        ("frame_id", "Yayınlanan `nav_msgs/OccupancyGrid` mesajının çerçeve adı."),
    ]),
    ("Harita YAML dosyası: eşik alanları", "Bunlar node parametresi değil, `map_saver`'ın yazdığı ya da `map_server`'a verilen `.yaml` dosyasının alanlarıdır. YAML ile yüklenen haritada bu üç alan zorunludur (eksikse harita yüklenmez). Varsayılan sütunundaki değerler, YAML'sız eski kullanımda (`map_server resim.pgm <çözünürlük>`) bu adlarla `~param` olarak okunan varsayılanlardır; `map_saver` da dosyaya aynı değerleri yazar.", [
        ("negate", "1 ise beyaz/siyah = engel/boş anlamı ters çevrilir (kodun kendi tanımı: `p = x/255` olur; normalde `p = (255−x)/255`)."),
        ("occupied_thresh", "Doluluk oranı (`p`) bunu aşan piksel \"dolu\" (100) sayılır."),
        ("free_thresh", "Doluluk oranı (`p`) bunun altında kalan piksel \"boş\" (0) sayılır. İkisi arasındakiler varsayılan `trinary` modunda −1 (bilinmiyor), `scale` modunda orantılı bir ara değer alır."),
    ]),
]

gm_html, gm_n = table("gm", "gmapping", GM_GROUPS)
ms_html, ms_n = table("ms", "map_server", MS_GROUPS)

PAGE3 = f"""<section id="gmapping-ref">
<h2>gmapping</h2>
<p><code>slam_gmapping</code>, lazer taramalarından ve odometriden parçacık filtresiyle (Rao-Blackwellized) harita çıkaran SLAM node'udur. Kavramsal anlatım için <a href="harita-ve-navigasyon.html#slam">Harita ve SLAM</a> bölümüne bak; burada <strong>{gm_n} parametrenin tamamı</strong> var.</p>
<div class="call"><b>Bu sayfadaki değerler nereden geliyor?</b>
<p>ROS paketi <code>ros-perception/slam_gmapping</code>'in kurulu <code>1.4.2</code> sürümünün kaynak kodundan (<code>gmapping/src/slam_gmapping.cpp</code>). Bu paketin dynamic_reconfigure tanımı yoktur; tüm parametreler yalnızca başlangıçta, <code>rosparam</code> ya da launch'tan okunur.</p></div>
<h4>Abone olunan / yayınlanan topic'ler</h4>
<div class="tw"><table><thead><tr><th>Ad</th><th>Yön</th><th>Tür</th></tr></thead><tbody>
<tr><td><code>scan</code></td><td>abone</td><td><code>sensor_msgs/LaserScan</code></td></tr>
<tr><td><code>tf</code></td><td>abone + yayın</td><td><code>tf2_msgs/TFMessage</code> (`map→odom`)</td></tr>
<tr><td><code>map</code></td><td>yayın</td><td><code>nav_msgs/OccupancyGrid</code></td></tr>
<tr><td><code>map_metadata</code></td><td>yayın</td><td><code>nav_msgs/MapMetaData</code></td></tr>
<tr><td><code>~entropy</code></td><td>yayın</td><td><code>std_msgs/Float64</code> — parçacık dağılımının belirsizliği; ani yükseliş genelde kötü bir eşleşmeye işaret eder</td></tr>
</tbody></table></div>
<h4>Sunulan servisler</h4>
<div class="tw"><table><thead><tr><th>Ad</th><th>Tür</th></tr></thead><tbody>
<tr><td><code>dynamic_map</code></td><td><code>nav_msgs/GetMap</code> — o anki haritayı döndürür</td></tr>
</tbody></table></div>

{gm_html}
</section>

<section id="map-server-ref">
<h2>map_server</h2>
<p><code>map_server</code>, kayıtlı bir haritayı <code>nav_msgs/OccupancyGrid</code> olarak servis eden node ve haritayı diskten okuyup yazan iki komut satırı aracı (<code>map_server</code>, <code>map_saver</code>) sağlar. Kavramsal anlatım için <a href="harita-ve-navigasyon.html#slam">Harita ve SLAM</a> bölümüne bak.</p>
<div class="call"><b>Bu sayfadaki değerler nereden geliyor?</b>
<p>ROS Noetic'in <code>map_server</code> kaynak kodundan (<code>ros-planning/navigation</code>, bu makinede kurulu olan <code>1.17.3</code> sürümünün etiketi: <code>src/main.cpp</code>, <code>src/image_loader.cpp</code>).</p></div>
<h4>Komut satırı kullanımı</h4>
<pre><code>rosrun map_server map_server harita.yaml
rosrun map_server map_saver -f harita          # → harita.pgm + harita.yaml yazar</code></pre>
<h4>Yayınlanan topic'ler ve servisler</h4>
<div class="tw"><table><thead><tr><th>Ad</th><th>Tür</th></tr></thead><tbody>
<tr><td><code>map</code></td><td>yayın, <code>nav_msgs/OccupancyGrid</code> (kalıcı/latched)</td></tr>
<tr><td><code>map_metadata</code></td><td>yayın, <code>nav_msgs/MapMetaData</code> (kalıcı/latched)</td></tr>
<tr><td><code>static_map</code></td><td>servis, <code>nav_msgs/GetMap</code></td></tr>
</tbody></table></div>

{ms_html}

<h3>Harita YAML dosyası: diğer alanlar</h3>
<div class="tw ptab"><table><thead><tr><th>Alan</th><th>Tür</th><th>Zorunlu mu?</th><th>Açıklama</th></tr></thead><tbody>
<tr><td><code>image</code></td><td>string</td><td>evet</td><td>Resim dosyasının yolu; mutlak ya da YAML dosyasının klasörüne göre göreli.</td></tr>
<tr><td><code>resolution</code></td><td>double</td><td>evet</td><td>Bir pikselin kenar uzunluğu (m).</td></tr>
<tr><td><code>origin</code></td><td>[x, y, yaw]</td><td>evet</td><td>Resmin sol-alt pikselinin <code>map</code> çerçevesindeki konumu ve yönü (m, m, rad). Birçok araç yaw'ı yok sayar.</td></tr>
<tr><td><code>mode</code></td><td>string</td><td>hayır (varsayılan <code>trinary</code>)</td><td><code>trinary</code>: hücreler yalnızca 0, 100 ya da −1 olur. <code>scale</code>: eşikler arası orantılı değer alır; resmin alfa kanalı varsa saydam pikseller −1 olur. <code>raw</code>: piksel değeri hücre değeri olarak doğrudan kullanılır.</td></tr>
</tbody></table></div>

<h4>Piksel değerinin hücre değerine çevrilmesi</h4>
<p>Her piksel değeri <code>x</code> (0–255), önce <code>p</code>'ye çevrilir: <code>negate: 0</code> iken <code>p = (255 − x) / 255</code> (yani koyu piksel = yüksek doluluk); <code>negate: 1</code> iken <code>p = x / 255</code> (tersi). Sonra <code>p &gt; occupied_thresh</code> ise hücre <strong>100</strong> (dolu), <code>p &lt; free_thresh</code> ise <strong>0</strong> (boş) olur. Arada kalan pikseller <code>trinary</code> modunda <strong>−1</strong> (bilinmiyor), <code>scale</code> modunda <code>99 × (p − free_thresh) / (occupied_thresh − free_thresh)</code> ile orantılı bir ara değer alır. <code>raw</code> modunda bu hesap yapılmaz.</p>
</section>
"""
PAGES.joinpath("ref-slam-harita.html").write_text(PAGE3, encoding="utf-8")

# ============================================================= twist_mux / ira_laser_tools
tm = DATA["twist_mux"]
TM_FIELD_ROWS = "\n".join(
    f'<tr><td><code>{n}</code></td><td>{t}</td><td>{d}</td></tr>'
    for n, t, d in [
        ("name", "string", "Yalnızca tanılama (diagnostics) için okunabilir ad."),
        ("topic", "string", "Dinlenecek topic adı."),
        ("timeout", "double", "Bu süre (sn) boyunca mesaj gelmezse kaynak zaman aşımına uğramış sayılır. <code>0</code>: hiç zaman aşımına uğramaz. Kilitlerde zaman aşımı kilidi <strong>etkinleştirir</strong> (bkz. aşağı)."),
        ("priority", "int (0–255)", "Öncelik; büyük olan kazanır."),
    ]
)
IRA_GROUPS = [
    ("laserscan_multi_merger", "Birden çok `sensor_msgs/LaserScan` kaynağını tek bir taramada (ve isteğe bağlı bir nokta bulutunda) birleştirir. Çıktı, `destination_frame`'in merkezinde duran tek bir sanal lidardan geliyormuş gibi üretilir; kaynak taramaların birbirini engellemesi (oklüzyon) hesaba katılmaz.", [
        ("laserscan_topics", "Birleştirilecek girdi topic'leri, boşlukla ayrılmış."),
        ("destination_frame", "Birleşik çıktının ifade edileceği çerçeve."),
        ("scan_destination_topic", "Çıktı `LaserScan` topic'i."),
        ("cloud_destination_topic", "Aynı verinin `PointCloud2` biçimindeki çıktı topic'i."),
        ("angle_min", "Çıktı taramasının başlangıç açısı (rad)."),
        ("angle_max", "Çıktı taramasının bitiş açısı (rad)."),
        ("angle_increment", "Çıktı taramasında iki ışın arası açı (rad)."),
        ("range_min", "Çıktı taramasında geçerli sayılacak en küçük mesafe (m)."),
        ("range_max", "Çıktı taramasında geçerli sayılacak en büyük mesafe (m)."),
        ("scan_time", "Çıktı mesajının `scan_time` alanına yazılacak değer (sn)."),
    ]),
]
ira_html, ira_n = table("ira", "ira_laser_tools", IRA_GROUPS)

PAGE4 = f"""<section id="twist-mux-ref">
<h2>twist_mux</h2>
<p><code>twist_mux</code>, birden çok <code>geometry_msgs/Twist</code> kaynağını (navigasyon, joystick, klavye, acil durdurma) önceliğe göre tek bir çıktıda birleştiren seçicidir. Kavramsal anlatım için <a href="gorev-ve-docking.html#twist-mux">Komut kaynaklarını yönetmek</a> bölümüne bak.</p>
<div class="call"><b>Bu sayfadaki değerler nereden geliyor?</b>
<p>ROS paketi <code>ros-teleop/twist_mux</code>'ın kaynak kodundan (<code>noetic-devel</code> dalı: <code>src/twist_mux.cpp</code>, <code>include/twist_mux/topic_handle.h</code>).</p></div>
<h4>Arayüz</h4>
<div class="tw"><table><thead><tr><th>Ad</th><th>Yön</th><th>Tür</th></tr></thead><tbody>
<tr><td><code>cmd_vel_out</code></td><td>yayın</td><td><code>geometry_msgs/Twist</code> — tek çıktı; genelde <code>/cmd_vel</code>'e <em>remap</em> edilir</td></tr>
<tr><td><code>topics</code> altındaki her topic</td><td>abone</td><td><code>geometry_msgs/Twist</code></td></tr>
<tr><td><code>locks</code> altındaki her topic</td><td>abone</td><td><code>std_msgs/Bool</code></td></tr>
</tbody></table></div>
<h3>Parametre yapısı</h3>
<p><code>topics</code> ve <code>locks</code>, her biri aynı dört alanı taşıyan birer liste olarak verilir:</p>
<div class="tw ptab"><table><thead><tr><th>Alan</th><th>Tür</th><th>Anlamı</th></tr></thead><tbody>
{TM_FIELD_ROWS}
</tbody></table></div>
<p>Seçim mantığı: bir hız girdisine mesaj geldiğinde, zaman aşımına uğramamış ve kilitlerce bastırılmamış girdiler arasında <strong>en yüksek öncelikli</strong> olan o ise mesaj <code>cmd_vel_out</code>'a aynen yazılır; değilse atılır. Bir girdi, etkin bir kilidin önceliğinden <em>düşük</em> öncelikliyse bastırılır (eşitse bastırılmaz). Bir kilit, topic'ine <code>true</code> geldiğinde <strong>ya da</strong> <code>timeout &gt; 0</code> iken bu süre boyunca mesaj gelmediğinde (başlangıçta henüz hiç mesaj gelmemişken de) etkindir; yani kilit yayıncısı çökerse kilit kapanmaz, devreye girer. Tanılama (<code>/diagnostics</code>) saniyede bir güncellenir.</p>
<div class="call warn"><b>twist_mux sıfır hız yayınlamaz</b>
<p><code>twist_mux</code> yalnızca bir girdiye mesaj geldiğinde yayın yapar. Tüm girdiler zaman aşımına uğradığında ya da bir kilit devreye girdiğinde çıkışa <strong>sıfır hız yazmaz, sadece susar</strong>. Robot sürücüsünün kendi komut zaman aşımı yoksa (Gazebo'nun <code>diff_drive</code> eklentisinde yoktur) robot son komutla gitmeye devam eder. Durdurma için sürücü tarafında bir zaman aşımı ya da <code>twist_mux</code> çıkışından sonra bir watchdog kullan (bkz. <a href="pratik.html#log-tanilama">Basit bir watchdog</a>).</p></div>
<pre><code># örnek yapılandırma
topics:
  - {{name: navigation, topic: cmd_vel_nav,    timeout: 0.5, priority: 10}}
  - {{name: joystick,   topic: cmd_vel_joy,    timeout: 0.5, priority: 100}}
locks:
  - {{name: e_stop,     topic: e_stop_active,  timeout: 0.0, priority: 255}}</code></pre>
</section>

<section id="ira-laser-tools-ref">
<h2>ira_laser_tools</h2>
<p><code>ira_laser_tools</code>, birden çok 2D lidarı tek bir taramada birleştiren <code>laserscan_multi_merger</code> node'unu sağlar. Kavramsal anlatım için <a href="robot-ve-simulasyon.html#sensorler">Birden çok lidarı tek taramada birleştirmek</a> bölümüne bak.</p>
<div class="call"><b>Bu sayfadaki değerler nereden geliyor?</b>
<p>ROS paketi <code>iralabdisco/ira_laser_tools</code>'un kurulu <code>1.0.7</code> sürümünün kaynak kodundan (<code>src/laserscan_multi_merger.cpp</code>). Kurulumu: <code>sudo apt install ros-noetic-ira-laser-tools</code>.</p></div>
{ira_html}
</section>
"""
PAGES.joinpath("ref-yardimci-paketler.html").write_text(PAGE4, encoding="utf-8")

print(f"AMCL {amcl_n} param | move_base {mb_n}+{rot_n}+{clr_n} param | costmap {cm_n}+{sl_n}+{ob_n}+{obs_n}+{inf_n}+{vx_n} param | gmapping {gm_n} | map_server {ms_n} | ira {ira_n}")
