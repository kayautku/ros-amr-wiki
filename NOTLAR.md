## GitHub deposu (29 Eylül 2026)

Site git'e alındı ve https://github.com/kayautku/ros-amr-wiki adresine gönderildi (SSH, `main` dalı; commit kimliği depo-yerel: kayautku / kayautku08@gmail.com). Değişikliklerden sonra: `git add -A && git commit -m "..." && git push`. GitHub Pages istenirse: Settings → Pages → main / (root).

## ~/.bashrc açıklaması netleştirildi (29 Eylül 2026)

`yapi-ve-araclar` "Workspace kurma" ve `baslarken` 3. adım: `.bashrc`'ye ekleme artık `echo ... >> ~/.bashrc` + `source ~/.bashrc` komutuyla gösteriliyor; `.bashrc`'nin ne olduğu, `>>`/`>` farkı, `tail -n 3` ile kontrol, satır sırası (önce /opt/ros, sonra workspace), ilk `catkin_make`'ten sonra ekleme, göreli/tam yol farkı ve çift eklenme uyarısı eklendi. Build temiz (19 sayfa, 58 bölüm), sayfa headless Chrome'da kontrol edildi. claude.ai yayını henüz güncellenmedi.

## claude.ai yayını (28 Eylül 2026)

Site telefondan erişim için özel Artifact olarak yayınlandı: https://claude.ai/artifact/4bf5Xnc1MJ2z7vymekzcGt (yalnızca sahibi açabilir; paylaşım sayfanın Share menüsünden). Yayın otomatik güncellenmez: site değişince yeniden yayınlanmalı (bu URL `url` olarak verilerek). Not: `assets/mermaid.min.js` içindeki tek bir düz U+FFFD karakteri yayın aracınca reddediliyor; yayında dizgi içindeki bu karakter `\uFFFD` kaçışıyla değiştirilmiş bir kopya kullanıldı (anlamı aynı, projedeki dosya değiştirilmedi).

## SMACH rehberi (28 Eylül 2026)

Kullanıcı isteği: SMACH ile ilgili hataları düzelt, tam bir rehber yap.

**Yapıldı:**
- Yeni sayfa `_src/pages/smach.html` ("B · AMR yığını", `gorev-ve-docking`'den sonra). Bölümler: `smach` (giriş), `smach-durum`, `smach-makine`, `smach-userdata`, `smach-ros` (SimpleActionState/ServiceState/MonitorState), `smach-kapsayici` (iç içe, Concurrence, Sequence/Iterator), `smach-izleme` (IntrospectionServer, Ctrl+C, ActionServerWrapper), `smach-ornek` (pil izlemeli devriye, tam kod), `smach-hatalar`.
- `gorev-ve-docking.html`'deki eski SMACH bölümü kısa özet + bağlantıya indirildi. Düzeltilen hatalar: tanımsız `GoTo`/`DockState` sınıflı çalışmayan kod parçası, "smach_viewer çalışan makineyi gösterir" iddiası (IntrospectionServer gerekir), sonsuz "failed → kendine dön" diyagramı. Zihin haritası, yol haritası ve sözlük bağlantıları `#smach`'a çevrildi. README sayfa tablosu güncellendi.
- Tüm API iddiaları kurulu kaynaktan (smach/smach_ros 2.5.3) okundu. Tam örnek, sahte move_base + pil yayıncısıyla (ayrı port roscore) çalıştırıldı: normal bitiş, ulaşılamayan noktanın 3 denemede atlanması, düşük pil → GO_CHARGE, 8 farklı anda Ctrl+C → hepsi temiz `preempted`, move_base hedefi iptal edildi. `smach_viewer.py` adı Noetic deb'inden (4.1.0) doğrulandı.
- Test sırasında bulunan ve rehbere yazılan gerçek tuzaklar: `cb_interface`'te `io_keys` yok; yalnızca output_keys'teki anahtar geri okunamaz; bildirilmemiş anahtara yazma sadece loglanır; tutarlılık hatasında `execute()` `None` döner; **`set_preempt_handler` + ana thread'de `execute()` Ctrl+C'de kilitlenir** (sinyal işleyicisi ana thread'de makineyi bekler) → çözüm worker thread; MonitorState `cond_cb` True=devam.
- Build: 19 sayfa, 58 bölüm; kırık bağlantı 0; smach ve gorev sayfalarındaki mermaid'ler çiziliyor (headless Chrome).

## Wiki tarzına geçiş, örnek robot ayrı sayfada (28 Eylül 2026)

Kullanıcı kararı: site belirli bir örnek projeye bağlı öğretici olmaktan çıkıp **wiki.ros.org gibi bilgi içerikli** olacak; örnek robot **ayrı bir sayfaya** taşınıp "geliştirilecek" olarak işaretlenecek.

**Yapıldı (kaynak dosyalarda):**
- Yeni sayfa `_src/pages/ornek-robot.html` ("E · Örnek (geliştiriliyor)" grubu, `build.py` PAGES'e eklendi). Bölümler: `ornek-robot`, `ornek-urdf`, `ornek-sim`, `ornek-navigasyon`, `ornek-yapilacaklar`. Sayfanın başında "geliştirme aşamasında" uyarısı var. Gerçek TEB değerleri (footprint ±0,95×±0,70, inflation 1,1, max_vel_x 0,5 …) buraya taşındı.
- Öğretici sayfalar genelleştirildi: `amr_*` → `myrobot_*`, `~/amr_ws` → `~/catkin_ws`, `/robot/camera/image_raw` → `/camera/image_raw`, üç lidar topic'i → genel `/scan`. `robot-ve-simulasyon.html` baştan yazıldı (joint türleri tablosu, xacro makrolu genel iskelet, diff drive varsayılan tablosu, empty_world argümanları, Gazebo eklenti listesi, genel lidar birleştirme örneği). `harita-ve-navigasyon.html`'deki örnek robota özgü tablo, genel "başlangıç değerleri" tablosu + 0,40×0,30 m'lik robot için YAML ile değiştirildi; TEB `footprint_model` uyarısı eklendi.
- İncelemede bulunan hatalar düzeltildi: map_server `mode` (trinary/scale/raw) ve zorunlu YAML alanları, `cost_scaling_factor` formülü (iç yarıçap, 252 çarpanı), "4 katımın" yazım hatası, RViz Path topic'i, zihin haritasındaki IMU ve `#param` bağlantısı, TF diyagramı (örnek sayfada `kule_link` eklendi), map_saver mutlak yol iddiası, watchdog/twist_mux topic tutarsızlığı, `mission_node`'un doğrudan `/cmd_vel`'e yazması, actionlib'e SimpleActionServer örneği.
- `gen_nav_reference.py` de aynı değişikliklerle güncellendi (map_server, costmap formülü, yazım hatası, ira başlığı), böylece yeniden üretim düzeltmeleri silmez.
- Kenar çubuğundaki "Örnek proje: ~/amr_ws" satırı kaldırıldı. README güncellendi.

**Yapılmadı / doğrulanacak:**
- Üreticiler ve `build.py` çalıştırıldı: 18 sayfa, 49 bölüm, "bilinmeyen bölüm bağlantısı" uyarısı yok. Sayfalar tarayıcıda (headless Chrome ile) **görsel olarak kontrol edilmedi**; kopyala butonları, mermaid ve zihin haritasındaki yeni "Örnek robot" dalı gözle bakılmalı.
- **Parametre doğrulaması yapıldı (aynı gün, sonraki tur).** Kurulu sürümlerin etiketli kaynak kodu indirildi (navigation 1.17.3, slam_gmapping 1.4.2, ira_laser_tools 1.0.7, teb_local_planner 0.9.1, twist_mux noetic-devel) ve JSON'daki her ad/varsayılan `param()`/`getParam()` çağrılarıyla, aralıklar kurulu `dynamic_reconfigure` cfg modülleriyle otomatik karşılaştırıldı. AMCL (52), gmapping (37), ira (10), DWA (35 cfg + 6 ek), map_server adları: hepsi doğru çıktı. Düzeltilenler:
  - move_base varsayılan `recovery_behaviors`: 4 adım (sonda ikinci `rotate_recovery`), 3 değil.
  - `clear_costmap_recovery/layer_names` varsayılanı `["obstacles"]` (birebir ad eşleşmesi); `["costmap"]` yanlıştı. Katmanı `obstacle_layer` adlı yapılandırmalarda varsayılan temizleme hiçbir şey yapmıyor; harita-ve-navigasyon YAML örneğine ve örnek robot yapılacaklarına eklendi.
  - `rotate_recovery`: `yaw_goal_tolerance`, `max_vel_theta` (1,0), `min_in_place_vel_theta` (0,4), `acc_lim_theta` (3,2) hangi planlayıcı kullanılırsa kullanılsın `~/TrajectoryPlannerROS/`'tan okunuyor; tabloya eklendi.
  - twist_mux: timeout/kilitte **sıfır hız yayınlamaz, susar**; `timeout: 0` = hiç zaman aşımı yok; zaman aşımına uğrayan kilit *etkin* sayılır. gorev-ve-docking ve pratik'teki "sıfır hız kullanır" iddiaları düzeltildi.
  - TEB: `max_vel_y`, `acc_lim_y`, `min_turning_radius`, `wheelbase`, `cmd_angle_instead_rotvel` canlı değiştirilebilir ("yalnızca YAML" değil) → 79 canlı. `footprint_model/*` alt parametrelerinin varsayılanı yok (eksikse point'e düşer). `costmap_converter_rate` 0.9.1'de hiç okunmuyor (5 Hz sabit) → tablodan çıkarıldı, not düşüldü.
  - DWA: eksik `odom_topic` (varsayılan `odom`) eklendi.
  - costmap: `width`/`height` üst sınırı, voxel `origin_z` sınırı, `combination_method` (99 = hiçbir şey yazma), voxel `max_obstacle_height` eklendi; AMCL ve inflation aralıkları cfg'den dolduruldu.
  - map_server eşikleri: YAML'da zorunlu; tablodaki varsayılanlar YAML'sız eski kullanımın `~param` varsayılanları.
  - AMCL `recovery_alpha_*` ve move_base `controller_patience`: kaynak varsayılanı (0,001/0,1 ve 15) başlangıçta geçerli, ama cfg varsayılanı (0 ve 5) farklı; rqt "Restore defaults" notu eklendi.
- **Genel tarama (aynı gün, son tur):** 18 sayfada kırık bağlantı/çapa, eksik dosya, yinelenen id, dengesiz HTML etiketi yok. 31 kod parçası (Python/XML/YAML) çözümleyiciden geçti. headless Chrome: JS konsol hatası yok, 9 mermaid diyagramının hepsi çiziliyor, her `pre`'de kopyala butonu var. Örnek launch dosyaları `roslaunch --nodes` ile çözümleniyor. Düzeltilen: genel URDF iskeletinde gövde kutusu zemine değiyordu (6 cm yukarı alındı), tekerlek ataletinde büyük eksen `izz` yerine `iyy` olmalıydı; REP-3 platform cümlesi netleştirildi ("önerilen", Fedora'ya paket yok). `check_urdf` bu makinede kurulu değil (`liburdfdom-tools`); URDF yapısı betikle denetlendi.
- **Kalıcı doğrulama aracı eklendi:** `_src/verify_params.py` (kullanım README'de). Bugünkü tüm elle yapılan karşılaştırmaları otomatikleştirir: kaynak kod (iki yönlü: JSON→kaynak ve kaynak→JSON), dynamic_reconfigure, DWA/TEB ek parametreleri ve 13 "kritik davranış" denetimi. Güncel veride 418 denetim, 0 hata. Doğrulayıcının kendisi test edildi: düzeltme öncesi JSON'la ve yapay hatalarla çalıştırıldığında bugün elle bulunan hataların hepsini (toparlanma listesi, layer_names, rotate_recovery eksikleri, TEB 5 canlı parametre, costmap_converter_rate, footprint uydurma varsayılanı, aralıklar) ve önbellekteki kaynakta değiştirilen bir varsayılanı yakaladı. Kaynak önbelleği `_src/.kaynak_onbellek/` (~0,6 MB, silinebilir, yeniden indirilir). `_src/data/nav_stack_local.json` (kullanılmayan eski dynamic_reconfigure dökümü) kullanıcı onayıyla silindi.
- **Açıklama metinleri denetimi (aynı gün, son tur):** Tüm Türkçe parametre açıklamaları kurulu cfg açıklamalarıyla ve gerektiğinde kaynak koddaki davranışla (amcl_laser.cpp, pf.c, costmap_2d_ros.cpp, clear_costmap_recovery.cpp, dwa_planner.cpp, teb_local_planner_ros.cpp, gazebo_ros_diff_drive.cpp) karşılaştırıldı. Düzeltilen anlam hataları: AMCL `beam_skip_threshold` (tersine anlatılmıştı), `beam_skip_error_threshold` (tüm ışınlar kullanılır), `do_beamskip` (yalnızca likelihood_field_prob + yakınsamış filtre), `laser_z_hit` (üç modelde de), `recovery_alpha_*` (kapatmak için ikisi de 0); costmap `plugins` (verilmezse Hydro öncesi düzene döner, boş kalmaz); voxel `unknown_threshold`/`mark_threshold`; static `lethal_cost_threshold` (≥), `use_maximum`; `reset_distance`/`conservative_reset_dist` (kenarı bu uzunlukta kare → robottan yarısı kadar ötesi); DWA `acc_lim_trans` (okunur ama kullanılmaz), `global_frame_id` (yörünge bulutu çerçevesi); TEB `map_frame` (costmap global_frame ile eziliyor, etkisiz); harita-ve-navigasyon'da "global planlayıcı saniyede birkaç kez yenilenir" (varsayılan planner_frequency 0). Gazebo diff_drive varsayılanları ve komut zaman aşımı olmaması kaynaktan doğrulandı.

**Örnek robot: geliştirilecek** (ayrıntı `ornek-robot.html#ornek-yapilacaklar`'da):
1. `depo.world` kapısı 1,5 m → robot (footprint 1,4 m, inflation 1,1 m) geçemez; genişlet (ör. 3 m), "üst lidar ~1,7 m" yorumunu 1,54 m yap.
2. `sim.launch`'ın `odom_source` argümanı URDF'te karşılıksız → `xacro:arg` + `<odometrySource>` ekle. (Önceki "sürüş hatası 0,000 m" sonucu bu yüzden anlamsız: odometri zaten `world`.)
3. Casterlar tekerleklerle aynı seviyede zemine değiyor (z=0,10, r=0,10); encoder odometrisiyle patinaj testi yap.
4. gmapping, AMCL, move_base bu robotla denenmedi; `amr_navigation` paketini yaz.
5. `amr_msgs`, `amr_docking`, `amr_mission` yok; docking şeridi olan dünya yok.
6. TurtleBot3 Waffle bölümü (aşağıdaki eski notlardaki karşılaştırma tablosu ESKİ robota göre: artık örnek robotta da `base_footprint` kök, kamera `/robot/camera/image_raw`, IMU yok; tabloyu buna göre düzelt).
7. `sim.launch`'taki "gövde merkezi 0,175 m" yorumu eski robottan; 0,317 m.

**Not:** Aşağıdaki eski bölümlerdeki "D · Paket referansı" adı artık "C · Paket referansı"; `lidar_merge.launch` gerçek yeri `examples/amr_description/launch/`.

---

## Kopyala butonu (25 Eylül 2026, dördüncü tur)

Kullanıcı: "kurulum için kodlar vermişsin ya onların kolay kopyalanmasını sağla tek tek uğraşmasınlar". Tüm kod/terminal bloklarına (mermaid diyagramları ve `.tree` dosya ağacı hariç) otomatik kopyala butonu eklendi.

**Yapıldı:**
- `assets/style.css`: `pre{position:relative}`, `.copybtn` (ve `.copied`/`.copyerr`/`.term .copybtn` varyantları) stilleri eklendi (satır ~69-90 civarı).
- `assets/site.js`: `initCopyButtons()` fonksiyonu eklendi — seçici `main pre:not(.mermaid):not(.tree)`, her `pre`'ye sağ üst köşede buton ekliyor. Kopyalama: `navigator.clipboard.writeText()` birincil, başarısız olursa gizli `<textarea>` + `execCommand('copy')` yedeği. Tıklayınca 1,5 sn "kopyalandı" (yeşil tik ikonu) ya da hata (turuncu) durumuna geçiyor. `boot()` içinde `initSearch(); initNav(); initCopyButtons(); runMermaid();` sırasıyla çağrılıyor.
- Doğrulama: headless Chrome ile `--dump-dom` kullanılarak her sayfada `.pre` sayısı = `.copybtn` sayısı olduğu, mermaid/`.tree` bloklarında buton OLMADIĞI, konsol hatası olmadığı doğrulandı. Zorla `opacity:1` CSS enjekte edilip ekran görüntüsüyle görsel yerleşim (sağ üst köşe, terminal başlığını bozmuyor) de kontrol edildi.
- `python3 _src/build.py` tekrar çalıştırıldı (assets/ dosyaları statik olduğu için build'e ihtiyaç yoktu ama emin olmak için çalıştırıldı, 17 sayfa/44 bölüm, hatasız).

**Not:** Bu değişiklik yalnızca `assets/style.css` ve `assets/site.js`'te; `_src/pages/*.html` içeriğine dokunulmadı.

## Öncelik güncellemesi (25 Eylül 2026, sonraki oturum)

Kullanıcının asıl amacı: **wiki.ros.org'un Türkçe bir alternatifini üretmek** (wiki sürekli erişim korumasına (Anubis) takılıp kapanıyor). Bu, sitenin kapsamını genişletti: artık yalnızca "kendi projen için öğretici" değil, gerçek ROS paketlerinin tam parametre referansı da hedefleniyor.

**Yapıldı:** Yeni "D · Paket referansı" bölümü, 6 sayfa: `ref-amcl-move-base.html` (AMCL 52 param + move_base 17+3+5 param), `ref-costmap.html` (costmap_2d + 4 katman, 59 param), `ref-slam-harita.html` (gmapping 37 param + map_server), `ref-tf-actionlib.html` (tf2/REP-105/actionlib, elle yazıldı), `ref-yardimci-paketler.html` (twist_mux + ira_laser_tools), `planlayici-parametreleri.html` (mevcut DWA/TEB, gruba taşındı). Veri kaynağı: ROS Noetic kaynak kodu (GitHub, `noetic-devel` — wiki.ros.org gibi engellenmiyor) + kurulu paketlerin `dynamic_reconfigure` tanımları. Üretici: `_src/gen_nav_reference.py` + `_src/data/nav_stack_verified.json`; her tablo satırı JSON'a karşı otomatik doğrulanıyor (uydurma parametre imkânsız). Zihin haritasına 7. dal (mor, "Paket referansı") eklendi; `--violet`/`--violet-tint` CSS token'ları yeni. Tüm öğretici sayfalardan (harita-ve-navigasyon, gorev-ve-docking, robot-ve-simulasyon, yapi-ve-araclar, iletisim, yol-haritasi, index) yeni sayfalara çapraz bağlantı eklendi. Site 17 sayfa, 580 bağlantı, 0 hata (tam doğrulama yapıldı).

**Devam edecek olursa sıradaki adaylar:** rosbag/rosparam/roslaunch XML gibi çekirdek CLI araçları için referans sayfası (kullanıcı önceki soruda "istersen bunu da ekle" seçeneğini reddetmemişti, seçmedi de); apriltag_ros, robot_localization, diagnostic_updater gibi bu oturumda kaynağı bulunmuş ama sayfası yazılmamış paketler.

## Güncelleme: örnek URDF artık gerçek robottan (aynı gün, üçüncü tur)

Kullanıcı "örnek urdf olarak benim pcdekini koysana" dedi. `~/catkin_ws/src/robot_v1_description/urdf/robot_v1_combined.urdf` **aynen** (`<robot name="robot_v1">` → `<robot name="amr">` dışında hiçbir şey değiştirilmeden) `examples/amr_description/urdf/amr.urdf.xacro`'ya kopyalandı. Ekransız Gazebo'da uçtan uca test edildi: xacro/SDF geçerli, spawn/sensör/TF/sürüş doğru (bkz. yukarıdaki "Yapıldı" test sonuçları, bu gerçek robotla tekrarlandı — sürüş hatası 0,000 m).

**Önemli fark, siteye yansıtıldı:** Gerçek robotun kök çerçevesi `base_footprint`'tir (`base_link` diye ayrı bir çerçeve **yok**), kamera topic'i `/robot/camera/image_raw`'dır, **IMU yok**. Bunlar önceki (icat edilmiş) örnek robotta `base_link` + `/camera/image_raw` + IMU var şeklindeydi. Aşağıdaki dosyalar bulunup düzeltildi (find-and-fix, tek tek kontrol edilerek — paket referans sayfalarındaki `base_link` mentions'lar PAKETİN gerçek varsayılanı olduğu için (AMCL/costmap_2d/gmapping) **dokunulmadı**, sadece "bizim örneğimiz" bağlamındaki mentions'lar değişti):
`robot-ve-simulasyon.html` (URDF iskeleti artık gerçek dosyadan alıntı + "gerçek, test edilmiş" callout'u, sensör tablosu gerçek sayılarla, IMU-yok notu), `harita-ve-navigasyon.html` (footprint/inflation/costmap/TEB değerleri artık `~/catkin_ws`'teki GERÇEK production config'ten — 0,95×0,70 footprint, inflation 1,1, TEB max_vel_x 0,5 max_vel_theta 0,3 vb.), `yapi-ve-araclar.html` (TF bölümü, mermaid diyagramı gerçek link adlarıyla — `left_wheel`, `kule_link`, 4×caster grubu, IMU çıkarıldı), `pratik.html`, `index.html`, `iletisim.html`, `gorev-ve-docking.html`, `ref-tf-actionlib.html`'deki örnek komut.

Site 17 sayfa, 537+ bağlantı, 0 hata ile tekrar tam doğrulandı. examples/amr_gazebo/launch/lidar_merge.launch'taki `destination_frame` de `base_link`→`base_footprint` düzeltildi (bu olmadan `/scan` hiç yayınlanmıyordu — gerçek testte yakalandı).

**Hâlâ yapılmayan:** TurtleBot3 Waffle sayfası (kullanıcı istemiş ama bu oturumda hiç dokunulmadı, öncelik değişti).

---

# Duraklatılan iş: örnek URDF ve TurtleBot3 Waffle sayfası

Durum tarihi: 25 Eylül 2026. Kullanıcı bu işi (Waffle testini özellikle) durdurup not düşülmesini istedi; yukarıdaki paket referansı önceliği bitmeden buna dönülmeyecek.

## İstenen
1. Siteye **örnek URDF** eklemek (sıfırdan öğrenen biri robotu görüp çalıştırabilsin).
2. İsteyenin, kendi robotunu yazmadan **TurtleBot3 Waffle ile de** deneyebilmesi için siteye **kısa bir sayfa/bölüm** eklemek.
   Waffle'ı derleyip test etmek istenmedi, yalnızca sayfa. (Yanlışlıkla derleyip test etmeye başlamıştım, bırakıldı.)

## Yapılanlar
- `examples/amr_description/` (URDF/xacro, `display.launch`, `lidar_merge.launch`) ve `examples/amr_gazebo/` (`sim.launch`, `depo.world`) yazıldı.
  Robot: diferansiyel sürüş, 0,8 x 0,6 m gövde, 3 lidar (`/scan_front_left`, `/scan_rear_right`, `/scan_top`), kamera, IMU.
- Gazebo'da ekransız (`gui:=false`) **test edildi ve çalıştı:**
  - xacro -> URDF geçerli; `gz sdf -p` ile SDF'e çevriliyor.
  - Robot yerleşiyor, dengede (z = 0,175 m). Tüm topic'ler var.
  - Hızlar: lidarlar 10 Hz, birleşik `/scan` 10 Hz (720 ışın, `base_link`), IMU ve odom 100 Hz, kamera ~18 Hz (ekransız yazılımsal render).
  - TF ağacı tam. Birleşik taramadaki duvar mesafeleri dünyayla örtüşüyor (batı 4,00 / kuzey 6,00 / ileri 16,00 m).
  - Sürüş: 0,3 m/s x 5,5 s -> gerçek 1,651 m, odometri 1,649 m. 0,5 rad/s x 6,28 s -> yaklaşık 180°.
- **Düzeltilen hata:** casterlar tekerlekle aynı yükseklikteydi, sert casterlar yükü taşıyıp tekerlekler patinaj yaptı
  (odometri 1,65 m diyordu, gerçek robot 7 cm gitmişti). Casterlar 1,5 mm yukarı alınınca düzeldi (`caster_z = -0.1235`).
- `sim.launch` ve URDF'e `odom_source` argümanı eklendi. Varsayılan `world` (Gazebo'nun gerçek pozu, kayma yok).

## Yapılmayanlar / açık konular
- **Siteye sayfa henüz eklenmedi.** Yapılacak:
  - `_src/pages/ornek-robot.html` yazmak (bölümler: örnek URDF ve Gazebo, TurtleBot3 Waffle) ve `_src/build.py` içindeki `PAGES` listesine eklemek.
  - Robot sayfasındaki kısaltılmış URDF iskeletini kaldırıp bu sayfaya bağlamak; yol haritası (aşama 3), dosya haritası, zihin haritası ve README'yi güncellemek.
  - Sayfadaki kod, `examples/` altındaki gerçek dosyalardan üretilmeli (tutarsızlık olmasın).
- **Haritalama (gmapping) bu robotla doğrulanmadı.** İlk denemede `odom_source: encoder` ile hızlı, çok sayıda yerinde dönüşlü rotada
  harita bozuk çıktı (odalar birbirinin üstüne döndü). `world` odometriyle deneme yarım kaldı (kapatıldı).
  Beklenen açıklama: encoder odometri yaw hatası birikiyor ve hızlı dönüşlerde 3 lidarın birleşik taraması zaman kayması yaşıyor.
  Sonra denenecek: yavaş sürüş (0,3 m/s, 0,3 rad/s), `world` odometri, gerekirse yalnızca `/scan_top` ile gmapping.
- **AMCL + move_base (sitedeki navigasyon örnekleriyle) bu robotla denenmedi.** Sitedeki sayılar (footprint 0,84 x 0,64 m, DWA/TEB örnekleri) ayrı testte çalıştı ama bu robotun fiziğiyle sınanmadı.
- Gazebo GUI, gerçek robot, docking (renkli şerit dünyası yok) test edilmedi.

## TurtleBot3 Waffle sayfası için toplanan bilgi (kaynak: ROBOTIS-GIT, `noetic` dalı; ÇALIŞTIRILIP DENENMEDİ)
- Kurulum: `sudo apt install ros-noetic-turtlebot3 ros-noetic-turtlebot3-simulations` (paket adları apt'te var). Ortam: `export TURTLEBOT3_MODEL=waffle` ya da `waffle_pi`.
- Komutlar: `roslaunch turtlebot3_gazebo turtlebot3_world.launch` (ya da `turtlebot3_empty_world.launch`),
  `roslaunch turtlebot3_teleop turtlebot3_teleop_key.launch`,
  `roslaunch turtlebot3_slam turtlebot3_slam.launch slam_methods:=gmapping`, `rosrun map_server map_saver -f ~/map`,
  `roslaunch turtlebot3_navigation turtlebot3_navigation.launch map_file:=$HOME/map.yaml`.
  Launch dosyaları `TURTLEBOT3_MODEL` ister; slam ve navigasyon `turtlebot3_bringup` paketine bağlı.
- Farklar (sitenin örnek robotu <-> Waffle):
  - Lidar: 3 lidar + birleştirici <-> tek LDS: `/scan`, çerçeve `base_scan`, 360 ışın, menzil 0,12–3,5 m. Birleştirici gerekmez.
  - Gövde çerçevesi: `base_link` <-> `base_footprint` (AMCL ve costmap ayarlarında bu ad kullanılır).
  - Kamera: `/camera/image_raw` <-> `/camera/rgb/image_raw` (çerçeve `camera_rgb_optical_frame`). IMU: `/imu/data` <-> `/imu`.
  - Boyut/hız (waffle): tekerlekler arası 0,287 m, tekerlek çapı 0,066 m; DWA `max_vel_x` 0,26 m/s, `max_vel_theta` 1,82 rad/s;
    costmap footprint yaklaşık 0,28 x 0,31 m, `inflation_radius` 1,0. Sitedeki örnek navigasyon sayılarını Waffle'a kopyalama; kendi param dosyaları var (`turtlebot3_navigation/param/`).
  - Uygulanabilir site tarifleri: haritalama, navigasyon, waypoint görevi. Uygulanamaz: 3 lidar birleştirme, renkli şerit docking (dünya yok).
    `twist_mux` için TurtleBot3'ün teleop'u doğrudan `/cmd_vel` yayınlar, remap gerekir.

## Test dosyaları
- `_src/tests/`: `drive_test.py` (sürüş doğruluğu), `map_route.py` (haritalama rotası; ortam değişkenleri `V`, `W`), `pgm2png.py` (haritayı PNG'ye çevirir).
  Bunlar geçici test klasörüne göre yazıldı; yolları uyarlamak gerekebilir.
- Geçici çalışma klasörleri (silinebilir): `/tmp/claude-1000/.../scratchpad/rt2` ve `.../tb3`.
- Test için açılan roscore (port 11396), Gazebo, gmapping ve rota kapatıldı. Sisteme hiçbir paket kurulmadı.
