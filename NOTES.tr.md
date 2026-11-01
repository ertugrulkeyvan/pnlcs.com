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

`[data-stat]` öğeleri: yıldız, fork, açık issue, son sürüm ve Docker indirme tarayıcıda shields.io JSON'dan (CORS açık,
ziyaretçi sınırı yok); katkıcı sayısı + duvar GitHub contributors API'den (anonim sınır saatte 60 istek / IP, artık sayfa başına 1).
HTML'deki yedek değerler elle yazılmaz: `build.py` her derlemede shields.io'dan çeker ve `data/stats.json`'a yazar; ağ yoksa
(ya da `--offline`) o dosyadaki son değerler kullanılır. 2026-10-12'de canlı sitede 59 yıldız görünmesinin sebebi buydu:
testler kullanıcının IP'sinin GitHub hakkını bitirmişti ve yedek değer 29 Eylül'den kalmaydı.

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

## Tarayıcı diline göre açılış (2026-10-12)

İngilizce (kök) sayfalarda `<head>`'in en başındaki küçük betik (`build.py` → `lang_redirect`): ziyaretçi siteye dışarıdan geldiyse ve
tarayıcı dili sitedeki 9 dilden biriyse `/<dil>/aynı-sayfa`'ya geçer (pt → pt-br; zh-TW/HK geleneksel Çince olduğu için geçmez).
Dil menüsünden seçilen dil `localStorage` → `pnlcs-lang` olarak hatırlanır ve her zaman kazanır; site içi tıklamalar yönlendirmez.

## Paylaşım görselleri ve yazı tipleri (2026-10-12)

- `python3 tools/og.py` (Pillow + Mac sistem yazı tipleri; ru/zh/ja için Arial Narrow / Hiragino Sans GB) → `assets/og/<dil>/<sayfa>.jpg`,
  kayıt ve yayıncı sayfaları için `assets/og/x/`. Yalnız başlığı/açıklaması değişenleri yeniden çizer (`assets/og/stamps.json`); `--all` hepsini.
  **Sayfa başlığı ya da açıklaması değişince ve yeni kayıt birleşince çalıştırıp commit et.** Görsel yoksa build ürün ekran görüntüsünü kullanır.
- Yazı tipleri artık siteden: `assets/fonts/` (Archivo değişken, JetBrains Mono; OFL lisans dosyaları yanında). Google Fonts bağlantısı ve
  gizlilik sayfasındaki "Google Fonts" satırı kaldırıldı.

## Açık işler

- [ ] Ekibe sun; geri bildirim.
- [x] Vitrindeki ikahost ve ENA Hosting metinleri onaylandı (2026-10-12); `draft` işareti kaldırıldı.
- [x] og:image: her sayfa ve dil için 1200×630 görsel (2026-10-12), yukarıda.
- [ ] Tema önizlemesi şematik; ileride her temanın gerçek ekran görüntüsü.
- [x] Yayın (2026-10-15): site artık kendi sunucumuzda (srv1.pratix.ai), statik. `main`'e push yayınlamaz;
  yeni sürüm: karar → `python3 build.py` → `site/` içeriği sunucuya kopyalanır. Yayındaki sürüm şu an 8b4a1a9.

Eski tek sayfalık ilk taslak: `../.playwright-mcp/eski-tek-sayfa/` (karşılaştırma için).

## Ölçüm, çerez onayı ve ücretli kurulum CTA'sı (2026-10-06)

- **GTM** (`GTM-MDCZNJKP`) `src/layout.html` içinde. Önünde Consent Mode v2 varsayılanı: her şey `denied`.
  Bant `partials/consent.html`, tercih `localStorage` → `pnlcs-consent`. Seçim yapılınca `dataLayer`'a
  `{event: 'consent_update', consent_status: 'granted'|'denied'}` gider (Meta Pixel / Clarity tetikleyicisi bu).
  Footer'daki "Cookie settings" bandı yeniden açar. GA, Clarity, Meta Pixel siteye değil GTM'e eklenir.
- **"Start a hosting company"**: PNLCS geliştiricilerinden **ücretli** kurulum, ilk görüşme ücretsiz.
  Sayfa `start-a-hosting-company.html`; bant `partials/offer.html`, sayfaya `{{offer}}` yazınca çıkar
  (ana sayfa, shared-hosting, docker-apps, vps, get-started). Menü: Resources → Start; footer: Solutions.
- **Ön görüşme formu** Web3Forms'a gider (anahtar `build.py` → `WEB3FORMS_KEY`, herkese açık olması normal).
  Başarılı gönderimde `dataLayer` → `discovery_form_submit`. CTA'larda `data-cta` (offer-band, page-intro, menu, footer, discovery-submit …).
- **Gizlilik politikası** `privacy.html`, veri sorumlusu Panelica, LLC. Hukuki metin: ekip/avukat okumalı.
- Not: `sync_i18n.py` tr `get-started.html`'de `<code>index.php</code>` sonrasına boşluk ekliyor; senkron sonrası kontrol et.

## Modüller ve temalar dizini (2026-10-06, marketplace düzeni 2026-10-12)

- Kayıtlar `data/extensions.json`'dan (PR ile), isteğe bağlı yayıncı bilgisi `data/publishers.json`'dan. Alanlar README "List a module or theme".
- Üç tür üretilen sayfa, hepsi `build.py` içinde Python ile yazılır (çevrilmiş şablon dosyası yok, metinler `strings.json` → `ext_*`):
  `extensions.html` (gezinme), `module-<slug>.html` / `theme-<slug>.html` (kayıt), `publisher-<ad>.html` (yayıncı).
  `src/**/pages/extensions.html` yalnız front matter + `{{extensions_page}}`.
- Header'da üst seviye link (Ürün menüsündeki kopya kaldırıldı). Yer açmak için GitHub yazısı kalktı (ikon + yıldız kaldı), menü
  boşlukları daraldı, "Başlarken" 1101–1300px arası gizli, GitHub linki 1101–1180px arası gizli. 9 dil × 1116–1460px ölçüldü, taşma yok.
- Filtre sırası: tür, fiyat, kategori, kaynak kod, yayıncı. Tür, fiyat ve kaynak kod hep tam görünür (0 olan seçenek gri, seçilemez);
  kategori ve yayıncıda 0 olan gösterilmez. Üstteki sayaçlar "8 Kayıt | 8 Modül" diye bölmeli kutu; 0 olan sayaç gösterilmez.
- Uyarı metni: ekip kaydın bilgilerini kontrol eder (PR'ı birleştiren yönetici), kodu test etmez/desteklemez. Eski "incelemez" ifadesi
  PR inceleme adımıyla çelişiyordu.
- Duyuru şeridi ve "son güncelleme" başlığı: `src/i18n/<dil>/releases.json` (changelog slug → çeviri). Yeni sürüm notu gelip çevirisi
  eklenmezse çevrili sayfalar "<tarih> sürüm notları" yazar, İngilizce başlık göstermez.
- Görseller: her kartın üstünde kapak alanı var. Sıra: `assets/extensions/<slug>-cover.webp` (2:1) → ilk ekran görüntüsü →
  slug'dan üretilen desen (`ext_pattern`, WordPress.org'un üretilmiş banner'ları gibi; temada sahte sayfa çizimi). Telefonda
  üretilmiş desen kartta gizlenir. Kayıt sayfasında kapak galerinin başında tam genişlikte; desen her zaman başlığın sağ arka planında.
- Filtre paneli masaüstünde iç kaydırma yapmaz: ekrana sığıyorsa yapışkan (site.js `is-sticky`), sığmıyorsa sayfayla kayar. Mobil çekmece kendi içinde kayar.
- Resmî 16 tema "Hazır Temalar" adını aldı (menü, footer, themes.html başlığı, 9 dil) ki üst menüdeki topluluk kataloğuyla karışmasın; katalogdaki Temalar grubunun başlığında ona link var.
- Sayfa yolu: `crumbs: short` front matter'ı "Ana sayfa / Sayfa" verir (üst menüdeki sayfalar için).
- Filtre yokken uzun grup ilk 9 modül / 6 temayı gösterir, altında "Tümünü gör (n)" türü seçer.
- Kayıt sayfasında "… sitesinden edinin" kutusu hero'nun sağında (ilk ekranda); yan sütunda yayıncı kartı ve uyarı.
- Gezinme sayfası: büyük arama kutusu (`/` kısayolu), kategori çipleri, solda filtreler (tür, kategori, fiyat, açık kaynak, yayıncı;
  sayısı 0 olan seçenek gösterilmez), sıralama, kaldırılabilir filtre etiketleri. Filtreler adres satırına yazılır (`?q=&type=&cat=&price=&pub=&open=&sort=`),
  paylaşılabilir. Modüller ve temalar ayrı gruplarda (tema kartı görselli). Dar ekranda filtreler yandan açılan panel.
  JS'siz her kart görünür; JS yalnız gizler/sıralar (`site.js` → "Modules and themes").
- Kayıt sayfası: başlık, galeri (büyütme penceresi, ok tuşları), genel bakış, özellikler, ayrıntılar; sağda "{yayıncı} sitesinden edinin"
  düğmesi + demo/belge/destek/kaynak bağlantıları, yayıncı kartı, uyarı, sorun bildir (GitHub issue). Altta "yayıncıdan diğerleri" ve "benzer kayıtlar".
- Her yerde "Community-built, not official"; satış yayıncının sitesinde, dış bağlantılar `rel="ugc noopener"`.
- Rozet/öne çıkarma bilerek yok (kayırma görünmesin). Varsayılan sıra "son güncellenen".
- Tarihler HTML'de `2026-10-06`, tarayıcıda ziyaretçinin dil biçimine çevrilir.
- Ölçek denemesi: `.playwright-mcp/sandbox/` (sahte 24 kayıt + 7 yayıncı; depoya girmez).
