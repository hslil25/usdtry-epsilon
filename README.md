# Epsilon Tracker: USD/TRY

## 🔗 [hslil25.github.io/usdtry-epsilon](https://hslil25.github.io/usdtry-epsilon/)

**USD/TRY vadeli işlem primlerini CIP (Faiz Oranı Paritesi) bileşenine ve artık ε'a (devalüasyon primine) ayrıştıran canlı analiz aracı.**

## Ne Yapar?

VIOP'ta işlem gören USD/TRY vadeli sözleşmelerinin piyasa fiyatlarını çekerek her vade için iki temel soruyu yanıtlar:

- **CIP fiyatı nedir?** → Türkiye ve ABD faiz farkından teorik olarak beklenen kur
- **ε nedir?** → Piyasa fiyatı ile CIP fiyatı arasındaki fark (piyasanın "ekstra" fiyatladığı devalüasyon baskısı)

| ε sinyali | Anlam |
|---|---|
| Compression | Piyasa CIP'in altında; carry trade baskısı |
| Neutral | CIP ile uyumlu |
| Break Premium | Piyasa CIP'in üzerinde; kur baskısı var |
| Acute Stress | Ciddi ayrışma; yüksek devalüasyon beklentisi |

## Veri Kaynakları

- **VIOP sözleşmeleri** — borsapy (canlı)
- **Spot kur & 7 günlük geçmiş** — yfinance (USDTRY=X)
- **ABD faizi** — FRED FEDFUNDS API
- **TR faizi** — `.env` ile manuel (R_TRY)
