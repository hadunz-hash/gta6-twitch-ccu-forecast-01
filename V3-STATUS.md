# GTA6 make.fun — v3 SIAP SUBMIT (parent: bundle + submit)

## Commit baru
- (lihat git log — commit v3 di origin/main)
- Repo: https://github.com/hadunz-hash/gta6-twitch-ccu-forecast-01
- v2 yang sudah scored: submission 01a1ef03-d9e3-713c-b55a-9facfb254a86 (commit c13b0c9)

## Yang diubah (2 langkah edit terpisah di main.py — syarat thinking_revised)
1. **Edit 1 — window + blend per-jam:** HI_SHARE 0.75 → 0.90 (menambah
   tepat 1 launch ke training set: Cyberpunk 2077, share 0.797, hour-1
   852k — analog mega-launch terdekat dengan GTA VI); BLEND_W 0.5 flat
   → BLEND_EARLY 0.2 / BLEND_LATE 0.8 (regresi paling bisa dipercaya di
   jam-jam akhir, saat efek skala paling kuat).
2. **Edit 2 — spread:** SPREAD_LATE 1.4 → 1.2 (spread 1.2/1.2); dengan
   window lebih lebar + blend akhir lebih kuat, spread 1.4 over-widen.

## Angka LOO pinball (kode shipped, work_cv12.py)
- Target day-building C (n=12): **v3 0.1883 vs v2 0.1993 (-5,5%)**,
  baseline persistence 0.2755.
- Target eligible A (n=12): **v3 0.2512 vs v2 0.2856 (-12,0%)**,
  baseline 0.2566 (v3 kini MENGALAHKAN baseline di A — v2 tidak).
- Per-target terbesar (set A): ELDEN RING 0.228 → 0.144, Cyberpunk 2077
  0.278 → 0.243, Starfield 0.462 → 0.408, Borderlands 4 0.447 → 0.374,
  TLOU2 0.274 → 0.186. Satu-satunya kemunduran besar: Monster Hunter
  Wilds 0.364 → 0.404 (polanya melawan regresi; sudah begitu sejak v2).
- Ronde sweep (work_cv13/14/15/16.py): blend weight flat 0.3-0.8, spread
  1.0/1.2 s.d. 1.4/1.6 + ramp, slope shrinkage 0.3-0.7, kernel-weighted
  quantiles bw 0.5-1.5, window (0.15,0.8)/(0.25,0.7)/(0.2,1.0)/(0.3,0.75),
  asym spread 4 arah, winsor 0.90/0.95. Yang DITOLAK di v3: semua di atas
  kecuali kombinasi pemenang; kernel membantu A tapi merugikan C;
  window (0.2,1.0) merusak C (0.210); winsor & shrinkage merugikan
  keduanya. Catatan kehati-hatian: gain C tidak merata per-target (4 dari
  12 target C membaik, 8 sedikit memburuk) — tapi 3 kemenangan besar
  (Borderlands, TLOU2, Yōtei) mendominasi, dan gain di A merata di
  launch-launch besar yang paling mirip GTA VI.

## Uji lokal v3 (4 practice cases p00–p03)
- Deterministik (2 run identik byte-per-byte), 23 jam × 5 kuantil valid,
  non-decreasing, > 0; ~0.29 dtk untuk 4 case (batas 8 dtk/case); stdlib
  only, offline.
- Median v3 vs v2 di p00: rata-rata |log ratio| 0.187, maks 0.345 —
  median sore ditarik turun oleh blend regresi yang lebih kuat (sesuai
  desain: mega launch tumbuh lebih pelan).

## Submit ulang (parent)
- Bundle harus mencakup sesi ini (edit v3) + sesi v2 (0b5e888b) seperti
  pola v2; prompt.txt sudah berisi kata-kata Steven "Gas, ikut GTA6";
  system-prompt.txt sudah ada.
- Submit dengan commit v3 yang baru.
- Kuota: v2 pakai 1 submit hari ini (total dipakai 18 Nov: repo refusal 1
  + v1 1 + v2 1 = 3); sisa ~7 untuk lomba ini hari ini. Deadline keras:
  2026-11-19T01:00:00Z (08:00 WIB 19 Nov).
- Claim code v2 (AF-NJZ8W...) sudah tidak berlaku untuk v3 — submission
  baru akan dapat claim code baru; simpan ke claim-code-gta6.txt (0600).
