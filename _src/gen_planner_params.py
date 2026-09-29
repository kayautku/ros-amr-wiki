#!/usr/bin/env python3
"""DWA ve TEB parametre sayfasını üretir: _src/pages/planlayici-parametreleri.html

Veri kaynağı (Noetic paketlerinden okundu):
  _src/data/planner_params.json   dinamik ayar (dynamic_reconfigure) tanımlarından: ad, tür, varsayılan, aralık
  Bu dosyadaki EK_* listeleri      yalnızca YAML'dan okunan parametreler (teb_config.h ve kütüphane dizgilerinden)

Kullanım:  python3 _src/gen_planner_params.py && python3 _src/build.py
"""
import html
import json
import re
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = json.loads((ROOT / "_src" / "data" / "planner_params.json").read_text(encoding="utf-8"))
OUT = ROOT / "_src" / "pages" / "planlayici-parametreleri.html"

INF = float("inf")


def fmt(v):
    if isinstance(v, tuple) and v and v[0] == "raw":
        return v[1]
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, str):
        return f'"{v}"'
    if v is None:
        return "—"
    if isinstance(v, (int, float)):
        if v >= 2147483000:
            return "∞"
        if v <= -2147483000 or v == -INF:
            return "−∞"
        if v == INF:
            return "∞"
        return ("%g" % v)
    return str(v)


def rng(p):
    if p["type"] in ("bool", "str", "string"):
        return "—"
    lo, hi = p.get("min"), p.get("max")
    if lo is None and hi is None:
        return "—"
    lo_s, hi_s = fmt(lo), fmt(hi)
    if lo_s == "−∞" and hi_s == "∞":
        return "—"
    return f"{lo_s} … {hi_s}"


# ------------------------------------------------------------------ DWA
# grup -> [(ad, açıklama)]; cfg'de olmayan ek parametreler DWA_EK'te
DWA_GROUPS = [
    ("Hız sınırları", "Robotun hangi hızlarda gidip dönebileceğini belirler. Diferansiyel sürüşlü robotta yana kayma (`y`) hızlarını 0 yap.", [
        ("max_vel_x", "En yüksek ileri hız (m/s). Diferansiyel sürüşlü robotta asıl hız sınırı budur."),
        ("min_vel_x", "En düşük ileri hız (m/s). Negatif verirsen robot geri de gidebilir; 0 iken geri gitmez."),
        ("max_vel_y", "Yana kayma hızının üst sınırı (m/s). Yana kayamayan robotta 0 yap."),
        ("min_vel_y", "Yana kayma hızının alt sınırı (m/s). Yana kayamayan robotta 0 yap."),
        ("max_vel_trans", "Öteleme hızının mutlak büyüklüğü için üst sınır (m/s)."),
        ("min_vel_trans", "Öteleme hızının mutlak büyüklüğü için alt sınır (m/s)."),
        ("max_vel_theta", "En yüksek dönüş hızı (rad/s), mutlak değer."),
        ("min_vel_theta", "En düşük dönüş hızı (rad/s), mutlak değer. Motorların yenebileceği en küçük dönüş olmalı; çok büyük olursa robot hassas dönemez."),
    ]),
    ("İvme sınırları", "Hız değişiminin ne kadar ani olabileceğini sınırlar. Yük taşıyan robotlarda düşük tut.", [
        ("acc_lim_x", "İleri yönde ivme sınırı (m/s²)."),
        ("acc_lim_y", "Yana kayma yönünde ivme sınırı (m/s²)."),
        ("acc_lim_theta", "Dönüşte açısal ivme sınırı (rad/s²)."),
        ("acc_lim_trans", "Öteleme ivmesinin mutlak büyüklüğü için üst sınır (m/s²). Noetic DWA'sında (1.17.3) bu değer okunur ama yörünge örneklemesinde kullanılmaz; ivmeyi `acc_lim_x`/`acc_lim_y`/`acc_lim_theta` sınırlar."),
    ]),
    ("Hedef ve durma toleransı", "Robotun \"hedefe vardım\" ve \"durdum\" demesi için gereken hassasiyet.", [
        ("xy_goal_tolerance", "Hedefe bu mesafeden (m) yakınsa konum olarak vardı sayılır. Çok küçük olursa robot hedefte titreyebilir."),
        ("yaw_goal_tolerance", "Hedef yönüne bu açıdan (rad) az fark varsa yön olarak vardı sayılır."),
        ("trans_stopped_vel", "Öteleme hızı bunun altındaysa robot ötelemede \"durmuş\" sayılır (m/s)."),
        ("theta_stopped_vel", "Dönüş hızı bunun altındaysa robot dönmede \"durmuş\" sayılır (rad/s)."),
        ("latch_xy_goal_tolerance", "true ise robot konum toleransına bir kez girdikten sonra konumu tekrar denetlenmez, yalnızca hedef yönüne döner. Hedefte kayıp geri çıkıp titreyen robotlarda işe yarar."),
    ]),
    ("İleri simülasyon ve örnekleme", "DWA'nın çekirdeği: geçerli hız aralığından örnekler alır, her biri için kısa bir yörünge simüle eder, en iyisini seçer.", [
        ("sim_time", "Yörüngelerin ileriye doğru simüle edileceği süre (sn). Büyütmek daha uzağı görür ve akıcı gider, ama dar yerlerde robotu \"korkak\" yapar ve hesabı artırır."),
        ("sim_granularity", "Her yörünge boyunca çarpışma denetiminin adım aralığı (m)."),
        ("angular_sim_granularity", "Dönüşler için çarpışma denetiminin açısal adım aralığı (rad)."),
        ("vx_samples", "İleri hız uzayından alınacak örnek sayısı."),
        ("vy_samples", "Yana hız uzayından alınacak örnek sayısı. En az 1; yana kayamayan robotta `max_vel_y`/`min_vel_y` 0 iken 1 kullan."),
        ("vth_samples", "Dönüş hızı uzayından alınacak örnek sayısı. Büyütmek dönüşleri inceltir, işlemciyi artırır."),
        ("use_dwa", "true ise örnekleme, robotun ivme sınırlarının izin verdiği küçük bir \"dinamik pencere\" ile kısıtlanır; false ise tüm hız uzayı taranır."),
    ]),
    ("Maliyet fonksiyonu", "Aday yörüngeler bu ağırlıklarla puanlanır; ağırlıkların birbirine oranı robotun tavrını belirler.", [
        ("path_distance_bias", "Global yola yakın kalmanın ağırlığı. Büyütürsen robot planı daha sadık izler."),
        ("goal_distance_bias", "Hedefe yaklaşmanın ağırlığı. Büyütürsen robot yoldan sapıp hedefe doğru kestirmeyi dener."),
        ("occdist_scale", "Engellerden uzak durmanın ağırlığı. Büyütürsen robot engellerden daha çok kaçınır, dar geçitlerde takılabilir."),
        ("twirling_scale", "Robotun yönünü değiştirmesini cezalandıran ağırlık; büyükse robot dönmekten kaçınır."),
        ("stop_time_buffer", "Bir yörüngenin geçerli sayılması için robotun çarpışmadan en az bu kadar süre (sn) önce durabilmesi gerekir."),
        ("forward_point_distance", "Robot merkezinin ilerisine konan ek puanlama noktasının merkezden uzaklığı (m)."),
        ("sum_scores", "true ise engel maliyeti yörünge boyunca toplanır; false ise yörüngenin en yüksek engel maliyeti alınır. (Resmî wiki'de yok; Noetic kaynak kodunda doğrulandı.)"),
        ("cheat_factor", "Hedefe yaklaşırken robotun \"burnunu yola hizalama\" maliyetinin ne zaman kapatılacağını belirleyen çarpan: hedefe uzaklığın karesi `forward_point_distance`² × `cheat_factor` değerinden küçükse hizalama maliyeti devre dışı kalır. (Resmî wiki'de yok; Noetic kaynak kodundan.)"),
    ]),
    ("Ayak izi ölçekleme", "Hız arttıkça robotun ayak izini büyüterek yüksek hızda engellere daha çok pay bırakır.", [
        ("scaling_speed", "Ayak izi ölçeklemesinin başladığı hız (m/s)."),
        ("max_scaling_factor", "Ayak izinin ölçekleneceği en büyük çarpan (ek pay oranı)."),
    ]),
    ("Salınım ve plan", "Robotun sağa sola gidip gelmesini (salınım) ve global planın izlenişini yönetir.", [
        ("oscillation_reset_dist", "Salınım bayrakları sıfırlanmadan önce robotun kat etmesi gereken mesafe (m)."),
        ("oscillation_reset_angle", "Salınım bayrakları sıfırlanmadan önce robotun dönmesi gereken açı (rad)."),
        ("prune_plan", "true ise robot global planın ilk noktası yerine kendisine en yakın noktasından izlemeye başlar."),
    ]),
    ("Yayın ve çerçeve", "Görselleştirme çıktıları ve çerçeve adı.", [
        ("global_frame_id", "`publish_traj_pc` ile yayınlanan yörünge bulutunun çerçevesi; yerel costmap'in global çerçevesiyle aynı olmalı."),
        ("odom_topic", "Robotun anlık hızının okunduğu `nav_msgs/Odometry` topic'i. Odometri başka bir adla yayınlanıyorsa (ör. EKF çıktısı `odometry/filtered`) bunu ayarla."),
        ("publish_traj_pc", "true ise değerlendirilen yörüngeleri bir PointCloud olarak yayınlar (hata ayıklama)."),
        ("publish_cost_grid_pc", "true ise maliyet ızgarasını renkli bir PointCloud olarak yayınlar (hata ayıklama)."),
    ]),
]
# cfg'de olmayan, kodda okunan DWA parametreleri: ad -> (tür, varsayılan)
DWA_EK = {
    "latch_xy_goal_tolerance": ("bool", False),
    "sum_scores": ("bool", False),
    "cheat_factor": ("double", 1.0),
    "global_frame_id": ("string", "odom"),
    "publish_traj_pc": ("bool", False),
    "publish_cost_grid_pc": ("bool", False),
    "odom_topic": ("string", "odom"),
}

# ------------------------------------------------------------------ TEB
TEB_GROUPS = [
    ("Genel", "Planlayıcının hangi topic ve çerçeveyle çalışacağı.", [
        ("odom_topic", "Robot sürücüsünün yayınladığı odometri topic'i; robotun anlık hızı buradan okunur."),
        ("map_frame", "Eski bir parametre: kurulu sürümde (0.9.1) planlayıcı başlarken bunu yerel costmap'in `global_frame`'iyle ezer, bu yüzden ayarlamanın etkisi yoktur. Planlama çerçevesini değiştirmek için yerel costmap'in `global_frame`'ini değiştir."),
    ]),
    ("Yörünge", "Zaman ayarlı elastik bandın (yörüngenin) nasıl örneklendiği ve global plana nasıl bağlandığı.", [
        ("teb_autosize", "Yörünge uzunluğunu zamansal çözünürlüğe (`dt_ref`) göre optimizasyon sırasında otomatik ayarlar. Önerilen: true."),
        ("dt_ref", "Yörüngenin zaman adımı (sn). Genelde kontrol döngüsü periyodu (1 / `controller_frequency`) civarında seçilir. Küçültmek daha ince ama daha ağır bir plan demektir."),
        ("dt_hysteresis", "Otomatik yeniden boyutlandırmada kullanılan histerezis (sn); genelde `dt_ref`'in %10'u. Zaman adımı bu bandın içindeyse örnek eklenmez/çıkarılmaz."),
        ("min_samples", "Yörüngedeki en az örnek (poz) sayısı. 2'den büyük olmalı; 3'ün altı uyarı verir."),
        ("max_samples", "Yörüngedeki en çok örnek sayısı. Çok küçükse çözünürlük robot modeli ve engellerden kaçınma için yetersiz kalır."),
        ("global_plan_overwrite_orientation", "Bazı global planlayıcılar ara hedeflerin yönünü üretmez; true ise TEB bu yönleri kendisi belirler."),
        ("allow_init_with_backwards_motion", "Hedef yerel costmap içinde robotun arkasındaysa yörüngenin geri hareketle başlatılmasına izin verir. Yalnızca robotun arkasında sensör varsa önerilir."),
        ("max_global_plan_lookahead_dist", "Optimizasyonda dikkate alınan global plan parçasının en büyük uzunluğu (m). 0 ya da negatifse sınırsız; her durumda yerel costmap boyutuyla da sınırlıdır. Büyütmek daha uzağı planlar ama hesabı artırır."),
        ("global_plan_prune_distance", "Global plan budanırken robotun gerisinde tutulacak mesafe (m); robotun bu mesafeden daha gerisinde kalan plan noktaları atılır."),
        ("exact_arc_length", "true ise hız, ivme ve dönüş hızı hesaplarında tam yay uzunluğu kullanılır (daha doğru, daha fazla işlemci); false ise öklid yaklaşımı."),
        ("force_reinit_new_goal_dist", "Hedef bu mesafeden (m) fazla değişirse yörünge sıfırdan başlatılır (sıcak başlangıç atlanır)."),
        ("force_reinit_new_goal_angular", "Hedef yönü bu açıdan (rad) fazla değişirse yörünge sıfırdan başlatılır."),
        ("feasibility_check_no_poses", "Tahmin edilen planın kaçıncı pozuna kadar uygulanabilirliğin (çarpışma vb.) her adımda denetleneceği. Büyütmek daha ileriyi denetler."),
        ("control_look_ahead_poses", "Hız komutunu çıkarmak için yörüngenin kaçıncı pozunun kullanılacağı. 1 = hemen bir sonraki poz."),
        ("min_resolution_collision_check_angular", "Costmap çarpışma denetiminde kullanılan en küçük açısal çözünürlük (rad); sağlanmazsa ara örnekler eklenir."),
        ("publish_feedback", "Tam yörüngeyi ve etkin engel listesini yayınlar. Yalnızca değerlendirme ve hata ayıklama için aç."),
        ("visualize_with_time_as_z_axis_scale", "0'dan büyükse yörünge ve engeller zamanı z ekseni alarak 3B görselleştirilir. En çok dinamik engellerde işe yarar."),
    ]),
    ("Via (ara) noktaları", "Global plandan çıkarılan ara noktaların yörüngeye ne kadar bağlı olduğu.", [
        ("global_plan_viapoint_sep", "Global plandan çıkarılan ardışık via noktaları arası en küçük mesafe (m). Negatifse via noktaları kullanılmaz."),
        ("via_points_ordered", "true ise planlayıcı via noktalarının sırasına uyar."),
    ]),
    ("Robot", "Robotun hız/ivme sınırları ve sürüş tipi. Diferansiyel sürüşlü robot için `min_turning_radius: 0`, `max_vel_y: 0` olmalı.", [
        ("max_vel_x", "En yüksek ileri hız (m/s)."),
        ("max_vel_x_backwards", "Geri giderken en yüksek hız (m/s). Robotun geri gitmesini istemiyorsan çok küçük ver (alt sınırı 0,01) ve `weight_kinematics_forward_drive`'ı büyüt."),
        ("max_vel_y", "Yana kayma hızı sınırı (m/s). Holonomik olmayan (diferansiyel, araba benzeri) robotlarda 0 olmalı."),
        ("max_vel_theta", "En yüksek dönüş hızı (rad/s)."),
        ("acc_lim_x", "En yüksek öteleme ivmesi (m/s²)."),
        ("acc_lim_y", "Yana kayma ivmesi sınırı (m/s²); yalnızca holonomik robotlarda kullanılır."),
        ("acc_lim_theta", "En yüksek dönüş ivmesi (rad/s²)."),
        ("min_turning_radius", "Araba benzeri robot için en küçük dönüş yarıçapı (m). Diferansiyel sürüşlü robotta 0 olmalı; sıfırdan büyük değer robotun yerinde dönmesini kısıtlar."),
        ("wheelbase", "Arka aks ile ön aks arası mesafe (m). Yalnızca `cmd_angle_instead_rotvel` açık araba benzeri robotlarda gerekir; arka tekerlekten sürülenlerde negatif olabilir."),
        ("cmd_angle_instead_rotvel", "true ise komuttaki dönüş hızı yerine ilgili direksiyon açısı [−π/2, π/2] yazılır (araba benzeri robotlar için). Dönüş hızının anlamı değiştiği için dikkatli kullan."),
        ("is_footprint_dynamic", "true ise uygulanabilirlik denetiminden önce ayak izi güncellenir (ayak izi zamanla değişiyorsa)."),
    ]),
    ("Ayak izi modeli", "TEB'in engel mesafesi hesaplarında kullandığı robot şekli. YAML'da `footprint_model:` altında verilir. Costmap'in `footprint`'inden bağımsızdır (o, uygulanabilirlik denetimi için kullanılır); ikisini tutarlı tut. Araba benzeri robotlarda [0, 0] noktası arka aksın (dönme ekseninin) üzerindedir. Çizgi modelinde robotun tamamını kapsamak için `min_obstacle_dist`'i ayrıca artırman gerekir. `type` verilmezse `point` kullanılır. Seçilen modelin alt parametrelerinin **varsayılanı yoktur**: eksikse TEB bir hata yazıp `point` modeline döner (loglarda \"Footprint model ... cannot be loaded\" satırına bak).", [
        ("footprint_model/type", "Robot modeli: `point`, `circular`, `line`, `two_circles` ya da `polygon`. Karmaşık model daha doğru ama daha ağırdır."),
        ("footprint_model/radius", "`circular` modeli için yarıçap (m). Dairenin merkezi robotun dönme eksenindedir."),
        ("footprint_model/line_start", "`line` modeli için çizginin başlangıç noktası [x, y] (m)."),
        ("footprint_model/line_end", "`line` modeli için çizginin bitiş noktası [x, y] (m)."),
        ("footprint_model/front_offset", "`two_circles` modeli için ön dairenin merkezinin, robotun x ekseni boyunca dönme ekseninden ne kadar ileride olduğu (m). Dönme ekseni [0, 0] kabul edilir; ofsetler negatif olabilir."),
        ("footprint_model/front_radius", "`two_circles` modeli için ön dairenin yarıçapı (m)."),
        ("footprint_model/rear_offset", "`two_circles` modeli için arka dairenin merkezinin, robotun x ekseni boyunca dönme ekseninden ne kadar geride olduğu (m)."),
        ("footprint_model/rear_radius", "`two_circles` modeli için arka dairenin yarıçapı (m)."),
        ("footprint_model/vertices", "`polygon` modeli için köşe noktaları [[x1, y1], [x2, y2], …] (m), robotun dönme eksenine göre. Çokgen her zaman kapalıdır: ilk köşeyi sonda tekrarlama."),
    ]),
    ("Hedef toleransı", "Hedefe varış hassasiyeti.", [
        ("xy_goal_tolerance", "Hedef konumuna izin verilen son öklid uzaklığı (m)."),
        ("yaw_goal_tolerance", "Hedef yönüne izin verilen son yön hatası (rad)."),
        ("free_goal_vel", "true ise planlama sırasında robotun hedefte sıfırdan farklı (örneğin azami) hızla varmasına izin verilir; robot hedefte durmak zorunda kalmaz."),
        ("complete_global_plan", "true ise robot hedefi geçse bile global planı erken bitirmez; planın sonuna kadar gider."),
    ]),
    ("Engeller", "Engellerden ne kadar uzak durulacağı ve costmap engellerinin nasıl işleneceği.", [
        ("min_obstacle_dist", "Engellerden korunması istenen en küçük mesafe (m). Mesafe, seçtiğin `footprint_model`'e göre ölçülür: varsayılan `point` modelinde robotun merkez noktasından ölçülür, bu yüzden robotun yarıçapını bu değere kendin eklemelisin; `circular` modelinde yarıçap otomatik eklenir. Robot engellere fazla yaklaşıyorsa büyüt, dar geçitten geçemiyorsa küçült."),
        ("inflation_dist", "Engel çevresinde sıfırdan büyük ceza uygulanan tampon bölge (m). Etkili olması için `min_obstacle_dist`'ten büyük olmalı."),
        ("dynamic_obstacle_inflation_dist", "Dinamik engellerin tahmin edilen konumları çevresindeki tampon bölge (m)."),
        ("include_dynamic_obstacles", "true ise dinamik engellerin hareketi sabit hız modeliyle tahmin edilir (homotopi sınıfı aramasını da etkiler); false ise tüm engeller durağan sayılır."),
        ("include_costmap_obstacles", "Costmap'teki engellerin doğrudan hesaba katılıp katılmayacağı. Ayrı bir engel algılama/kümeleme yoksa true olmalı. Dolu her costmap hücresi bir nokta engel sayılır; bu yüzden costmap çözünürlüğünü çok küçük seçme (hesap süresi artar)."),
        ("legacy_obstacle_association", "true ise eski ilişkilendirme (her engel için en yakın TEB pozunu bul), false ise yenisi (her poz için yalnızca ilgili engelleri bul)."),
        ("obstacle_association_force_inclusion_factor", "Yeni ilişkilendirmede `min_obstacle_dist`'in bu katı kadar yakındaki tüm engeller zorunlu olarak dahil edilir. Örn. 2,0: 2 × `min_obstacle_dist` yarıçapı."),
        ("obstacle_association_cutoff_factor", "`min_obstacle_dist`'in bu katından uzak tüm engeller optimizasyonda yok sayılır. Önce `force_inclusion_factor` işlenir."),
        ("costmap_obstacles_behind_robot_dist", "Robotun arkasındaki dolu costmap hücrelerinden, ne kadar uzaklığa (m) kadar olanların planlamada dikkate alınacağı."),
        ("obstacle_poses_affected", "Her engel yörüngedeki en yakın poza bağlanır (hesap yükünü azaltmak için); bu pozun ayrıca kaç komşusunun etkileneceği."),
        ("costmap_converter_plugin", "Costmap hücrelerini nokta/çizgi/çokgene çeviren `costmap_converter` eklentisinin adı. Boş bırakılırsa dolu her hücre nokta engel sayılır."),
        ("costmap_converter_spin_thread", "true ise dönüştürücü kendi geri çağırma kuyruğunu ayrı bir iş parçacığında çalıştırır. Dönüştürücünün çalışma sıklığı bu sürümde (0.9.1) parametreyle ayarlanamaz, 5 Hz'e sabittir; `costmap_converter_rate` verilse de okunmaz."),
    ]),
    ("Optimizasyon", "Optimizasyonun kaç adım çalışacağı ve hangi hedeflerin ne kadar önemli olduğu. Ağırlıklar bir \"ceza\" gibidir: büyütülen hedef daha sıkı uygulanır.", [
        ("no_inner_iterations", "Her dış döngü adımında çözücünün çalıştırılacağı iç iterasyon sayısı."),
        ("no_outer_iterations", "Her dış döngü adımı yörüngeyi yeniden boyutlandırır ve `no_inner_iterations` kadar çözücü çalıştırır. İkisinin çarpımı planlama süresini belirler."),
        ("optimization_activate", "Optimizasyonu açar/kapatır."),
        ("optimization_verbose", "Ayrıntılı optimizasyon bilgisi yazdırır."),
        ("penalty_epsilon", "Sert kısıtları yaklaşık ifade eden ceza fonksiyonlarına küçük bir güvenlik payı ekler."),
        ("weight_max_vel_x", "Azami öteleme hızı sınırına uyma ağırlığı."),
        ("weight_max_vel_y", "Azami yana kayma hızına uyma ağırlığı (yalnızca holonomik robotlar)."),
        ("weight_max_vel_theta", "Azami dönüş hızı sınırına uyma ağırlığı."),
        ("weight_acc_lim_x", "Azami öteleme ivmesi sınırına uyma ağırlığı."),
        ("weight_acc_lim_y", "Azami yana kayma ivmesine uyma ağırlığı (yalnızca holonomik robotlar)."),
        ("weight_acc_lim_theta", "Azami dönüş ivmesi sınırına uyma ağırlığı."),
        ("weight_kinematics_nh", "Holonomik olmayan kinematiğe (yana kayamama) uyma ağırlığı. Diferansiyel ve araba benzeri robotta yüksek tut (genelde 1000)."),
        ("weight_kinematics_forward_drive", "Robotu yalnızca ileri yönü seçmeye zorlama ağırlığı (pozitif hızlar; yalnızca diferansiyel sürüş). Büyütürsen robot geri gitmekten kaçınır."),
        ("weight_kinematics_turning_radius", "En küçük dönüş yarıçapını zorlama ağırlığı (araba benzeri robotlar)."),
        ("weight_optimaltime", "Yörüngeyi geçiş süresi bakımından kısaltma ağırlığı. Büyütmek robotu daha hızlı ve atak yapar."),
        ("weight_shortest_path", "Yörüngeyi yol uzunluğu bakımından kısaltma ağırlığı."),
        ("weight_obstacle", "Engellerden en az mesafeyi koruma ağırlığı. Robot engellere fazla yaklaşıyorsa büyüt."),
        ("weight_inflation", "Şişirme (inflation) cezasının ağırlığı; küçük olmalı."),
        ("weight_dynamic_obstacle", "Dinamik engellerden en az mesafeyi koruma ağırlığı."),
        ("weight_dynamic_obstacle_inflation", "Dinamik engel şişirme cezasının ağırlığı; küçük olmalı."),
        ("weight_viapoint", "Via noktalarına uzaklığı azaltma ağırlığı."),
        ("weight_prefer_rotdir", "Belirli bir dönüş yönünü tercih etme ağırlığı; şu an yalnızca salınım algılandığında (`oscillation_recovery`) etkin."),
        ("weight_adapt_factor", "Bazı özel ağırlıklar (şu an `weight_obstacle`) her dış TEB iterasyonunda bu çarpanla büyütülür (yeni = eski × çarpan). Baştan çok büyük bir değer vermek yerine kademeli artırmak sayısal koşulları iyileştirir."),
        ("obstacle_cost_exponent", "Doğrusal olmayan engel maliyeti için üs; 1 ise doğrusal maliyet (varsayılan)."),
    ]),
    ("Homotopi sınıfı planlama", "Birden çok alternatif yörüngeyi (bir engelin solundan ya da sağından geçmek gibi) aynı anda optimize edip en iyisini seçer. Tek yörüngeli planlamadan çok daha fazla işlemci ister.", [
        ("enable_homotopy_class_planning", "Homotopi sınıfı planlamasını açar. Kapalıyken tek bir yörünge optimize edilir."),
        ("enable_multithreading", "Birden çok yörüngenin paralel planlanması için çoklu iş parçacığını açar."),
        ("simple_exploration", "true ise alternatif yörüngeler basit sol-sağ yaklaşımıyla (her engelin solundan ya da sağından geç) üretilir; false ise başlangıç ile hedef arasındaki bir bölgede rastgele yol haritası örneklenir."),
        ("max_number_classes", "Kabul edilen en çok alternatif homotopi sınıfı sayısı (hesap yükünü sınırlar)."),
        ("selection_cost_hysteresis", "Yeni bir adayın seçilmiş yörüngenin yerini alması için maliyetinin ne kadar düşük olması gerektiği (seçim: yeni_maliyet < eski_maliyet × çarpan). 1'in altındaki değer geçiş için gerçek bir iyileşme ister."),
        ("selection_prefer_initial_plan", "Başlangıç planının eşdeğerlik sınıfındaki yörüngenin maliyetine (0, 1) aralığında bir azaltma çarpanı uygular; küçüldükçe bu sınıf tercih edilir."),
        ("selection_obst_cost_scale", "En iyi adayı seçerken engel maliyetlerine uygulanan ek ölçek."),
        ("selection_viapoint_cost_scale", "En iyi adayı seçerken via noktası maliyetlerine uygulanan ek ölçek."),
        ("selection_alternative_time_cost", "true ise zaman maliyeti yerine toplam geçiş süresi kullanılır."),
        ("switching_blocking_period", "Yeni bir eşdeğerlik sınıfına geçişe izin verilmeden önce geçmesi gereken süre (sn). Yörünge sürekli değişiyorsa büyüt."),
        ("roadmap_graph_no_samples", "`simple_exploration` kapalıyken yol haritası grafiği için üretilecek örnek sayısı."),
        ("roadmap_graph_area_width", "Başlangıç ile hedef arasında örneklerin üretileceği dikdörtgen bölgenin genişliği (m); yüksekliği başlangıç-hedef mesafesine eşittir."),
        ("roadmap_graph_area_length_scale", "Bölgenin uzunluğu başlangıç-hedef mesafesinden belirlenir; bu parametre mesafeyi (geometrik merkez sabit kalacak şekilde) ölçekler."),
        ("h_signature_prescaler", "Çok sayıda engele izin vermek için engel değerlerini ölçekler. Çok küçük seçme; engeller birbirinden ayırt edilemez (0,2 < H ≤ 1)."),
        ("h_signature_threshold", "İki h-imzası, gerçek ve sanal kısımlarının farkı bu eşiğin altındaysa eşit sayılır."),
        ("obstacle_keypoint_offset", "`simple_exploration` açıkken engelin sol ve sağında (`min_obstacle_dist`'e ek olarak) yeni anahtar nokta oluşturulacak mesafe (m)."),
        ("obstacle_heading_threshold", "Engel yönü ile hedef yönü arasındaki normalize skaler çarpımın, engellerin keşifte dikkate alınması için eşiği [0, 1]."),
        ("viapoints_all_candidates", "true ise farklı topolojideki tüm yörüngeler via noktalarına bağlanır; false ise yalnızca başlangıç/global planla aynı topolojide olan."),
        ("visualize_hc_graph", "Yeni homotopi sınıflarını keşfetmek için oluşturulan grafiği görselleştirir."),
        ("delete_detours_backwards", "Açıksa, en iyi plana göre geriye doğru dolambaç yapan planlar atılır."),
        ("detours_orientation_tolerance", "Bir planın başlangıç yönü en iyi plandan bu değerden (rad) fazla farklıysa dolambaç sayılır."),
        ("length_start_orientation_vector", "Bir planın başlangıç yönünü hesaplamakta kullanılan vektörün uzunluğu (m)."),
        ("max_ratio_detours_duration_best_duration", "Bir planın süresinin en iyi planın süresine oranı bunu aşarsa dolambaç sayılıp atılır."),
    ]),
    ("Kurtarma", "Planlayıcı sıkıştığında ya da salındığında devreye giren önlemler.", [
        ("shrink_horizon_backup", "Otomatik algılanan sorunlarda planlayıcının ufku geçici olarak küçültmesine (%50) izin verir."),
        ("shrink_horizon_min_duration", "Uygulanamaz yörünge algılandığında küçültülmüş ufkun en az ne kadar (sn) korunacağı."),
        ("oscillation_recovery", "Aynı eşdeğerlik sınıfındaki çözümler arasında (sol/sağ/ileri/geri) sık gidip gelmeyi algılayıp çözmeye çalışır."),
        ("oscillation_v_eps", "Ortalama normalize doğrusal hız için eşik: bu ve `oscillation_omega_eps` birlikte aşılmazsa olası bir salınım algılanır."),
        ("oscillation_omega_eps", "Ortalama normalize açısal hız için eşik: bu ve `oscillation_v_eps` birlikte aşılmazsa olası bir salınım algılanır."),
        ("oscillation_recovery_min_duration", "Salınım algılandıktan sonra kurtarma kipinin en az kaç sn açık kalacağı."),
        ("oscillation_filter_duration", "Salınım algılaması için filtre uzunluğu/süresi (sn)."),
    ]),
]
# YAML'dan okunan, dinamik ayarda bulunmayan TEB parametreleri: ad -> (tür, varsayılan)
TEB_EK = {
    "odom_topic": ("string", "odom"), "map_frame": ("string", "odom"),
    "min_samples": ("int", 3), "max_samples": ("int", 500),
    "global_plan_prune_distance": ("double", 1.0),
    "min_resolution_collision_check_angular": ("double", math.pi),
    "control_look_ahead_poses": ("int", 1),
    "footprint_model/type": ("string", "point"),
    "footprint_model/radius": ("double", None), "footprint_model/line_start": ("double[2]", None),
    "footprint_model/line_end": ("double[2]", None), "footprint_model/front_offset": ("double", None),
    "footprint_model/front_radius": ("double", None), "footprint_model/rear_offset": ("double", None),
    "footprint_model/rear_radius": ("double", None), "footprint_model/vertices": ("double[][2]", None),
    "complete_global_plan": ("bool", True),
    "costmap_converter_plugin": ("string", ""), "costmap_converter_spin_thread": ("bool", True),
    "weight_prefer_rotdir": ("double", 50.0),
    "enable_homotopy_class_planning": ("bool", True), "simple_exploration": ("bool", False),
    "obstacle_keypoint_offset": ("double", 0.1),
    "delete_detours_backwards": ("bool", True),
    "detours_orientation_tolerance": ("double", math.pi / 2),
    "length_start_orientation_vector": ("double", 0.4),
    "max_ratio_detours_duration_best_duration": ("double", 3.0),
    "shrink_horizon_min_duration": ("double", 10.0),
    "oscillation_v_eps": ("double", 0.1), "oscillation_omega_eps": ("double", 0.1),
    "oscillation_recovery_min_duration": ("double", 10.0), "oscillation_filter_duration": ("double", 10.0),
}


def md_code(text):
    """Açıklamalardaki `kod` işaretlerini <code>'a, **kalın**'ı <strong>'a çevirir."""
    out, parts = [], html.escape(text).split("`")
    for i, part in enumerate(parts):
        out.append(f"<code>{part}</code>" if i % 2 else part)
    return re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", "".join(out))


def table(prefix, groups, cfg_list, extra):
    cfg = {}
    for p in cfg_list:
        cfg.setdefault(p["name"], p)          # aynı ad iki grupta varsa ilkini al
    used, parts = set(), []
    for gname, gintro, items in groups:
        rows = []
        for name, desc in items:
            used.add(name)
            if name in cfg:
                p = cfg[name]
                typ, default, rg, live = p["type"], fmt(p["default"]), rng(p), True
            elif name in extra:
                typ, dflt = extra[name]
                default = fmt(dflt) if dflt is not None else "—"
                rg, live = "—", False
            else:
                raise SystemExit(f"Tanımsız parametre: {prefix}/{name}")
            tag = "" if live else ' <span class="tag2">yalnızca YAML</span>'
            rows.append(
                f'<tr id="{prefix}-{name.replace("/", "-")}"><td><code>{html.escape(name)}</code>{tag}</td>'
                f'<td>{html.escape(typ)}</td><td class="n"><code>{html.escape(default)}</code></td>'
                f'<td class="n">{html.escape(rg)}</td><td>{md_code(desc)}</td></tr>'
            )
        parts.append(
            f"<h3>{html.escape(gname)}</h3>\n<p>{md_code(gintro)}</p>\n"
            '<div class="tw ptab"><table><thead><tr><th>Parametre</th><th>Tür</th><th class="n">Varsayılan</th>'
            '<th class="n">Aralık</th><th>Açıklama</th></tr></thead><tbody>\n' + "\n".join(rows) + "\n</tbody></table></div>"
        )
    missing = set(cfg) - used - {"restore_defaults"}
    if missing:
        raise SystemExit(f"Açıklaması yazılmamış cfg parametreleri ({prefix}): {sorted(missing)}")
    n_cfg = len([n for n in used if n in cfg])
    return "\n".join(parts), len(used), n_cfg


DWA_HTML, dwa_total, dwa_live = table("dwa", DWA_GROUPS, DATA["dwa"], DWA_EK)
TEB_HTML, teb_total, teb_live = table("teb", TEB_GROUPS, DATA["teb"], TEB_EK)

PAGE = f"""<section id="dwa-parametreleri">
<h2>DWA parametreleri</h2>
<p><code>dwa_local_planner/DWAPlannerROS</code> yerel planlayıcısının <strong>{dwa_total} parametresi</strong>. Bunların {dwa_live}'ü çalışırken <code>rqt_reconfigure</code> ile değiştirilebilir; kalanı yalnızca YAML'dan okunur.</p>
<div class="call"><b>Bu sayfadaki değerler nereden geliyor?</b>
<p>Parametre adları, türler, varsayılanlar ve aralıklar bu dökümanın hazırlandığı ROS Noetic paketlerinden (<code>dwa_local_planner</code> 1.17.3, <code>teb_local_planner</code> 0.9.1) okundu: paketlerin dinamik ayar tanımlarından, başlık dosyalarından ve derlenmiş kütüphanelerinin içindeki parametre adlarından. Açıklamalar Türkçe özetlerdir; kesin tanım için resmî ROS wiki sayfalarına bak. Sürümün farklıysa küçük farklar olabilir.</p></div>

<h3>Nasıl verilir?</h3>
<p><code>move_base</code>'e hangi yerel planlayıcının kullanılacağını söyler, parametreleri planlayıcının adı altında bir YAML dosyasına yazarsın:</p>
<pre><code># move_base parametresi (launch'ta ya da YAML'da)
base_local_planner: "dwa_local_planner/DWAPlannerROS"

# dwa.yaml
DWAPlannerROS:
  max_vel_x: 0.5
  min_vel_x: -0.1
  max_vel_y: 0.0
  min_vel_y: 0.0
  vy_samples: 1
  max_vel_theta: 1.0
  min_vel_theta: 0.2
  acc_lim_x: 0.5
  acc_lim_theta: 1.0
  sim_time: 2.0
  xy_goal_tolerance: 0.10
  yaw_goal_tolerance: 0.10</code></pre>
<p>Yazmadığın her parametre bu tablodaki varsayılanı alır. Varsayılanlar genel amaçlıdır, senin robotuna göre ayarlanmamıştır; hız ve ivme sınırlarını mutlaka kendi robotuna göre belirle.</p>
<div class="call"><b>DWA'nın simülasyon adımı</b>
<p>DWA, yörüngeleri simüle ederken kullandığı zaman adımını (<code>sim_period</code>) <code>1 / controller_frequency</code> olarak hesaplar; parametreyi bulamazsa 20 Hz varsayar (Noetic kaynak kodunda doğrulandı, wiki'de yazmaz). Bu yüzden <code>controller_frequency</code>'yi değiştirmek DWA'nın davranışını da değiştirir.</p></div>

{DWA_HTML}

<h3>Sık görülen durumlar için başlangıç noktaları</h3>
<p>Bunlar kesin kurallar değil, denemeye başlanacak yerlerdir. Her seferinde <strong>tek parametre</strong> değiştir ve sonucu RViz'de izle.</p>
<div class="tw"><table><thead><tr><th>Belirti</th><th>Önce bunlara bak</th></tr></thead><tbody>
<tr><td>Robot global yoldan sapıyor, kestirme yapıyor</td><td><code>path_distance_bias</code> ↑ ya da <code>goal_distance_bias</code> ↓</td></tr>
<tr><td>Robot yola fazla yapışıyor, hedefe ilerlemiyor</td><td><code>goal_distance_bias</code> ↑ ya da <code>path_distance_bias</code> ↓</td></tr>
<tr><td>Engellere fazla yaklaşıyor</td><td><code>occdist_scale</code> ↑; costmap'te <code>inflation_radius</code> ve <code>footprint</code></td></tr>
<tr><td>Dar geçitten geçmiyor</td><td><code>occdist_scale</code> ↓; costmap'te <code>inflation_radius</code> ↓</td></tr>
<tr><td>Sağa sola gidip geliyor (salınım)</td><td><code>sim_time</code> ↑, <code>oscillation_reset_dist</code>, <code>occdist_scale</code> ↓</td></tr>
<tr><td>Yerinde dönemiyor ya da dönüşte takılıyor</td><td><code>min_vel_theta</code> ↓, <code>acc_lim_theta</code> ↑, <code>twirling_scale</code> 0</td></tr>
<tr><td>Hedefte titriyor</td><td><code>xy_goal_tolerance</code> ↑, <code>latch_xy_goal_tolerance: true</code></td></tr>
<tr><td>Çok yavaş</td><td><code>max_vel_x</code> ↑, <code>acc_lim_x</code> ↑, <code>vx_samples</code> ↑</td></tr>
<tr><td>Robot yana kaymayı deniyor (diferansiyel robot)</td><td><code>max_vel_y: 0</code>, <code>min_vel_y: 0</code>, <code>vy_samples: 1</code></td></tr>
<tr><td>İşlemci yükü yüksek</td><td><code>vx_samples</code>, <code>vth_samples</code> ↓; <code>sim_time</code> ↓</td></tr>
</tbody></table></div>
</section>

<section id="teb-parametreleri">
<h2>TEB parametreleri</h2>
<p><code>teb_local_planner/TebLocalPlannerROS</code> yerel planlayıcısının <strong>{teb_total} parametresi</strong>. Bunların {teb_live}'ü çalışırken <code>rqt_reconfigure</code> ile değiştirilebilir; geri kalanı (ayak izi modeli, dönüş yarıçapı, örnek sayıları gibi) yalnızca YAML'dan okunur ve tabloda <span class="tag2">yalnızca YAML</span> etiketiyle işaretlidir.</p>
<p><strong>TEB</strong> (Timed Elastic Band), yolu zaman etiketli bir "elastik bant" olarak ele alır: başlangıç yörüngesini engellerden uzaklaştırıp hız, ivme ve kinematik kısıtlarına uydurur ve toplam süreyi kısaltır. Her hedef (engelden uzak dur, hızlı git, kısıtlara uy) bir <strong>ağırlıkla</strong> ifade edilir; parametrelerin çoğu bu dengeyi ayarlamak içindir.</p>

<h3>Nasıl verilir?</h3>
<pre><code>base_local_planner: "teb_local_planner/TebLocalPlannerROS"

# teb.yaml (diferansiyel sürüşlü robot için başlangıç)
TebLocalPlannerROS:
  odom_topic: odom
  map_frame: odom

  max_vel_x: 0.5
  max_vel_x_backwards: 0.1
  max_vel_theta: 1.0
  acc_lim_x: 0.5
  acc_lim_theta: 1.0
  min_turning_radius: 0.0        # diferansiyel sürüş: 0
  footprint_model:
    type: "polygon"
    vertices: [[0.4, 0.3], [0.4, -0.3], [-0.4, -0.3], [-0.4, 0.3]]

  xy_goal_tolerance: 0.10
  yaw_goal_tolerance: 0.10
  min_obstacle_dist: 0.3
  inflation_dist: 0.5
  include_costmap_obstacles: true
  enable_homotopy_class_planning: false</code></pre>
<div class="call warn"><b>Varsayılanlar üç katmandan gelir</b>
<p>Bir parametreyi YAML'a yazmazsan değeri şu sırayla belirlenir (sağdaki soldakini ezer): <em>kaynak koddaki başlangıç değeri</em> → <em>dinamik ayar tanımındaki varsayılan</em> → <em>YAML'da verdiğin değer</em>. Bu sayfadaki "Varsayılan" sütunu, geçerli olan değeri gösterir: dinamik ayarda tanımlı olanlar için o değer, <span class="tag2">yalnızca YAML</span> olanlar için kaynak koddaki başlangıç değeri (ayak izi modeli parametrelerinde TEB wiki'sindeki varsayılanlar). Bu yüzden kaynak koddaki bazı sabitlerle (örneğin <code>selection_obst_cost_scale</code> için 100) sayfadaki değer (2) farklı olabilir.</p></div>
<div class="call"><b>Costmap ayak izi ile TEB ayak izi</b>
<p>Costmap'in <code>footprint</code>'i, yolun uygulanabilir olup olmadığını (çarpışma denetimi) belirler; TEB'in <code>footprint_model</code>'i ise optimizasyonda engellerden uzaklığı hesaplamak için kullanılır. İkisi robotun gerçek şekliyle <strong>tutarlı</strong> olmalıdır; biri diğerinden küçükse robot ya dar yerlerden geçemez ya da engellere yaklaşır.</p></div>
<div class="call"><b>Eski adlar</b>
<p>Bazı parametreler yeniden adlandırılmıştır; TEB eski adı görürse uyarı verir. Örneğin <code>global_plan_via_point_sep</code> artık <code>global_plan_viapoint_sep</code>, <code>alternative_time_cost</code> ise <code>selection_alternative_time_cost</code>'tir.</p></div>

{TEB_HTML}

<h3>Sık görülen durumlar için başlangıç noktaları</h3>
<p>Bunlar kesin kurallar değil, denemeye başlanacak yerlerdir. Her seferinde <strong>tek parametre</strong> değiştir; ağırlıkları çok büyütmek optimizasyonu kararsızlaştırabilir.</p>
<div class="tw"><table><thead><tr><th>Belirti</th><th>Önce bunlara bak</th></tr></thead><tbody>
<tr><td>Engellere fazla yaklaşıyor</td><td><code>min_obstacle_dist</code> ↑, <code>weight_obstacle</code> ↑, <code>inflation_dist</code> ↑; <code>footprint_model</code> gerçek şekle uyuyor mu?</td></tr>
<tr><td>Dar geçitten geçmiyor</td><td><code>min_obstacle_dist</code> ↓; costmap'te <code>inflation_radius</code> ↓</td></tr>
<tr><td>Yerinde dönmüyor, geniş kavis çiziyor</td><td><code>min_turning_radius: 0</code> (diferansiyel sürüşte), <code>weight_kinematics_turning_radius</code></td></tr>
<tr><td>Sürekli geri geri gidiyor</td><td><code>weight_kinematics_forward_drive</code> ↑, <code>max_vel_x_backwards</code> ↓, <code>allow_init_with_backwards_motion: false</code></td></tr>
<tr><td>Yavaş ve tereddütlü</td><td><code>max_vel_x</code> ↑, <code>acc_lim_x</code> ↑, <code>weight_optimaltime</code> ↑</td></tr>
<tr><td>Yörünge sürekli sağ-sol değişiyor</td><td><code>selection_cost_hysteresis</code> ↓, <code>switching_blocking_period</code> ↑, <code>oscillation_recovery: true</code></td></tr>
<tr><td>Hedefte oyalanıyor</td><td><code>xy_goal_tolerance</code> ↑, <code>yaw_goal_tolerance</code> ↑, <code>free_goal_vel</code></td></tr>
<tr><td>"Trajectory not feasible" uyarıları</td><td><code>feasibility_check_no_poses</code>, <code>min_obstacle_dist</code>; costmap footprint'i ile TEB <code>footprint_model</code>'in tutarlılığı</td></tr>
<tr><td>İşlemci yükü yüksek</td><td><code>enable_homotopy_class_planning: false</code>, <code>no_inner_iterations</code> ve <code>no_outer_iterations</code> ↓, <code>max_samples</code> ↓, <code>dt_ref</code> ↑</td></tr>
<tr><td>Robot geç tepki veriyor</td><td><code>dt_ref</code> ↓ (kontrol periyodu ile uyumlu), <code>controller_frequency</code> ↑ (move_base)</td></tr>
</tbody></table></div>
<p>Kavramsal karşılaştırma (DWA mı, TEB mi?) ve genel navigasyon ayar sırası için <a href="#navigasyon">Harita ve navigasyon</a> sayfasına dön.</p>
</section>
"""
OUT.write_text(PAGE, encoding="utf-8")
print(f"DWA: {dwa_total} parametre ({dwa_live} canlı) | TEB: {teb_total} parametre ({teb_live} canlı)")
