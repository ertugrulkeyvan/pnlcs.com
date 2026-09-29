# pnlcs.com yenileme teklifi

pnlcs.com Panelica ekibinin sitesi. Ekip "yapabilirsin" dedi (2026-09-28); bu klasör onlara sunulacak tasarım.
**Marka onların:** lacivert `#405189`, turkuaz nokta `#0ab39c` (themes/panelica/theme.json). ikahost renkleri burada kullanılmaz.

## Çalıştırma

```bash
cd ~/Desktop/ikahost/pnlcs/pnlcs-website
python3 build.py              # src/ → site/  (yalnız Python standart kütüphanesi)
python3 build.py --refresh    # önce CHANGELOG + temaları pnlcs kopyasından tazele (PNLCS_SRC ile yol değişir)
cd site && python3 -m http.server 8093 --bind 127.0.0.1   # → http://127.0.0.1:8093/
```
**Yayına giden klasör `site/`** — düz HTML, sunucu tarafı gerekmez. `site/` elle düzenlenmez, her derlemede silinip yeniden yazılır.

## Yapı

| | |
|---|---|
| `src/layout.html` | Her sayfanın iskeleti (head, meta, JSON-LD) |
| `src/partials/header.html` | Duyuru şeridi + ana menü (açılır menüler) — **tek yerden** |
| `src/partials/footer.html` | 5 sütunlu alt bilgi + proje durumu şeridi |
| `src/partials/cta.html` | Sayfa sonu "Own your billing stack" bandı (`cta: no` ile kapatılır) |
| `src/pages/*.html` | 14 sayfa; başta `title / description / section` bilgisi |
| `data/CHANGELOG.md` | pnlcs'in CHANGELOG'u → "What's new" sayfası ve duyuru şeridi otomatik |
| `assets/` | `site.css`, `site.js`, `themes.json`, `img/*.webp` (pnlcs `docs/screenshots`, MIT) |

Derleme ayrıca `sitemap.xml`, `robots.txt` üretir; css/js adresine içerik özeti ekler (önbellek sorunu olmasın).

## Sayfalar

| Menü | Sayfa |
|---|---|
| — | `index` ana sayfa |
| Product | `features`, `integrations`, `themes`, `compare` (WHMCS) |
| Solutions | `shared-hosting`, `docker-apps`, `vps` |
| Resources | `get-started`, `whats-new` (+ docs, API, MCP dış bağlantı) |
| Community | `community`, `showcase` (+ Discussions, Forum) |
| Project | `about`, `security` |

## Canlı veriler (tarayıcıda, yedek değer HTML'de)

`[data-stat]` öğeleri: yıldız / fork / son commit (GitHub API), son sürüm (GitHub releases), katkıcı sayısı + duvar
(contributors API), Docker indirme (shields.io JSON, CORS açık). API erişilemezse HTML'deki değer kalır.
GitHub API'nin anonim sınırı saatte 60 istek / IP — ziyaretçi başına 4 istek, sorun değil.

## Kararlar

1. **Ürün görünüyor** — açılışta 4 sekmeli gerçek ekran görüntüsü; her çözüm sayfasında ilgili görüntüler.
2. **Güven sinyalleri geri geldi** (kullanıcı istedi, 2026-09-28): teknoloji yığını + canlı proje durumu açılışta ve alt bilgide.
   Düğme hiyerarşisi: ana = Live demo, ikincil = Documentation, metin bağlantısı = GitHub / Docker / katkı.
3. **Test etiketi yok** (kullanıcı kararı, 2026-09-28) — modül başına "tested / needs testing" yazılmaz; entegrasyonlar renkli logo karolarıyla listelenir.
4. **WHMCS'ten geçiş** — "tek tık içe aktarma yok" açıkça yazıyor (docs/guides/migrate-from-whmcs.md), kademeli geçiş adımları var.
5. Sola hizalı başlıklar, AA kontrast, klavye ile menü (Esc kapatır), mobil akordeon menü, `prefers-reduced-motion`.

## AI kalıplarından arındırma (2026-09-28, kullanıcı istedi)

Rehber: `impeccable` + bağımsız metin denetimi (ajan). Bağlam dosyası: `PRODUCT.md` (kullanıcılar, ses, anti-referanslar).

- **Yazı tipi:** Instrument Sans ("refleks font" listesinde) → **Archivo** (genişlik ekseni; başlıklar dar kesim, gövde normal).
- **Kaldırılanlar:** büyük sayı + küçük etiket şeridi · renkli sol şeritler (kutular, alıntı) · her sayfada gradyanlı koyu açılış
  (iç sayfalar artık açık zemin) · 3'lü/6'lı kart ızgaraları (→ tablo, tanım listesi, bağlantı listesi) · hap şeklinde teknoloji rozetleri (→ tek cümle)
  · ana sayfadaki çözüm kartları (sekmelerle aynı şeyi söylüyordu) · ana sayfadaki karşılaştırma tablosu ve alıntı (Compare/About'ta var) · 37 ölü CSS kuralı.
- **Metin:** "X, not Y" kalıpları, kişileştirme ("invoices follow up on their own"), kanıtsız süreler ("in a minute", "tonight"),
  "biz dürüstüz" gösterisi, sahiplik sloganı tekrarı (7 → 1), uzun tire (—) yok. "Try the live demo" 34 → ana sayfa açılışı + kapanış bandı.
  Kapanış bandı Get started, What's new, Community, Showcase, Security, About'ta kapalı (`cta: no`).
- **Bilerek dokunulmayan:** Panelica ekibinin alıntısı kelimesi kelimesine korundu (About'ta). Eski başlık "The hosting billing platform
  that belongs to everyone" ekibin kendi cümlesi; yerine somut başlık kondu, ekip isterse geri alınabilir.
- Tema açıklamaları (`themes.json`) pnlcs'in kendi verisi, olduğu gibi gösteriliyor.

## Diller (9): en, es, de, fr, pt-br, tr, ru, zh, ja

İngilizce kök dizinde, diğerleri `/<kod>/` altında. Çeviriler `src/i18n/<kod>/` (sayfalar, partial'lar, `strings.json`).
Akış: İngilizceyi değiştir → `python3 tools/sync_i18n.py` (eski çevirileri taşır, eksikleri `tools/i18n-missing.json`'a yazar)
→ eksikleri doldur → `python3 tools/sync_i18n.py --apply <dolu.json>` → `python3 tools/check_i18n.py` (CI de çalıştırır).

## Sonradan eklenenler (2026-09-29)

- Mega menüler (ikonlu), dil seçici en sağda (SVG bayraklar), ana sayfada katkıcı duvarı ve showcase karuseli (dolma çubuğu, oklar, otomatik geçiş).
- Showcase: firmalar `data/showcase.json`'a PR atar (ikahost, ENA Hosting).
- Get started: Docker'sız kurulum (`#server`) — Ubuntu 24.04, Debian 13, AlmaLinux 9 / Rocky 9 sekmeleri; komutlar pnlcs
  `docs/install/native.md`'den (81f96c7). Kopyala-yapıştır güvenli olsun diye `.env` `pn sed` ile, cron `crontab -l | … | crontab -` ile, Nginx `tee` ile yazılıyor.

## Kaynaktan doğrulanan her sayı (pnlcs 4717255)

30 dil · 16 tema · 7 sunucu modülü + Custom · 8 ödeme · 6 kayıt firması + Manual · GoGetSSL · 4 Addon · 27 rapor ·
171 API işlemi · 45+ yetki · 2.232 çeviri anahtarı · MCP 15 okuma + 7 yazma aracı · 95/98 uygulama logosu ·
güvenlik süreleri SECURITY.md'den. Hosting araçları **yalnız Panelica modülüyle**. Docker komutları README'den birebir.
Bütün docs.pnlcs.com bağlantıları 200 döndü (2026-09-28).

## Açık işler

- [ ] Ekibe sun; geri bildirim.
- [ ] Vitrindeki ikahost (taslak) ve ENA Hosting metinleri — firmaların onayı.
- [ ] og:image için 1200×630 özel görsel (şimdilik ürün ekran görüntüsü).
- [ ] Tema önizlemesi şematik; ileride her temanın gerçek ekran görüntüsü.
- [ ] Ekip siteyi nasıl yayınlıyor — `site/` klasörü mü, kendi araçları mı.

Eski tek sayfalık ilk taslak: `../.playwright-mcp/eski-tek-sayfa/` (karşılaştırma için).
