# Océan V2 — cycle interpolé plus lent

**64 phases × 50 ms = boucle de 3,2 secondes.** L’ancien aperçu PNG avait 8 × 160 ms = 1,28 s ; le mod natif précédent utilisait 8 × 10 ticks à 60 Hz = environ 1,33 s.

Les changements arrivent plus fréquemment, mais chaque changement est plus petit et le cycle complet est plus lent. Les huit palettes d’origine sont conservées aux phases 00, 08, 16, 24, 32, 40, 48 et 56. Chaque transition reçoit huit sous-phases.

Les indices du PNG et son alpha restent strictement fixes. Seules les huit entrées cycliques de palette changent ; pas de déformation, glissement de texture, flou ou fondu entre géométries. Le raccord 63 → 00 a le même petit pas que le reste de la boucle : variation maximale de 7 niveaux RGB par canal, contre 56 auparavant.

Cadence suggérée pour une future intégration PMDO : **FrameLength 3 ticks à 60 Hz** pour chacune des 64 phases. Ce JSON ne modifie pas automatiquement le moteur : aucun mod natif n’a été changé. Les PNG ne sont pas encore assemblés en banque `.tile` avec index.

| Phase | Jour | Nuit Abyss |
|---|---|---|
| 00 | [PNG](jour_00.png) | [PNG](nuit_00.png) |
| 01 | [PNG](jour_01.png) | [PNG](nuit_01.png) |
| 02 | [PNG](jour_02.png) | [PNG](nuit_02.png) |
| 03 | [PNG](jour_03.png) | [PNG](nuit_03.png) |
| 04 | [PNG](jour_04.png) | [PNG](nuit_04.png) |
| 05 | [PNG](jour_05.png) | [PNG](nuit_05.png) |
| 06 | [PNG](jour_06.png) | [PNG](nuit_06.png) |
| 07 | [PNG](jour_07.png) | [PNG](nuit_07.png) |
| 08 | [PNG](jour_08.png) | [PNG](nuit_08.png) |
| 09 | [PNG](jour_09.png) | [PNG](nuit_09.png) |
| 10 | [PNG](jour_10.png) | [PNG](nuit_10.png) |
| 11 | [PNG](jour_11.png) | [PNG](nuit_11.png) |
| 12 | [PNG](jour_12.png) | [PNG](nuit_12.png) |
| 13 | [PNG](jour_13.png) | [PNG](nuit_13.png) |
| 14 | [PNG](jour_14.png) | [PNG](nuit_14.png) |
| 15 | [PNG](jour_15.png) | [PNG](nuit_15.png) |
| 16 | [PNG](jour_16.png) | [PNG](nuit_16.png) |
| 17 | [PNG](jour_17.png) | [PNG](nuit_17.png) |
| 18 | [PNG](jour_18.png) | [PNG](nuit_18.png) |
| 19 | [PNG](jour_19.png) | [PNG](nuit_19.png) |
| 20 | [PNG](jour_20.png) | [PNG](nuit_20.png) |
| 21 | [PNG](jour_21.png) | [PNG](nuit_21.png) |
| 22 | [PNG](jour_22.png) | [PNG](nuit_22.png) |
| 23 | [PNG](jour_23.png) | [PNG](nuit_23.png) |
| 24 | [PNG](jour_24.png) | [PNG](nuit_24.png) |
| 25 | [PNG](jour_25.png) | [PNG](nuit_25.png) |
| 26 | [PNG](jour_26.png) | [PNG](nuit_26.png) |
| 27 | [PNG](jour_27.png) | [PNG](nuit_27.png) |
| 28 | [PNG](jour_28.png) | [PNG](nuit_28.png) |
| 29 | [PNG](jour_29.png) | [PNG](nuit_29.png) |
| 30 | [PNG](jour_30.png) | [PNG](nuit_30.png) |
| 31 | [PNG](jour_31.png) | [PNG](nuit_31.png) |
| 32 | [PNG](jour_32.png) | [PNG](nuit_32.png) |
| 33 | [PNG](jour_33.png) | [PNG](nuit_33.png) |
| 34 | [PNG](jour_34.png) | [PNG](nuit_34.png) |
| 35 | [PNG](jour_35.png) | [PNG](nuit_35.png) |
| 36 | [PNG](jour_36.png) | [PNG](nuit_36.png) |
| 37 | [PNG](jour_37.png) | [PNG](nuit_37.png) |
| 38 | [PNG](jour_38.png) | [PNG](nuit_38.png) |
| 39 | [PNG](jour_39.png) | [PNG](nuit_39.png) |
| 40 | [PNG](jour_40.png) | [PNG](nuit_40.png) |
| 41 | [PNG](jour_41.png) | [PNG](nuit_41.png) |
| 42 | [PNG](jour_42.png) | [PNG](nuit_42.png) |
| 43 | [PNG](jour_43.png) | [PNG](nuit_43.png) |
| 44 | [PNG](jour_44.png) | [PNG](nuit_44.png) |
| 45 | [PNG](jour_45.png) | [PNG](nuit_45.png) |
| 46 | [PNG](jour_46.png) | [PNG](nuit_46.png) |
| 47 | [PNG](jour_47.png) | [PNG](nuit_47.png) |
| 48 | [PNG](jour_48.png) | [PNG](nuit_48.png) |
| 49 | [PNG](jour_49.png) | [PNG](nuit_49.png) |
| 50 | [PNG](jour_50.png) | [PNG](nuit_50.png) |
| 51 | [PNG](jour_51.png) | [PNG](nuit_51.png) |
| 52 | [PNG](jour_52.png) | [PNG](nuit_52.png) |
| 53 | [PNG](jour_53.png) | [PNG](nuit_53.png) |
| 54 | [PNG](jour_54.png) | [PNG](nuit_54.png) |
| 55 | [PNG](jour_55.png) | [PNG](nuit_55.png) |
| 56 | [PNG](jour_56.png) | [PNG](nuit_56.png) |
| 57 | [PNG](jour_57.png) | [PNG](nuit_57.png) |
| 58 | [PNG](jour_58.png) | [PNG](nuit_58.png) |
| 59 | [PNG](jour_59.png) | [PNG](nuit_59.png) |
| 60 | [PNG](jour_60.png) | [PNG](nuit_60.png) |
| 61 | [PNG](jour_61.png) | [PNG](nuit_61.png) |
| 62 | [PNG](jour_62.png) | [PNG](nuit_62.png) |
| 63 | [PNG](jour_63.png) | [PNG](nuit_63.png) |
