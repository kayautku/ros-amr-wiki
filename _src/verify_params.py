#!/usr/bin/env python3
"""Paket referansı verisini (_src/data/*.json) gerçek ROS paketlerine karşı doğrular.

Kullanım:
    source /opt/ros/noetic/setup.bash
    python3 _src/verify_params.py            # önbellekteki kaynakla (yoksa indirir)
    python3 _src/verify_params.py --yenile   # kaynak dosyaları yeniden indir

Ne denetlenir:
  1. Kaynak kod: JSON'daki her parametre adı, KURULU sürümün etiketli kaynak kodunda
     gerçekten okunuyor mu ve varsayılanı koddakiyle aynı mı (param(), getParam() +
     yedek atama, loadParameterWithDeprecation, teb_config.h kurucu değerleri).
  2. dynamic_reconfigure: varsayılan / min / max, kurulu cfg modülleriyle aynı mı;
     cfg'deki her parametre JSON'da var mı; "yalnızca YAML" sayılanlar gerçekten cfg dışı mı.
  3. Bugüne kadar bulunmuş kritik davranışlar hâlâ geçerli mi (toparlanma listesi,
     clear_costmap katman adı, rotate_recovery isim alanı, twist_mux sıfır hız yayınlamaması,
     TEB map_frame ezilmesi, DWA acc_lim_trans kullanılmaması). Sürüm yükseltilince
     bunlardan biri değişirse sayfadaki açıklama da gözden geçirilmelidir.

Açıklama metinlerinin (Türkçe özetlerin) anlamı otomatik denetlenemez; bu araç ad, tür,
varsayılan, aralık ve yukarıdaki davranışları denetler.

Çıkış kodu: 0 = sorun yok, 1 = beklenmeyen fark var, 2 = kaynak indirilemedi / ROS yok.
"""
import argparse
import importlib
import json
import math
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "_src" / "data"
CACHE = ROOT / "_src" / ".kaynak_onbellek"
SHARE = Path("/opt/ros/noetic/share")

# depo, sürümü okunacak kurulu paket (yoksa dal), indirilecek dosyalar
REPOS = {
    "navigation": ("ros-planning/navigation", "move_base", "noetic-devel", [
        "amcl/src/amcl_node.cpp", "amcl/src/amcl/sensors/amcl_laser.cpp", "amcl/src/amcl/pf/pf.c",
        "move_base/src/move_base.cpp", "rotate_recovery/src/rotate_recovery.cpp",
        "clear_costmap_recovery/src/clear_costmap_recovery.cpp",
        "costmap_2d/src/costmap_2d_ros.cpp", "costmap_2d/src/footprint.cpp",
        "costmap_2d/plugins/static_layer.cpp", "costmap_2d/plugins/obstacle_layer.cpp",
        "costmap_2d/plugins/voxel_layer.cpp", "costmap_2d/plugins/inflation_layer.cpp",
        "map_server/src/main.cpp",
        "dwa_local_planner/src/dwa_planner.cpp", "dwa_local_planner/src/dwa_planner_ros.cpp",
        "base_local_planner/src/latched_stop_rotate_controller.cpp",
        "base_local_planner/src/simple_trajectory_generator.cpp",
    ]),
    "slam_gmapping": ("ros-perception/slam_gmapping", "gmapping", "melodic-devel", ["gmapping/src/slam_gmapping.cpp"]),
    "teb": ("rst-tu-dortmund/teb_local_planner", "teb_local_planner", "noetic-devel", [
        "src/teb_config.cpp", "src/teb_local_planner_ros.cpp", "include/teb_local_planner/teb_config.h"]),
    "ira": ("iralabdisco/ira_laser_tools", "ira_laser_tools", "ros1-master", ["src/laserscan_multi_merger.cpp"]),
    "twist_mux": ("ros-teleop/twist_mux", "twist_mux", "noetic-devel", [
        "src/twist_mux.cpp", "include/twist_mux/topic_handle.h"]),
}

# Kaynaktan otomatik okunamayan (hesaplanan) varsayılanlar: JSON'da beklenen değer ve gerekçe.
HESAPLANAN = {
    ("amcl", "initial_pose_x"): (0.0, "init_pose_[0] = 0.0"),
    ("amcl", "initial_pose_y"): (0.0, "init_pose_[1] = 0.0"),
    ("amcl", "initial_pose_a"): (0.0, "init_pose_[2] = 0.0"),
    ("amcl", "initial_cov_xx"): (0.25, "0.5 * 0.5"),
    ("amcl", "initial_cov_yy"): (0.25, "0.5 * 0.5"),
    ("amcl", "initial_cov_aa"): (0.0685, "(M_PI/12)^2"),
    ("amcl", "update_min_a"): (0.5236, "M_PI/6"),
    ("move_base", "clearing_radius"): (None, "circumscribed_radius_"),
    ("move_base", "recovery_behaviors"): (None, "ayrıca DAVRANIS denetiminde"),
    ("clear_costmap_recovery", "layer_names"): (None, "ayrıca DAVRANIS denetiminde"),
    ("gmapping", "maxRange"): (None, "ilk taramanın range_max - 0.01'i"),
    ("gmapping", "maxUrange"): (None, "maxRange"),
    ("gmapping", "tf_delay"): (None, "transform_publish_period"),
    ("obstacle_layer", "track_unknown_space"): (None, "layered_costmap_->isTrackingUnknown()"),
    ("obstacle_layer_source", "topic"): (None, "kaynak adı"),
    ("costmap_2d_common", "footprint"): (None, "footprint.cpp: boş liste"),
    ("costmap_2d_common", "robot_radius"): (None, "cfg varsayılanı (footprint.cpp yedeği 1.234)"),
    ("costmap_2d_common", "plugins"): (None, "verilmezse Hydro öncesi düzen"),
}
# Kaynakta okunan ama referansa bilerek alınmayan adlar (dahili, eski ya da başka paketin parametresi).
KAPSAM_DISI = {
    "amcl": {"beam_skip_error_threshold_"},                      # eski yazım, geriye uyumluluk
    "move_base": {"global_costmap/robot_base_frame", "global_costmap/global_frame",
                  "local_costmap/inscribed_radius", "local_costmap/circumscribed_radius"},  # costmap'ten okunur
    "costmap_2d_common": {"footprint_topic", "published_footprint_topic", "static_map", "map_type",
                          "observation_sources"},                # dahili / Hydro öncesi
    "obstacle_layer_source": {"track_unknown_space", "transform_tolerance", "observation_sources",
                              "obstacle_range", "raytrace_range"},  # katman düzeyinde listelenir
    "voxel_layer": {"track_unknown_space", "transform_tolerance", "observation_sources", "topic", "sensor_frame",
                    "observation_persistence", "expected_update_rate", "data_type", "min_obstacle_height",
                    "max_obstacle_height", "inf_is_valid", "clearing", "marking", "obstacle_range",
                    "raytrace_range"},                            # obstacle_layer ile ortak, orada listelenir
}
KAPSAM_DISI["obstacle_layer"] = {"topic", "sensor_frame", "observation_persistence", "expected_update_rate",
                                 "data_type", "inf_is_valid", "clearing", "marking"}  # kaynak düzeyinde listelenir
# Kaynak koddaki varsayılanın cfg varsayılanından bilinçli olarak farklı olduğu yerler:
# node ilk dynamic_reconfigure çağrısını yok sayar, kaynak kod varsayılanı geçerlidir.
CFG_FARKI_BEKLENEN = {("amcl", "recovery_alpha_slow"), ("amcl", "recovery_alpha_fast"),
                      ("move_base", "controller_patience")}


class Rapor:
    def __init__(self):
        self.hata, self.uyari, self.ok = [], [], 0

    def h(self, msg):
        self.hata.append(msg)

    def u(self, msg):
        self.uyari.append(msg)


# ------------------------------------------------------------------ kaynak indirme
def surum(pkg):
    f = SHARE / pkg / "package.xml"
    if not f.exists():
        return None
    m = re.search(r"<version>([^<]+)</version>", f.read_text())
    return m.group(1).strip() if m else None


def kaynaklari_getir(yenile):
    yollar = {}
    for key, (repo, pkg, dal, files) in REPOS.items():
        ref = surum(pkg) or dal
        hedef = CACHE / f"{key}-{ref}"
        for f in files:
            dosya = hedef / f
            if yenile or not dosya.exists():
                url = f"https://raw.githubusercontent.com/{repo}/{ref}/{f}"
                try:
                    veri = urllib.request.urlopen(url, timeout=20).read()
                except Exception as e:
                    print(f"  ! indirilemedi: {url} ({e})")
                    if not dosya.exists():
                        return None, None
                    continue
                dosya.parent.mkdir(parents=True, exist_ok=True)
                dosya.write_bytes(veri)
            yollar[Path(f).name] = dosya
        print(f"  {key:14s} {repo} @ {ref}" + ("" if surum(pkg) else "  (paket kurulu değil, dal kullanıldı)"))
    return yollar, True


# ------------------------------------------------------------------ kaynak çözümleme
def argumanlar(s):
    out, derin, cur, q = [], 0, "", False
    for ch in s:
        if ch == '"':
            q = not q
        if not q:
            if ch in "([{":
                derin += 1
            elif ch in ")]}":
                derin -= 1
            elif ch == "," and derin == 0:
                out.append(cur.strip())
                cur = ""
                continue
        cur += ch
    out.append(cur.strip())
    return out


def cagrilar(txt, fonk):
    """fonk( ... ) çağrılarının argüman listeleri."""
    txt = re.sub(r"//[^\n]*", "", txt)
    for m in re.finditer(r"\b(?:%s)\s*(?:<[^>(]*>)?\s*\(" % fonk, txt):
        i = j = m.end()
        derin = 1
        while j < len(txt) and derin:
            derin += {"(": 1, ")": -1}.get(txt[j], 0)
            j += 1
        yield argumanlar(txt[i:j - 1])


def kaynak_varsayilanlari(txt, sabitler=None):
    """ad -> varsayılan ifadesi (metin). Birden çok biçimi tanır."""
    d = {}
    for a in cagrilar(txt, "param"):
        if a and a[0].startswith('"') and len(a) >= 3:
            d.setdefault(a[0].strip('"'), a[2])
        elif a and a[0].startswith('"') and len(a) == 2:
            d.setdefault(a[0].strip('"'), None)
    for a in cagrilar(txt, "loadParameterWithDeprecation"):
        if len(a) >= 4:
            d.setdefault(a[1].strip('"'), a[3])
    # if(!nh.getParam("x", var)) var = DEĞER;
    for m in re.finditer(r'getParam\(\s*"([^"]+)"\s*,\s*([\w.]+)\s*\)\s*\)\s*\n?\s*\2\s*=\s*([^;]+);', txt):
        d.setdefault(m.group(1), m.group(3))
    for a in cagrilar(txt, "getParam|hasParam|searchParam"):
        if a and a[0].startswith('"'):
            d.setdefault(a[0].strip('"'), None)
    # double obstacle_range = 2.5; if (source_node.searchParam("obstacle_range", ...
    for m in re.finditer(r'double\s+(\w+)\s*=\s*([-\d.]+);\s*\n\s*if\s*\(\s*\w+\.searchParam\(\s*"\1"', txt):
        d[m.group(1)] = m.group(2)
    if sabitler:
        for k, v in list(d.items()):
            if v and re.fullmatch(r"[\w.]+", v.strip()) and v.split(".")[-1] in sabitler:
                d[k] = sabitler[v.split(".")[-1]]
    return d


def deger(ifade):
    """C++ varsayılan ifadesini Python değerine çevirir; olmazsa None."""
    if ifade is None:
        return None
    e = ifade.strip()
    e = re.sub(r'std::string\(\s*("[^"]*")\s*\)', r"\1", e)
    e = re.sub(r"\b(?:int|double)\((.+)\)$", r"\1", e)
    e = e.replace("M_PI", str(math.pi)).replace("true", "True").replace("false", "False")
    e = re.sub(r"(\d)f\b", r"\1", e)
    try:
        return eval(e, {"__builtins__": {}})
    except Exception:
        return None


def esit(a, b):
    if isinstance(a, bool) or isinstance(b, bool):
        return bool(a) == bool(b)
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        if math.isinf(a) or math.isinf(b):
            return a == b
        return abs(a - b) <= 1e-4 * max(1.0, abs(a), abs(b))
    return str(a).strip('"') == str(b).strip('"')


# ------------------------------------------------------------------ 1) kaynak kod
def denetle_kaynak(r, K, D):
    oku = lambda *fs: "\n".join(K[f].read_text(errors="replace") for f in fs)
    kaynaklar = {
        "amcl": oku("amcl_node.cpp"),
        "move_base": oku("move_base.cpp"),
        "rotate_recovery": oku("rotate_recovery.cpp"),
        "clear_costmap_recovery": oku("clear_costmap_recovery.cpp"),
        "costmap_2d_common": oku("costmap_2d_ros.cpp", "footprint.cpp"),
        "static_layer": oku("static_layer.cpp"),
        "obstacle_layer": oku("obstacle_layer.cpp"),
        "obstacle_layer_source": oku("obstacle_layer.cpp"),
        "voxel_layer": oku("voxel_layer.cpp"),
        "gmapping": oku("slam_gmapping.cpp"),
        "map_server": oku("main.cpp"),
        "ira_laser_tools": oku("laserscan_multi_merger.cpp"),
    }
    for key, txt in kaynaklar.items():
        src = kaynak_varsayilanlari(txt)
        for row in D[key]:
            ad, varsayilan = row[0], row[2]
            kod_adi = ad.split("/")[-1]
            if (key, ad) in HESAPLANAN:
                beklenen = HESAPLANAN[(key, ad)][0]
                if beklenen is not None and not esit(varsayilan, beklenen):
                    r.h(f"{key}/{ad}: JSON={varsayilan}, beklenen {beklenen} ({HESAPLANAN[(key, ad)][1]})")
                else:
                    r.ok += 1
                continue
            if kod_adi not in src:
                # cfg'den gelen parametreler 2. adımda denetlenir
                if key in ("costmap_2d_common", "obstacle_layer", "voxel_layer"):
                    continue
                r.h(f"{key}/{ad}: kaynak kodda okunmuyor")
                continue
            v = deger(src[kod_adi])
            if src[kod_adi] is None:
                r.ok += 1
            elif v is None:
                r.u(f"{key}/{ad}: kaynak varsayılanı çözümlenemedi ({src[kod_adi]}); JSON={varsayilan}")
            elif not esit(varsayilan, v):
                r.h(f"{key}/{ad}: JSON varsayılanı {varsayilan}, kaynakta {src[kod_adi]}")
            else:
                r.ok += 1
        # ters yön: kaynakta okunan her ad JSON'da (ya da bilinçli kapsam dışında) olmalı
        json_adlari = {row[0].split("/")[-1] for row in D[key]}
        disarida = KAPSAM_DISI.get(key, set())
        for ad in src:
            if ad not in json_adlari and ad not in disarida:
                r.h(f"{key}/{ad}: kaynakta okunuyor ama referansta yok")
    # twist_mux: alan adları ve öncelik sınırı
    tm = oku("twist_mux.cpp", "topic_handle.h")
    for alan, *_ in D["twist_mux"]["topic_alanlari"]:
        if f'"{alan}"' not in tm:
            r.h(f"twist_mux: '{alan}' alanı kaynakta okunmuyor")
        else:
            r.ok += 1
    if "priority_type(255)" not in tm:
        r.h("twist_mux: öncelik sınırı 0–255 kaynakta bulunamadı")


# ------------------------------------------------------------------ 2) dynamic_reconfigure
def cfg(mod):
    def duz(g):
        o = list(g["parameters"])
        for s in g.get("groups", []):
            o += duz(s)
        return o
    return {p["name"]: p for p in duz(importlib.import_module(mod).config_description)}


def sonlu(v):
    return v is not None and not (isinstance(v, float) and math.isinf(v)) and abs(v) < 1e9


def denetle_cfg(r, D, P):
    ciftler = [("amcl", "amcl.cfg.AMCLConfig"), ("move_base", "move_base.cfg.MoveBaseConfig"),
               ("costmap_2d_common", "costmap_2d.cfg.Costmap2DConfig"),
               ("inflation_layer", "costmap_2d.cfg.InflationPluginConfig"),
               ("obstacle_layer", "costmap_2d.cfg.ObstaclePluginConfig"),
               ("voxel_layer", "costmap_2d.cfg.VoxelPluginConfig")]
    for key, mod in ciftler:
        c = cfg(mod)
        satir = {x[0]: x for x in D[key]}
        for ad, p in c.items():
            if ad in ("restore_defaults",):
                continue
            if ad not in satir:
                r.h(f"{key}/{ad}: dynamic_reconfigure'da var, JSON'da yok")
                continue
            _, tur, v, lo, hi = satir[ad]
            if not esit(v, p["default"]) and (key, ad) not in CFG_FARKI_BEKLENEN:
                r.h(f"{key}/{ad}: varsayılan JSON={v}, cfg={p['default']}")
            if p["type"] not in ("str", "bool"):
                for etiket, j, cv in (("min", lo, p["min"]), ("max", hi, p["max"])):
                    beklenen = cv if sonlu(cv) else None
                    if not ((j is None and beklenen is None) or (j is not None and beklenen is not None and esit(j, beklenen))):
                        r.h(f"{key}/{ad}: {etiket} JSON={j}, cfg={cv}")
            r.ok += 1
    for key, mod in [("dwa", "dwa_local_planner.cfg.DWAPlannerConfig"),
                     ("teb", "teb_local_planner.cfg.TebLocalPlannerReconfigureConfig")]:
        c = cfg(mod)
        satir = {x["name"]: x for x in P[key]}
        for ad, p in c.items():
            if ad == "restore_defaults":
                continue
            if ad not in satir:
                r.h(f"{key}/{ad}: dynamic_reconfigure'da var, planner_params.json'da yok (sayfada 'yalnızca YAML' görünür)")
                continue
            x = satir[ad]
            for etiket in ("default", "min", "max"):
                if p["type"] in ("str", "bool") and etiket != "default":
                    continue
                if not esit(x[etiket], p[etiket]):
                    r.h(f"{key}/{ad}: {etiket} JSON={x[etiket]}, cfg={p[etiket]}")
            r.ok += 1
        for ad in satir:
            if ad not in c and ad != "restore_defaults":
                r.h(f"{key}/{ad}: planner_params.json'da var, kurulu cfg'de yok")


# ------------------------------------------------------------------ 3) planlayıcı ek parametreleri
def ek_sozlukleri():
    src = (ROOT / "_src" / "gen_planner_params.py").read_text()
    ns = {"math": math}
    for ad in ("DWA_EK", "TEB_EK"):
        i = src.index(ad + " = {")
        j = src.index("\n}\n", i) + 3
        exec(src[i:j], ns)
    return ns["DWA_EK"], ns["TEB_EK"]


def denetle_ek(r, K):
    dwa_ek, teb_ek = ek_sozlukleri()
    c_teb = cfg("teb_local_planner.cfg.TebLocalPlannerReconfigureConfig")
    c_dwa = cfg("dwa_local_planner.cfg.DWAPlannerConfig")
    teb_h = K["teb_config.h"].read_text()
    teb_sabit = {}
    for m in re.finditer(r"(\w+)\s*=\s*([^;=]+);", teb_h):
        teb_sabit.setdefault(m.group(1), m.group(2))
    teb_okunan = kaynak_varsayilanlari(K["teb_config.cpp"].read_text() + K["teb_local_planner_ros.cpp"].read_text())
    for ad, (tur, v) in teb_ek.items():
        if ad in c_teb:
            r.h(f"teb/{ad}: 'yalnızca YAML' işaretli ama dynamic_reconfigure ile değiştirilebiliyor")
        if ad not in teb_okunan:
            r.h(f"teb/{ad}: kurulu sürümde parametreden okunmuyor (ayar etkisiz)")
            continue
        if ad.startswith("footprint_model/"):
            beklenen = "point" if ad.endswith("/type") else None
            yanlis = (not esit(v, beklenen)) if beklenen else (v is not None)
            if yanlis:
                r.h(f"teb/{ad}: sayfa varsayılanı {v}; kaynakta varsayılan yok (eksikse point modeline düşer)")
            else:
                r.ok += 1
            continue
        kod = teb_sabit.get(ad)
        if kod is None or deger(kod) is None:
            r.u(f"teb/{ad}: teb_config.h varsayılanı çözümlenemedi ({kod}); sayfa={v}")
        elif not esit(v, deger(kod)):
            r.h(f"teb/{ad}: sayfa varsayılanı {v}, teb_config.h'de {kod}")
        else:
            r.ok += 1
    dwa_src = kaynak_varsayilanlari(K["dwa_planner.cpp"].read_text() + K["latched_stop_rotate_controller.cpp"].read_text()
                                    + K["dwa_planner_ros.cpp"].read_text())
    for ad, (tur, v) in dwa_ek.items():
        if ad in c_dwa:
            r.h(f"dwa/{ad}: 'yalnızca YAML' işaretli ama dynamic_reconfigure ile değiştirilebiliyor")
        if ad not in dwa_src:
            r.h(f"dwa/{ad}: kaynak kodda okunmuyor")
        elif ad == "odom_topic":
            ok = 'odom_helper_("odom")' in K["dwa_planner_ros.cpp"].read_text() and v == "odom"
            if ok:
                r.ok += 1
            else:
                r.h("dwa/odom_topic: varsayılan 'odom' kaynakta doğrulanamadı")
        elif not esit(v, deger(dwa_src[ad])):
            r.h(f"dwa/{ad}: sayfa varsayılanı {v}, kaynakta {dwa_src[ad]}")
        else:
            r.ok += 1


# ------------------------------------------------------------------ 4) bilinen kritik davranışlar
def denetle_davranis(r, K, D):
    mb = K["move_base.cpp"].read_text()
    i = mb.index("void MoveBase::loadDefaultRecoveryBehaviors")
    govde = mb[i:mb.index("\n  }\n", i)]
    sira = re.findall(r'recovery_behavior_names_\.push_back\("(\w+)"\)', govde)
    json_liste = [x.strip() for x in str(next(x for x in D["move_base"] if x[0] == "recovery_behaviors")[2]).strip("[]").split(",")]
    kontroller = [
        ("move_base varsayılan toparlanma listesi", sira == json_liste, f"kaynak={sira}, JSON={json_liste}"),
        ("clear_costmap_recovery layer_names varsayılanı",
         (m := re.search(r'clearable_layers_default\.push_back\(\s*std::string\("(\w+)"\)', K["clear_costmap_recovery.cpp"].read_text()))
         and f'["{m.group(1)}"]' == next(x for x in D["clear_costmap_recovery"] if x[0] == "layer_names")[2],
         "kaynaktaki varsayılan katman adı JSON'dakinden farklı"),
        ("clear_costmap katman adı birebir eşleşme (sayfa uyarısının dayanağı)",
         "clearable_layers_.count(name)" in K["clear_costmap_recovery.cpp"].read_text(), "eşleşme biçimi değişmiş"),
        ("clear_costmap alanı: kenarı reset_distance olan kare",
         "reset_distance_ / 2" in K["clear_costmap_recovery.cpp"].read_text(), "temizleme geometrisi değişmiş"),
        ("rotate_recovery hız/ivme ayarlarını ~/TrajectoryPlannerROS'tan okur",
         '"~/TrajectoryPlannerROS"' in K["rotate_recovery.cpp"].read_text(), "isim alanı değişmiş"),
        ("twist_mux yalnızca gelen mesajda yayın yapar (zaman aşımında sıfır hız yok)",
         K["twist_mux.cpp"].read_text().count("cmd_pub_.publish") == 1 and "publishTwist(msg)" in K["topic_handle.h"].read_text(),
         "yayın mantığı değişmiş"),
        ("twist_mux: zaman aşımına uğrayan kilit etkin sayılır",
         "return hasExpired() || getMessage().data;" in K["topic_handle.h"].read_text(), "kilit mantığı değişmiş"),
        ("TEB map_frame, costmap global_frame ile eziliyor",
         "cfg_.map_frame = global_frame_" in K["teb_local_planner_ros.cpp"].read_text(), "map_frame artık ezilmiyor olabilir"),
        ("TEB costmap_converter_rate parametreden okunmuyor",
         '"costmap_converter_rate"' not in K["teb_config.cpp"].read_text(), "artık okunuyor; sayfaya geri eklenmeli"),
        ("DWA acc_lim_trans yörünge üretiminde kullanılmıyor",
         "acc_lim_trans" not in K["simple_trajectory_generator.cpp"].read_text(), "artık kullanılıyor; sayfa notu düzeltilmeli"),
        ("AMCL beam skip yalnızca yakınsamış filtrede",
         "do_beamskip && !set->converged" in K["amcl_laser.cpp"].read_text(), "beam skip koşulu değişmiş"),
        ("map_server YAML'da mode verilmezse trinary",
         "assuming Trinary" in K["main.cpp"].read_text(), "mode varsayılanı değişmiş"),
        ("AMCL/move_base ilk dynamic_reconfigure çağrısını yok sayar (kaynak varsayılanı geçerli)",
         "first_reconfigure_call_" in K["amcl_node.cpp"].read_text() and "if(!setup_)" in mb,
         "cfg varsayılanları artık geçerli olabilir; CFG_FARKI_BEKLENEN'i gözden geçir"),
    ]
    for ad, ok, neden in kontroller:
        if ok:
            r.ok += 1
        else:
            r.h(f"DAVRANIŞ: {ad}: {neden}")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--yenile", action="store_true", help="kaynak dosyaları yeniden indir")
    a = ap.parse_args()
    try:
        importlib.import_module("amcl.cfg.AMCLConfig")
    except ImportError:
        print("ROS ortamı yüklü değil: önce 'source /opt/ros/noetic/setup.bash'")
        return 2
    print("Kaynak kod (kurulu sürümlerin etiketleri):")
    K, ok = kaynaklari_getir(a.yenile)
    if not ok:
        print("Kaynak indirilemedi ve önbellekte yok; internet bağlantısını kontrol et.")
        return 2
    D = json.loads((DATA / "nav_stack_verified.json").read_text(encoding="utf-8"))
    P = json.loads((DATA / "planner_params.json").read_text(encoding="utf-8"))
    r = Rapor()
    for baslik, f in [("1) Kaynak kod: ad ve varsayılan", lambda: denetle_kaynak(r, K, D)),
                      ("2) dynamic_reconfigure: varsayılan ve aralık", lambda: denetle_cfg(r, D, P)),
                      ("3) Planlayıcı ek parametreleri", lambda: denetle_ek(r, K)),
                      ("4) Bilinen kritik davranışlar", lambda: denetle_davranis(r, K, D))]:
        once = (len(r.hata), len(r.uyari))
        f()
        print(f"{baslik}: {len(r.hata) - once[0]} hata, {len(r.uyari) - once[1]} uyarı")
    for m in r.uyari:
        print("  uyarı:", m)
    for m in r.hata:
        print("  HATA :", m)
    print(f"\nToplam: {r.ok} denetim geçti, {len(r.hata)} hata, {len(r.uyari)} uyarı.")
    return 1 if r.hata else 0


if __name__ == "__main__":
    sys.exit(main())
