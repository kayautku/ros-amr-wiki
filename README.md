# ROS AMR Wiki

ROS 1 Noetic ve otonom mobil robotlar (AMR) için Türkçe, çok sayfalı, tamamen çevrimdışı çalışan, wiki.ros.org tarzı bir bilgi sitesi. wiki.ros.org'un zaman zaman erişilemez olmasına karşı Türkçe bir alternatif olarak; kavram ve öğretici sayfalarının yanında gerçek ROS paketlerinin (AMCL, move_base, costmap_2d, gmapping, map_server, tf, actionlib, twist_mux, ira_laser_tools, DWA, TEB) kaynak kodundan çıkarılmış tam parametre referansını içerir ("C · Paket referansı" bölümü).

Öğretici sayfalar belirli bir robota bağlı değildir; kod parçalarında temsili `myrobot_*` paket adları ve `~/catkin_ws` kullanılır. Tek bir somut robot örneği ayrı bir sayfadadır ("E · Örnek robot", geliştirme aşamasında; dosyaları `examples/` altında).

## Açmak

`index.html` dosyasına çift tıkla (tarayıcıda açılır). İnternet gerekmez: yazı tipleri ve diyagram kütüphanesi (Mermaid) `assets/` içinde.

İstersen küçük bir yerel sunucuyla da açabilirsin:

```bash
cd ~/ros-amr-wiki
python3 -m http.server 8000      # sonra tarayıcıda http://localhost:8000
```

## Sayfalar

| Dosya | İçerik |
|---|---|
| `index.html` | Genel bakış ve büyük resim |
| `yol-haritasi.html` | Öğrenme yol haritası (8 aşama) |
| `zihin-haritasi.html` | Açılır kapanır zihin haritası |
| `baslarken.html` | Kurulum, ROS nedir, node ve master |
| `iletisim.html` | Topic, servis, action, parametre |
| `yapi-ve-araclar.html` | Launch, catkin, TF, komut satırı araçları |
| `robot-ve-simulasyon.html` | Proje yapısı, URDF/xacro, Gazebo, sensörler |
| `harita-ve-navigasyon.html` | SLAM, AMCL, move_base |
| `gorev-ve-docking.html` | Görev katmanı, docking, twist_mux |
| `smach.html` | Durum makinesi (SMACH) rehberi: durumlar, userdata, smach_ros durumları, kapsayıcılar, izleme/kapatma ve test edilmiş tam görev örneği |
| `ref-amcl-move-base.html` | **Paket referansı:** AMCL (52) ve move_base (17 + toparlanma davranışları 6+5) parametrelerinin tamamı |
| `ref-costmap.html` | **Paket referansı:** costmap_2d + 4 katmanının (static/obstacle/inflation/voxel) tamamı |
| `planlayici-parametreleri.html` | **Paket referansı:** DWA ve TEB parametrelerinin tamamı |
| `ref-slam-harita.html` | **Paket referansı:** gmapping (37) ve map_server parametrelerinin tamamı |
| `ref-tf-actionlib.html` | **Paket referansı:** tf/tf2 araçları, REP-105/103, actionlib (GoalStatus, SimpleActionClient) |
| `ref-yardimci-paketler.html` | **Paket referansı:** twist_mux ve ira_laser_tools parametrelerinin tamamı |
| `pratik.html` | Çalıştırma tarifleri, rosbag, gerçek robot, hata ayıklama |
| `referans.html` | Sözlük ve önerilen dosya düzeni |
| `ornek-robot.html` | **Geliştiriliyor:** üç lidarlı depo AMR'ının URDF'i, simülasyonu, navigasyon ayarları ve yapılacaklar listesi (`examples/`) |

Sitede arama: sol üstteki kutu (kısayol: `/`). Tema: sol alttaki düğme (Sistem / Açık / Koyu).

## Düzenlemek

`*.html` dosyaları **üretilir**; elle düzenleme, bir sonraki üretimde silinir. Kaynak dosyalar `_src/` altındadır:

- `_src/pages/<sayfa>.html`: sayfanın içeriği (bölümler `<section id="...">` ile).
- `_src/gen_planner_params.py`: DWA/TEB parametre sayfasını `_src/data/planner_params.json` verisinden üretir.
- `_src/gen_nav_reference.py`: AMCL/move_base, costmap_2d, gmapping/map_server, twist_mux/ira_laser_tools sayfalarını `_src/data/nav_stack_verified.json` verisinden üretir. `ref-tf-actionlib.html` bu ikisinin dışında, doğrudan elle yazıldı (tablo yerine çoğunlukla kavramsal içerik).
- `_src/verify_params.py`: parametre verisini kurulu paketlerin kaynak koduna ve `dynamic_reconfigure` tanımlarına karşı doğrular (bkz. aşağıda).
- `_src/build.py`: ortak menü, önceki/sonraki bağlantıları ve arama dizinini ekleyip sayfaları üretir. **Her zaman en son çalıştırılır.**
- `assets/style.css`, `assets/site.js`: ortak stil ve betik (elle düzenlenir).

Paket referansı sayfalarını üreten script'ler, her tabloyu `_src/data/*.json`'daki ham listeye karşı denetler: JSON'da olmayan bir parametre adı yazarsan ya da JSON'daki bir parametreyi açıklamayı unutursan script hata verip durur. Bu, sayfa ile JSON arasında tutarsızlığı önler; JSON'un kendisinin doğruluğunu ise `verify_params.py` denetler (aşağıda). Veriyi güncellemek için önce JSON'u (kaynak koddan ya da kurulu paketin `dynamic_reconfigure` tanımından) güncelle, sonra `verify_params.py`'yi, ardından ilgili `gen_*.py`'yi çalıştır.

### Parametre verisini doğrulamak

```bash
source /opt/ros/noetic/setup.bash
python3 _src/verify_params.py            # ilk çalıştırmada kaynak dosyaları indirir (internet gerekir)
python3 _src/verify_params.py --yenile   # paketler güncellendiyse kaynağı yeniden indir
```

Betik, bu makinede **kurulu** paketlerin sürümünü okur (`/opt/ros/noetic/share/<paket>/package.xml`), GitHub'dan o sürümün etiketli kaynak dosyalarını `_src/.kaynak_onbellek/` altına indirir ve şunları denetler:

1. JSON'daki her parametre kaynak kodda gerçekten okunuyor mu, varsayılanı aynı mı; kaynakta okunup referansta olmayan parametre var mı.
2. Varsayılan ve aralıklar kurulu `dynamic_reconfigure` tanımlarıyla aynı mı; planlayıcı sayfasında "yalnızca YAML" işaretli bir parametre aslında canlı değiştirilebiliyor mu.
3. DWA/TEB ek (cfg dışı) parametrelerinin varsayılanları ve gerçekten okunup okunmadığı.
4. Sayfalardaki önemli uyarıların dayandığı davranışlar hâlâ geçerli mi (varsayılan toparlanma listesi, `clear_costmap_recovery` katman adı, `rotate_recovery` isim alanı, twist_mux'ın sıfır hız yayınlamaması, TEB `map_frame`'in ezilmesi, DWA `acc_lim_trans`'ın kullanılmaması vb.).

Çıkış kodu 0: sorun yok; 1: fark var (her fark satır satır yazılır); 2: ROS ortamı yok ya da kaynak indirilemedi. Paketler güncellendikten sonra `--yenile` ile çalıştır; 4. bölümde bir davranış değiştiyse ilgili sayfadaki açıklamayı da gözden geçir. Bilinçli istisnalar (hesaplanan varsayılanlar, kapsam dışı dahili parametreler) betiğin başındaki `HESAPLANAN`, `KAPSAM_DISI` ve `CFG_FARKI_BEKLENEN` tablolarındadır. Açıklama metinlerinin anlamı otomatik denetlenemez.

Bir içeriği değiştirmek için `_src/pages/` altındaki ilgili dosyayı düzenle, sonra (paket referansı sayfalarından biriyse önce ilgili `gen_*.py`'yi, sonuçta her zaman):

```bash
python3 _src/build.py
```

Bölümler arası bağlantıları `href="#bolum-id"` biçiminde yaz; build hangi sayfada olduğunu kendisi bulup doğru adrese çevirir (aynı kural, zihin haritasının `<script>` içindeki `'#bolum-id'` JS dizgilerinde de geçerli).

### Yeni sayfa eklemek (ör. ROS 2)

1. `_src/pages/ros2.html` oluştur; içine `<section id="ros2-giris"><h2>…</h2>…</section>` bölümlerini yaz.
2. `_src/build.py` içindeki `PAGES` listesine bir satır ekle: `("ros2", "E · ROS 2", "ROS 2'ye geçiş", "ROS 2'ye geçiş")`.
3. `python3 _src/build.py` çalıştır. Menü, arama ve önceki/sonraki bağlantıları otomatik güncellenir.

### Yeni bir paket referans sayfası eklemek

1. Parametreleri **kaynak koddan** çıkar (GitHub'da `noetic-devel` dalı, `nh.param(...)`/`private_nh.param(...)` çağrıları) ya da kurulu paketin `dynamic_reconfigure` tanımından (`/opt/ros/noetic/lib/python3/dist-packages/<paket>/cfg/*Config.py`). wiki.ros.org bot korumasına takılabildiği için birincil kaynak olarak güvenme.
2. Ham veriyi `_src/data/nav_stack_verified.json`'a (ya da yeni bir JSON dosyasına) `[ad, tür, varsayılan, min, max]` biçiminde ekle.
3. `_src/gen_nav_reference.py`'ye (ya da yeni bir `gen_*.py`'ye) Türkçe açıklamalarla bir grup ekle; `table()` fonksiyonu JSON'a karşı otomatik denetler.
4. `_src/build.py`'nin `PAGES` listesine ekle, ardından `python3 _src/build.py` çalıştır.

## Üçüncü taraf dosyalar

- `assets/mermaid.min.js`: Mermaid 10.9.3 (MIT lisansı), diyagram çizimi için.
- `assets/fonts/`: IBM Plex Sans ve IBM Plex Mono (SIL Open Font License 1.1); yalnızca latin ve latin-ext altkümeleri.
